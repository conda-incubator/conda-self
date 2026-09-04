from __future__ import annotations

import json
import signal
import sys
import traceback
from contextlib import redirect_stdout
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from conda import CondaError, CondaMultiError
from conda.base.constants import PREFIX_FROZEN_FILE
from conda.base.context import context as conda_context
from conda.cli.main_list import print_explicit
from conda.exceptions import CondaHTTPError, CondaSignalInterrupt, ParseError
from conda.models.channel import Channel
from conda.models.enums import NoarchType
from conda.models.records import PackageRecord

from conda_self.cli.main_reset import Snapshot
from conda_self.constants import (
    RESET_FILE_BASE_PROTECTION,
    RESET_FILE_INSTALLER,
)
from conda_self.testing import conda_cli_subprocess, is_installed

if TYPE_CHECKING:
    from pathlib import Path

    from conda.testing.fixtures import CondaCLIFixture, TmpEnvFixture
    from pytest import MonkeyPatch


MD5 = "0" * 32
SHA256 = "a" * 64
INSTALLER_SNAPSHOT_CONTENT = (
    "# platform: linux-64\n"
    "@EXPLICIT\n"
    "https://conda.anaconda.org/conda-forge/linux-64/"
    f"mamba-1.5.3-py311h3072747_1.conda#{MD5}\n"
    "https://conda.anaconda.org/conda-forge/linux-64/"
    f"pip-24.0-pyhd8ed1ab_0.conda#{MD5}\n"
)


class FakeRecord:
    def __init__(self, name: str):
        self.name = name


def make_package_record(
    name: str,
    *,
    version: str = "1.0",
    build: str = "0",
    channel: str = "https://packages.example.test/conda-forge",
    url: str | None = None,
    subdir: str = "linux-64",
    md5: str = MD5,
    sha256: str = SHA256,
    noarch: NoarchType | None = None,
) -> PackageRecord:
    filename = f"{name}-{version}-{build}.conda"
    return PackageRecord(
        name=name,
        version=version,
        build=build,
        build_number=0,
        channel=Channel(channel),
        subdir=subdir,
        fn=filename,
        url=url or f"{channel}/{subdir}/{filename}",
        md5=md5,
        sha256=sha256,
        depends=(),
        noarch=noarch,
    )


def explicit_entry(record: PackageRecord, checksum: str = "sha256") -> str:
    digest = getattr(record, checksum)
    prefix = "sha256:" if checksum == "sha256" else ""
    return f"{record.url}#{prefix}{digest}"


@pytest.fixture
def reset_calls():
    return []


@pytest.fixture
def perm_deps_calls():
    return []


@pytest.fixture
def fake_reset_env(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    reset_calls: list,
    perm_deps_calls: list,
):
    conda_meta = tmp_path / "conda-meta"
    conda_meta.mkdir()
    monkeypatch.setattr(sys, "prefix", str(tmp_path))

    def fake_reset(**kwargs):
        reset_calls.append(kwargs)

    def fake_perm_deps(**kwargs):
        perm_deps_calls.append(kwargs)
        return {"conda", "conda-self"}

    monkeypatch.setattr("conda.base.context.context.quiet", True, raising=False)
    monkeypatch.setattr("conda_self.reset.reset", fake_reset)
    monkeypatch.setattr("conda_self.query.permanent_dependencies", fake_perm_deps)
    return tmp_path


@pytest.fixture
def fake_reset_output_env(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
):
    conda_meta = tmp_path / "conda-meta"
    conda_meta.mkdir()
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    monkeypatch.setattr("conda_self.reset.reset", lambda **kwargs: None)
    monkeypatch.setattr(
        "conda_self.query.permanent_dependencies", lambda **kwargs: {"conda"}
    )
    (conda_meta / RESET_FILE_INSTALLER).write_text(INSTALLER_SNAPSHOT_CONTENT)
    (conda_meta / RESET_FILE_BASE_PROTECTION).write_text(INSTALLER_SNAPSHOT_CONTENT)
    return tmp_path


@pytest.fixture
def stub_transaction(monkeypatch: MonkeyPatch):
    """Stub ``conda_self.reset.reset``'s disk dependencies.

    Returns a dict that, after ``reset()`` runs, is populated with the kwargs
    that would have been passed to ``PrefixSetup`` (``unlink_precs`` /
    ``link_precs`` in particular). Tests seed ``captured["installed"]`` with
    a list of ``FakeRecord`` instances to drive ``PrefixData.iter_records``.
    """
    captured: dict = {}

    class StubPrefixData:
        def __init__(self, *args, **kwargs):
            pass

        def iter_records(self):
            return iter(captured.get("installed", []))

    def stub_prefix_setup(**kwargs):
        captured.update(kwargs)
        return object()

    class StubTxn:
        def __init__(self, stp):
            pass

        def print_transaction_summary(self):
            pass

        def execute(self):
            pass

    monkeypatch.setattr("conda_self.reset.PrefixData", StubPrefixData)
    monkeypatch.setattr("conda_self.reset.PrefixSetup", stub_prefix_setup)
    monkeypatch.setattr("conda_self.reset.UnlinkLinkTransaction", StubTxn)
    return captured


@pytest.fixture
def snapshot_reset(monkeypatch: MonkeyPatch):
    captured: dict = {"installed": [], "fetched": []}

    class StubPrefixData:
        def __init__(self, *args, **kwargs):
            pass

        def get(self, name, default=None):
            return next(
                (record for record in captured["installed"] if record.name == name),
                default,
            )

        def query(self, spec):
            return (record for record in captured["installed"] if spec.match(record))

    def stub_fetch(entries):
        captured["fetch_entries"] = tuple(entries)
        if error := captured.get("fetch_error"):
            raise error
        return captured["fetched"]

    def stub_diff(
        prefix,
        final_precs,
        specs_to_add=(),
        force_reinstall=False,
    ):
        captured["diff"] = {
            "prefix": prefix,
            "final_precs": tuple(final_precs),
            "specs_to_add": tuple(specs_to_add),
            "force_reinstall": force_reinstall,
        }
        return (), ()

    monkeypatch.setattr("conda_self.reset.PrefixData", StubPrefixData)
    monkeypatch.setattr(
        "conda_self.reset.get_package_records_from_explicit", stub_fetch
    )
    monkeypatch.setattr("conda_self.reset.diff_for_unlink_link_precs", stub_diff)
    return captured


@pytest.mark.parametrize(
    "entry",
    [
        (
            "https://user:password@packages.example.test/t/tk-secret/linux-64/"
            "demo-1.0-0.conda?X-Amz-Credential=signed-secret#invalid"
        ),
        (
            "https://user:password@packages.example.test/t/tk-secret/linux-64/"
            f"demo-^signedsecret-0.conda#{SHA256}"
        ),
    ],
    ids=["checksum", "filename"],
)
def test_reset_snapshot_hides_invalid_explicit_entry(entry: str, tmp_path: Path):
    from conda_self.reset import reset

    snapshot = tmp_path / "snapshot.explicit.txt"
    snapshot.write_text(f"@EXPLICIT\n{entry}\n")

    with pytest.raises(ParseError) as exc_info:
        reset(prefix="/target", snapshot=snapshot)

    outputs = (
        str(exc_info.value),
        "".join(traceback.format_exception(exc_info.value)),
    )
    assert outputs[0] == "Could not parse a package URL in the snapshot."
    for secret in (
        "user:password",
        "tk-secret",
        "X-Amz-Credential",
        "signed-secret",
        "signedsecret",
        SHA256,
    ):
        assert all(secret not in output for output in outputs)


def test_reset_snapshot_reuses_installed_record_without_fetching(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
):
    from conda_self.reset import reset

    prefix = tmp_path / "prefix"
    conda_meta = prefix / "conda-meta"
    conda_meta.mkdir(parents=True)
    installed = make_package_record(
        "removed-upstream",
        channel="https://dead.example.test/conda-forge",
    )
    extra = make_package_record("extra")
    for record in (installed, extra):
        record_path = conda_meta / f"{record.name}-{record.version}-0.json"
        record_path.write_text(json.dumps(record.dump()))
    snapshot = tmp_path / "snapshot.explicit.txt"
    snapshot.write_text(f"@EXPLICIT\n{explicit_entry(installed)}\n")
    captured = {}

    def fail_fetch(entries):
        pytest.fail(f"unexpected fetch: {entries}")

    monkeypatch.setattr(
        "conda_self.reset.get_package_records_from_explicit", fail_fetch
    )

    def stub_prefix_setup(**kwargs):
        captured.update(kwargs)
        return object()

    class StubTxn:
        def __init__(self, stp):
            pass

        def print_transaction_summary(self):
            pass

        def execute(self):
            pass

    monkeypatch.setattr("conda_self.reset.PrefixSetup", stub_prefix_setup)
    monkeypatch.setattr("conda_self.reset.UnlinkLinkTransaction", StubTxn)

    reset(prefix=str(prefix), snapshot=snapshot)

    assert tuple(record.name for record in captured["unlink_precs"]) == ("extra",)
    assert captured["link_precs"] == ()


def test_reset_snapshot_fetches_only_missing_records_and_preserves_order(
    snapshot_reset: dict,
    tmp_path: Path,
):
    from conda_self.reset import reset

    missing_first = make_package_record("missing-first")
    installed = make_package_record("already-installed")
    missing_last = make_package_record("missing-last")
    entries = tuple(
        explicit_entry(record) for record in (missing_first, installed, missing_last)
    )
    snapshot = tmp_path / "snapshot.explicit.txt"
    snapshot.write_text("@EXPLICIT\n" + "\n".join(entries) + "\n")
    snapshot_reset["installed"] = [installed]
    snapshot_reset["fetched"] = [missing_first, missing_last]

    reset(prefix="/target", snapshot=snapshot)

    assert snapshot_reset["fetch_entries"] == (entries[0], entries[2])
    assert snapshot_reset["diff"]["final_precs"] == (
        missing_first,
        installed,
        missing_last,
    )
    assert tuple(spec.name for spec in snapshot_reset["diff"]["specs_to_add"]) == (
        "missing-first",
        "missing-last",
    )


@pytest.mark.parametrize("mismatch", ["checksum", "url"])
def test_reset_snapshot_reinstalls_same_package_for_url_or_checksum_mismatch(
    mismatch: str,
    snapshot_reset: dict,
    tmp_path: Path,
):
    from conda_self.reset import reset

    target = make_package_record("demo")
    if mismatch == "checksum":
        installed = make_package_record("demo", sha256="b" * 64)
    else:
        installed = make_package_record(
            "demo",
            url="https://mirror.example.test/linux-64/demo-1.0-0.conda",
        )
    assert installed == target

    snapshot = tmp_path / "snapshot.explicit.txt"
    snapshot.write_text(f"@EXPLICIT\n{explicit_entry(target)}\n")
    snapshot_reset["installed"] = [installed]
    snapshot_reset["fetched"] = [target]

    reset(prefix="/target", snapshot=snapshot)

    force_specs = snapshot_reset["diff"]["specs_to_add"]
    assert len(force_specs) == 1
    assert force_specs[0].match(target)
    assert not force_specs[0].match(installed)
    assert snapshot_reset["diff"]["force_reinstall"] is True
    assert snapshot_reset["diff"]["final_precs"] == (target,)


def test_reset_snapshot_download_error_reports_safe_context(
    snapshot_reset: dict,
    tmp_path: Path,
):
    from conda_self.reset import reset

    unavailable = make_package_record(
        "unavailable",
        url=(
            "https://user:password@bad%q.invalid/t/tk-secret/linux-64/"
            "unavailable-1.0-0.conda"
        ),
    )
    snapshot = tmp_path / "snapshot.explicit.txt"
    snapshot.write_text(f"@EXPLICIT\n{explicit_entry(unavailable)}\n")
    snapshot_reset["fetch_error"] = CondaMultiError(
        (
            CondaHTTPError(
                "server%body-secret",
                f"{unavailable.url}?X-Amz-Credential=signed-secret",
                404,
                "reason%secret",
                "-",
            ),
        )
    )

    with pytest.raises(CondaError) as exc_info:
        reset(prefix="/target", snapshot=snapshot)

    outputs = (
        str(exc_info.value),
        repr(exc_info.value.dump_map()),
        "".join(traceback.format_exception(exc_info.value)),
    )
    assert outputs[0] == (
        "Could not download or extract all packages required by the selected "
        "snapshot.\n"
        "Required packages:\n"
        "  - unavailable-1.0-0.conda\n"
        "The target environment was not changed, but the package cache may "
        "contain packages downloaded and extracted before the failure. Ensure "
        "the required package files are available from the URLs recorded in the "
        "snapshot and match any recorded checksums, or place matching package "
        "files in a configured package cache, then retry."
    )
    assert all("unavailable-1.0-0.conda" in output for output in outputs)
    for secret in (
        "user:password",
        "tk-secret",
        "X-Amz-Credential",
        "signed-secret",
        "server%body-secret",
        "reason%secret",
    ):
        assert all(secret not in output for output in outputs)
    assert "diff" not in snapshot_reset


@pytest.mark.parametrize(
    "nested_error",
    [RuntimeError("unexpected failure"), CondaSignalInterrupt(signal.SIGINT)],
    ids=["unexpected", "interrupt"],
)
def test_reset_snapshot_preserves_interrupt_or_unexpected_error(
    nested_error: BaseException,
    snapshot_reset: dict,
    tmp_path: Path,
):
    from conda_self.reset import reset

    package = make_package_record("missing")
    snapshot = tmp_path / "snapshot.explicit.txt"
    snapshot.write_text(f"@EXPLICIT\n{explicit_entry(package)}\n")
    error = CondaMultiError((CondaMultiError((nested_error,)),))
    snapshot_reset["fetch_error"] = error

    with pytest.raises(CondaMultiError) as exc_info:
        reset(prefix="/target", snapshot=snapshot)

    assert exc_info.value is error
    assert "diff" not in snapshot_reset


@pytest.mark.parametrize(
    "json_output, quiet",
    [(True, False), (False, True)],
    ids=["json", "quiet"],
)
def test_reset_snapshot_noop_suppresses_human_output(
    json_output: bool,
    quiet: bool,
    snapshot_reset: dict,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from conda_self.reset import reset

    package = make_package_record("installed")
    snapshot = tmp_path / "snapshot.explicit.txt"
    snapshot.write_text(f"@EXPLICIT\n{explicit_entry(package)}\n")
    snapshot_reset["installed"] = [package]
    monkeypatch.setattr(
        "conda_self.reset.context",
        SimpleNamespace(
            json=json_output,
            quiet=quiet,
            plugin_manager=conda_context.plugin_manager,
        ),
    )

    reset(prefix="/target", snapshot=snapshot)

    assert capsys.readouterr().out == ""


def test_reset_snapshot_fetches_noarch_python_package_for_python_relink(
    snapshot_reset: dict,
    tmp_path: Path,
):
    from conda_self.reset import reset

    installed_python = make_package_record("python", version="3.12.9")
    target_python = make_package_record("python", version="3.13.2")
    installed_noarch = make_package_record(
        "pip",
        version="25.0",
        subdir="noarch",
        noarch=NoarchType.python,
    )
    fetched_noarch = make_package_record(
        "pip",
        version="25.0",
        subdir="noarch",
        noarch=NoarchType.python,
    )
    installed_native = make_package_record("zlib")
    records = (installed_noarch, installed_native, target_python)
    entries = tuple(explicit_entry(record) for record in records)
    snapshot = tmp_path / "snapshot.explicit.txt"
    snapshot.write_text("@EXPLICIT\n" + "\n".join(entries) + "\n")
    snapshot_reset["installed"] = [
        installed_python,
        installed_noarch,
        installed_native,
    ]
    snapshot_reset["fetched"] = [fetched_noarch, target_python]

    reset(prefix="/target", snapshot=snapshot)

    assert snapshot_reset["fetch_entries"] == (entries[0], entries[2])
    assert snapshot_reset["diff"]["final_precs"] == (
        fetched_noarch,
        installed_native,
        target_python,
    )
    assert tuple(spec.name for spec in snapshot_reset["diff"]["specs_to_add"]) == (
        "pip",
        "python",
    )


def test_help(conda_cli: CondaCLIFixture):
    out, err, exc = conda_cli("self", "reset", "--help", raises=SystemExit)
    assert exc.value.code == 0


@pytest.mark.parametrize("snapshot", [snapshot.value for snapshot in Snapshot])
def test_reset_json_output(
    snapshot: str,
    conda_cli: CondaCLIFixture,
    fake_reset_output_env: Path,
):
    out, _err, _exc = conda_cli(
        "self", "reset", "--yes", "--json", "--snapshot", snapshot
    )

    assert json.loads(out) == {"success": True}


def test_reset_quiet_output(
    conda_cli: CondaCLIFixture,
    fake_reset_output_env: Path,
):
    out, _err, _exc = conda_cli(
        "self", "reset", "--yes", "--quiet", "--snapshot", "current"
    )

    assert out == ""


@pytest.mark.parametrize("choice", [s.value for s in Snapshot])
def test_help_shows_snapshot_choices(conda_cli: CondaCLIFixture, choice: str):
    out, err, exc = conda_cli("self", "reset", "--help", raises=SystemExit)
    assert choice in out


@pytest.mark.parametrize(
    "bad_value",
    ["totally-bogus", ""],
    ids=["bogus", "empty"],
)
def test_invalid_snapshot_value_rejected(conda_cli: CondaCLIFixture, bad_value: str):
    out, err, exc = conda_cli(
        "self", "reset", "--snapshot", bad_value, raises=SystemExit
    )
    assert exc.value.code != 0


@pytest.mark.parametrize(
    "snapshot_arg, expected_snapshot_file, expected_names",
    [
        ("installer", RESET_FILE_INSTALLER, None),
        ("installer-exact", RESET_FILE_INSTALLER, None),
        ("installer-updated", None, {"mamba", "pip", "conda", "conda-self"}),
        ("current", None, {"conda", "conda-self"}),
    ],
    ids=["installer", "installer-exact", "installer-updated", "current"],
)
def test_snapshot_dispatch(
    conda_cli: CondaCLIFixture,
    fake_reset_env: Path,
    reset_calls: list,
    snapshot_arg: str,
    expected_snapshot_file: str | None,
    expected_names: set[str] | None,
):
    installer_snapshot = fake_reset_env / "conda-meta" / RESET_FILE_INSTALLER
    installer_snapshot.write_text(INSTALLER_SNAPSHOT_CONTENT)

    conda_cli("self", "reset", "--yes", "--snapshot", snapshot_arg)

    assert len(reset_calls) == 1
    call = reset_calls[0]
    if expected_snapshot_file:
        assert call["snapshot"] == (
            fake_reset_env / "conda-meta" / expected_snapshot_file
        )
    else:
        assert "snapshot" not in call
    if expected_names is not None:
        assert expected_names <= call["uninstallable_packages"]


@pytest.mark.parametrize("snapshot", ["installer", "installer-exact"])
def test_installer_snapshot_missing_file_raises(
    snapshot: str,
    conda_cli: CondaCLIFixture,
    fake_reset_env: Path,
):
    conda_cli(
        "self",
        "reset",
        "--yes",
        "--snapshot",
        snapshot,
        raises=FileNotFoundError,
    )


@pytest.mark.parametrize(
    "snapshots_present, expected_snapshot_file, expected_names",
    [
        (
            ("base-protection", "installer"),
            RESET_FILE_BASE_PROTECTION,
            None,
        ),
        (
            ("installer",),
            None,
            {"mamba", "pip", "conda", "conda-self"},
        ),
        (
            (),
            None,
            {"conda", "conda-self"},
        ),
    ],
    ids=[
        "prefers-base-protection",
        "installer-updated-when-no-bp",
        "current-when-no-snapshots",
    ],
)
def test_fallback_ordering(
    conda_cli: CondaCLIFixture,
    fake_reset_env: Path,
    reset_calls: list,
    snapshots_present: tuple[str, ...],
    expected_snapshot_file: str | None,
    expected_names: set[str] | None,
):
    if "base-protection" in snapshots_present:
        bp = fake_reset_env / "conda-meta" / RESET_FILE_BASE_PROTECTION
        bp.write_text(INSTALLER_SNAPSHOT_CONTENT)
    if "installer" in snapshots_present:
        inst = fake_reset_env / "conda-meta" / RESET_FILE_INSTALLER
        inst.write_text(INSTALLER_SNAPSHOT_CONTENT)

    conda_cli("self", "reset", "--yes")

    assert len(reset_calls) == 1
    call = reset_calls[0]
    if expected_snapshot_file:
        assert call["snapshot"] == (
            fake_reset_env / "conda-meta" / expected_snapshot_file
        )
    else:
        assert "snapshot" not in call
    if expected_names is not None:
        assert expected_names <= call["uninstallable_packages"]


@pytest.mark.parametrize(
    "snapshot, expected_filename",
    [
        (Snapshot.CURRENT, None),
        (Snapshot.INSTALLER, RESET_FILE_INSTALLER),
        (Snapshot.INSTALLER_EXACT, RESET_FILE_INSTALLER),
        (Snapshot.INSTALLER_UPDATED, RESET_FILE_INSTALLER),
        (Snapshot.BASE_PROTECTION, RESET_FILE_BASE_PROTECTION),
    ],
    ids=[s.value for s in Snapshot],
)
def test_snapshot_file_path(
    snapshot: Snapshot,
    expected_filename: str | None,
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
):
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    if expected_filename is None:
        assert snapshot.file_path is None
    else:
        assert snapshot.file_path == tmp_path / "conda-meta" / expected_filename


@pytest.mark.parametrize(
    "installed_names, keep, expected_to_remove",
    [
        (
            ["conda", "conda-self", "conda-rattler-solver", "numpy", "python"],
            {
                "conda",
                "conda-self",
                "python",
                "conda-libmamba-solver",
                "pip",
                "conda-rattler-solver",
            },
            ["numpy"],
        ),
        (
            [
                "conda",
                "conda-self",
                "python",
                "conda-libmamba-solver",
                "conda-rattler-solver",
                "scipy",
            ],
            {
                "conda",
                "conda-self",
                "python",
                "conda-libmamba-solver",
                "pip",
                "conda-rattler-solver",
            },
            ["scipy"],
        ),
        (
            [
                "conda",
                "conda-self",
                "python",
                "conda-libmamba-solver",
                "pip",
                "numpy",
            ],
            {
                "conda",
                "conda-self",
                "python",
                "conda-libmamba-solver",
                "pip",
                "conda-rattler-solver",
            },
            ["numpy"],
        ),
    ],
    ids=[
        "replaced-libmamba-with-rattler",
        "both-solvers-installed",
        "pristine-plus-numpy",
    ],
)
def test_reset_uninstallable_never_installs(
    stub_transaction: dict,
    installed_names: list[str],
    keep: set[str],
    expected_to_remove: list[str],
):
    from conda_self.reset import reset

    stub_transaction["installed"] = [FakeRecord(n) for n in installed_names]

    reset(prefix="/fake", uninstallable_packages=keep)

    assert sorted(r.name for r in stub_transaction["unlink_precs"]) == (
        expected_to_remove
    )
    assert list(stub_transaction["link_precs"]) == []


def test_reset(
    conda_cli: CondaCLIFixture,
    monkeypatch: MonkeyPatch,
    base_env: Path,
    conda_channel: str,
):
    monkeypatch.setenv("CONDA_CHANNELS", conda_channel)

    prefix = base_env
    conda_cli("install", "conda-index", "numpy", "--yes", "--prefix", prefix)
    assert is_installed(prefix, "conda-index")
    assert is_installed(prefix, "numpy")

    conda_cli_subprocess(prefix, "self", "reset", "--yes")
    assert is_installed(prefix, "conda")
    assert is_installed(prefix, "conda-self")
    assert is_installed(prefix, "conda-index")
    assert not is_installed(prefix, "numpy")


@pytest.mark.parametrize("add_cli_arg", (True, False), ids=("no arg", "--snapshot"))
def test_reset_base_protection(
    add_cli_arg: bool,
    conda_cli: CondaCLIFixture,
    monkeypatch: MonkeyPatch,
    tmp_env: TmpEnvFixture,
    conda_channel: str,
    python_version: str,
):
    conda_version = "26.1.0"
    monkeypatch.setenv("CONDA_CHANNELS", conda_channel)

    with tmp_env(
        f"conda={conda_version}",
        f"python={python_version}",
        "conda-self",
        "conda-index",
        # Pin libmambapy <2.6 to work around a broken pybind11-abi==11
        # variant on Windows. See conda-forge/mamba-feedstock#384.
        "libmambapy <2.6",
    ) as prefix:
        (prefix / "conda-meta" / "pinned").write_text("libmambapy <2.6\n")
        frozen_file = prefix / PREFIX_FROZEN_FILE
        protection_state = prefix / "conda-meta" / RESET_FILE_BASE_PROTECTION

        frozen_file.touch()
        with protection_state.open(mode="w") as f:
            with redirect_stdout(f):
                print_explicit(prefix)
        assert frozen_file.exists()
        assert protection_state.exists()

        assert is_installed(prefix, f"conda={conda_version}"), (
            f"conda={conda_version} not in initial environment"
        )
        assert is_installed(prefix, "conda-index")

        conda_cli_subprocess(prefix, "self", "update", "--yes")
        assert is_installed(prefix, "conda")
        assert not is_installed(prefix, f"conda={conda_version}"), "conda not updated"
        conda_cli(
            "install",
            "constructor",
            "--override-frozen",
            "--yes",
            "--prefix",
            prefix,
        )
        assert is_installed(prefix, "constructor")

        conda_cli_subprocess(
            prefix,
            "self",
            "reset",
            "--yes",
            *(("--snapshot", "base-protection") if add_cli_arg else ()),
        )
        assert is_installed(prefix, f"conda={conda_version}"), "conda not reset"
        assert is_installed(prefix, "conda-index"), "conda-index has been removed"
        assert not is_installed(prefix, "constructor")

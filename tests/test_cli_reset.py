from __future__ import annotations

import sys
from contextlib import redirect_stdout
from typing import TYPE_CHECKING

import pytest
from conda.base.constants import PREFIX_FROZEN_FILE
from conda.cli.main_list import print_explicit

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


INSTALLER_SNAPSHOT_CONTENT = (
    "# platform: linux-64\n"
    "@EXPLICIT\n"
    "https://conda.anaconda.org/conda-forge/linux-64/"
    "mamba-1.5.3-py311h3072747_1.conda#abc\n"
    "https://conda.anaconda.org/conda-forge/linux-64/"
    "pip-24.0-pyhd8ed1ab_0.conda#def\n"
)


class FakeRecord:
    def __init__(self, name: str):
        self.name = name


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


def test_help(conda_cli: CondaCLIFixture):
    out, err, exc = conda_cli("self", "reset", "--help", raises=SystemExit)
    assert exc.value.code == 0


@pytest.mark.parametrize("choice", [s.value for s in Snapshot])
def test_help_shows_snapshot_choices(conda_cli: CondaCLIFixture, choice: str):
    out, err, exc = conda_cli("self", "reset", "--help", raises=SystemExit)
    assert choice in out


@pytest.mark.parametrize(
    "bad_value",
    ["installer", "totally-bogus", ""],
    ids=["bare-installer", "bogus", "empty"],
)
def test_invalid_snapshot_value_rejected(conda_cli: CondaCLIFixture, bad_value: str):
    out, err, exc = conda_cli(
        "self", "reset", "--snapshot", bad_value, raises=SystemExit
    )
    assert exc.value.code != 0


@pytest.mark.parametrize(
    "snapshot_arg, expected_snapshot_file, expected_names",
    [
        ("installer-exact", RESET_FILE_INSTALLER, None),
        ("installer-updated", None, {"mamba", "pip", "conda", "conda-self"}),
        ("current", None, {"conda", "conda-self"}),
    ],
    ids=["installer-exact", "installer-updated", "current"],
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


def test_installer_exact_missing_file_raises(
    conda_cli: CondaCLIFixture, fake_reset_env: Path
):
    conda_cli(
        "self",
        "reset",
        "--yes",
        "--snapshot",
        "installer-exact",
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
    "snapshot, display_name",
    [
        (Snapshot.CURRENT, "current"),
        (Snapshot.INSTALLER_EXACT, "installer-provided (exact)"),
        (Snapshot.INSTALLER_UPDATED, "installer-provided (with updates)"),
        (Snapshot.BASE_PROTECTION, "base-protection"),
    ],
    ids=[s.value for s in Snapshot],
)
def test_snapshot_display_name(snapshot: Snapshot, display_name: str):
    assert snapshot.display_name == display_name


@pytest.mark.parametrize(
    "snapshot, expected_filename",
    [
        (Snapshot.CURRENT, None),
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
    ) as prefix:
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

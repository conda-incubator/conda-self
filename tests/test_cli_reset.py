from __future__ import annotations

import sys
from contextlib import redirect_stdout
from typing import TYPE_CHECKING

import pytest
from conda.base.constants import PREFIX_FROZEN_FILE
from conda.cli.main_list import print_explicit

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


def test_help(conda_cli: CondaCLIFixture):
    out, err, exc = conda_cli("self", "reset", "--help", raises=SystemExit)
    assert exc.value.code == 0


@pytest.mark.parametrize(
    "choice",
    ["installer-exact", "installer-updated"],
    ids=["installer-exact", "installer-updated"],
)
def test_help_shows_installer_choices(conda_cli: CondaCLIFixture, choice: str):
    out, err, exc = conda_cli("self", "reset", "--help", raises=SystemExit)
    assert choice in out


def test_bare_installer_rejected(conda_cli: CondaCLIFixture):
    out, err, exc = conda_cli(
        "self", "reset", "--snapshot", "installer", raises=SystemExit
    )
    assert exc.value.code != 0


def test_installer_updates_uses_names_only(
    conda_cli: CondaCLIFixture,
    fake_reset_env: Path,
    reset_calls: list,
):
    snapshot = fake_reset_env / "conda-meta" / RESET_FILE_INSTALLER
    snapshot.write_text(INSTALLER_SNAPSHOT_CONTENT)

    conda_cli("self", "reset", "--yes", "--snapshot", "installer-updated")

    assert len(reset_calls) == 1
    call = reset_calls[0]
    assert "snapshot" not in call
    keep = call["uninstallable_packages"]
    assert {"mamba", "pip", "conda", "conda-self"} <= keep


def test_installer_exact_uses_snapshot_path(
    conda_cli: CondaCLIFixture,
    fake_reset_env: Path,
    reset_calls: list,
):
    snapshot = fake_reset_env / "conda-meta" / RESET_FILE_INSTALLER
    snapshot.write_text(INSTALLER_SNAPSHOT_CONTENT)

    conda_cli("self", "reset", "--yes", "--snapshot", "installer-exact")

    assert len(reset_calls) == 1
    call = reset_calls[0]
    assert call["snapshot"] == snapshot
    assert call.get("uninstallable_packages", set()) == set()


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


def test_reset(
    conda_cli: CondaCLIFixture,
    monkeypatch: MonkeyPatch,
    tmp_env: TmpEnvFixture,
    conda_channel: str,
    python_version: str,
):
    monkeypatch.setenv("CONDA_CHANNELS", conda_channel)

    with tmp_env(
        "conda",
        "conda-self",
        f"python={python_version}",
        "conda-index",
    ) as prefix:
        assert not is_installed(prefix, "numpy")

        conda_cli("install", "numpy", "--yes", "--prefix", prefix)
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

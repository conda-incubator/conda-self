from __future__ import annotations

import os
import sys
from contextlib import redirect_stdout
from typing import TYPE_CHECKING

from conda.base.constants import PREFIX_FROZEN_FILE
from conda.cli.main_list import print_explicit

from conda_self.constants import RESET_FILE_MIGRATE
from conda_self.testing import conda_cli_subprocess, is_installed

if TYPE_CHECKING:
    from conda.testing.fixtures import CondaCLIFixture, TmpEnvFixture
    from pytest import MonkeyPatch

CONDA_CHANNEL = os.environ.get("CONDA_CHANNEL", "conda-forge")
# Ensure that the Python version is the same in all environments
# to avoid ABI incompatibilities between the python version in the
# current working directory and the test environments.
PY_VER = f"{sys.version_info.major}.{sys.version_info.minor}"


def test_help(conda_cli: CondaCLIFixture):
    out, err, exc = conda_cli("self", "reset", "--help", raises=SystemExit)
    assert exc.value.code == 0


def test_reset(
    conda_cli: CondaCLIFixture, monkeypatch: MonkeyPatch, tmp_env: TmpEnvFixture
):
    monkeypatch.setenv("CONDA_CHANNELS", CONDA_CHANNEL)

    # Adding conda-index too to test that non-default plugins are kept
    with tmp_env("conda", "conda-self", f"python={PY_VER}", "conda-index") as prefix:
        assert not is_installed(prefix, "numpy")

        conda_cli("install", "numpy", "--yes", "--prefix", prefix)
        assert is_installed(prefix, "numpy")

        conda_cli_subprocess(prefix, "self", "reset", "--yes")
        # make sure conda-self didn't remove conda
        assert is_installed(prefix, "conda")
        # make sure conda-self didn't remove itself
        assert is_installed(prefix, "conda-self")
        # make sure conda-self didn't remove a non-default conda plugin
        assert is_installed(prefix, "conda-index")
        # but numpy should be gone
        assert not is_installed(prefix, "numpy")


def test_reset_migrate(
    conda_cli: CondaCLIFixture, monkeypatch: MonkeyPatch, tmp_env: TmpEnvFixture
):
    conda_version = "25.7.0"
    monkeypatch.setenv("CONDA_CHANNELS", CONDA_CHANNEL)

    with tmp_env(f"conda={conda_version}", f"python={PY_VER}", "conda-self") as prefix:
        frozen_file = prefix / PREFIX_FROZEN_FILE
        migrate_state = prefix / "conda-meta" / RESET_FILE_MIGRATE

        # Add sentintel files of a protected environment after migration
        frozen_file.touch()
        with migrate_state.open(mode="w") as f:
            with redirect_stdout(f):
                print_explicit(prefix)
        assert frozen_file.exists()
        assert migrate_state.exists()

        assert is_installed(prefix, f"conda={conda_version}"), (
            f"conda={conda_version} not in initial environment"
        )

        # Update conda and install an unrelated package
        conda_cli_subprocess(prefix, "self", "update")
        assert is_installed(prefix, "conda")
        assert not is_installed(prefix, f"conda={conda_version}"), "conda not updated"
        conda_cli(
            "install", "constructor", "--override-frozen", "--yes", "--prefix", prefix
        )
        assert is_installed(prefix, "constructor")

        # Conda should be downgraded and constructor should be gone
        conda_cli_subprocess(prefix, "self", "reset", "--yes", "--reset-to", "migrate")
        assert is_installed(prefix, f"conda={conda_version}"), "conda not reset"
        assert not is_installed(prefix, "constructor")

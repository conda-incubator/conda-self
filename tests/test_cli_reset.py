from __future__ import annotations

from contextlib import redirect_stdout
from typing import TYPE_CHECKING

import pytest
from conda.base.constants import PREFIX_FROZEN_FILE
from conda.cli.main_list import print_explicit

from conda_self.constants import RESET_FILE_MIGRATE
from conda_self.testing import conda_cli_subprocess, is_installed

if TYPE_CHECKING:
    from conda.testing.fixtures import CondaCLIFixture, TmpEnvFixture
    from pytest import MonkeyPatch


def test_help(conda_cli: CondaCLIFixture):
    out, err, exc = conda_cli("self", "reset", "--help", raises=SystemExit)
    assert exc.value.code == 0


@pytest.mark.skipif(
    "conda-canary" in __import__("os").environ.get("TEST_CONDA_CHANNEL", ""),
    reason="Integration test skipped for canary builds due to dependency resolution",
)
def test_reset(
    conda_cli: CondaCLIFixture,
    monkeypatch: MonkeyPatch,
    tmp_env: TmpEnvFixture,
    conda_channel: str,
    python_version: str,
):
    monkeypatch.setenv("CONDA_CHANNELS", conda_channel)

    # Adding conda-index too to test that non-default plugins are kept
    with tmp_env(
        "conda", "conda-self", f"python={python_version}", "conda-index"
    ) as prefix:
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


@pytest.mark.skipif(
    "conda-canary" in __import__("os").environ.get("TEST_CONDA_CHANNEL", ""),
    reason="Integration test skipped for canary builds due to dependency resolution",
)
@pytest.mark.parametrize("add_cli_arg", (True, False), ids=("no arg", "--snapshot"))
def test_reset_migrate(
    add_cli_arg: bool,
    conda_cli: CondaCLIFixture,
    monkeypatch: MonkeyPatch,
    tmp_env: TmpEnvFixture,
    conda_channel: str,
    python_version: str,
):
    conda_version = "25.7.0"
    monkeypatch.setenv("CONDA_CHANNELS", conda_channel)

    # Adding conda-index too to test that non-default plugins are kept
    with tmp_env(
        f"conda={conda_version}",
        f"python={python_version}",
        "conda-self",
        "conda-index",
    ) as prefix:
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
        assert is_installed(prefix, "conda-index")

        # Update conda and install an unrelated package
        conda_cli_subprocess(prefix, "self", "update")
        assert is_installed(prefix, "conda")
        assert not is_installed(prefix, f"conda={conda_version}"), "conda not updated"
        conda_cli(
            "install", "constructor", "--override-frozen", "--yes", "--prefix", prefix
        )
        assert is_installed(prefix, "constructor")

        # Conda should be downgraded and constructor should be gone
        conda_cli_subprocess(
            prefix,
            "self",
            "reset",
            "--yes",
            *(("--snapshot", "migrate") if add_cli_arg else ()),
        )
        assert is_installed(prefix, f"conda={conda_version}"), "conda not reset"
        assert is_installed(prefix, "conda-index"), "conda-index has been removed"
        assert not is_installed(prefix, "constructor")

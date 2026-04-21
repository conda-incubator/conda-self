from __future__ import annotations

from contextlib import redirect_stdout
from typing import TYPE_CHECKING

import pytest
from conda.base.constants import PREFIX_FROZEN_FILE
from conda.cli.main_list import print_explicit

from conda_self.constants import RESET_FILE_BASE_PROTECTION
from conda_self.testing import conda_cli_subprocess, is_installed

if TYPE_CHECKING:
    from pathlib import Path

    from conda.testing.fixtures import CondaCLIFixture, TmpEnvFixture
    from pytest import MonkeyPatch


def test_help(conda_cli: CondaCLIFixture):
    out, err, exc = conda_cli("self", "reset", "--help", raises=SystemExit)
    assert exc.value.code == 0


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
            "install", "constructor", "--override-frozen", "--yes", "--prefix", prefix
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

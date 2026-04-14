from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from conda_self.exceptions import PluginRemoveError
from conda_self.testing import conda_cli_subprocess, is_installed

if TYPE_CHECKING:
    from pathlib import Path

    from conda.testing.fixtures import CondaCLIFixture
    from pytest import MonkeyPatch


def test_help(conda_cli):
    out, err, exc = conda_cli("self", "remove", "--help", raises=SystemExit)
    assert exc.value.code == 0


@pytest.mark.parametrize(
    "spec,error",
    (
        ("conda", PluginRemoveError),
        ("conda-libmamba-solver", PluginRemoveError),
        ("python", PluginRemoveError),
    ),
)
def test_remove_protected_plugin(conda_cli, spec, error):
    conda_cli(
        "self",
        "remove",
        spec,
        raises=error,
    )


def test_remove_unprotected_plugin_passes_validation(conda_cli):
    """Verify non-essential specs pass validation and reach the confirmation prompt."""
    conda_cli(
        "self",
        "remove",
        "--yes",
        "flask",
    )


def test_remove_nonessential_plugin(
    conda_cli: CondaCLIFixture,
    monkeypatch: MonkeyPatch,
    base_env: Path,
    conda_channel: str,
):
    monkeypatch.setenv("CONDA_CHANNELS", conda_channel)

    conda_cli("install", "conda-index", "--yes", "--prefix", base_env)
    assert is_installed(base_env, "conda-index")
    conda_cli_subprocess(
        base_env,
        "self",
        "remove",
        "--yes",
        "conda-index",
    )
    assert not is_installed(base_env, "conda-index")

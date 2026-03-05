from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from conda_self.exceptions import SpecsCanNotBeRemoved
from conda_self.testing import conda_cli_subprocess, is_installed

if TYPE_CHECKING:
    from conda.testing.fixtures import TmpEnvFixture
    from pytest import MonkeyPatch


def test_help(conda_cli):
    out, err, exc = conda_cli("self", "remove", "--help", raises=SystemExit)
    assert exc.value.code == 0


@pytest.mark.parametrize(
    "spec,error",
    (
        ("conda", SpecsCanNotBeRemoved),
        ("conda-libmamba-solver", SpecsCanNotBeRemoved),
        ("python", SpecsCanNotBeRemoved),
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
    monkeypatch: MonkeyPatch,
    tmp_env: TmpEnvFixture,
    conda_channel: str,
    python_version: str,
):
    monkeypatch.setenv("CONDA_CHANNELS", conda_channel)

    # Adding conda-index as a non-essential plug-in
    with tmp_env(
        "conda", "conda-self", f"python={python_version}", "conda-index"
    ) as prefix:
        assert is_installed(prefix, "conda-index")
        conda_cli_subprocess(
            prefix,
            "self",
            "remove",
            "--yes",
            "conda-index",
        )
        assert not is_installed(prefix, "conda-index")

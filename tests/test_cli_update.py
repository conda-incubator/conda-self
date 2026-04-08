from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from conda.exceptions import CondaValueError

from conda_self.testing import conda_cli_subprocess

if TYPE_CHECKING:
    from conda.testing.fixtures import CondaCLIFixture, TmpEnvFixture
    from pytest import MonkeyPatch


def test_help(conda_cli: CondaCLIFixture):
    out, err, exc = conda_cli("self", "update", "--help", raises=SystemExit)
    assert exc.value.code == 0


def test_update_plugin_invalid(conda_cli: CondaCLIFixture):
    conda_cli(
        "self", "update", "--plugin", "conda-fake-solver", raises=CondaValueError
    )


@pytest.mark.parametrize(
    "extra_args,expected",
    (
        pytest.param((), "conda (installed:", id="conda"),
        pytest.param(
            ("--plugin", "conda-libmamba-solver"),
            "conda-libmamba-solver (installed:",
            id="plugin",
        ),
        pytest.param(("--all",), "conda (installed:", id="all"),
        pytest.param(
            ("--all", "--force-reinstall"),
            "conda (installed:",
            id="all+force-reinstall",
        ),
    ),
)
def test_update(
    extra_args: tuple[str, ...],
    expected: str,
    monkeypatch: MonkeyPatch,
    tmp_env: TmpEnvFixture,
    conda_channel: str,
    python_version: str,
):
    monkeypatch.setenv("CONDA_CHANNELS", conda_channel)

    with tmp_env("conda", "conda-self", f"python={python_version}") as prefix:
        result = conda_cli_subprocess(
            prefix,
            "self",
            "update",
            *extra_args,
            "--dry-run",
            "--yes",
            capture_output=True,
            text=True,
        )
        assert "Updating" in result.stdout
        assert expected in result.stdout

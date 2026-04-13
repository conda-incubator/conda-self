from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest
from conda.exceptions import CondaValueError, DryRunExit

from conda_self.testing import conda_cli_subprocess, is_installed

if TYPE_CHECKING:
    from conda.testing.fixtures import CondaCLIFixture, TmpEnvFixture
    from pytest import MonkeyPatch


def test_help(conda_cli: CondaCLIFixture):
    out, err, exc = conda_cli("self", "install", "--help", raises=SystemExit)
    assert exc.value.code == 0


def test_install_plugin_dry_run(
    conda_cli: CondaCLIFixture,
    monkeypatch: MonkeyPatch,
    conda_channel: str,
):
    monkeypatch.setenv("CONDA_CHANNELS", conda_channel)
    conda_cli(
        "self", "install", "--dry-run", "conda-libmamba-solver", raises=DryRunExit
    )


@pytest.mark.parametrize(
    "spec",
    (
        pytest.param("conda-fake-solver", id="dry-run-not-found"),
        pytest.param("idontexist", id="not-found"),
    ),
)
def test_install_not_found(conda_cli: CondaCLIFixture, spec: str):
    _, _, code = conda_cli("self", "install", spec)
    assert code != 0


@pytest.mark.parametrize("plugin_name", ("flask", "numpy"))
def test_install_not_plugins(
    plugin_name: str,
    monkeypatch: MonkeyPatch,
    tmp_env: TmpEnvFixture,
    conda_channel: str,
    python_version: str,
):
    monkeypatch.setenv("CONDA_CHANNELS", conda_channel)

    with tmp_env("conda", "conda-self", f"python={python_version}") as prefix:
        # Verify the subprocess targets this prefix (install.py uses sys.prefix)
        result = conda_cli_subprocess(
            prefix, "info", "--json", capture_output=True, text=True
        )
        info = json.loads(result.stdout)
        assert info["sys.prefix"] == str(prefix)

        result = conda_cli_subprocess(
            prefix,
            "self",
            "install",
            "--yes",
            plugin_name,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "NotAPluginError" in result.stderr
        assert not is_installed(prefix, plugin_name)


@pytest.mark.parametrize(
    "spec",
    (
        "conda-forge::conda-libmamba-solver",
        "defaults::conda-libmamba-solver",
    ),
)
def test_install_channel_in_spec_rejected(conda_cli: CondaCLIFixture, spec: str):
    conda_cli("self", "install", spec, raises=CondaValueError)


def test_install_plugin(
    monkeypatch: MonkeyPatch,
    tmp_env: TmpEnvFixture,
    conda_channel: str,
    python_version: str,
):
    monkeypatch.setenv("CONDA_CHANNELS", conda_channel)

    with tmp_env("conda", "conda-self", f"python={python_version}") as prefix:
        assert not is_installed(prefix, "conda-index")
        conda_cli_subprocess(
            prefix,
            "self",
            "install",
            "--yes",
            "conda-index",
        )
        assert is_installed(prefix, "conda-index")

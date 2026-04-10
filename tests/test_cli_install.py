import pytest
from conda.exceptions import CondaValueError, DryRunExit

from conda_self.exceptions import SpecsAreNotPlugins


def test_help(conda_cli):
    out, err, exc = conda_cli("self", "install", "--help", raises=SystemExit)
    assert exc.value.code == 0


def test_install_plugin_dry_run(conda_cli):
    conda_cli(
        "self", "install", "--dry-run", "conda-libmamba-solver", raises=DryRunExit
    )


def test_install_plugin_dry_run_not_found(conda_cli):
    _, _, code = conda_cli("self", "install", "--dry-run", "conda-fake-solver")
    assert code != 0


def test_install_package_not_found(conda_cli):
    _, _, code = conda_cli("self", "install", "idontexist")
    assert code != 0


@pytest.mark.parametrize("plugin_name", ("flask", "numpy"))
def test_install_not_plugins(conda_cli, plugin_name):
    conda_cli("self", "install", plugin_name, raises=SpecsAreNotPlugins)


@pytest.mark.parametrize(
    "spec",
    (
        "conda-forge::conda-libmamba-solver",
        "defaults::conda-libmamba-solver",
    ),
)
def test_install_channel_in_spec_rejected(conda_cli, spec):
    conda_cli("self", "install", spec, raises=CondaValueError)

import pytest
from conda.exceptions import CondaValueError, DryRunExit, PackagesNotFoundError

from conda_self.exceptions import SpecsAreNotPlugins


def test_help(conda_cli):
    out, err, exc = conda_cli("self", "install", "--help", raises=SystemExit)
    assert exc.value.code == 0


@pytest.mark.parametrize(
    "plugin_name,ok",
    (
        ("conda-libmamba-solver", True),
        ("conda-fake-solver", False),
    ),
)
def test_install_plugin_dry_run(conda_cli, plugin_name, ok):
    conda_cli(
        "self",
        "install",
        "--dry-run",
        plugin_name,
        raises=DryRunExit if ok else Exception,
    )


@pytest.mark.parametrize(
    "plugin_name,error",
    (
        ("idontexist", PackagesNotFoundError),
        ("flask", SpecsAreNotPlugins),
        ("numpy", SpecsAreNotPlugins),
    ),
)
def test_install_not_plugins(conda_cli, plugin_name, error):
    conda_cli(
        "self",
        "install",
        plugin_name,
        raises=error,
    )


@pytest.mark.parametrize(
    "spec",
    (
        "conda-forge::conda-libmamba-solver",
        "defaults::conda-libmamba-solver",
    ),
)
def test_install_channel_in_spec_rejected(conda_cli, spec):
    conda_cli("self", "install", spec, raises=CondaValueError)

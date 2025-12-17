from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from conda.exceptions import DryRunExit, PackagesNotFoundError

from conda_self.exceptions import SpecsAreNotPlugins

if TYPE_CHECKING:
    from conda.testing.fixtures import CondaCLIFixture


def test_help(conda_cli: CondaCLIFixture):
    out, err, exc = conda_cli(
        "self",
        "install",
        "--help",
        raises=SystemExit,  # type: ignore[arg-type]
    )
    assert exc.value.code == 0


@pytest.mark.parametrize(
    "plugin_name,ok",
    (
        ("conda-libmamba-solver", True),
        ("conda-fake-solver", False),
    ),
)
def test_install_plugin_dry_run(conda_cli: CondaCLIFixture, plugin_name: str, ok: bool):
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
def test_install_not_plugins(conda_cli: CondaCLIFixture, plugin_name: str, error):
    conda_cli(
        "self",
        "install",
        plugin_name,
        raises=error,
    )

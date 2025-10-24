import pytest
from conda import __version__ as conda_version
from conda.exceptions import CondaValueError, DryRunExit
from conda.models.channel import Channel
from conda.models.records import PackageRecord

from conda_self import query


def test_help(conda_cli):
    out, err, exc = conda_cli("self", "update", "--help", raises=SystemExit)
    assert exc.value.code == 0


@pytest.mark.parametrize(
    "latest_version,message",
    (
        pytest.param(
            "1",
            "conda is already using the latest version available!",
            id="Outdated",
        ),
        pytest.param(
            conda_version,
            "conda is already using the latest version available!",
            id="Same",
        ),
        pytest.param(
            "2040",
            "Latest conda: 2040",
            id="Updatable",
        ),
    ),
)
def test_update_conda(conda_cli, mocker, latest_version, message):
    mocker.patch.object(
        query,
        "latest",
        return_value=PackageRecord(
            name="conda",
            version=latest_version,
            build="0",
            build_number=0,
            channel=Channel("conda-forge"),
        ),
    )
    out, err, exc = conda_cli("self", "update", "--dry-run", raises=DryRunExit)
    assert f"Installed conda: {conda_version}" in out
    assert message in out


@pytest.mark.parametrize(
    "plugin_name,ok", (("conda-libmamba-solver", True), ("conda-fake-solver", False))
)
def test_update_plugin(conda_cli, plugin_name, ok):
    conda_cli(
        "self",
        "update",
        "--dry-run",
        "--plugin",
        plugin_name,
        raises=DryRunExit if ok else CondaValueError,
    )

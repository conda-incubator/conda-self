from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from conda import __version__ as conda_version
from conda.exceptions import CondaValueError, DryRunExit
from conda.models.channel import Channel
from conda.models.records import PackageRecord
from conda_libmamba_solver import __version__ as clms_version

from conda_self import query, validate

if TYPE_CHECKING:
    from collections.abc import Iterable

    from conda.testing.fixtures import CondaCLIFixture
    from pytest_mock import MockerFixture


def test_help(conda_cli: CondaCLIFixture):
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
def test_update_conda(
    conda_cli: CondaCLIFixture, mocker: MockerFixture, latest_version: str, message: str
):
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


def test_update_deps(conda_cli: CondaCLIFixture, mocker: MockerFixture):
    mocker.patch.object(
        query,
        "latest",
        return_value=PackageRecord(
            name="conda",
            version=conda_version,
            build="0",
            build_number=0,
            channel=Channel("conda-forge"),
        ),
    )
    message = (
        "conda is using the latest version available, "
        "but may have outdated dependencies."
    )
    out, err, exc = conda_cli(
        "self", "update", "--dry-run", "--update-deps", raises=DryRunExit
    )
    assert message in out


@pytest.mark.parametrize(
    "plugin_name,ok", (("conda-libmamba-solver", True), ("conda-fake-solver", False))
)
def test_update_plugin(
    conda_cli: CondaCLIFixture, plugin_name: str, ok: tuple[str, bool]
):
    conda_cli(
        "self",
        "update",
        "--dry-run",
        "--plugin",
        plugin_name,
        raises=DryRunExit if ok else CondaValueError,
    )


@pytest.mark.parametrize(
    "latest_versions,message_parts",
    (
        pytest.param(
            {
                "conda": conda_version,
                "conda-libmamba-solver": clms_version,
            },
            (
                "conda is already using the latest version available!",
                "conda-libmamba-solver is already using the latest version available!",
            ),
            id="No updates",
        ),
        pytest.param(
            {
                "conda": conda_version,
                "conda-libmamba-solver": "2080",
            },
            (
                "conda is already using the latest version available!",
                "Latest conda-libmamba-solver: 2080",
            ),
            id="Update one",
        ),
        pytest.param(
            {
                "conda": "2040",
                "conda-libmamba-solver": "2080",
            },
            (
                "Latest conda: 2040",
                "Latest conda-libmamba-solver: 2080",
            ),
            id="Update all",
        ),
    ),
)
def test_update_all(
    conda_cli: CondaCLIFixture,
    mocker: MockerFixture,
    latest_versions: dict[str, str],
    message_parts: tuple[str, ...],
):
    def mock_latest(package_name: str, _: str, __: Iterable[str]) -> PackageRecord:
        return PackageRecord(
            name=package_name,
            version=latest_versions.get(package_name),
            build="0",
            build_number=0,
            channel=Channel("conda-forge"),
        )

    mocker.patch.object(
        validate, "conda_plugin_packages", return_value=["conda-libmamba-solver"]
    )
    mocker.patch.object(query, "latest", mock_latest)
    out, _, _ = conda_cli(
        "self",
        "update",
        "--all",
        "--dry-run",
        raises=DryRunExit,
    )
    assert f"Installed conda: {conda_version}" in out
    assert f"Installed conda-libmamba-solver: {clms_version}" in out
    for message in message_parts:
        assert message in out

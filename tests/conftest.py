from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

import pytest
from conda.plugins.hookspec import CondaSpecs
from conda.plugins.manager import CondaPluginManager

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from conda.testing.fixtures import CondaCLIFixture, TmpEnvFixture

pytest_plugins = (
    "conda.testing",
    "conda.testing.fixtures",
)


@pytest.fixture
def conda_channel() -> str:
    return os.environ.get("TEST_CONDA_CHANNEL", "conda-forge")


@pytest.fixture
def python_version() -> str:
    return f"{sys.version_info.major}.{sys.version_info.minor}"


@pytest.fixture
def plugin_manager(mocker) -> CondaPluginManager:
    pm = CondaPluginManager()
    pm.add_hookspecs(CondaSpecs)
    mocker.patch("conda.plugins.manager.get_plugin_manager", return_value=pm)
    return pm


@pytest.fixture(scope="session")
def _session_env(
    session_tmp_env: TmpEnvFixture,
) -> Iterator[Path]:
    """Session-scoped env with conda + conda-self + python.

    Created once per test run. Tests get clones via ``base_env``.
    """
    channel = os.environ.get("TEST_CONDA_CHANNEL", "conda-forge")
    python_ver = f"{sys.version_info.major}.{sys.version_info.minor}"

    with session_tmp_env(
        "conda",
        "conda-self",
        f"python={python_ver}",
        f"--channel={channel}",
    ) as prefix:
        yield prefix


@pytest.fixture
def base_env(
    _session_env: Path,
    tmp_path: Path,
    conda_cli: CondaCLIFixture,
) -> Path:
    """Function-scoped clone of the session env (fast — hardlinks, no solving)."""
    conda_cli(
        "create",
        f"--prefix={tmp_path / 'env'}",
        f"--clone={_session_env}",
        "--yes",
        "--quiet",
    )
    return tmp_path / "env"

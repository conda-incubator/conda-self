import os
import sys

import pytest
from conda.plugins.hookspec import CondaSpecs
from conda.plugins.manager import CondaPluginManager

pytest_plugins = (
    # Add testing fixtures and internal pytest plugins here
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

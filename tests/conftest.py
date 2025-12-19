import os
import sys

import pytest

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

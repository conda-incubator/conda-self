import pytest
from conda.base.context import context, reset_context
from conda.common.configuration import YamlRawParameter
from conda.common.serialize import yaml
from conda.plugins.manager import CondaPluginManager

from conda_self import plugin as conda_self_plugin
from conda_self.constants import PERMANENT_PACKAGES, SELF_PERMANENT_PACKAGES_SETTING
from conda_self.query import permanent_dependencies

CONDARC_PERMANENT_PACKAGES = f"""\
plugins:
  {SELF_PERMANENT_PACKAGES_SETTING}:
    - python
"""


def test_permanent_dependencies():
    must_keep = permanent_dependencies()
    assert set(PERMANENT_PACKAGES).issubset(must_keep)


@pytest.fixture()
def clear_plugins_context_cache():
    try:
        del context.plugins
    except AttributeError:
        pass


@pytest.fixture()
def self_plugin_manager(
    plugin_manager: CondaPluginManager, clear_plugins_context_cache
):
    """Load the conda-self plugin module (including conda_settings)."""
    plugin_manager.load_plugins(conda_self_plugin)
    yield plugin_manager


@pytest.fixture()
def permanent_packages_condarc(self_plugin_manager):
    """Load a .condarc that sets self_permanent_packages to ['python']."""
    reset_context()
    context._set_raw_data(
        {
            "testdata": YamlRawParameter.make_raw_parameters(
                "testdata", yaml.loads(CONDARC_PERMANENT_PACKAGES)
            )
        }
    )
    return self_plugin_manager


def test_permanent_dependencies_with_setting(permanent_packages_condarc):
    """Packages listed in the self_permanent_packages setting are kept."""
    must_keep = permanent_dependencies()

    assert set(PERMANENT_PACKAGES).issubset(must_keep)
    assert "python" in must_keep


def test_permanent_dependencies_setting_empty_by_default(self_plugin_manager):
    """Without condarc config, the setting defaults to an empty list."""
    assert getattr(context.plugins, SELF_PERMANENT_PACKAGES_SETTING) == ()


def test_permanent_dependencies_without_setting():
    """Works normally when no plugin settings are loaded."""
    must_keep = permanent_dependencies()

    assert set(PERMANENT_PACKAGES).issubset(must_keep)

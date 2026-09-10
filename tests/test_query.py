import json
from types import SimpleNamespace

import pytest
from conda.base.context import context, reset_context
from conda.common.configuration import YamlRawParameter
from conda.common.serialize import yaml
from conda.models.records import PrefixRecord
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
    yield self_plugin_manager
    reset_context()


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


@pytest.mark.parametrize("add_plugins", [False, True])
def test_permanent_dependencies_preserves_plugins_and_their_dependencies(
    tmp_path, monkeypatch, self_plugin_manager, add_plugins
):
    conda_meta = tmp_path / "conda-meta"
    conda_meta.mkdir()
    (conda_meta / "history").touch()
    for name, depends, entry_point_group in (
        ("conda", ("conda-runtime",), None),
        ("conda-self", ("conda",), None),
        ("conda-runtime", (), None),
        ("example-plugin", ("plugin-helper",), "conda"),
        ("plugin-helper", ("native-library",), None),
        ("native-library", (), None),
        ("ordinary-package", ("plugin-helper",), "console_scripts"),
        ("unrelated-native", (), None),
    ):
        if entry_point_group:
            payload = f"site-packages/{name}-1.0.dist-info/entry_points.txt"
            content = f"[{entry_point_group}]\nexample = example:main\n"
        else:
            payload = f"share/{name}.txt"
            content = "installed package data\n"
        path = tmp_path / payload
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        record = PrefixRecord(
            name=name,
            version="1.0",
            build="0",
            build_number=0,
            subdir="noarch",
            depends=depends,
            files=(payload,),
        )
        (conda_meta / f"{name}-1.0-0.json").write_text(json.dumps(record.dump()))

    prefix = SimpleNamespace(prefix=str(tmp_path))
    monkeypatch.setattr("conda_self.query.sys", prefix)
    monkeypatch.setattr("conda_self.package_info.sys", prefix)

    expected = {"conda", "conda-self", "conda-runtime"}
    if add_plugins:
        expected |= {"example-plugin", "plugin-helper", "native-library"}
    assert permanent_dependencies(add_plugins=add_plugins) == expected

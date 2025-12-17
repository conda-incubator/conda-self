from contextlib import contextmanager
from types import SimpleNamespace

from conda.base.context import context


def test_help(conda_cli):
    out, err, exc = conda_cli("self", "update", "--help", raises=SystemExit)
    assert exc.value.code == 0


def test_update_conda_no_updates(conda_cli, monkeypatch):
    monkeypatch.setattr(context, "dry_run", False)
    monkeypatch.setattr(context, "quiet", True)
    monkeypatch.setattr("conda_self.validate.conda_plugin_packages", lambda: [])
    monkeypatch.setattr(
        "conda_self.validate.validate_plugin_is_installed",
        lambda name: None,
    )

    installed = SimpleNamespace(channel="defaults", version="1.0.0")
    latest = SimpleNamespace(version="1.0.0")
    monkeypatch.setattr(
        "conda_self.query.check_updates",
        lambda name, prefix: (False, installed, latest),
    )

    calls = {}

    def fake_install_package_list_in_protected_env(packages, channel, force_reinstall):
        calls["packages"] = packages
        calls["channel"] = channel
        calls["force_reinstall"] = force_reinstall
        return 0

    monkeypatch.setattr(
        "conda_self.install.install_package_list_in_protected_env",
        fake_install_package_list_in_protected_env,
    )

    @contextmanager
    def fake_spinner(_):
        yield None

    monkeypatch.setattr("conda.reporters.get_spinner", fake_spinner)

    out, err, exc = conda_cli("self", "update")

    assert exc == 0
    assert calls == {}


def test_update_conda_with_update(conda_cli, monkeypatch):
    monkeypatch.setattr(context, "dry_run", False)
    monkeypatch.setattr(context, "quiet", True)
    monkeypatch.setattr("conda_self.validate.conda_plugin_packages", lambda: [])
    monkeypatch.setattr(
        "conda_self.validate.validate_plugin_is_installed",
        lambda name: None,
    )

    installed = SimpleNamespace(channel="defaults", version="1.0.0")
    latest = SimpleNamespace(version="2.0.0")
    monkeypatch.setattr(
        "conda_self.query.check_updates",
        lambda name, prefix: (True, installed, latest),
    )

    calls = {}

    def fake_install_package_list_in_protected_env(packages, channel, force_reinstall):
        calls["packages"] = packages
        calls["channel"] = channel
        calls["force_reinstall"] = force_reinstall
        return 0

    monkeypatch.setattr(
        "conda_self.install.install_package_list_in_protected_env",
        fake_install_package_list_in_protected_env,
    )

    @contextmanager
    def fake_spinner(_):
        yield None

    monkeypatch.setattr("conda.reporters.get_spinner", fake_spinner)

    out, err, exc = conda_cli("self", "update")

    assert exc == 0
    assert calls["packages"] == {"conda": "2.0.0"}
    assert calls["channel"] == "defaults"
    assert calls["force_reinstall"] is False

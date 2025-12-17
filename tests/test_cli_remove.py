import pytest

from conda_self import exceptions


def test_help(conda_cli):
    out, err, exc = conda_cli(
        "self",
        "remove",
        "--help",
        raises=SystemExit,  # type: ignore[arg-type]
    )
    assert exc.value.code == 0


def test_disallow_permanent(conda_cli, monkeypatch):
    monkeypatch.setattr("conda_self.query.permanent_dependencies", lambda: {"conda"})

    with pytest.raises(exceptions.SpecsCanNotBeRemoved):
        conda_cli("self", "remove", "conda")


def test_remove_calls_uninstall(conda_cli, monkeypatch):
    monkeypatch.setattr("conda_self.query.permanent_dependencies", lambda: set())

    called = {}

    def fake_uninstall(specs, yes):
        called["specs"] = specs
        called["yes"] = yes
        return 0

    monkeypatch.setattr(
        "conda_self.install.uninstall_specs_in_protected_env",
        fake_uninstall,
    )

    out, err, exc = conda_cli("self", "remove", "conda-libmamba-solver")

    assert exc == 0
    assert called["specs"] == ["conda-libmamba-solver"]
    assert called["yes"] is False

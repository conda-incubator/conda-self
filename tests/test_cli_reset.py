def test_help(conda_cli):
    out, err, exc = conda_cli(
        "self",
        "reset",
        "--help",
        raises=SystemExit,  # type: ignore[arg-type]
    )
    assert exc.value.code == 0


def test_reset_invokes_reset(conda_cli, monkeypatch):
    monkeypatch.setattr("conda_self.query.permanent_dependencies", lambda: {"conda"})
    monkeypatch.setattr("conda.reporters.confirm_yn", lambda *_, **__: None)

    called = {}

    def fake_reset(uninstallable_packages):
        called["packages"] = uninstallable_packages

    monkeypatch.setattr("conda_self.reset.reset", fake_reset)

    out, err, exc = conda_cli("self", "reset", "--yes")

    assert exc == 0
    assert called["packages"] == {"conda"}

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from conda.testing.fixtures import CondaCLIFixture


def test_help(conda_cli: CondaCLIFixture):
    out, err, exc = conda_cli("plugins", "list", "--help", raises=SystemExit)
    assert exc.value.code == 0


def test_plugins_help(conda_cli: CondaCLIFixture):
    out, err, exc = conda_cli("plugins", "--help", raises=SystemExit)
    assert exc.value.code == 0
    assert "list" in out


def test_list_table(conda_cli: CondaCLIFixture):
    """Table output includes conda-self (always installed in the test env)."""
    out, err, code = conda_cli("plugins", "list")
    assert code == 0
    assert "Name" in out
    assert "Version" in out
    assert "Status" in out
    assert "Hooks" in out
    assert "conda-self" in out
    assert "active" in out


def test_list_json(conda_cli: CondaCLIFixture):
    """JSON output is a list of objects with the expected keys."""
    out, err, code = conda_cli("plugins", "list", "--json")
    assert code == 0
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) >= 1

    self_entry = next(p for p in data if p["name"] == "conda-self")
    assert set(self_entry.keys()) == {
        "name",
        "version",
        "canonical_name",
        "status",
        "hooks",
    }
    assert self_entry["status"] == "active"
    assert isinstance(self_entry["hooks"], list)
    assert "subcommands" in self_entry["hooks"]


@pytest.mark.parametrize(
    "hook",
    [
        pytest.param("subcommands", id="subcommands"),
        pytest.param("settings", id="settings"),
        pytest.param("health_checks", id="health_checks"),
    ],
)
def test_list_conda_self_hooks(conda_cli: CondaCLIFixture, hook: str):
    """conda-self registers these hooks; verify they appear in JSON output."""
    out, err, code = conda_cli("plugins", "list", "--json")
    data = json.loads(out)
    self_entry = next(p for p in data if p["name"] == "conda-self")
    assert hook in self_entry["hooks"]

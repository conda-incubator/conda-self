"""Tests for base-protection health check."""

from __future__ import annotations

import sys
from argparse import Namespace
from typing import TYPE_CHECKING

import pytest
from conda.base.constants import PREFIX_FROZEN_FILE
from conda.core.prefix_data import PrefixData
from conda.exceptions import CondaValueError

from conda_self.constants import RESET_FILE_INSTALLER
from conda_self.health_checks import base_protection
from conda_self.plugin import conda_health_checks

if TYPE_CHECKING:
    from pathlib import Path

    from pytest import CaptureFixture, MonkeyPatch


class _FakePrefixData:
    """Minimal stand-in for PrefixData.from_name() return value."""

    def __init__(self, tmp_path: Path):
        self.prefix_path = tmp_path / "envs" / "default"

    def is_environment(self) -> bool:
        return False

    def exists(self) -> bool:
        return False


class _FakeEnvironment:
    """Minimal stand-in for Environment.from_prefix()."""

    external_packages: list = []


class _FakeConfigFile:
    """Minimal stand-in for ConfigurationFile context manager."""

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_key(self, key, value):
        pass


@pytest.fixture
def fake_base_env(tmp_path: Path, monkeypatch: MonkeyPatch) -> Path:
    """Create a fake base environment by patching sys.prefix."""
    conda_meta = tmp_path / "conda-meta"
    conda_meta.mkdir()
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    return tmp_path


@pytest.fixture
def protected_base_env(fake_base_env: Path) -> Path:
    """Create a fake protected (frozen) base environment."""
    frozen_file = fake_base_env / PREFIX_FROZEN_FILE
    frozen_file.write_text("{}")
    return fake_base_env


@pytest.fixture
def reset_calls():
    """Accumulator for calls to the patched reset function."""
    return []


@pytest.fixture
def perm_deps_calls():
    """Accumulator for calls to the patched permanent_dependencies function."""
    return []


@pytest.fixture
def fixable_base_env(
    fake_base_env: Path,
    monkeypatch: MonkeyPatch,
    reset_calls: list,
    perm_deps_calls: list,
):
    """A fake base env wired with lightweight stubs for fix() to run end-to-end."""
    PrefixData._cache_.clear()

    def fake_reset(**kwargs):
        reset_calls.append(kwargs)

    def fake_perm_deps(**kwargs):
        perm_deps_calls.append(kwargs)
        return {"conda", "conda-self"}

    def fake_get_exporter(fmt):
        raise CondaValueError("no exporter")

    monkeypatch.setattr("conda.base.context.context.quiet", True, raising=False)
    monkeypatch.setattr(
        "conda.base.context.context.plugin_manager.get_environment_exporter_by_format",
        fake_get_exporter,
    )
    monkeypatch.setattr("conda_self.reset.reset", fake_reset)
    monkeypatch.setattr("conda.misc.clone_env", lambda *a, **kw: None)
    monkeypatch.setattr(
        "conda.models.environment.Environment.from_prefix",
        lambda *a, **kw: _FakeEnvironment(),
    )
    monkeypatch.setattr("conda_self.query.permanent_dependencies", fake_perm_deps)
    monkeypatch.setattr(
        PrefixData, "from_name", lambda *a, **kw: _FakePrefixData(fake_base_env)
    )
    monkeypatch.setattr(
        "conda.cli.condarc.ConfigurationFile.from_user_condarc",
        _FakeConfigFile,
    )

    return fake_base_env


def test_is_base_environment_returns_true_for_base():
    assert base_protection.is_base_environment(sys.prefix) is True


def test_is_base_environment_returns_false_for_other_prefix(tmp_path: Path):
    assert base_protection.is_base_environment(str(tmp_path)) is False


def test_is_base_protected_returns_true_when_frozen(protected_base_env: Path):
    PrefixData._cache_.clear()
    assert base_protection.is_base_protected() is True


def test_is_base_protected_returns_false_when_not_frozen(fake_base_env: Path):
    PrefixData._cache_.clear()
    assert base_protection.is_base_protected() is False


def test_check_skips_non_base_environment(tmp_path: Path, capsys: CaptureFixture):
    base_protection.check(str(tmp_path), False)

    captured = capsys.readouterr()
    assert "Skipping" in captured.out
    assert "not running on base environment" in captured.out


def test_check_reports_protected_base(protected_base_env: Path, capsys: CaptureFixture):
    PrefixData._cache_.clear()
    base_protection.check(str(protected_base_env), False)

    captured = capsys.readouterr()
    assert "protected" in captured.out.lower()
    assert "not protected" not in captured.out.lower()


def test_check_reports_unprotected_base(fake_base_env: Path, capsys: CaptureFixture):
    PrefixData._cache_.clear()
    base_protection.check(str(fake_base_env), False)

    captured = capsys.readouterr()
    assert "not protected" in captured.out.lower()
    assert "conda doctor --fix" in captured.out


def test_fix_skips_non_base_environment(tmp_path: Path, capsys: CaptureFixture):
    args = Namespace()
    confirm_called = []

    result = base_protection.fix(str(tmp_path), args, confirm_called.append)

    assert result == 0
    captured = capsys.readouterr()
    assert "Skipping" in captured.out
    assert len(confirm_called) == 0


def test_fix_skips_already_protected(protected_base_env: Path, capsys: CaptureFixture):
    args = Namespace()
    confirm_called = []

    PrefixData._cache_.clear()
    result = base_protection.fix(str(protected_base_env), args, confirm_called.append)

    assert result == 0
    captured = capsys.readouterr()
    assert "already protected" in captured.out
    assert len(confirm_called) == 0


def test_fix_calls_confirm_callback(fake_base_env: Path):
    args = Namespace()
    confirm_called = []

    class UserCancelled(Exception):
        pass

    def confirm(msg: str) -> None:
        confirm_called.append(msg)
        raise UserCancelled()

    PrefixData._cache_.clear()
    with pytest.raises(UserCancelled):
        base_protection.fix(str(fake_base_env), args, confirm)

    assert confirm_called == ["Proceed?"]


def test_fix_uses_installer_snapshot_when_available(
    fixable_base_env: Path,
    reset_calls: list,
    perm_deps_calls: list,
):
    snapshot = fixable_base_env / "conda-meta" / RESET_FILE_INSTALLER
    snapshot.write_text("@EXPLICIT\n")

    args = Namespace()
    base_protection.fix(str(fixable_base_env), args, lambda msg: None)

    assert len(reset_calls) == 1
    assert reset_calls[0]["snapshot"] == snapshot
    assert "uninstallable_packages" not in reset_calls[0]
    assert perm_deps_calls == []


def test_fix_falls_back_to_permanent_deps_without_snapshot(
    fixable_base_env: Path,
    reset_calls: list,
    perm_deps_calls: list,
):
    args = Namespace()
    base_protection.fix(str(fixable_base_env), args, lambda msg: None)

    assert len(reset_calls) == 1
    assert reset_calls[0]["uninstallable_packages"] == {"conda", "conda-self"}
    assert "snapshot" not in reset_calls[0]
    assert len(perm_deps_calls) == 1


def test_health_check_registered():
    health_checks = list(conda_health_checks())

    assert len(health_checks) == 1
    hc = health_checks[0]
    assert hc.name == "base-protection"
    assert hc.action == base_protection.check
    assert hc.fixer == base_protection.fix
    assert hc.summary is not None
    assert hc.fix is not None

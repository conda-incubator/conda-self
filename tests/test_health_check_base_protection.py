# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for base-protection health check."""

from __future__ import annotations

import sys
from argparse import Namespace
from typing import TYPE_CHECKING

import pytest
from conda.base.constants import PREFIX_FROZEN_FILE
from conda.core.prefix_data import PrefixData

from conda_self.health_checks import base_protection

if TYPE_CHECKING:
    from pathlib import Path

    from pytest import CaptureFixture, MonkeyPatch


@pytest.fixture
def fake_base_env(tmp_path: Path, monkeypatch: MonkeyPatch) -> Path:
    """Create a fake base environment by patching sys.prefix."""
    # Create conda-meta directory to make it look like a conda env
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


# -- is_base_environment tests --


def test_is_base_environment_returns_true_for_base():
    """Returns True when prefix matches sys.prefix."""
    assert base_protection.is_base_environment(sys.prefix) is True


def test_is_base_environment_returns_false_for_other_prefix(tmp_path: Path):
    """Returns False when prefix doesn't match sys.prefix."""
    assert base_protection.is_base_environment(str(tmp_path)) is False


# -- is_base_protected tests --


def test_is_base_protected_returns_true_when_frozen(protected_base_env: Path):
    """Returns True when PREFIX_FROZEN_FILE exists."""
    # Clear the PrefixData cache to pick up our patched sys.prefix
    PrefixData._cache_.clear()
    assert base_protection.is_base_protected() is True


def test_is_base_protected_returns_false_when_not_frozen(fake_base_env: Path):
    """Returns False when PREFIX_FROZEN_FILE doesn't exist."""
    PrefixData._cache_.clear()
    assert base_protection.is_base_protected() is False


# -- check action tests --


def test_check_skips_non_base_environment(tmp_path: Path, capsys: CaptureFixture):
    """Prints skip message when not on base environment."""
    base_protection.check(str(tmp_path), False)

    captured = capsys.readouterr()
    assert "Skipping" in captured.out
    assert "not running on base environment" in captured.out


def test_check_reports_protected_base(protected_base_env: Path, capsys: CaptureFixture):
    """Reports OK when base is protected."""
    PrefixData._cache_.clear()
    base_protection.check(str(protected_base_env), False)

    captured = capsys.readouterr()
    assert "protected" in captured.out.lower()
    assert "not protected" not in captured.out.lower()


def test_check_reports_unprotected_base(fake_base_env: Path, capsys: CaptureFixture):
    """Reports X when base is not protected."""
    PrefixData._cache_.clear()
    base_protection.check(str(fake_base_env), False)

    captured = capsys.readouterr()
    assert "not protected" in captured.out.lower()
    assert "conda doctor --fix" in captured.out


# -- fix fixer tests --


def test_fix_skips_non_base_environment(tmp_path: Path, capsys: CaptureFixture):
    """Skips when not on base environment."""
    args = Namespace()
    confirm_called = []

    def confirm(msg: str) -> None:
        confirm_called.append(msg)

    result = base_protection.fix(str(tmp_path), args, confirm)

    assert result == 0
    captured = capsys.readouterr()
    assert "Skipping" in captured.out
    assert len(confirm_called) == 0


def test_fix_skips_already_protected(protected_base_env: Path, capsys: CaptureFixture):
    """Returns early when base is already protected."""
    args = Namespace()
    confirm_called = []

    def confirm(msg: str) -> None:
        confirm_called.append(msg)

    PrefixData._cache_.clear()
    result = base_protection.fix(str(protected_base_env), args, confirm)

    assert result == 0
    captured = capsys.readouterr()
    assert "already protected" in captured.out
    assert len(confirm_called) == 0


def test_fix_calls_confirm_callback(fake_base_env: Path):
    """Calls confirm callback when proceeding with fix."""
    args = Namespace()
    confirm_called = []

    class UserCancelled(Exception):
        """Raised when user cancels."""

    def confirm(msg: str) -> None:
        confirm_called.append(msg)
        # Simulate user cancellation to stop execution after first confirm
        raise UserCancelled()

    PrefixData._cache_.clear()
    with pytest.raises(UserCancelled):
        base_protection.fix(str(fake_base_env), args, confirm)

    assert confirm_called == ["Proceed?"]


# -- plugin registration tests --


def test_health_check_registered():
    """Verify the health check is registered correctly.

    Works with both old and new conda versions.
    """

    from conda_self.plugin import conda_health_checks

    health_checks = list(conda_health_checks())

    assert len(health_checks) == 1
    hc = health_checks[0]
    assert hc.name == "base-protection"
    assert hc.action == base_protection.check

    # Additional fields only available in conda >= 26.1.0
    if hasattr(hc, "fixer"):
        assert hc.fixer == base_protection.fix
        assert hc.summary is not None
        assert hc.fix is not None

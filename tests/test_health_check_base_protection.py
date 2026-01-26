# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for base-protection health check."""

from __future__ import annotations

import sys
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

# These constants may not be available in older conda versions
try:
    from conda.base.constants import OK_MARK, X_MARK
except ImportError:
    OK_MARK = "✓"
    X_MARK = "✗"

from conda.base.constants import PREFIX_FROZEN_FILE

from conda_self.health_checks import base_protection

if TYPE_CHECKING:
    from conda.testing.fixtures import TmpEnvFixture


class TestIsBaseEnvironment:
    """Tests for is_base_environment function."""

    def test_returns_true_for_base(self):
        """Returns True when prefix matches sys.prefix."""
        assert base_protection.is_base_environment(sys.prefix) is True

    def test_returns_false_for_other_prefix(self, tmp_path: Path):
        """Returns False when prefix doesn't match sys.prefix."""
        assert base_protection.is_base_environment(str(tmp_path)) is False


class TestIsBaseProtected:
    """Tests for is_base_protected function."""

    def test_returns_true_when_frozen_file_exists(self, tmp_path: Path):
        """Returns True when PREFIX_FROZEN_FILE exists."""
        with patch.object(base_protection, "sys") as mock_sys:
            mock_sys.prefix = str(tmp_path)

            # Create the frozen file
            frozen_file = tmp_path / PREFIX_FROZEN_FILE
            frozen_file.parent.mkdir(parents=True, exist_ok=True)
            frozen_file.touch()

            with patch(
                "conda_self.health_checks.base_protection.PrefixData"
            ) as mock_pd:
                mock_pd_instance = MagicMock()
                mock_pd_instance.prefix_path = tmp_path
                mock_pd.return_value = mock_pd_instance

                assert base_protection.is_base_protected() is True

    def test_returns_false_when_frozen_file_missing(self, tmp_path: Path):
        """Returns False when PREFIX_FROZEN_FILE doesn't exist."""
        with patch.object(base_protection, "sys") as mock_sys:
            mock_sys.prefix = str(tmp_path)

            with patch(
                "conda_self.health_checks.base_protection.PrefixData"
            ) as mock_pd:
                mock_pd_instance = MagicMock()
                mock_pd_instance.prefix_path = tmp_path
                mock_pd.return_value = mock_pd_instance

                assert base_protection.is_base_protected() is False


class TestCheck:
    """Tests for check health check action."""

    def test_skips_non_base_environment(self, tmp_path: Path, capsys):
        """Does nothing when not on base environment."""
        base_protection.check(str(tmp_path), False)

        captured = capsys.readouterr()
        assert captured.out == ""

    def test_reports_protected_base(self, capsys):
        """Reports OK when base is protected."""
        with patch.object(
            base_protection, "is_base_environment", return_value=True
        ), patch.object(base_protection, "is_base_protected", return_value=True):
            base_protection.check(sys.prefix, False)

            captured = capsys.readouterr()
            assert "protected" in captured.out.lower()

    def test_reports_unprotected_base(self, capsys):
        """Reports X when base is not protected."""
        with patch.object(
            base_protection, "is_base_environment", return_value=True
        ), patch.object(base_protection, "is_base_protected", return_value=False):
            base_protection.check(sys.prefix, False)

            captured = capsys.readouterr()
            assert "not protected" in captured.out.lower()
            assert "conda doctor --fix" in captured.out


class TestFix:
    """Tests for fix health check fixer.

    Note: The fix function has complex dependencies on unreleased conda APIs.
    These tests mock at the function entry points to test the logic flow.
    """

    def test_skips_non_base_environment(self, tmp_path: Path, capsys):
        """Skips when not on base environment."""
        args = Namespace()
        confirm = MagicMock()

        # Mock the imports inside fix to avoid ImportError
        with patch.dict("sys.modules", {"conda.cli.condarc": MagicMock()}):
            result = base_protection.fix(str(tmp_path), args, confirm)

        assert result == 0
        captured = capsys.readouterr()
        assert "Skipping" in captured.out
        confirm.assert_not_called()

    def test_skips_already_protected(self, capsys):
        """Returns early when base is already protected."""
        args = Namespace()
        confirm = MagicMock()

        with patch.object(
            base_protection, "is_base_environment", return_value=True
        ), patch.object(
            base_protection, "is_base_protected", return_value=True
        ), patch.dict("sys.modules", {"conda.cli.condarc": MagicMock()}):
            result = base_protection.fix(sys.prefix, args, confirm)

        assert result == 0
        captured = capsys.readouterr()
        assert "already protected" in captured.out
        confirm.assert_not_called()

    def test_calls_confirm_callback(self):
        """Calls confirm callback when proceeding with fix."""
        args = Namespace()
        confirm = MagicMock()

        # Mock context at the module level before it's imported
        mock_context = MagicMock()
        mock_context.quiet = False

        with patch.object(
            base_protection, "is_base_environment", return_value=True
        ), patch.object(
            base_protection, "is_base_protected", return_value=False
        ), patch.dict(
            "sys.modules",
            {
                "conda.cli.condarc": MagicMock(),
                "conda.base.context": MagicMock(context=mock_context),
            },
        ):
            # confirm will raise to stop execution after first call
            confirm.side_effect = SystemExit(0)

            with pytest.raises(SystemExit):
                base_protection.fix(sys.prefix, args, confirm)

            confirm.assert_called_once_with("Proceed?")


class TestPluginRegistration:
    """Tests for plugin registration."""

    def test_health_check_registered(self):
        """Verify the health check is registered correctly.

        This test requires conda >= 26.1.0 which has the 'fixer' parameter.
        """
        # Check if the fixer parameter is available in CondaHealthCheck
        from conda.plugins.types import CondaHealthCheck

        if "fixer" not in CondaHealthCheck.__dataclass_fields__:
            pytest.skip("conda version doesn't support 'fixer' parameter (requires >= 26.1.0)")

        from conda_self.plugin import conda_health_checks

        health_checks = list(conda_health_checks())

        assert len(health_checks) == 1
        hc = health_checks[0]
        assert hc.name == "base-protection"
        assert hc.action == base_protection.check
        assert hc.fixer == base_protection.fix
        assert hc.summary is not None
        # The 'fix' description field
        assert hc.fix is not None

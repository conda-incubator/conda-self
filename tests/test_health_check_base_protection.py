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
    def __init__(self, tmp_path: Path):
        self.prefix_path = tmp_path / "envs" / "default"

    def is_environment(self) -> bool:
        return False

    def exists(self) -> bool:
        return False


class _FakeEnvironment:
    external_packages: list = []


class _FakeConfigFile:
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
    return []


@pytest.fixture
def perm_deps_calls():
    return []


@pytest.fixture
def fixable_base_env(
    fake_base_env: Path,
    monkeypatch: MonkeyPatch,
    reset_calls: list,
    perm_deps_calls: list,
):
    """Fake base env wired with stubs for fix() to run."""
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
        PrefixData,
        "from_name",
        lambda *a, **kw: _FakePrefixData(fake_base_env),
    )
    monkeypatch.setattr(
        "conda.cli.condarc.ConfigurationFile.from_user_condarc",
        _FakeConfigFile,
    )

    return fake_base_env


@pytest.mark.parametrize(
    "use_base, expected",
    [
        (True, True),
        (False, False),
    ],
    ids=["base", "other"],
)
def test_is_base_environment(tmp_path: Path, use_base: bool, expected: bool):
    prefix = sys.prefix if use_base else str(tmp_path)
    assert base_protection.is_base_environment(prefix) is expected


@pytest.mark.parametrize(
    "frozen, expected",
    [
        (True, True),
        (False, False),
    ],
    ids=["frozen", "not-frozen"],
)
def test_is_base_protected(fake_base_env: Path, frozen: bool, expected: bool):
    if frozen:
        (fake_base_env / PREFIX_FROZEN_FILE).write_text("{}")
    PrefixData._cache_.clear()
    assert base_protection.is_base_protected() is expected


@pytest.mark.parametrize(
    "env_fixture, expected_output, unexpected_output",
    [
        ("tmp_path", "skipping", None),
        ("protected_base_env", "protected", "not protected"),
        ("fake_base_env", "not protected", None),
    ],
    ids=["non-base", "protected", "unprotected"],
)
def test_check(
    env_fixture: str,
    expected_output: str,
    unexpected_output: str | None,
    request: pytest.FixtureRequest,
    capsys: CaptureFixture,
):
    prefix = str(request.getfixturevalue(env_fixture))
    PrefixData._cache_.clear()
    base_protection.check(prefix, False)

    captured = capsys.readouterr()
    assert expected_output in captured.out.lower()
    if unexpected_output:
        assert unexpected_output not in captured.out.lower()


@pytest.mark.parametrize(
    "env_fixture, expected_output",
    [
        ("tmp_path", "Skipping"),
        ("protected_base_env", "already protected"),
    ],
    ids=["non-base", "already-protected"],
)
def test_fix_skips(
    env_fixture: str,
    expected_output: str,
    request: pytest.FixtureRequest,
    capsys: CaptureFixture,
):
    prefix = str(request.getfixturevalue(env_fixture))
    confirm_called: list[str] = []

    PrefixData._cache_.clear()
    result = base_protection.fix(prefix, Namespace(), confirm_called.append)

    assert result == 0
    assert expected_output in capsys.readouterr().out
    assert confirm_called == []


def test_fix_calls_confirm_callback(fake_base_env: Path):
    confirm_called: list[str] = []

    class UserCancelled(Exception):
        pass

    def confirm(msg: str) -> None:
        confirm_called.append(msg)
        raise UserCancelled()

    PrefixData._cache_.clear()
    with pytest.raises(UserCancelled):
        base_protection.fix(str(fake_base_env), Namespace(), confirm)

    assert confirm_called == ["Proceed?"]


@pytest.mark.parametrize(
    "create_snapshot, expect_names_only, expected_keep",
    [
        (
            True,
            True,
            {"conda", "conda-self", "mamba", "pip"},
        ),
        (
            False,
            True,
            {"conda", "conda-self"},
        ),
    ],
    ids=[
        "with-installer-snapshot",
        "without-installer-snapshot",
    ],
)
def test_fix_reset_strategy(
    fixable_base_env: Path,
    reset_calls: list,
    perm_deps_calls: list,
    create_snapshot: bool,
    expect_names_only: bool,
    expected_keep: set[str],
):
    if create_snapshot:
        snapshot = fixable_base_env / "conda-meta" / RESET_FILE_INSTALLER
        snapshot.write_text(
            "@EXPLICIT\n"
            "https://conda.anaconda.org/conda-forge/noarch/"
            "mamba-1.5.0-pyh_0.conda#md5=0123456789abcdef0123456789abcdef\n"
            "https://conda.anaconda.org/conda-forge/noarch/"
            "pip-24.0-pyhd8ed1ab_0.conda\n"
        )

    base_protection.fix(str(fixable_base_env), Namespace(), lambda msg: None)

    assert len(reset_calls) == 1
    assert "snapshot" not in reset_calls[0]
    assert expected_keep <= reset_calls[0]["uninstallable_packages"]
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

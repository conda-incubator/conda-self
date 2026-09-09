"""Tests for base-protection health check."""

from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from conda.base.constants import PREFIX_FROZEN_FILE
from conda.core.prefix_data import PrefixData
from conda.exceptions import (
    CondaOSError,
    CondaSystemExit,
    CondaValueError,
    EnvironmentIsFrozenError,
)

from conda_self.constants import RESET_FILE_BASE_PROTECTION, RESET_FILE_INSTALLER
from conda_self.health_checks import base_protection
from conda_self.plugin import conda_health_checks

if TYPE_CHECKING:
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


@pytest.fixture
def base_protection_env(
    fake_base_env: Path,
    monkeypatch: MonkeyPatch,
    reset_calls: list,
) -> Path:
    """Use real package metadata, exports, and configuration for failure tests."""
    conda_meta = fake_base_env / "conda-meta"
    (conda_meta / "history").touch()
    for name in ("conda", "user-package"):
        filename = f"{name}-1.0-0.conda"
        (conda_meta / f"{name}-1.0-0.json").write_text(
            json.dumps(
                {
                    "name": name,
                    "version": "1.0",
                    "build": "0",
                    "build_number": 0,
                    "subdir": "noarch",
                    "fn": filename,
                    "url": f"https://packages.example.test/noarch/{filename}",
                    "depends": [],
                }
            )
        )
    PrefixData._cache_.clear()
    destination = fake_base_env / "envs" / "default"
    monkeypatch.setattr(PrefixData, "from_name", lambda name: PrefixData(destination))
    condarc = fake_base_env / "user.condarc"
    condarc.write_text("default_activation_env: work\nchannels:\n  - conda-forge\n")
    monkeypatch.setattr("conda.base.context.user_rc_path", str(condarc))
    monkeypatch.setattr("conda.misc.clone_env", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        "conda_self.reset.reset", lambda **kwargs: reset_calls.append(kwargs)
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
        ("protected_base_env", "marked as frozen", "not marked as frozen"),
        ("fake_base_env", "not marked as frozen", None),
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
    "is_environment", [True, False], ids=["environment", "directory"]
)
def test_fix_cancel_preserves_existing_destination(
    base_protection_env: Path,
    monkeypatch: MonkeyPatch,
    reset_calls: list,
    is_environment: bool,
):
    destination = base_protection_env / "envs" / "default"
    destination.mkdir(parents=True)
    if is_environment:
        (destination / "conda-meta").mkdir()
        (destination / "conda-meta" / "history").touch()
    sentinel = destination / "keep.txt"
    sentinel.write_text("existing user data\n")
    prompts: list[str] = []

    def confirm(message: str):
        prompts.append(message)
        if len(prompts) == 2:
            raise CondaSystemExit("Aborted")

    def unexpected_clone(*args, **kwargs):
        pytest.fail("Cloning must wait for destination confirmation")

    monkeypatch.setattr("conda.misc.clone_env", unexpected_clone)

    with pytest.raises(CondaSystemExit, match="Aborted"):
        base_protection.fix(str(base_protection_env), Namespace(), confirm)

    assert len(prompts) == 2
    assert sentinel.read_text() == "existing user data\n"
    assert not (base_protection_env / PREFIX_FROZEN_FILE).exists()
    assert reset_calls == []


@pytest.mark.parametrize("failing_operation", ["clone", "reset"])
def test_fix_preserves_recovery_snapshot_after_failure(
    base_protection_env: Path,
    monkeypatch: MonkeyPatch,
    failing_operation: str,
):
    conda_meta = base_protection_env / "conda-meta"
    snapshot = conda_meta / RESET_FILE_BASE_PROTECTION
    snapshots_before_clone: list[str] = []

    def clone(*args, **kwargs):
        snapshots_before_clone.append(snapshot.read_text())
        if failing_operation == "clone":
            raise OSError("clone failed")

    def reset(**kwargs):
        (conda_meta / "user-package-1.0-0.json").unlink()
        raise OSError("reset failed")

    monkeypatch.setattr("conda.misc.clone_env", clone)
    monkeypatch.setattr("conda_self.reset.reset", reset)

    with pytest.raises(OSError, match=f"{failing_operation} failed"):
        base_protection.fix(str(base_protection_env), Namespace(), lambda msg: None)

    assert len(snapshots_before_clone) == 1
    assert snapshot.read_text() == snapshots_before_clone[0]
    assert {
        line for line in snapshot.read_text().splitlines() if not line.startswith("#")
    } == {
        "@EXPLICIT",
        "https://packages.example.test/noarch/conda-1.0-0.conda",
        "https://packages.example.test/noarch/user-package-1.0-0.conda",
    }
    assert not (base_protection_env / PREFIX_FROZEN_FILE).exists()


def test_fix_freeze_failure_preserves_activation_config(
    base_protection_env: Path,
    monkeypatch: MonkeyPatch,
    reset_calls: list,
):
    condarc = base_protection_env / "user.condarc"
    original_config = condarc.read_bytes()
    frozen_file = base_protection_env / PREFIX_FROZEN_FILE
    write_text = Path.write_text

    def fail_freeze(path, *args, **kwargs):
        if path == frozen_file:
            raise PermissionError("Cannot write frozen marker")
        return write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_freeze)

    with pytest.raises(CondaOSError, match="Could not protect environment"):
        base_protection.fix(str(base_protection_env), Namespace(), lambda msg: None)

    assert len(reset_calls) == 1
    assert not frozen_file.exists()
    assert condarc.read_bytes() == original_config


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


def test_fix_writes_actionable_frozen_message(fixable_base_env: Path):
    base_protection.fix(str(fixable_base_env), Namespace(), lambda msg: None)

    frozen_file = fixable_base_env / PREFIX_FROZEN_FILE
    frozen_message = json.loads(frozen_file.read_text())["message"]
    rendered_error = str(EnvironmentIsFrozenError(fixable_base_env, frozen_message))

    assert frozen_message == base_protection.BASE_PROTECTION_FROZEN_MESSAGE
    assert "conda self --help" in rendered_error
    assert "--override-frozen" in rendered_error


def test_health_check_registered():
    health_checks = list(conda_health_checks())

    assert len(health_checks) == 1
    hc = health_checks[0]
    assert hc.name == "base-protection"
    assert hc.action == base_protection.check
    assert hc.fixer == base_protection.fix
    assert hc.summary is not None
    assert hc.fix is not None

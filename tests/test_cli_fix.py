import sys
from pathlib import Path

import conda
import pytest
from conda.base.context import sys_rc_path
from pytest_mock import MockerFixture

import conda_self


def _skip_if_fix_unavailable(conda_cli):
    try:
        out, err, exc = conda_cli("fix", "--help", raises=SystemExit)
    except SystemExit as exc:  # pragma: no cover - defensive
        pytest.skip("conda 'fix' subcommand not available")
    else:
        if exc.value.code != 0:
            pytest.skip("conda 'fix' subcommand not available")


def test_help(conda_cli):
    _skip_if_fix_unavailable(conda_cli)

    out, err, exc = conda_cli("fix", "--help", raises=SystemExit)
    assert exc.value.code == 0


def test_help_base(conda_cli):
    _skip_if_fix_unavailable(conda_cli)

    out, err, exc = conda_cli("fix", "base", "--help", raises=SystemExit)
    assert exc.value.code == 0


def test_list(conda_cli):
    _skip_if_fix_unavailable(conda_cli)

    out, err, exc = conda_cli("fix", "--list")
    assert "Available fix tasks:" in out
    assert "base" in out


def test_list_json(conda_cli):
    import json

    _skip_if_fix_unavailable(conda_cli)

    out, err, exc = conda_cli("fix", "--list", "--json")
    tasks = json.loads(out)
    assert any(task["name"] == "base" for task in tasks)


def test_no_task(conda_cli):
    _skip_if_fix_unavailable(conda_cli)

    out, err, exc = conda_cli("fix", raises=SystemExit)
    assert exc.value.code == 2


def test_fix_base(conda_cli, mocker: MockerFixture, tmpdir: Path, monkeypatch):
    _skip_if_fix_unavailable(conda_cli)

    # Set the root prefix to the temporary directory
    monkeypatch.setenv("CONDA_ROOT_PREFIX", str(tmpdir))

    # Make sure the envs dir exists in the temporary root prefix
    env_dir = tmpdir / "envs"
    env_dir.mkdir()
    monkeypatch.setenv("CONDA_ENVS_DIRS", str(env_dir))

    new_default_env = "mynewdefaultenv"

    # Ensure the environment doesn't already exist
    out, err, exc = conda_cli("env", "list")
    assert new_default_env not in out

    # mock conda.misc.clone_env so we don't create a new environment
    mocker.patch("conda.misc.clone_env")

    # mock reset function, so we don't reset the running environment
    mocker.patch("conda_self.reset.reset")

    # mock reading/writing the rc file to control the contents of the file
    mocker.patch("conda.cli.main_config._read_rc", return_value={})
    mocker.patch("conda.cli.main_config._write_rc")

    # mock printing the explicit environment
    mocker.patch("conda.cli.main_list.print_explicit")

    out, err, exc = conda_cli(
        "fix",
        "base",
        "--default-env",
        new_default_env,
        "--yes",
    )

    # ensure a backup environment file was created
    conda.cli.main_list.print_explicit.assert_called_once_with(sys.prefix)

    # ensure the base environment was cloned to the new env
    conda.misc.clone_env.assert_called_once_with(
        sys.prefix, env_dir / new_default_env, verbose=False, quiet=True
    )

    # ensure the base environment was reset
    conda_self.reset.reset.assert_called_once()  # type: ignore

    # ensure the system rc file was updated to reflect the new default env
    default_activation_env_path = tmpdir / "envs" / new_default_env
    conda.cli.main_config._write_rc.assert_called_once_with(
        sys_rc_path, {"default_activation_env": str(default_activation_env_path)}
    )

    # ensure the base was protected
    assert Path(sys.prefix, "conda-meta", "frozen").exists()

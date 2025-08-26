import sys
from pathlib import Path

import conda
from conda.base.context import sys_rc_path
from pytest_mock import MockerFixture

import conda_self


def test_help(conda_cli):
    out, err, exc = conda_cli("migrate", "--help", raises=SystemExit)
    assert exc.value.code == 0


def test_protect(conda_cli, mocker: MockerFixture, tmpdir: Path, monkeypatch):
    # Set the root prefix to the temporary directory
    monkeypatch.setenv("CONDA_ROOT_PREFIX", str(tmpdir))
    monkeypatch.setenv("CONDA_ALWAYS_YES", "True")
    # Make sure the envs dir exists in the temporary root prefix
    env_dir = tmpdir / "envs"
    env_dir.mkdir()
    monkeypatch.setenv("CONDA_ENVS_DIRS", str(env_dir))

    new_default_env = "mynewdefaultenv"

    # Ensure the environment doesn't already exist
    out, err, exc = conda_cli(
        "env",
        "list",
    )
    assert new_default_env not in out

    # mock conda.misc.clone_env so we don't create a new environment as part of the test
    mocker.patch("conda.misc.clone_env")

    # mock conda-self reset function, so we don't reset the running environment
    mocker.patch(
        "conda_self.reset.reset",
        new_callable=mocker.PropertyMock,
    )

    # mock reading/writing the rc file to control the contents of the file
    mocker.patch("conda.cli.main_config._read_rc", return_value={})
    mocker.patch("conda.cli.main_config._write_rc")

    # mock printing the explicit environemnt
    mocker.patch("conda.cli.main_list.print_explicit")

    out, err, exc = conda_cli(
        "migrate",
        "--default-env",
        new_default_env,
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

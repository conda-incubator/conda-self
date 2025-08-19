import sys
import subprocess

from conda.core.prefix_data import PrefixData
from conda.testing.fixtures import TmpEnvFixture


def test_help(conda_cli):
    out, err, exc = conda_cli("self", "reset", "--help", raises=SystemExit)
    assert exc.value.code == 0


def test_reset(conda_cli, tmp_path):
    tmp_prefix = sys.prefix

    assert len(tuple(PrefixData(tmp_prefix).query("numpy"))) == 0

    conda_cli("install", "numpy", "--yes")

    assert len(tuple(PrefixData(tmp_prefix).query("numpy"))) == 1

    conda_cli(
        "self",
        "reset",
    )

    assert len(tuple(PrefixData(tmp_prefix).query("numpy"))) == 0


def test_reset_conda_self_present(conda_cli, tmp_env: TmpEnvFixture):
    with tmp_env("conda", "conda-self") as prefix:
        # platform is "win32" even in win64 machines
        if sys.platform=="win32":
            python_bin = prefix / "python.exe"
        else:
            python_bin=prefix / "python" / "bin"
            
        result=subprocess.run([str(python_bin), "-m", "conda", "self", "reset"], check=True)

        assert PrefixData(prefix).get("conda")  # make sure conda-self didn't remove conda
        assert PrefixData(prefix).get("conda-self")  # make sure conda-self didn't remove itself


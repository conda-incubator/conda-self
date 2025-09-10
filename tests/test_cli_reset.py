import subprocess
import sys
from pathlib import Path

from conda.core.prefix_data import PrefixData
from conda.testing.fixtures import TmpEnvFixture


def test_help(conda_cli):
    out, err, exc = conda_cli("self", "reset", "--help", raises=SystemExit)
    assert exc.value.code == 0


def test_reset(conda_cli, tmp_path):
    tmp_prefix = sys.prefix

    # unprotect the environement if protected
    if Path(tmp_prefix, "conda-meta", "frozen").exists():
        Path(tmp_prefix, "conda-meta", "frozen").unlink()

    assert len(tuple(PrefixData(tmp_prefix).query("numpy"))) == 0

    conda_cli("install", "numpy", "--yes")

    assert len(tuple(PrefixData(tmp_prefix).query("numpy"))) == 1

    conda_cli(
        "self",
        "reset",
        "--yes",
    )

    assert len(tuple(PrefixData(tmp_prefix).query("numpy"))) == 0


def test_reset_conda_self_present(tmp_env: TmpEnvFixture):
    with tmp_env("conda", "conda-self") as prefix:
        # platform is "win32" even in win64 machines
        if sys.platform == "win32":
            python_bin = prefix / "python.exe"
        else:
            python_bin = prefix / "bin" / "python"

        PrefixData._cache_.clear()
        # Note: Running python -m conda self incidentally loads 'conda_self' from
        # the repo because the working directory happens to contain it. We should
        # actually 'pip install .' the repo but in this case we are lucky and don't
        # need to.
        subprocess.run(
            [str(python_bin), "-m", "conda", "self", "reset", "--yes"],
            check=True,
        )

        # make sure conda-self didn't remove conda
        assert PrefixData(prefix).get("conda")
        # make sure conda-self didn't remove itself
        assert PrefixData(prefix).get("conda-self")

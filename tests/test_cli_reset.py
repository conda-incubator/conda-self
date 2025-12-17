from conda.testing.fixtures import TmpEnvFixture

from conda_self.testing import conda_cli_subprocess, is_installed


def test_help(conda_cli):
    out, err, exc = conda_cli("self", "reset", "--help", raises=SystemExit)
    assert exc.value.code == 0


def test_reset(conda_cli, tmp_env: TmpEnvFixture):
    # Adding conda-index too to test that non-default plugins are kept
    with tmp_env("conda", "conda-self", "conda-index") as prefix:
        assert not is_installed(prefix, "numpy")

        conda_cli("install", "numpy", "--yes", "--prefix", prefix)
        assert is_installed(prefix, "numpy")

        conda_cli_subprocess(prefix, "self", "reset", "--yes")
        # make sure conda-self didn't remove conda
        assert is_installed(prefix, "conda")
        # make sure conda-self didn't remove itself
        assert is_installed(prefix, "conda-self")
        # make sure conda-self didn't remove a non-default conda plugin
        assert is_installed(prefix, "conda-index")
        # but numpy should be gone
        assert not is_installed(prefix, "numpy")

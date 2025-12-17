import pytest

from conda_self.exceptions import SpecsCanNotBeRemoved


def test_help(conda_cli):
    out, err, exc = conda_cli("self", "remove", "--help", raises=SystemExit)
    assert exc.value.code == 0


@pytest.mark.parametrize(
    "spec,error",
    (
        ("conda", SpecsCanNotBeRemoved),
        ("python", SpecsCanNotBeRemoved),
        ("flask", None),
    ),
)
def test_remove_plugin(conda_cli, spec, error):
    conda_cli(
        "self",
        "remove",
        spec,
        raises=error,
    )

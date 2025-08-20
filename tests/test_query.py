from conda_self.constants import PERMANENT_PACKAGES
from conda_self.query import permanent_dependencies


def test_permanent_dependencies():
    must_keep = permanent_dependencies()
    assert set(PERMANENT_PACKAGES).issubset(must_keep)

import sys
from functools import cache

from conda.exceptions import CondaValueError

if sys.version_info >= (3, 12):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points


@cache
def conda_plugin_packages():
    # Both Python 3.12+ and importlib-metadata support ep.dist
    # but the return type and attributes differ slightly
    return set(
        name
        for ep in entry_points(group="conda")
        if ep.dist is not None
        and (name := ep.dist.name.strip())
        and name != "conda-self"
    )


def validate_plugin_is_installed(name: str) -> None:
    if name not in conda_plugin_packages():
        raise CondaValueError(
            f"Package '{name}' does not seem to be a valid conda plugin. "
            "Try one of:\n- " + "\n- ".join(sorted(conda_plugin_packages()))
        )

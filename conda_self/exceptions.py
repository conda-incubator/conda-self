from __future__ import annotations

from typing import TYPE_CHECKING

from conda.common.io import dashlist
from conda.exceptions import CondaError

if TYPE_CHECKING:
    from pathlib import Path


class NotAPluginError(CondaError):
    def __init__(self, specs: list[str]):
        super().__init__(
            f"The following requested specs are not plugins:{dashlist(specs)}"
        )


class PluginRemoveError(CondaError):
    def __init__(self, specs: list[str]):
        super().__init__(f"Packages can not be removed:{dashlist(specs)}")


class NoDistInfoDirFound(CondaError):
    def __init__(self, package_name: str, path: str | Path):
        super().__init__(
            f"No *.dist-info directories found for '{package_name}' in '{path}'."
        )

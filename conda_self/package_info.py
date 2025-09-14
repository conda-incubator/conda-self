from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import TYPE_CHECKING

from .exceptions import NoDistInfoDirFound

if TYPE_CHECKING:
    from conda.models.records import PackageCacheRecord


# This is required for reading entry point info from an extracted package
# ref: https://packaging.python.org/en/latest/specifications/entry-points/#file-format
class CaseSensitiveConfigParser(configparser.ConfigParser):
    optionxform = staticmethod(str)  # type: ignore


class PackageInfo:
    def __init__(self, dist_info_path: Path):
        """Describe the dist-info for a Python package installed as a conda package"""
        self.dist_info_path = dist_info_path

    @classmethod
    def from_record(cls, record: PackageCacheRecord) -> list[PackageInfo]:
        dist_infos = set()
        for path in record.files:
            if record.name == "conda-index":
                print(path, os.path.dirname(path))
            if (maybe_dist_info := os.path.dirname(path)).endswith(".dist-info"):
                dist_infos.add(maybe_dist_info)
        if len(dist_infos) == 0:
            raise NoDistInfoDirFound(record.extracted_package_dir)
        return [cls(Path(record.extracted_package_dir, p)) for p in sorted(dist_infos)]

    @classmethod
    def from_conda_extracted_package_path(cls, path: str | Path) -> list[PackageInfo]:
        """Create a PackageInfo object given the path to an extracted conda package"""
        path = Path(path)
        matching_paths = [p for p in path.rglob("**/site-packages/*.dist-info/")]
        if len(matching_paths) == 0:
            raise NoDistInfoDirFound(path)
        return [cls(matching_path) for matching_path in matching_paths]

    def entry_points(self) -> dict[str, dict[str, str]]:
        """Get the entry points for a package.

        The return value for this function has the form:

        {
            entry_point_group:{
                name: entry_point,
                . . .
            }
            . . .
        }

        :returns: a dictionary of entry point groups and the corresponding entry points
                  expressed as a dict.

        ref: https://packaging.python.org/en/latest/specifications/entry-points/#file-format
        """
        entry_point_file = self.dist_info_path / "entry_points.txt"
        entry_points_config = CaseSensitiveConfigParser()
        entry_points_config.read(entry_point_file)

        entry_points = {}
        for section in entry_points_config.sections():
            entry_points[section] = dict(entry_points_config[section])

        return entry_points

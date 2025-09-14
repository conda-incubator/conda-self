from __future__ import annotations

import configparser
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .exceptions import NoDistInfoDirFound

if TYPE_CHECKING:
    from conda.models.records import PackageCacheRecord, PrefixRecord


# This is required for reading entry point info from an extracted package
# ref: https://packaging.python.org/en/latest/specifications/entry-points/#file-format
class CaseSensitiveConfigParser(configparser.ConfigParser):
    optionxform = staticmethod(str)  # type: ignore


class PackageInfo:
    def __init__(self, dist_info_path: Path):
        """Describe the dist-info for a Python package installed as a conda package"""
        self.dist_info_path = dist_info_path

    @classmethod
    def from_record(
        cls, record: PrefixRecord | PackageCacheRecord
    ) -> list[PackageInfo]:
        if not (paths := getattr(record, "files", None)):
            try:
                paths = (
                    Path(record.extracted_package_dir, "info/files")
                    .read_text()
                    .splitlines()
                )
            except FileNotFoundError:
                # empty packages have no info/files manifest and that's ok
                paths = []
        if not paths:
            return []
        dist_infos = set()
        for path in paths:
            if (maybe_dist_info := os.path.dirname(path)).endswith(".dist-info"):
                dist_infos.add(maybe_dist_info)
        basedir = getattr(record, "extracted_package_dir", sys.prefix)
        if not dist_infos:
            raise NoDistInfoDirFound(record.name, basedir)
        return [cls(Path(basedir, p)) for p in dist_infos]

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

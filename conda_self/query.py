""" """

from __future__ import annotations

import sys
from contextlib import suppress
from typing import TYPE_CHECKING

from conda.base.context import context
from conda.core.prefix_data import PrefixData
from conda.core.subdir_data import SubdirData
from conda.exceptions import (
    PackageNotInstalledError,
    PackagesNotFoundError,
)
from conda.models.channel import Channel
from conda.models.prefix_graph import PrefixGraph
from conda.models.version import VersionOrder

from .constants import PERMANENT_PACKAGES
from .exceptions import NoDistInfoDirFound
from .package_info import PackageInfo

if TYPE_CHECKING:
    from collections.abc import Iterable

    from conda.common.path import PathType
    from conda.models.records import PackageRecord, PrefixRecord


def check_updates(
    package_name: str,
    prefix: PathType = sys.prefix,
) -> tuple[bool, PrefixRecord, PackageRecord]:
    installed = PrefixData(prefix).get(package_name)
    if not installed:
        raise PackageNotInstalledError(prefix, package_name)

    subdir = installed.subdir
    subdirs = (subdir, (context.subdir if subdir == "noarch" else "noarch"))
    latest_available = latest(installed.name, installed.channel.base_url, subdirs)
    update_available = VersionOrder(latest_available.version) > VersionOrder(
        installed.version
    )

    return update_available, installed, latest_available


def latest(
    package_name: str, channel_url: str, subdirs: Iterable[str]
) -> PackageRecord:
    best = None
    max_version = VersionOrder("0.0.0dev0")
    channels = []
    for subdir in subdirs:
        channel = Channel(f"{channel_url}/{subdir}")
        channels.append(channel)
        for record in SubdirData(channel).query(package_name):
            if (record_version := VersionOrder(record.version)) > max_version:
                best = record
                max_version = record_version
    if best is None:
        raise PackagesNotFoundError(package_name, channels)
    return best


def permanent_dependencies() -> set[str]:
    """Get the full list of dependencies for all the permanent packages."""
    # In some dev environments, conda-self is installed as a PyPI package
    # and does not have its conda-meta/conda-self-*.json entry, which makes it
    # invisible to PrefixData()... unless we enable interoperability.
    installed = list(PrefixData(sys.prefix, interoperability=True).iter_records())
    prefix_graph = PrefixGraph(installed)

    protect = [*PERMANENT_PACKAGES]
    for record in installed:
        with suppress(NoDistInfoDirFound):
            for pkg_info in PackageInfo.from_record(record):
                if "conda" in pkg_info.entry_points():
                    protect.append(record.name)
                    break

    packages = []
    for pkg in dict.fromkeys(protect):
        node = next((rec for rec in prefix_graph.records if rec.name == pkg), None)
        if node:
            packages.append(node.name)
            packages.extend(
                [record.name for record in prefix_graph.all_ancestors(node)]
            )
    return set(packages)

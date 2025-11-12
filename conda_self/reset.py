from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from conda.base.context import context
from conda.core.link import PrefixSetup, UnlinkLinkTransaction
from conda.core.prefix_data import PrefixData
from conda.gateways.disk.read import yield_lines
from conda.misc import get_package_records_from_explicit

if TYPE_CHECKING:
    from pathlib import Path


def reset(
    prefix: str = sys.prefix,
    uninstallable_packages: set[str] = set(),
    reset_to: Path | None = None,
):
    installed = sorted(PrefixData(prefix).iter_records(), key=lambda x: x.name)
    if reset_to:
        reset_to_content = list(yield_lines(reset_to))
        packages_in_reset_env = sorted(
            get_package_records_from_explicit(reset_to_content), key=lambda x: x.name
        )
        packages_to_remove = [
            package for package in installed if package not in packages_in_reset_env
        ]
        packages_to_install = [
            package for package in packages_in_reset_env if package not in installed
        ]
        if not packages_to_remove and not packages_to_install:
            print("Environment is already reset")
            return
    else:
        packages_to_remove = [
            pkg for pkg in installed if pkg.name not in uninstallable_packages
        ]
        packages_to_install = []

    stp = PrefixSetup(
        target_prefix=prefix,
        unlink_precs=packages_to_remove,
        link_precs=packages_to_install,
        remove_specs=(),
        update_specs=(),
        neutered_specs=(),
    )

    txn = UnlinkLinkTransaction(stp)
    if not context.json and not context.quiet:
        txn.print_transaction_summary()
    txn.execute()

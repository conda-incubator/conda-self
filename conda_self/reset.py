from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from boltons.setutils import IndexedSet
from conda.base.context import context
from conda.core.link import PrefixSetup, UnlinkLinkTransaction
from conda.core.prefix_data import PrefixData
from conda.core.solve import diff_for_unlink_link_precs
from conda.gateways.disk.read import yield_lines
from conda.misc import get_package_records_from_explicit

if TYPE_CHECKING:
    from pathlib import Path


def reset(
    prefix: str = sys.prefix,
    uninstallable_packages: set[str] = set(),
    snapshot: Path | None = None,
):
    if snapshot:
        snapshot_content = list(yield_lines(snapshot))
        packages_in_reset_env = IndexedSet(
            get_package_records_from_explicit(snapshot_content)
        )
        packages_to_remove, packages_to_install = diff_for_unlink_link_precs(
            prefix, packages_in_reset_env
        )
        if not packages_to_remove and not packages_to_install:
            print("Nothing to do. Packages in target environment match the selected snapshot.")
            return
    else:
        installed = sorted(PrefixData(prefix).iter_records(), key=lambda x: x.name)
        packages_to_remove = tuple(
            pkg for pkg in installed if pkg.name not in uninstallable_packages
        )
        packages_to_install = ()

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

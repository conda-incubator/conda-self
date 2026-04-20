from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from boltons.setutils import IndexedSet
from conda.base.constants import EXPLICIT_MARKER
from conda.base.context import context
from conda.core.link import PrefixSetup, UnlinkLinkTransaction
from conda.core.prefix_data import PrefixData
from conda.core.solve import diff_for_unlink_link_precs
from conda.gateways.disk.read import yield_lines
from conda.misc import get_package_records_from_explicit
from conda.models.match_spec import MatchSpec

if TYPE_CHECKING:
    from pathlib import Path


def names_from_explicit(path: Path) -> set[str]:
    """Extract package names from a CEP-23 ``@EXPLICIT`` file without fetching.

    Parses each URL line with :class:`~conda.models.match_spec.MatchSpec`,
    which reads ``name``/``version``/``build`` from the tarball filename and
    strips any ``#md5=…``/``#sha256=…`` checksum fragment as a comment.  No
    network access, unlike :func:`conda.misc.get_package_records_from_explicit`.
    """
    return {
        MatchSpec(line).name for line in yield_lines(path) if line != EXPLICIT_MARKER
    }


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
            print(
                "Nothing to do. "
                "Packages in target environment match the selected snapshot."
            )
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

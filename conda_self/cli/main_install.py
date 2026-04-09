from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

HELP = "Add conda plugins to the 'base' environment."


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.description = HELP
    parser.add_argument(
        "--force-reinstall",
        action="store_true",
        help="Reinstall plugin even if it's already installed.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only report available updates, do not install.",
    )
    parser.add_argument("specs", nargs="+", help="Plugins to install")
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    import sys

    from conda.api import PackageCacheData, Solver
    from conda.base.context import context
    from conda.cli.common import stdout_json_success
    from conda.common.path import is_package_file
    from conda.core.package_cache_data import ProgressiveFetchExtract
    from conda.exceptions import CondaValueError, DryRunExit
    from conda.misc import _match_specs_from_explicit
    from conda.models.match_spec import MatchSpec
    from conda.reporters import confirm_yn

    from ..exceptions import SpecsAreNotPlugins
    from ..package_info import NoDistInfoDirFound, PackageInfo

    print("Installing plugins:", *args.specs)

    specs_to_add = []

    num_cp = sum(is_package_file(s) for s in args.specs)
    if num_cp:
        if num_cp == len(args.specs):
            specs_to_add = list(_match_specs_from_explicit(args.specs))
        else:
            raise CondaValueError(
                "cannot mix specifications with conda package filenames"
            )
    else:
        specs_to_add = [MatchSpec(spec) for spec in args.specs]

    specs_with_channels = [str(s) for s in specs_to_add if s.get("channel")]
    if specs_with_channels:
        joined = ", ".join(specs_with_channels)
        raise CondaValueError(
            f"Channel specifications are not supported: {joined}\n"
            "Configure channels via `conda config --add channels <channel>` instead."
        )

    solver = Solver(sys.prefix, context.channels, specs_to_add=specs_to_add)
    transaction = solver.solve_for_transaction()

    # If it's a dry run we don't want to be downloading anything
    if context.dry_run:
        actions = transaction._make_legacy_action_groups()[0]
        stdout_json_success(prefix=sys.prefix, actions=actions, dry_run=True)
        raise DryRunExit()

    specs_to_add_names = [spec.name for spec in specs_to_add]
    requested = [
        record
        for record in transaction.prefix_setups[sys.prefix].link_precs
        if record.name in specs_to_add_names
    ]

    # Download requested
    ProgressiveFetchExtract(requested).execute()

    package_cache_records = [PackageCacheData.query_all(prec)[0] for prec in requested]
    invalid_names = []
    for pcr in package_cache_records:
        try:
            infos = PackageInfo.from_record(pcr)
        except NoDistInfoDirFound:
            invalid_names.append(pcr.name)
        else:
            if not any("conda" in info.entry_points().keys() for info in infos):
                invalid_names.append(pcr.name)

    if invalid_names:
        raise SpecsAreNotPlugins(invalid_names)

    if not context.json:
        transaction.print_transaction_summary()
        confirm_yn()

    transaction.execute()

    if context.json:
        actions = transaction._make_legacy_action_groups()[0]
        stdout_json_success(prefix=sys.prefix, actions=actions)

    return 0

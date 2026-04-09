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

    from conda.api import Solver
    from conda.base.context import context
    from conda.exceptions import CondaValueError, DryRunExit
    from conda.models.match_spec import MatchSpec

    from ..exceptions import SpecsAreNotPlugins
    from ..install import (
        install_specs_in_protected_env,
        uninstall_specs_in_protected_env,
    )
    from ..validate import conda_plugin_packages, reload_plugin_packages

    specs_to_add = [MatchSpec(spec) for spec in args.specs]

    specs_with_channels = [str(s) for s in specs_to_add if s.get("channel")]
    if specs_with_channels:
        joined = ", ".join(specs_with_channels)
        raise CondaValueError(
            f"Channel specifications are not supported: {joined}\n"
            "Configure channels via `conda config --add channels <channel>` instead."
        )

    print("Installing plugins:", *args.specs)

    if context.dry_run:
        # Use in-process solver for dry-run so exceptions propagate correctly
        Solver(
            sys.prefix, context.channels, specs_to_add=specs_to_add
        ).solve_for_transaction()
        raise DryRunExit()

    returncode = install_specs_in_protected_env(
        args.specs,
        force_reinstall=args.force_reinstall,
        json=context.json,
        yes=context.always_yes,
    )

    if returncode != 0:
        return returncode

    reload_plugin_packages()

    spec_names = [spec.name for spec in specs_to_add]
    invalid_names = [name for name in spec_names if name not in conda_plugin_packages()]

    if invalid_names:
        uninstall_specs_in_protected_env(invalid_names, yes=True)
        raise SpecsAreNotPlugins(invalid_names)

    return 0

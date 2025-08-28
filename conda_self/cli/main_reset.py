from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

HELP = "Reset 'base' environment to essential packages only."


def configure_parser(parser: argparse.ArgumentParser) -> None:
    from conda.cli.helpers import add_output_and_prompt_options

    parser.description = HELP
    add_output_and_prompt_options(parser)
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    from conda.base.context import context
    from conda.reporters import confirm_yn

    from ..query import permanent_dependencies
    from ..reset import reset

    confirm_yn(
        "Proceed with resetting your 'base' environment?[y/n]:\n",
        default="no",
        dry_run=context.dry_run,
    )
    if context.quiet:
        print("Resetting 'base' environment...")
    uninstallable_packages = permanent_dependencies()
    reset(uninstallable_packages=uninstallable_packages)

    return 0

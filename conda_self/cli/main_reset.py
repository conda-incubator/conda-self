from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

HELP = "Reset 'base' environment to essential packages only."
RESET_TO_HELP = dedent(
    """
    State to reset the `base` environment to.\n
    `current` removes all packages except for `conda`, its plugins,
    and their dependencies.
    `installer` resets the `base` environment to the state provided
    by the installer.
    `migrate` resets the `base` environment to state after the last
    `conda self migrate` command.
    """
).lstrip()

WHAT_TO_EXPECT = dedent(
    """
    This will reset your `base` to ONLY contain `conda`, its plugins,
    and their dependencies.
    """
).lstrip()
SUCCESS = dedent(
    """
    SUCCESS!
    Reset the `base` environment to only the essential packages and plugins.
    """
).lstrip()
SUCCESS_STATE = dedent(
    """
    SUCCESS!
    Reset the `base` environment to pre-{state} state.
    """
).lstrip()


def configure_parser(parser: argparse.ArgumentParser) -> None:
    from conda.cli.helpers import add_output_and_prompt_options

    parser.description = HELP
    add_output_and_prompt_options(parser)
    parser.add_argument(
        "--reset-to",
        choices=("current", "installer", "migrate"),
        default="current",
        help=RESET_TO_HELP,
    )
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    from conda.base.context import context
    from conda.reporters import confirm_yn

    from ..constants import RESET_FILE_INSTALLER, RESET_FILE_MIGRATE
    from ..query import permanent_dependencies
    from ..reset import reset

    if not context.quiet:
        print(WHAT_TO_EXPECT)

    if args.reset_to == "installer":
        reset_file = Path(sys.prefix, "conda-meta", RESET_FILE_INSTALLER)
    elif args.reset_to == "migrate":
        reset_file = Path(sys.prefix, "conda-meta", RESET_FILE_MIGRATE)
    else:
        reset_file = None

    if reset_file and not reset_file.exists():
        raise FileNotFoundError(
            f"Failed to reset to `{args.reset_to}`. "
            f"Required file {reset_file} not found."
        )

    confirm_yn(
        "Proceed with resetting your 'base' environment?[y/n]:\n",
        default="no",
        dry_run=context.dry_run,
    )

    if not context.quiet:
        print("Resetting 'base' environment...")
    uninstallable_packages = (
        permanent_dependencies() if args.reset_to == "current" else set()
    )
    reset(uninstallable_packages=uninstallable_packages, reset_to=reset_file)

    if not context.quiet:
        if args.reset_to == "current":
            print(SUCCESS)
        else:
            print(SUCCESS_STATE.format(state=args.reset_to))

    return 0

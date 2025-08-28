from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

HELP = "Reset 'base' environment to essential packages only."

WHAT_TO_EXPECT = dedent("""
This will:
1.Reset your `base` to ONLY contain `conda` (and its dependencies), `conda` plugins
and `conda-self`.
2.Protect the `base` from further modifications
(unless the `--override-frozen` flag is used).
""").lstrip()
SUCCESS = dedent("""
SUCCESS!
The following operations were completed:

1. Resetting of the `base` to only the essential packages and plugins.
2. Protection of the `base` which prevents it from being modified
(unless an override flag is used).
""")


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

    if not context.quiet:
        print(WHAT_TO_EXPECT)

    confirm_yn(
        "Proceed with resetting your 'base' environment?[y/n]:\n",
        default="no",
        dry_run=context.dry_run,
    )

    if not context.quiet:
        print("Resetting 'base' environment...")
    uninstallable_packages = permanent_dependencies()
    reset(uninstallable_packages=uninstallable_packages)

    if not context.quiet:
        print(SUCCESS)

    return 0

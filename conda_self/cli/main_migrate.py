from __future__ import annotations

from typing import TYPE_CHECKING
from conda.reporters import confirm_yn


if TYPE_CHECKING:
    import argparse

HELP = "Migrate your `base` environment into a new  environment named `default` and protect your base."
WHAT_TO_EXPECT ="""
    This will:

    1. Duplicate your base environment in a new environment named `default`.
    2. Reset the `base` environment to only the essential packages and plugins.
    3. Protect the `base` environment, which prevents you from making further changes to it 
       (this behavior can be overriden using the `--override-frozen` flag).
    4. Activate your duplicate environment.

    This helps prevent issues like:

    1. Accidental breakage of the conda installation    
    2. Bloated and complex environments
    """

def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.description = HELP
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    from ..query import permanent_dependencies
    from ..reset import reset

    print(WHAT_TO_EXPECT)

    confirm_yn("Proceed with migrating your base environment?[y/n]:\n", default="no", dry_run=False)

    print("Resetting 'base' environment...")
    uninstallable_packages = permanent_dependencies()
    reset(uninstallable_packages=uninstallable_packages)

    return 0
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

HELP = "Update 'conda' and/or its plugins in the 'base' environment."


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.description = HELP
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Only report available updates, do not install.",
    )
    parser.add_argument(
        "--force-reinstall",
        action="store_true",
        help="Install latest conda available even "
        "if currently installed is more recent.",
    )
    parser.add_argument(
        "--plugin",
        help="Name of a conda plugin to update",
    )
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    import sys

    from conda.base.context import context
    from conda.exceptions import DryRunExit
    from conda.reporters import get_spinner

    from ..install import install_package_in_protected_env
    from ..query import check_updates
    from ..validate import validate_plugin_is_installed

    if args.plugin:
        validate_plugin_is_installed(args.plugin)
        package_name = args.plugin
    else:
        package_name = "conda"
    with get_spinner(f"Checking updates for {package_name}"):
        update_available, installed, latest = check_updates(package_name, sys.prefix)

    if not context.quiet:
        print(f"Installed {package_name}: {installed.version}")
        print(f"Latest {package_name}: {latest.version}")

    if not update_available:
        if not args.force_reinstall:
            print(f"{package_name} is already using the latest version available!")
            if args.dry_run:
                raise DryRunExit()
            return 0

    if args.dry_run:
        raise DryRunExit()

    return install_package_in_protected_env(
        package_name=package_name,
        package_version=latest.version,
        channel=installed.channel,
        force_reinstall=args.force_reinstall,
    )

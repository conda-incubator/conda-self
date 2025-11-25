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
        "--update-deps",
        action="store_true",
        help="Update dependencies that have available updates.",
    )
    update_group = parser.add_mutually_exclusive_group()
    update_group.add_argument(
        "--plugin",
        help="Name of a conda plugin to update",
    )
    update_group.add_argument(
        "--all",
        action="store_true",
        help="Update conda and all plugins.",
    )
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    from conda.base.context import context
    from conda.exceptions import DryRunExit
    from conda.reporters import get_spinner

    from ..install import install_package_list_in_protected_env
    from ..query import check_updates
    from ..validate import conda_plugin_packages, validate_plugin_is_installed

    if args.plugin:
        validate_plugin_is_installed(args.plugin)
        package_names = [args.plugin]
    elif args.all:
        package_names = ["conda", *conda_plugin_packages()]
    else:
        package_names = ["conda"]

    updates = {}
    channel = ""
    for package_name in package_names:
        with get_spinner(f"Checking updates for {package_name}"):
            update_available, installed, latest = check_updates(
                package_name, context.root_prefix
            )
        if not channel:
            channel = installed.channel

        if not context.quiet:
            print(f"Installed {package_name}: {installed.version}")
            print(f"Latest {package_name}: {latest.version}")

        if not update_available and not args.force_reinstall and not args.update_deps:
            print(f"{package_name} is already using the latest version available!")
        else:
            if not update_available and args.update_deps:
                print(
                    f"{package_name} is using the latest version available, "
                    "but may have outdated dependencies."
                )
            updates[package_name] = latest.version

    if args.dry_run:
        raise DryRunExit()
    elif not updates:
        return 0

    return install_package_list_in_protected_env(
        packages=updates,
        channel=channel,
        force_reinstall=args.force_reinstall,
        update_deps=args.update_deps,
    )

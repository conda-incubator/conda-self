from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

HELP = "Remove conda plugins from the 'base' environment."


def configure_parser(parser: argparse.ArgumentParser) -> None:
    parser.description = HELP
    parser.add_argument("specs", nargs="+", help="Plugins to remove/uninstall")
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    from ..exceptions import SpecsCanNotBeRemoved
    from ..install import uninstall_specs_in_protected_env
    from ..query import permanent_dependencies

    uninstallable_packages = permanent_dependencies(add_plugins=False)
    invalid_specs = []
    for spec in args.specs:
        if spec in uninstallable_packages:
            invalid_specs.append(spec)

    if invalid_specs:
        raise SpecsCanNotBeRemoved(invalid_specs)

    print("Removing plugins:", *args.specs)

    uninstall_specs_in_protected_env(args.specs, yes=False)
    return 0

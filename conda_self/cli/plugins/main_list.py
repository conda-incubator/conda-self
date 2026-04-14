from __future__ import annotations

import json as json_mod
from dataclasses import asdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

HELP = "List installed conda plugins."


def configure_parser(parser: argparse.ArgumentParser) -> None:
    from conda.cli.helpers import add_output_and_prompt_options

    parser.description = HELP
    add_output_and_prompt_options(parser)
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    from conda.base.context import context

    from ...validate import installed_plugins

    plugins = installed_plugins()

    if context.json:
        print(json_mod.dumps([asdict(p) for p in plugins], indent=2))
        return 0

    if not plugins:
        print("No plugins installed.")
        return 0

    name_w = max(len(p.name) for p in plugins)
    ver_w = max(len(p.version) for p in plugins)
    status_w = max(len(p.status) for p in plugins)

    header = f"{'Name':<{name_w}}  {'Version':<{ver_w}}  {'Status':<{status_w}}  Hooks"
    print(header)
    print("-" * len(header))

    for p in plugins:
        hooks_str = ", ".join(p.hooks) if p.hooks else ""
        print(
            f"{p.name:<{name_w}}  "
            f"{p.version:<{ver_w}}  "
            f"{p.status:<{status_w}}  "
            f"{hooks_str}"
        )

    return 0

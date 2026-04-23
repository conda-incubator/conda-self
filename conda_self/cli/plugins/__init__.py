from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def configure_parser(parser: argparse.ArgumentParser) -> None:
    from functools import partial

    from .main_list import HELP as LIST_HELP
    from .main_list import configure_parser as configure_parser_list

    subparsers = parser.add_subparsers(
        title="subcommands",
        dest="subcommand",
    )

    configure_parser_list(subparsers.add_parser("list", help=LIST_HELP))
    parser.set_defaults(func=partial(parser.parse_args, ["--help"]))


def execute(args: argparse.Namespace) -> int:
    return args.func(args)

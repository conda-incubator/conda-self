"""
Plugin definition for 'conda self' subcommand.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from conda import plugins

from .cli import configure_parser, execute, main_reset, main_migrate

if TYPE_CHECKING:
    from collections.abc import Iterable


@plugins.hookimpl
def conda_subcommands() -> Iterable[plugins.CondaSubcommand]:
    yield plugins.CondaSubcommand(
        name="self",
        action=execute,
        configure_parser=configure_parser,
        summary="Manage your conda 'base' environment safely.",
    )

@plugins.hookimpl
def conda_subcommands() -> Iterable[plugins.CondaSubcommand]:
    yield plugins.CondaSubcommand(
        name="migrate",
        action=main_migrate.execute,
        configure_parser=main_migrate.configure_parser,
        summary="Migrate your base into a 'default' environement and protect your base.",
    )

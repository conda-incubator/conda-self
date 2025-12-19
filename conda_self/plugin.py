"""
Plugin definition for 'conda self' subcommand.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from conda import plugins

from .cli import configure_parser, execute

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

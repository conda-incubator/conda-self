"""Plugin hook implementations for conda-self."""

from __future__ import annotations

from typing import TYPE_CHECKING

from conda.plugins.hookspec import hookimpl
from conda.plugins.types import CondaSubcommand

from .cli import configure_parser, execute

if TYPE_CHECKING:
    from collections.abc import Iterable


@hookimpl
def conda_subcommands() -> Iterable[CondaSubcommand]:
    """Expose the `self` subcommand."""

    yield CondaSubcommand(
        name="self",
        action=execute,
        configure_parser=configure_parser,
        summary="Manage your conda 'base' environment safely.",
    )

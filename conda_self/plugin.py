"""Plugin hook implementations for conda-self."""

from __future__ import annotations

from typing import TYPE_CHECKING

from conda.plugins.hookspec import hookimpl
from conda.plugins.types import CondaFixTask, CondaSubcommand

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


@hookimpl
def conda_fix_tasks():
    """Register the base fix task provided by conda-self."""
    from .cli import main_fix_base

    yield CondaFixTask(
        name="base",
        summary=main_fix_base.SUMMARY,
        configure_parser=main_fix_base.configure_parser,
        execute=main_fix_base.execute,
    )

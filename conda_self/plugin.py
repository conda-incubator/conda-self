"""Plugin hook implementations for conda-self."""

from __future__ import annotations

from typing import TYPE_CHECKING

from conda.plugins.hookspec import hookimpl
from conda.plugins.types import CondaHealthCheck, CondaSubcommand

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
def conda_health_checks() -> Iterable[CondaHealthCheck]:
    """Register the base environment protection health check.

    The fixer API (with ConfirmCallback) requires conda >= 26.1.0.
    On older conda versions, only the check action is registered.
    """
    from .health_checks import base_protection

    # Check if the new fixer API is available (conda >= 26.1.0)
    has_fixer_api = "fixer" in CondaHealthCheck.__dataclass_fields__

    if has_fixer_api:
        yield CondaHealthCheck(
            name="base-protection",
            action=base_protection.check,
            fixer=base_protection.fix,
            summary="Check if base environment is protected from accidental modifications",
            fix="Clone base to 'default' environment, reset base, and freeze it",
        )
    else:
        # Fallback for older conda versions without fixer support
        yield CondaHealthCheck(
            name="base-protection",
            action=base_protection.check,
        )

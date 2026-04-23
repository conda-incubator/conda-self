"""Plugin hook implementations for conda-self."""

from __future__ import annotations

from typing import TYPE_CHECKING

from conda.common.configuration import PrimitiveParameter, SequenceParameter
from conda.plugins.hookspec import hookimpl
from conda.plugins.types import CondaHealthCheck, CondaSetting, CondaSubcommand

from .cli import configure_parser, execute
from .cli.plugins import (
    configure_parser as configure_parser_plugins,
)
from .cli.plugins import (
    execute as execute_plugins,
)
from .constants import PERMANENT_PACKAGES, SELF_PERMANENT_PACKAGES_SETTING

if TYPE_CHECKING:
    from collections.abc import Iterable


@hookimpl
def conda_subcommands() -> Iterable[CondaSubcommand]:
    """Expose the `self` and `plugins` subcommands."""
    yield CondaSubcommand(
        name="self",
        action=execute,
        configure_parser=configure_parser,
        summary="Manage your conda 'base' environment safely.",
    )
    yield CondaSubcommand(
        name="plugins",
        action=execute_plugins,
        configure_parser=configure_parser_plugins,
        summary="Manage conda plugins.",
    )


@hookimpl
def conda_health_checks() -> Iterable[CondaHealthCheck]:
    """Register the base environment protection health check."""
    from .health_checks import base_protection

    yield CondaHealthCheck(
        name="base-protection",
        action=base_protection.check,
        fixer=base_protection.fix,
        summary="Check if base is frozen to prevent accidental modifications",
        fix="Clone base to 'default' environment, reset base, and freeze it",
    )


@hookimpl
def conda_settings() -> Iterable[CondaSetting]:
    """Register conda-self plugin settings."""
    yield CondaSetting(
        name=SELF_PERMANENT_PACKAGES_SETTING,
        description=(
            f"Additional packages (besides {', '.join(PERMANENT_PACKAGES)})"
            " to always keep in the 'base' environment. "
            "These packages and their dependencies will not be removed."
        ),
        parameter=SequenceParameter(PrimitiveParameter("", element_type=str)),
    )

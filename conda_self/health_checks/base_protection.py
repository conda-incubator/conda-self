# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""Health check: Base environment protection.

Checks if the base environment is protected (frozen) and offers to
protect it by cloning to a default environment and resetting base.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from conda.base.constants import OK_MARK, PREFIX_FROZEN_FILE, X_MARK
from conda.core.prefix_data import PrefixData
from conda.plugins.hookspec import hookimpl
from conda.plugins.types import CondaHealthCheck

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import Iterable


def is_base_environment(prefix: str) -> bool:
    """Check if the given prefix is the base environment."""
    return prefix == sys.prefix


def is_base_protected() -> bool:
    """Check if the base environment is protected (frozen)."""
    frozen_file = PrefixData(sys.prefix).prefix_path / PREFIX_FROZEN_FILE
    return frozen_file.exists()


def check(prefix: str, verbose: bool) -> None:
    """Health check: Verify base environment protection status.

    Only runs when checking the base environment.
    """
    if not is_base_environment(prefix):
        # Only check when running on base environment
        return

    if is_base_protected():
        print(f"{OK_MARK} Base environment is protected (frozen).\n")
    else:
        print(f"{X_MARK} Base environment is not protected.\n")
        if verbose:
            print(
                "  The base environment should be protected to prevent accidental\n"
                "  modifications that could break your conda installation.\n"
                "  Run `conda self install` or `conda doctor --fix` to protect it.\n"
            )


def fix(prefix: str, args: Namespace) -> int:
    """Fix: Protect the base environment.

    This clones the base environment to a new 'default' environment,
    resets base to essentials, and freezes it.
    """
    if not is_base_environment(prefix):
        print("Skipping: not running on base environment.")
        return 0

    if is_base_protected():
        print("Base environment is already protected.")
        return 0

    # Import and run the base protection workflow
    from ..cli.main_fix_base import execute

    # Set up args for the fix
    args.default_env = getattr(args, "default_env", "default")
    args.message = getattr(args, "message", "Protected by conda doctor --fix")

    return execute(args)


@hookimpl
def conda_health_checks() -> Iterable[CondaHealthCheck]:
    """Register the base environment protection health check."""
    yield CondaHealthCheck(
        name="Base Environment Protection",
        action=check,
        fix=fix,
        summary="Protect base environment from accidental modifications",
    )


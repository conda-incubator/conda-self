# Copyright (C) 2012 Anaconda, Inc
# SPDX-License-Identifier: BSD-3-Clause
"""Health check: Base environment protection.

Checks if the base environment is protected (frozen) and offers to
protect it by cloning to a default environment and resetting base.
"""

from __future__ import annotations

import sys
from textwrap import dedent
from typing import TYPE_CHECKING

from conda.base.constants import OK_MARK, PREFIX_FROZEN_FILE, X_MARK
from conda.core.prefix_data import PrefixData

if TYPE_CHECKING:
    from argparse import Namespace

WHAT_TO_EXPECT = dedent(
    """
    This will:

    1. Duplicate your `base` environment to a new environment named `{env_name}`.
    2. Reset the `base` environment to only the essential packages and plugins.
    3. Protect the `base` environment, which prevents you from making further
       changes to it (this behavior can be overridden using `--override-frozen`).

    This helps prevent issues like:

    1. Accidental breakage of the conda installation
    2. Bloated and complex environments that are difficult to update
    """
).lstrip()

SUCCESS_MESSAGE = dedent(
    """
    SUCCESS!
    The following operations were completed:

    1. Duplication of your current `base` environment to `{env_name}`.
    2. Resetting of the `base` to only the essential packages and plugins.
    3. Protection of the `base` which prevents it from being modified
       (unless an override flag is used).

    To use your packages, activate the new environment:

        conda activate {env_name}
    """
).lstrip()

BEST_PRACTICES = dedent(
    """
    BEST PRACTICES
    Follow these tips for a smoother `conda` experience:

    1. Do not modify the `base` environment.
    2. Use a different environment for your work going forward.
    3. Create a new environment for each new project.
    """
).lstrip()


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
                "  Run `conda doctor --fix` to protect it.\n"
            )


def fix(prefix: str, args: Namespace) -> int:
    """Fix: Protect the base environment.

    This clones the base environment to a new 'default' environment,
    resets base to essentials, and freezes it.
    """
    import json
    from contextlib import redirect_stdout
    from datetime import datetime
    from pathlib import Path

    from conda.base.context import context, sys_rc_path
    from conda.cli.main_config import _read_rc, _write_rc
    from conda.cli.main_list import print_explicit
    from conda.exceptions import CondaOSError
    from conda.gateways.disk.delete import rm_rf
    from conda.misc import clone_env
    from conda.reporters import confirm_yn

    from ..query import permanent_dependencies
    from ..reset import reset

    # Skip if not base or already protected
    if not is_base_environment(prefix):
        print("Skipping: not running on base environment.")
        return 0

    if is_base_protected():
        print("Base environment is already protected.")
        return 0

    default_env = getattr(args, "default_env", "default")
    message = getattr(args, "message", "Protected by conda doctor --fix")
    base_prefix = Path(sys.prefix)

    if not context.quiet:
        print(WHAT_TO_EXPECT.format(env_name=default_env))

    confirm_yn(
        "Proceed with protecting your base environment?",
        default="no",
        dry_run=context.dry_run,
    )

    if not context.quiet:
        print("Protecting 'base' environment...")

    # Get packages to keep in base
    uninstallable_packages = permanent_dependencies()

    # Check destination environment
    dest_prefix_data = PrefixData.from_name(default_env)

    if dest_prefix_data.is_environment():
        confirm_yn(
            f"WARNING: Environment '{default_env}' already exists.\n"
            "Remove it and recreate from base?",
            default="no",
            dry_run=context.dry_run,
        )
        reset(prefix=dest_prefix_data.prefix_path)
        rm_rf(dest_prefix_data.prefix_path)
    elif dest_prefix_data.exists():
        confirm_yn(
            f"WARNING: Directory exists at '{dest_prefix_data.prefix_path}' "
            "but is not a conda environment.\nContinue?",
            default="no",
            dry_run=context.dry_run,
        )

    # Take a snapshot
    snapshot_file = (
        base_prefix / "conda-meta" / f"explicit.{datetime.now():%Y-%m-%d-%H-%M-%S}.txt"
    )
    if not context.quiet:
        print(f"Taking snapshot: {snapshot_file}")
    with open(snapshot_file, "w") as f:
        with redirect_stdout(f):
            print_explicit(str(base_prefix))

    # Clone base to new default environment
    if not context.quiet:
        print(f"Cloning 'base' to '{default_env}'...")
    clone_env(
        str(base_prefix), str(dest_prefix_data.prefix_path), verbose=False, quiet=True
    )

    # Reset base
    if not context.quiet:
        print("Resetting 'base' environment...")
    reset(uninstallable_packages=uninstallable_packages)

    # Freeze base
    try:
        frozen_path = base_prefix / PREFIX_FROZEN_FILE
        frozen_path.write_text(json.dumps({"message": message}) if message else "")
    except OSError as e:
        raise CondaOSError(f"Could not protect environment: {e}") from e

    # Update default activation environment
    if not context.quiet:
        print(f"Setting default environment to '{default_env}'")
    rc_config = _read_rc(sys_rc_path)
    rc_config["default_activation_env"] = str(dest_prefix_data.prefix_path)
    _write_rc(sys_rc_path, rc_config)

    if not context.quiet:
        print(SUCCESS_MESSAGE.format(env_name=default_env))
        print(BEST_PRACTICES)
    return 0

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

from ..constants import RESET_FILE_BASE_PROTECTION, RESET_FILE_INSTALLER

if TYPE_CHECKING:
    import argparse


class Snapshot(Enum):
    """Snapshot modes accepted by ``conda self reset --snapshot``.

    Plain :class:`enum.Enum` for Python 3.10 compatibility; the string values
    double as argparse choices and user-facing mode names. Switch to
    :class:`enum.StrEnum` when 3.11 becomes the minimum supported version
    (mirrors the TODO on conda's ``EnvironmentFormat``).
    """

    CURRENT = "current"
    INSTALLER_EXACT = "installer-exact"
    INSTALLER_UPDATED = "installer-updated"
    BASE_PROTECTION = "base-protection"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        match self:
            case Snapshot.CURRENT:
                return "current"
            case Snapshot.INSTALLER_EXACT:
                return "installer-provided (exact)"
            case Snapshot.INSTALLER_UPDATED:
                return "installer-provided (with updates)"
            case Snapshot.BASE_PROTECTION:
                return "base-protection"

    @property
    def file_path(self) -> Path | None:
        """The ``conda-meta/*.txt`` file this snapshot mode reads, if any."""
        match self:
            case Snapshot.INSTALLER_EXACT | Snapshot.INSTALLER_UPDATED:
                return Path(sys.prefix, "conda-meta", RESET_FILE_INSTALLER)
            case Snapshot.BASE_PROTECTION:
                return Path(sys.prefix, "conda-meta", RESET_FILE_BASE_PROTECTION)
            case Snapshot.CURRENT:
                return None


# Tried in order when --snapshot is not provided; the first mode whose file
# exists on disk wins, otherwise we fall through to CURRENT.
FALLBACK_ORDER: tuple[Snapshot, ...] = (
    Snapshot.BASE_PROTECTION,
    Snapshot.INSTALLER_UPDATED,
)


HELP = "Reset 'base' environment to essential packages only."
SNAPSHOT_HELP = dedent(
    """
    Snapshot to reset the `base` environment to.
    `current` removes all packages except for `conda`, its plugins,
    and their dependencies.
    `installer-exact` restores the `base` environment to exactly what the
    installer shipped (may downgrade packages you have updated).
    `installer-updated` keeps the packages the installer shipped at their
    currently installed versions (no downgrade).
    `base-protection` restores the `base` environment to the snapshot saved
    by `conda doctor --fix` before protecting base.

    If not set, `conda self` will try to reset to the base-protection snapshot
    first, then to the installer-provided (preserving updates), and finally
    to the current snapshot.
    """
).lstrip()

WHAT_TO_EXPECT_ESSENTIALS = dedent(
    """
    This will reset your 'base' to ONLY contain 'conda', its plugins,
    and their dependencies.
    """
).lstrip()
WHAT_TO_EXPECT_SNAPSHOT = dedent(
    """
    This resets your 'base' to the {snapshot_name} snapshot
    and removes any packages outside of it.
    """
).lstrip()
SUCCESS = "Reset the 'base' environment to only the essential packages and plugins.\n"
SUCCESS_SNAPSHOT = "Reset the 'base' environment to {snapshot_name} snapshot.\n"


def configure_parser(parser: argparse.ArgumentParser) -> None:
    from conda.cli.helpers import add_output_and_prompt_options

    parser.description = HELP
    add_output_and_prompt_options(parser)
    parser.add_argument(
        "--snapshot",
        type=Snapshot,
        choices=list(Snapshot),
        help=SNAPSHOT_HELP,
    )
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    from conda.base.context import context
    from conda.reporters import confirm_yn

    from ..query import permanent_dependencies
    from ..reset import names_from_explicit, reset

    snapshot: Snapshot | None = args.snapshot
    reset_file: Path | None = None

    if snapshot is not None:
        reset_file = snapshot.file_path
    else:
        for fallback in FALLBACK_ORDER:
            candidate = fallback.file_path
            if candidate is not None and candidate.exists():
                snapshot = fallback
                reset_file = candidate
                break

    if reset_file is not None and not reset_file.exists():
        raise FileNotFoundError(
            f"Failed to reset to '{snapshot}'.\nRequired file {reset_file} not found."
        )

    if not context.quiet:
        if snapshot is not None:
            print(WHAT_TO_EXPECT_SNAPSHOT.format(snapshot_name=snapshot.display_name))
        else:
            print(WHAT_TO_EXPECT_ESSENTIALS)

    prompt = "Proceed with resetting your 'base' environment"
    if snapshot is not None:
        prompt += f" to the {snapshot.display_name} snapshot"
    confirm_yn(f"{prompt}?[y/n]:\n", default="no", dry_run=context.dry_run)

    if not context.quiet:
        print("Resetting 'base' environment...")

    match snapshot:
        case Snapshot.INSTALLER_UPDATED if reset_file is not None:
            keep = permanent_dependencies(add_plugins=True) | names_from_explicit(
                reset_file
            )
            reset(uninstallable_packages=keep)
        case Snapshot.INSTALLER_EXACT | Snapshot.BASE_PROTECTION:
            reset(snapshot=reset_file)
        case _:
            reset(uninstallable_packages=permanent_dependencies(add_plugins=True))

    if not context.quiet:
        if snapshot is not None:
            print(SUCCESS_SNAPSHOT.format(snapshot_name=snapshot.display_name))
        else:
            print(SUCCESS)

    return 0

from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse
    from typing import TypedDict

    class SnapshotData(TypedDict):
        file_path: Path
        snapshot_name: str


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

WHAT_TO_EXPECT = dedent(
    """
    This will reset your `base` to ONLY contain `conda`, its plugins,
    and their dependencies.
    """
).lstrip()
SUCCESS = dedent(
    """
    SUCCESS!
    Reset the `base` environment to only the essential packages and plugins.
    """
).lstrip()
SUCCESS_SNAPSHOT = dedent(
    """
    SUCCESS!
    Reset the `base` environment to {snapshot_name} snapshot.
    """
).lstrip()


def configure_parser(parser: argparse.ArgumentParser) -> None:
    from conda.cli.helpers import add_output_and_prompt_options

    parser.description = HELP
    add_output_and_prompt_options(parser)
    parser.add_argument(
        "--snapshot",
        choices=(
            "current",
            "installer-exact",
            "installer-updated",
            "base-protection",
        ),
        help=SNAPSHOT_HELP,
    )
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    from conda.base.context import context
    from conda.reporters import confirm_yn

    from ..constants import RESET_FILE_BASE_PROTECTION, RESET_FILE_INSTALLER
    from ..query import permanent_dependencies
    from ..reset import names_from_explicit, reset

    if not context.quiet:
        print(WHAT_TO_EXPECT)

    reset_data: dict[str, SnapshotData] = {
        "installer-exact": {
            "file_path": Path(sys.prefix, "conda-meta", RESET_FILE_INSTALLER),
            "snapshot_name": "installer-provided (exact)",
        },
        "installer-updated": {
            "file_path": Path(sys.prefix, "conda-meta", RESET_FILE_INSTALLER),
            "snapshot_name": "installer-provided (with updates)",
        },
        "base-protection": {
            "file_path": Path(sys.prefix, "conda-meta", RESET_FILE_BASE_PROTECTION),
            "snapshot_name": "base-protection",
        },
    }

    reset_file: Path | None = None
    snapshot_name = ""
    snapshot_choice = args.snapshot

    if not snapshot_choice:
        for fallback in ("base-protection", "installer-updated"):
            snapshot_data = reset_data[fallback]
            if snapshot_data["file_path"].exists():
                reset_file = snapshot_data["file_path"]
                snapshot_name = snapshot_data["snapshot_name"]
                snapshot_choice = fallback
                break
    elif snapshot_choice in reset_data:
        reset_file = reset_data[snapshot_choice]["file_path"]
        snapshot_name = reset_data[snapshot_choice]["snapshot_name"]

    if reset_file and not reset_file.exists():
        raise FileNotFoundError(
            f"Failed to reset to `{snapshot_choice}`.\n"
            f"Required file {reset_file} not found."
        )

    prompt = "Proceed with resetting your 'base' environment"
    if snapshot_name:
        prompt += f" to the {snapshot_name} snapshot"
    confirm_yn(f"{prompt}?[y/n]:\n", default="no", dry_run=context.dry_run)

    if not context.quiet:
        print("Resetting 'base' environment...")

    if snapshot_choice in ("installer-exact", "base-protection"):
        reset(snapshot=reset_file)
    elif snapshot_choice == "installer-updated":
        assert reset_file is not None
        keep = permanent_dependencies(add_plugins=True) | names_from_explicit(
            reset_file
        )
        reset(uninstallable_packages=keep)
    else:
        reset(uninstallable_packages=permanent_dependencies(add_plugins=True))

    if not context.quiet:
        if snapshot_name:
            print(SUCCESS_SNAPSHOT.format(snapshot_name=snapshot_name))
        else:
            print(SUCCESS)

    return 0

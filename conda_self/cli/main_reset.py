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
    `snapshot` removes all packages except for `conda`, its plugins,
    and their dependencies.
    `installer` resets the `base` environment to the snapshot provided
    by the installer.
    `migrate` resets the `base` environment to the snapshot after the last
    `conda migrate` command run.

    If not set, `conda self` will try to reset to the post-migration snapshot first,
    then to the installer-provided, and finally to the current snapshot.
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
        choices=("current", "installer", "migrate"),
        help=SNAPSHOT_HELP,
    )
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    from conda.base.context import context
    from conda.reporters import confirm_yn

    from ..constants import RESET_FILE_INSTALLER, RESET_FILE_MIGRATE
    from ..query import permanent_dependencies
    from ..reset import reset

    if not context.quiet:
        print(WHAT_TO_EXPECT)

    reset_data: dict[str, SnapshotData] = {
        "installer": {
            "file_path": Path(sys.prefix, "conda-meta", RESET_FILE_INSTALLER),
            "snapshot_name": "installer-provided",
        },
        "migrate": {
            "file_path": Path(sys.prefix, "conda-meta", RESET_FILE_MIGRATE),
            "snapshot_name": "post-migration",
        },
    }

    reset_file: Path | None = None
    snapshot_name = ""
    if not args.snapshot:
        for snapshot in ("migrate", "installer"):
            snapshot_data = reset_data[snapshot]
            if not snapshot_data["file_path"].exists():
                continue
            reset_file = snapshot_data["file_path"]
            snapshot_name = snapshot_data["snapshot_name"]
            break
    elif args.snapshot in reset_data:
        reset_file = reset_data[args.snapshot]["file_path"]
        snapshot_name = reset_data[args.snapshot]["snapshot_name"]

    if reset_file and not reset_file.exists():
        raise FileNotFoundError(
            f"Failed to reset to `{args.snapshot}`.\n"
            f"Required file {reset_file} not found."
        )

    prompt = "Proceed with resetting your 'base' environment"
    if snapshot_name:
        prompt += f" to the {snapshot_name} snapshot"
    confirm_yn(f"{prompt}?[y/n]:\n", default="no", dry_run=context.dry_run)

    if not context.quiet:
        print("Resetting 'base' environment...")
    uninstallable_packages = permanent_dependencies() if not reset_file else set()
    reset(uninstallable_packages=uninstallable_packages, snapshot=reset_file)

    if not context.quiet:
        if snapshot_name:
            print(SUCCESS_SNAPSHOT.format(snapshot_name=snapshot_name))
        else:
            print(SUCCESS)

    return 0

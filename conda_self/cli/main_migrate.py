from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

HELP = (
    "Protect `base` from accidental modifications and provide a modifiable copy "
    "that will be configured as default."
)
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
    4. Activation your duplicate environment `{env_name}`.
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


def configure_parser(parser: argparse.ArgumentParser) -> None:
    from conda.cli.helpers import add_output_and_prompt_options

    parser.description = HELP
    parser.add_argument(
        "--default-env",
        action="store",
        default="default",
        help="Name of the new default environment",
    )
    parser.add_argument(
        "--message",
        action="store",
        default=None,
        help="Message to add to the `conda-meta/frozen` file",
    )
    add_output_and_prompt_options(parser)
    parser.set_defaults(func=execute)


def execute(args: argparse.Namespace) -> int:
    from contextlib import redirect_stdout
    from datetime import datetime

    from conda.base.context import context, sys_rc_path
    from conda.cli.main_config import _read_rc, _write_rc
    from conda.cli.main_list import print_explicit
    from conda.core.prefix_data import PrefixData
    from conda.gateways.disk.delete import rm_rf
    from conda.misc import clone_env
    from conda.reporters import confirm_yn

    from ..query import permanent_dependencies
    from ..reset import reset

    if not context.quiet:
        print(WHAT_TO_EXPECT.format(env_name=args.default_env))

    confirm_yn(
        "Proceed with migrating your base environment?[y/n]:\n",
        default="no",
        dry_run=context.dry_run,
    )

    if not context.quiet:
        print("Protecting 'base' environment...")
    uninstallable_packages = permanent_dependencies()

    # Ensure the destination default environment does not exist already
    dest_prefix_data = PrefixData.from_name(args.default_env)

    if dest_prefix_data.is_environment():
        confirm_yn(
            "WARNING: A conda environment already exists at "
            f"'{dest_prefix_data.prefix_path}'\n\n"
            "Remove existing environment?\nThis will remove ALL packages "
            "contained within this specified prefix directory.\n\n",
            default="no",
            dry_run=context.dry_run,
        )
        reset(prefix=dest_prefix_data.prefix_path)
        rm_rf(dest_prefix_data.prefix_path)
    elif dest_prefix_data.exists():
        confirm_yn(
            "WARNING: A directory already exists at the target "
            f"location '{dest_prefix_data.prefix_path}'\n"
            "but it is not a conda environment.\n"
            "Continue creating environment",
            default="no",
            dry_run=context.dry_run,
        )

    src_prefix = sys.prefix

    # Take a snapshot of the current base environment by generating the explicit file.
    snapshot_filename = f"explicit.{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.txt"
    snapshot_dest = f"{src_prefix}/conda-meta/{snapshot_filename}"
    if not context.quiet:
        print(f"Taking a snapshot of 'base' and saving it to '{snapshot_dest}'...")
    with open(snapshot_dest, "w") as f:
        with redirect_stdout(f):
            print_explicit(src_prefix)

    # Clone the current base environment into the new default environment
    if not context.quiet:
        print(f"Cloning 'base' environment into '{args.default_env}'...")
    dest_prefix = str(dest_prefix_data.prefix_path)
    clone_env(src_prefix, dest_prefix, verbose=False, quiet=True)

    # Reset the base environment
    if not context.quiet:
        print("Resetting 'base' environment...")
    reset(uninstallable_packages=uninstallable_packages)

    # protect the base environment
    if args.message:
        try:
            Path(sys.prefix, "conda-meta", "frozen").write_text(
                json.dumps({"message": args.message})
            )
        except OSError:
            print("Environment could not be protected due to the following error: {e}")
            return 0
    else:
        try:
            Path(sys.prefix, "conda-meta", "frozen").touch()
        except OSError:
            print("Environment could not be protected due to the following error: {e}")
            return 0

    # Update the system level condarc default environment to point
    # to the new default environment
    if not context.quiet:
        print(f"Updating default environment location to '{args.default_env}'")
    rc_config = _read_rc(sys_rc_path)
    rc_config["default_activation_env"] = str(dest_prefix_data.prefix_path)
    _write_rc(sys_rc_path, rc_config)

    if not context.quiet:
        print(SUCCESS_MESSAGE.format(env_name=args.default_env))
        print(BEST_PRACTICES)
    return 0

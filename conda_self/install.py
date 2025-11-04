import sys
from subprocess import run

from conda.base.context import context


def install_package_in_protected_env(
    package_name: str,
    package_version: str,
    channel: str,
    force_reinstall: bool = False,
    json: bool = False,
) -> int:
    return install_package_list_in_protected_env(
        {package_name: package_version},
        channel,
        force_reinstall,
        json,
    )


def install_package_list_in_protected_env(
    packages: dict[str, str],
    channel: str,
    force_reinstall: bool = False,
    json: bool = False,
) -> int:
    specs = [f"{name}={version}" for name, version in packages.items()]
    process = run(
        [
            sys.executable,
            "-m",
            "conda",
            "install",
            f"--prefix={sys.prefix}",
            *(
                ("--override-frozen",)
                if hasattr(context, "protect_frozen_envs")
                else ()
            ),
            *(("--force-reinstall",) if force_reinstall else ()),
            *(("--json",) if json else ()),
            "--update-specs",
            "--override-channels",
            f"--channel={channel}",
            *specs,
        ]
    )
    return process.returncode


def uninstall_specs_in_protected_env(
    specs: list[str],
    json: bool = False,
    yes: bool = True,
) -> int:
    cmd = [
        sys.executable,
        "-m",
        "conda",
        "remove",
        f"--prefix={sys.prefix}",
        *(("--override-frozen",) if hasattr(context, "protect_frozen_envs") else ()),
        *(("--json",) if json else ()),
        *(("--yes",) if yes else ()),
        *specs,
    ]
    process = run(cmd)
    return process.returncode

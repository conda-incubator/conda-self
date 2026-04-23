from __future__ import annotations

from dataclasses import dataclass, field
from functools import cache
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

from conda.exceptions import CondaValueError

if TYPE_CHECKING:
    from conda.plugins.manager import CondaPluginManager

HOOK_PREFIX = "conda_"


def _normalize(name: str) -> str:
    """Normalize package name for comparison (hyphens vs underscores)."""
    return name.lower().replace("_", "-")


@dataclass(frozen=True)
class PluginInfo:
    """Metadata for an installed conda plugin."""

    name: str
    version: str
    canonical_name: str
    status: str
    hooks: list[str] = field(default_factory=list)

    @classmethod
    def from_plugin_manager(
        cls,
        pm: CondaPluginManager,
    ) -> list[PluginInfo]:
        """Discover all externally installed conda plugins.

        Walks ``importlib.metadata`` entry points in the ``conda``
        group, resolves each to its canonical plugin name, and
        collects version, status, and registered hooks.
        """
        seen: dict[str, PluginInfo] = {}
        for ep in entry_points(group="conda"):
            if ep.dist is None:
                continue
            loaded = ep.load()
            canonical = pm.get_name(loaded)
            if canonical is None or canonical in seen:
                continue
            status = "disabled" if pm.is_blocked(canonical) else "active"
            hooks = cls.hooks_for(pm, canonical)
            seen[canonical] = cls(
                name=ep.dist.name,
                version=ep.dist.metadata["Version"],
                canonical_name=canonical,
                status=status,
                hooks=hooks,
            )
        return sorted(seen.values(), key=lambda p: p.canonical_name)

    @staticmethod
    def hooks_for(
        pm: CondaPluginManager,
        canonical_name: str,
    ) -> list[str]:
        """Return the hook short names implemented by a plugin."""
        hooks: list[str] = []
        for attr_name in sorted(dir(pm.hook)):
            if not attr_name.startswith(HOOK_PREFIX):
                continue
            hook_caller = getattr(pm.hook, attr_name)
            for impl in hook_caller.get_hookimpls():
                if impl.plugin_name == canonical_name:
                    hooks.append(attr_name[len(HOOK_PREFIX) :])
                    break
        return hooks


@cache
def installed_plugins() -> list[PluginInfo]:
    """Return metadata for all installed conda plugins (cached)."""
    from conda.base.context import context

    return PluginInfo.from_plugin_manager(context.plugin_manager)


@cache
def conda_plugin_packages() -> set[str]:
    """Return normalized dist names of installed conda plugins.

    Scans entry points on disk so it works for newly installed
    packages that are not yet loaded into the plugin manager.
    Excludes conda-self.
    """
    return {
        _normalize(name)
        for ep in entry_points(group="conda")
        if ep.dist is not None
        and (name := ep.dist.name.strip())
        and _normalize(name) != "conda-self"
    }


def reload_plugin_packages() -> None:
    """Invalidate the caches to pick up newly installed packages."""
    installed_plugins.cache_clear()
    conda_plugin_packages.cache_clear()


def validate_plugin_is_installed(name: str) -> None:
    if _normalize(name) not in conda_plugin_packages():
        raise CondaValueError(
            f"Package '{name}' does not seem to be a valid conda plugin. "
            "Try one of:\n- " + "\n- ".join(sorted(conda_plugin_packages()))
        )

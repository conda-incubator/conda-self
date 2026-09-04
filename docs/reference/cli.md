# CLI reference

All commands are available as `conda self <cmd>`.

---

## self install

Add conda plugins to the base environment.

```
conda self install <specs>... [--force-reinstall] [--dry-run] [--yes] [--json] [--quiet]
```

`specs`
: One or more package names to install. Inline channel specs
  (`channel::pkg`) are rejected -- use [conda config](inv:conda:std:doc#commands/config) instead.

`--force-reinstall`
: Reinstall the plugin even if it is already installed.

`--dry-run`
: Show what would be installed without making changes.

`--yes`
: Skip confirmation prompts.

`--json`
: Output in JSON format.

`--quiet`
: Suppress non-essential output.

```bash
# Install a plugin
conda self install conda-index

# Force reinstall
conda self install --force-reinstall conda-index
```

After installation, conda-self validates that the package registers
a `conda` entry point. If it does not, the package is automatically
uninstalled and a `SpecsAreNotPlugins` error is raised.

---

## self remove

Remove conda plugins from the base environment.

```
conda self remove <specs>... [--dry-run] [--yes] [--json] [--quiet]
```

`specs`
: One or more package names to remove.

`--dry-run`
: Show what would be removed without making changes.

`--yes`
: Skip confirmation prompts.

Essential packages (conda, its core dependencies, and anything in
`plugins.self_permanent_packages`) cannot be removed. Attempting to do so
raises a `SpecsCanNotBeRemoved` error.

```bash
conda self remove conda-index
```

---

## self update

Update conda and/or its plugins in the base environment.

```
conda self update [--plugin NAME | --all] [--force-reinstall] [--dry-run] [--yes] [--json] [--quiet]
```

`--plugin`
: Update a single installed conda plugin.

`--all`
: Update conda, all plugins, and their dependencies. Passes `--all`
  to `conda install`.

`--force-reinstall`
: Force reinstall of packages.

`--dry-run`
: Show what would change without making modifications.

`--yes`
: Skip confirmation prompts.

```bash
# Update conda
conda self update

# Update a plugin
conda self update --plugin conda-libmamba-solver

# Update conda, plugins, and dependencies
conda self update --all
```

Bare `conda self update` and `--plugin` use `conda install --update-deps`
so the requested package's dependency chain can move when needed. `--all`
uses `conda install --all` so plugins and their dependencies can move
together.

---

## self reset

Reset the base environment from a snapshot or to essential packages.

```
conda self reset [--snapshot <type>] [--dry-run] [--yes] [--json] [--quiet]
```

`--snapshot`
: Which snapshot to reset to. Options:

  `current`
  : Remove all packages except conda, its plugins, and their
    dependencies, plus packages configured in
    `plugins.self_permanent_packages`.

  `installer-exact`
  : Restore the exact packages saved by the installer in
    `conda-meta/initial-state.explicit.txt`. This may downgrade packages.

  `installer-updated`
  : Retain currently installed packages whose names appear in the installer
    snapshot. This does not install missing packages. It also retains
    installed conda plugins and their dependencies.

  `base-protection`
  : Reset to the snapshot saved by `conda doctor --fix`
    (`conda-meta/base-protection-state.explicit.txt`).

  If not specified, conda-self selects `base-protection` when that snapshot
  exists, otherwise `installer-updated` when the installer snapshot exists,
  and otherwise `current`. It does not select `installer-exact`
  automatically.

```bash
# Auto-detect best snapshot
conda self reset

# Restore the exact installer state
conda self reset --snapshot installer-exact

# Keep installer-provided packages at installed versions
conda self reset --snapshot installer-updated

# Reset to base-protection snapshot
conda self reset --snapshot base-protection

# Strip to current essentials
conda self reset --snapshot current
```

Exact snapshot modes reuse packages already installed in base when their
URL, filename-derived identity, and any supplied checksum match the
explicit entry. Other artifacts that must be installed or relinked must be
available in the package cache or downloadable from the recorded URL. If
an artifact is unavailable from both sources, the exact reset cannot
proceed.

`installer-updated` does not remove installed conda plugins. Use
`installer-exact` or a suitable `base-protection` snapshot when reset must
remove a plugin that is not part of the selected snapshot.

---

## conda doctor base-protection

Check and fix the base environment protection status. This is a
health check registered via conda's `conda_health_checks`
[plugin hook](inv:conda:std:doc#dev-guide/plugins/index). See also
[conda doctor](inv:conda:std:doc#commands/doctor) for how health checks work.

```
conda doctor base-protection [--fix] [--dry-run]
```

`--fix`
: Enable base protection. This:
  1. Clones the current base environment to `default`
  2. Saves a snapshot to `conda-meta/base-protection-state.explicit.txt`
  3. Resets base to essential packages
  4. Freezes base via `PREFIX_FROZEN_FILE`

Without `--fix`, reports whether base is currently protected.

```bash
# Check status
conda doctor base-protection

# Enable protection
conda doctor base-protection --fix

# See all available health checks
conda doctor --list
```

:::{warning}
If your base environment contains non-conda packages (e.g. pip-installed),
`--fix` will warn you before proceeding. These packages are preserved
in the cloned `default` environment but will become non-functional
in the reset base.
:::

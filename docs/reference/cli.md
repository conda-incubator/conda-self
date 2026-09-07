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
`self_permanent_packages`) cannot be removed. Attempting to do so
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

Reset the base environment to essential packages only.

```
conda self reset [--snapshot <type>] [--dry-run] [--yes] [--json] [--quiet]
```

`--snapshot`
: Which snapshot to reset to. Options:

  `current`
  : Remove all packages except conda, its plugins, and their
    dependencies.

  `installer-exact`
  : Reset to the exact snapshot saved by the installer
    (`conda-meta/initial-state.explicit.txt`). This may downgrade packages.

  `installer-updated`
  : Retain currently installed packages whose names appear in the installer
    snapshot, alongside conda, conda-self, installed conda plugins, configured
    permanent packages, and their dependencies. This does not update packages
    or install missing packages.

  `base-protection`
  : Reset to the snapshot saved by `conda doctor --fix`
    (`conda-meta/base-protection-state.explicit.txt`).

  If not specified, conda-self tries `base-protection` first, then
  `installer-updated`, and falls back to `current`.

  `--snapshot installer` reports a migration error before confirmation or
  environment changes. Replace it with `installer-exact` to restore the exact
  recorded packages, or `installer-updated` to retain their currently installed
  versions alongside the packages described above.

```bash
# Auto-detect best snapshot
conda self reset

# Reset to installer state
conda self reset --snapshot installer-exact

# Retain installed versions of installer packages
conda self reset --snapshot installer-updated

# Reset to base-protection snapshot
conda self reset --snapshot base-protection

# Strip to current essentials
conda self reset --snapshot current
```

Exact resets reuse an installed package when its package URL and any recorded
checksum match the snapshot and it does not need to be reinstalled. Conda
prepares any remaining packages in a package cache before changing the target
environment. This includes noarch Python packages that must be relinked after
a Python major or minor version change. If preparation fails, the target
environment is unchanged. See {doc}`../guides/resetting-base` for details.

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

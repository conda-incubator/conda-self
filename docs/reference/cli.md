# CLI reference

All commands are available as `conda self <cmd>`.

---

## self install

Install conda plugins in the base environment.

```
conda self install <specs>... [--force-reinstall] [--dry-run] [--yes] [--json] [--quiet]
```

`specs`
: One or more package names to install. Channel-qualified package specs
  (`channel::pkg`) are rejected -- use [conda config](inv:conda:std:doc#commands/config) instead.

`--force-reinstall`
: Reinstall each requested plugin even if it is already installed.

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

After installation, conda-self validates that the package registers a `conda`
entry point. If it does not, the package is automatically uninstalled and a
`NotAPluginError` is raised.

---

## self remove

Remove conda plugins from the base environment.

```
conda self remove <specs>... [--force] [--dry-run] [--yes] [--json] [--quiet]
```

`specs`
: One or more package names to remove.

`--force`
: Remove packages even when they are protected from removal because they are
  permanent or dependencies of permanent packages.

`--dry-run`
: Show what would be removed without making changes.

`--yes`
: Skip confirmation prompts.

Conda, conda-self, packages configured in `plugins.self_permanent_packages`,
and their dependencies cannot be removed without `--force`. Attempting to do
so raises a `PluginRemoveError`.

```bash
conda self remove conda-index
```

---

## self update

Update conda, one conda plugin, or all packages in the base environment.

```
conda self update [--plugin NAME | --all] [--force-reinstall] [--dry-run] [--yes] [--json] [--quiet]
```

`--plugin`
: Update a single installed conda plugin.

`--all`
: Update all installed packages in the base environment. Passes `--all` to
  `conda install`.

`--force-reinstall`
: Uninstall and reinstall each requested package, even if it is already
  installed.

`--dry-run`
: Show what would change without making modifications.

`--yes`
: Skip confirmation prompts.

```bash
# Update conda
conda self update

# Update a plugin
conda self update --plugin conda-libmamba-solver

# Update all installed packages
conda self update --all
```

Bare `conda self update` and `--plugin` use `conda install --update-deps`
so the requested package's dependency chain can move when needed. `--all`
uses `conda install --all` so every installed package can move.

---

## self reset

Reset the base environment using a selected reset mode.

```
conda self reset [--snapshot <type>] [--dry-run] [--yes] [--json] [--quiet]
```

`--snapshot`
: Reset mode. Options:

  `current`
  : Remove all packages except conda, conda-self, installed conda plugins,
    packages configured in `plugins.self_permanent_packages`, and their
    dependencies.

  `installer`, `installer-exact`
  : Restore the exact packages saved by the installer in
    `conda-meta/initial-state.explicit.txt`. Both names select the same mode,
    which may downgrade packages.

  `installer-updated`
  : Retain currently installed packages whose names appear in the installer
    snapshot. This does not install missing packages. It also retains conda,
    conda-self, installed conda plugins, configured permanent packages, and
    their dependencies.

  `base-protection`
  : Reset to the snapshot saved by `conda doctor base-protection --fix`
    (`conda-meta/base-protection-state.explicit.txt`).

  If not specified, conda-self selects `base-protection` when that snapshot
  exists, otherwise `installer-updated` when the installer snapshot exists,
  and otherwise `current`. It does not select `installer` or
  `installer-exact` automatically.

```bash
# Automatically select a reset mode
conda self reset

# Restore the exact installer state
conda self reset --snapshot installer

# Keep installer-provided packages at installed versions
conda self reset --snapshot installer-updated

# Reset to base-protection snapshot
conda self reset --snapshot base-protection

# Remove all other packages
conda self reset --snapshot current
```

Exact snapshot modes reuse a package already installed in base when its
package URL and any checksum match the corresponding values in the snapshot.
For each remaining package, Conda uses the package from a package cache or
downloads and extracts it from its URL. If a required package cannot be made
available in a package cache, the exact reset stops before the target
environment is changed.

`installer-updated` does not remove installed conda plugins. Use `installer`,
`installer-exact`, or a suitable `base-protection` snapshot when reset must
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
  3. Removes packages not retained by base protection
  4. Marks base as frozen with the `conda-meta/frozen` environment marker file

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

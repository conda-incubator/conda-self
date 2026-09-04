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
: Reinstall each requested package even if it is already installed.

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
: Bypass conda-self's check for permanent packages and their dependencies.
  Conda still applies its own transaction checks and may refuse the removal.

`--dry-run`
: Show what would be removed without making changes.

`--yes`
: Skip confirmation prompts.

Without `--force`, conda-self refuses a direct request to remove conda,
conda-self, a package configured in `plugins.self_permanent_packages`, or one
of their dependencies. Conda's own transaction checks still apply with
`--force`.

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
so conda can update dependencies of the requested package. `--all` uses
`conda install --all` to update all installed packages.

---

## self reset

Reset the base environment using a selected reset mode.

```
conda self reset [--snapshot <type>] [--dry-run] [--yes] [--json] [--quiet]
```

`--snapshot`
: Reset mode. Options:

  `current`
  : Remove all conda packages except conda, conda-self, installed conda plugins,
    packages configured in `plugins.self_permanent_packages`, and their
    dependencies.

  `installer`, `installer-exact`
  : Restore exactly the conda packages saved by the installer in
    `conda-meta/initial-state.explicit.txt`. Both names select the same mode,
    which may downgrade packages.

  `installer-updated`
  : Retain currently installed conda packages whose names appear in the
    installer snapshot. This does not install missing packages. It also retains
    conda, conda-self, installed conda plugins, configured permanent packages,
    and their dependencies.

  `base-protection`
  : Reset to the snapshot saved by `conda doctor -n base base-protection --fix`
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

# Keep packages recorded by the installer at their installed versions
conda self reset --snapshot installer-updated

# Reset to base-protection snapshot
conda self reset --snapshot base-protection

# Remove all other conda packages
conda self reset --snapshot current
```

Exact snapshot modes reuse a conda package already installed in base when its
package URL and any checksum match the corresponding values in the snapshot.
For every other conda package, conda makes it available in a package cache,
downloading, verifying, and extracting it as needed. If a required package
cannot be made available in a package cache, the exact reset stops before the
target environment is changed.

`installer-updated` does not remove installed conda plugins. Use `installer`,
`installer-exact`, or a suitable `base-protection` snapshot when reset must
remove a plugin that is not part of the selected snapshot.

---

## conda doctor -n base base-protection

Check and fix the base environment protection status. This is a
health check registered via conda's `conda_health_checks`
[plugin hook](inv:conda:std:doc#dev-guide/plugins/index). See also
[conda doctor](inv:conda:std:doc#commands/doctor) for how health checks work.

```
conda doctor -n base base-protection [--fix] [--dry-run]
```

`--fix`
: Enable base protection. This:
  1. Attempts to save a snapshot to
     `conda-meta/base-protection-state.explicit.txt`
  2. Clones the current base environment to `default`
  3. Removes conda packages not retained by base protection
  4. Marks base as frozen with the `conda-meta/frozen` environment marker file

Snapshot export can be skipped when base cannot be represented in conda's
explicit format.

Without `--fix`, reports whether base is currently protected.

```bash
# Check status
conda doctor -n base base-protection

# Enable protection
conda doctor -n base base-protection --fix

# See all available health checks
conda doctor --list
```

:::{warning}
If your base environment contains external packages, such as packages installed
with pip, `--fix` will warn you before proceeding. These packages are preserved
in the cloned `default` environment but may no longer work in the reset base
environment.
:::

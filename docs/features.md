# Features

An overview of what conda-self provides and how the pieces fit
together.

## Base environment protection

The base environment is special -- it contains conda itself and is
always activated. Installing arbitrary packages into base risks
breaking conda. conda-self provides a health check that protects
base:

```bash
conda doctor base-protection --fix
```

This:

1. **Clones** the current base to a `default` environment, preserving
   all your packages for continued use
2. **Saves a snapshot** of base in `@EXPLICIT` format to
   `conda-meta/base-protection-state.explicit.txt`
3. **Resets** base to conda, its plugins, their dependencies, and any
   installer-provided packages (e.g. `mamba` in Miniforge)
4. **Freezes** base by writing a `PREFIX_FROZEN_FILE`, preventing
   regular [conda install](inv:conda:std:doc#commands/install) from modifying it

After protection, only `conda self` commands can modify base.

### Checking protection status

```bash
conda doctor base-protection
```

This reports whether base is currently protected (frozen) and whether
a snapshot exists.

## Plugin management

conda-self provides three commands for managing plugins in a protected
base environment:

### Install

![Install a plugin](../demos/install-plugin.gif)

```bash
conda self install conda-index
```

The install command:

1. Runs `conda install` as a subprocess with `--override-frozen`
2. After installation, scans `importlib.metadata` entry points for
   the `conda` group
3. If the installed package is not a valid [conda plugin](inv:conda:std:doc#dev-guide/plugins/index), uninstalls
   it and raises an error

This prevents non-plugin packages from accumulating in base.

### Update

![Update plugins](../demos/update.gif)

```bash
conda self update                    # update conda
conda self update --plugin conda-index
conda self update --all              # conda, plugins, and dependencies
conda self update --force-reinstall
```

Bare `conda self update` and `--plugin` pass their requested package to
`conda install --update-deps` so its dependency chain can move when
needed. `--all` passes `--all` so plugins and their dependencies can
move together.

### Remove

![Remove a plugin](../demos/remove.gif)

```bash
conda self remove conda-index
```

Essential packages (conda itself, its core dependencies, and packages
listed in `plugins.self_permanent_packages`) cannot be removed.

## Snapshots and reset

When base protection is enabled, conda-self saves a snapshot of the
pre-protection state. This snapshot can be used to restore base:

```bash
conda self reset                              # auto-detect the reset mode
conda self reset --snapshot installer        # restore exact installer state
conda self reset --snapshot installer-updated  # keep installer packages updated
conda self reset --snapshot base-protection  # restore protection snapshot
conda self reset --snapshot current          # strip to essentials only
```

Without `--snapshot`, conda-self selects `base-protection` when that
snapshot exists, otherwise `installer-updated` when the installer snapshot
exists, and otherwise `current`. Automatic reset does not select the
`installer` or `installer-exact` mode because an exact reset may downgrade
packages. Both names select the same exact installer reset.

`installer`, `installer-exact`, and `base-protection` reuse an installed
package when its URL, filename-derived identity, and any supplied checksum
match the explicit snapshot entry. Other required artifacts must be present
in the package cache or available from their recorded URLs. `installer-updated`
retains currently installed packages whose names appear in the installer
snapshot. It also retains installed conda plugins and their dependencies,
so it is not a substitute for an exact reset when removing an accidentally
installed plugin.

Snapshots are stored as `@EXPLICIT` files in `conda-meta/`:

- `base-protection-state.explicit.txt` -- saved by `conda doctor --fix`
- `initial-state.explicit.txt` -- saved by the installer (if available)

## Health check integration

conda-self registers a `base-protection` health check with conda's
[conda doctor](inv:conda:std:doc#commands/doctor) system:

```bash
conda doctor --list              # see all health checks
conda doctor base-protection     # check protection status
conda doctor base-protection --fix  # enable protection
```

This uses conda's `conda_health_checks` plugin hook, so the health
check appears alongside any other registered checks.

## Plugin validation

When installing packages, conda-self validates that they are actual
conda plugins by checking `importlib.metadata.entry_points(group="conda")`.
Package names are normalized (hyphens vs underscores) to handle
differences between conda naming conventions and Python packaging
metadata.

If a package is not a plugin, it is automatically uninstalled and
a `SpecsAreNotPlugins` error is raised.

## Permanent packages

The `plugins.self_permanent_packages` setting configures packages retained
by `conda self remove` and the `current` and `installer-updated` reset modes.
Exact snapshot modes may remove them when they are absent from the selected
snapshot.

Configure it in the [`.condarc` configuration file](inv:conda:std:doc#configuration):

```yaml
plugins:
  self_permanent_packages:
    - pip
    - setuptools
```

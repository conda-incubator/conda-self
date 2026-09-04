# Features

An overview of what conda-self provides and how the pieces fit
together.

## Base environment protection

The base environment contains conda itself. Installing arbitrary packages into
base risks breaking conda. conda-self provides a health check that protects
base:

```bash
conda doctor -n base base-protection --fix
```

This:

1. **Attempts to save a snapshot** of base in conda's explicit format to
   `conda-meta/base-protection-state.explicit.txt`. The file contains an
   `@EXPLICIT` marker followed by complete package URLs. Protection continues
   without the snapshot when base cannot be exported in this format
2. **Clones** the current base to a `default` environment, preserving all your
   packages for continued use
3. **Removes conda packages** other than conda, conda-self, configured permanent
   packages, their dependencies, and installed conda packages named in an
   available installer snapshot
4. **Marks** base as frozen by writing the `conda-meta/frozen` environment
   marker file

Regular conda commands refuse to modify the frozen base environment unless
`--override-frozen` is passed. `conda self install`, `update`, and `remove` pass
that option to conda.

### Checking protection status

```bash
conda doctor -n base base-protection
```

This reports whether base is currently protected.

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
3. If the installed package is not a valid
   [conda plugin](inv:conda:std:doc#dev-guide/plugins/index), uninstalls it and
   raises an error

This removes the requested package when plugin validation fails. Packages
installed as its dependencies may remain.

### Update

![Update plugins](../demos/update.gif)

```bash
conda self update                    # update conda
conda self update --plugin conda-index
conda self update --all              # all installed packages
conda self update --force-reinstall
```

Bare `conda self update` and `--plugin` use `conda install --update-deps` so
conda can update dependencies of the requested package. `--all` passes
`--all` to update all installed packages.

### Remove

![Remove a plugin](../demos/remove.gif)

```bash
conda self remove conda-index
```

Conda-self protects conda, conda-self, packages listed in
`plugins.self_permanent_packages`, and their dependencies from direct removal
requests unless `--force` is passed. Conda's own transaction checks still
apply.

## Snapshots and reset

When base protection is enabled, conda-self tries to save a snapshot of the
pre-protection state. When export succeeds, this snapshot can restore base:

```bash
conda self reset                              # auto-detect the reset mode
conda self reset --snapshot installer        # restore exact installer state
conda self reset --snapshot installer-updated  # retain installed versions
conda self reset --snapshot base-protection  # restore protection snapshot
conda self reset --snapshot current          # remove all other conda packages
```

Without `--snapshot`, conda-self selects `base-protection` when that
snapshot exists, otherwise `installer-updated` when the installer snapshot
exists, and otherwise `current`. Automatic reset does not select the
`installer` or `installer-exact` mode because an exact reset may downgrade
packages. Both names select the same exact installer reset.

`installer`, `installer-exact`, and `base-protection` reuse an installed conda
package when its package URL and any checksum match the corresponding values in
the snapshot. For every other conda package, conda makes it available in a
package cache, downloading, verifying, and extracting it as needed.
`installer-updated` retains currently installed conda packages whose names
appear in the installer snapshot. It also retains conda, conda-self, installed
conda plugins, configured permanent packages, and their dependencies, so it is
not a substitute for an exact reset when removing an accidentally installed
plugin.

Snapshots are stored in conda's explicit format in `conda-meta/`. Each file
contains an `@EXPLICIT` marker followed by complete package URLs:

- `base-protection-state.explicit.txt` -- saved by
  `conda doctor -n base base-protection --fix` when base can be exported
- `initial-state.explicit.txt` -- saved by the installer (if available)

## Health check integration

conda-self registers a `base-protection` health check with conda's
[conda doctor](inv:conda:std:doc#commands/doctor) system:

```bash
conda doctor --list              # see all health checks
conda doctor -n base base-protection     # check protection status
conda doctor -n base base-protection --fix  # enable protection
```

This uses conda's `conda_health_checks` plugin hook, so the health
check appears alongside any other registered checks.

## Plugin validation

When installing packages, conda-self validates that they are conda plugins by
checking `importlib.metadata.entry_points(group="conda")`. For validation,
conda-self compares package names case-insensitively and treats hyphens and
underscores as equivalent.

If a package is not a conda plugin, it is automatically uninstalled and a
`NotAPluginError` is raised.

## Permanent packages

The `plugins.self_permanent_packages` setting configures packages protected
from `conda self remove` and retained by the `current` and `installer-updated`
reset modes. Exact snapshot modes may remove them when they are absent from the
selected snapshot.

Configure it in the [`.condarc` configuration file](inv:conda:std:doc#configuration):

```yaml
plugins:
  self_permanent_packages:
    - pip
    - setuptools
```

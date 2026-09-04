# Resetting the base environment

How to restore your base environment from a snapshot or remove conda packages
not retained by the current mode.

## Automatically select a reset mode

```bash
conda self reset
```

conda-self selects the first available mode in this order:

1. `base-protection` -- restore the exact snapshot saved by
   [conda doctor -n base base-protection --fix](inv:conda:std:doc#commands/doctor)
2. `installer-updated` -- retain installed conda packages whose names appear
   in the installer snapshot
3. `current` -- retain conda, conda-self, installed conda plugins, configured
   permanent packages, and their dependencies

Snapshot availability is based on whether its file exists. A failure while
applying the selected snapshot is reported instead of switching modes.
Automatic reset does not select `installer` or `installer-exact`, which may
downgrade packages to the versions shipped by the installer.

## Select a reset mode

### Base-protection snapshot

Restore to the state captured by
`conda doctor -n base base-protection --fix`:

```bash
conda self reset --snapshot base-protection
```

This uses `conda-meta/base-protection-state.explicit.txt`.

### Exact installer snapshot

Restore to the original state from the installer (e.g. Miniforge):

```bash
conda self reset --snapshot installer
```

This uses `conda-meta/initial-state.explicit.txt` to restore exactly the conda
packages recorded by the installer and remove conda packages outside that
snapshot. `installer-exact` is an equivalent, more explicit name. Both may
downgrade packages that have since been updated.

Use this mode, or a suitable `base-protection` snapshot, when an
accidentally installed plugin must be removed. Not all installers provide
this file.

### Retain installed versions of installer packages

Retain currently installed conda packages whose names appear in the installer
snapshot:

```bash
conda self reset --snapshot installer-updated
```

This mode does not install packages that are missing from base. It also
keeps conda, conda-self, installed conda plugins, packages configured in
`plugins.self_permanent_packages`, and their dependencies. It does not remove
an accidentally installed plugin and does not recreate the exact installer
environment.

### Current mode

Remove all conda packages except conda, conda-self, installed
[conda plugins](inv:conda:std:doc#dev-guide/plugins/index), packages configured
in `plugins.self_permanent_packages`, and their dependencies, without using a
snapshot file:

```bash
conda self reset --snapshot current
```

## Dry run

Preview what a reset would do:

```bash
conda self reset --dry-run
conda self reset --snapshot installer --dry-run
```

## Packages required for an exact reset

For `installer`, `installer-exact`, and `base-protection`, conda-self first
reuses a conda package already installed in base when its package URL and any
checksum match the corresponding values in the snapshot. For every other conda
package, conda makes it available in a package cache, downloading, verifying,
and extracting it as needed.

Each conda package that must be installed or reinstalled must be present in a
package cache or downloadable from its URL in the snapshot. This can include
noarch Python packages that must be relinked after a Python major or minor
version change. If conda cannot make a required package available in a package
cache, the exact reset stops before the target environment is changed. Packages
downloaded and extracted before the failure may remain in a package cache.

## After a reset

After resetting, your base environment contains the conda packages selected by
the reset mode. [conda list](inv:conda:std:doc#commands/list) shows what is left
in base. You may need to reinstall plugins:

```bash
conda self install conda-index
```

Your `default` environment (created during base protection) is
unaffected by resets.

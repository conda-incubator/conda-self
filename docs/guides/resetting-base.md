# Resetting the base environment

How to restore your base environment from a snapshot when things go
wrong.

## Auto-detect the best snapshot

```bash
conda self reset
```

conda-self selects the first available mode in this order:

1. `base-protection` -- restore the exact snapshot saved by
   [conda doctor base-protection --fix](inv:conda:std:doc#commands/doctor)
2. `installer-updated` -- retain installed packages whose names appear in
   the installer snapshot
3. `current` -- strip to essentials without a snapshot

Snapshot availability is based on whether its file exists. A failure while
applying the selected snapshot is reported instead of switching modes.
Automatic reset does not select `installer` or `installer-exact`, which may
downgrade packages to the versions shipped by the installer.

## Reset to a specific snapshot

### Base-protection snapshot

Restore to the state captured when you first protected base:

```bash
conda self reset --snapshot base-protection
```

This uses `conda-meta/base-protection-state.explicit.txt`.

### Exact installer snapshot

Restore to the original state from the installer (e.g. Miniforge):

```bash
conda self reset --snapshot installer
```

This uses `conda-meta/initial-state.explicit.txt` to restore the exact
package artifacts shipped by the installer and remove packages outside
that snapshot. `installer-exact` is an equivalent, more explicit name. Both
may downgrade packages that have since been updated.
Use this mode, or a suitable `base-protection` snapshot, when an
accidentally installed plugin must be removed. Not all installers provide
this file.

### Updated installer packages

Retain currently installed packages whose names appear in the installer
snapshot:

```bash
conda self reset --snapshot installer-updated
```

This mode does not install packages that are missing from base. It also
keeps conda, installed conda plugins, their dependencies, and packages
configured in `plugins.self_permanent_packages`. It does not remove an
accidentally installed plugin and does not recreate the exact installer
environment.

### Current essentials

Strip base to only conda, its
[plugins](inv:conda:std:doc#dev-guide/plugins/index), their dependencies,
and packages configured in `plugins.self_permanent_packages`, without using a
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

## Unavailable snapshot artifacts

For `installer`, `installer-exact`, and `base-protection`, conda-self first
reuses packages already installed in base when they match the complete
explicit snapshot entry, including its URL and any supplied checksum. It
resolves only the remaining entries through the package cache or their
recorded URLs.

An exact reset still needs package bytes for any artifact that must be
installed or relinked. This can include `noarch: python` packages after a
Python major or minor version change. If the required artifact is neither
in the package cache nor downloadable, conda-self cannot complete the exact
reset and leaves the target prefix unchanged. Artifacts downloaded before
the failure may remain in the package cache.

## After a reset

After resetting, your base environment contains the packages selected by
the reset mode. [conda list](inv:conda:std:doc#commands/list) shows what is
left in base. You may need to reinstall plugins:

```bash
conda self install conda-index
```

Your `default` environment (created during base protection) is
unaffected by resets.

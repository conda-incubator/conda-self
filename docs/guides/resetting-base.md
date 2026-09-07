# Resetting the base environment

How to restore your base environment from a snapshot when things go
wrong.

## Auto-detect the best snapshot

```bash
conda self reset
```

conda-self tries snapshots in this order:

1. `base-protection` -- the snapshot saved by [conda doctor base-protection --fix](inv:conda:std:doc#commands/doctor)
2. `installer-updated` -- retain installed versions of packages named in the installer snapshot
3. `current` -- strip to essentials without a snapshot

## Reset to a specific snapshot

### Base-protection snapshot

Restore to the state captured when you first protected base:

```bash
conda self reset --snapshot base-protection
```

This uses `conda-meta/base-protection-state.explicit.txt`.

### Installer snapshot

Restore to the original state from the installer (e.g. Miniforge):

```bash
conda self reset --snapshot installer-exact
```

This uses `conda-meta/initial-state.explicit.txt`. Not all
installers provide this file. Restoring the exact snapshot may downgrade
packages that have since been updated.

### Installer snapshot with updated packages

Retain currently installed packages whose names appear in the installer
snapshot:

```bash
conda self reset --snapshot installer-updated
```

This also keeps conda, conda-self, installed conda plugins, configured
permanent packages, and their dependencies. It does not update packages or
install missing packages. Use `installer-exact` or a suitable
`base-protection` snapshot to remove a plugin outside the snapshot.

### Current essentials

Strip base to only conda, its [plugins](inv:conda:std:doc#dev-guide/plugins/index), and their dependencies,
without using any snapshot file:

```bash
conda self reset --snapshot current
```

## Migrate commands that use `installer`

`conda self reset --snapshot installer` reports a migration error before
asking for confirmation or changing the environment. Replace `installer`
with `installer-exact` to restore the exact recorded packages, or
`installer-updated` to retain their currently installed versions alongside
conda, conda-self, installed conda plugins, configured permanent packages,
and their dependencies. `installer-updated` does not update packages or
install missing packages.

## Dry run

Preview what a reset would do:

```bash
conda self reset --dry-run
conda self reset --snapshot installer-exact --dry-run
```

## Packages required for an exact reset

For `installer-exact` and `base-protection`, conda-self reuses a package
already installed in base when its package URL and any recorded checksum
match the snapshot and it does not need to be reinstalled. An unavailable
snapshot URL therefore does not prevent an exact reset when that package can
be reused.

Each package that must be installed or reinstalled must be present in a
package cache or downloadable from its URL in the snapshot. Conda downloads,
verifies, and extracts these packages as needed. This includes noarch Python
packages that must be relinked after a Python major or minor version change.
If a required package cannot be prepared, the exact reset stops before the
target environment is changed. Packages downloaded and extracted before the
failure may remain in a package cache.

## After a reset

After resetting, your base environment contains only essentials.
[conda info](inv:conda:std:doc#commands/info) lists what is left in base. You may need to reinstall plugins:

```bash
conda self install conda-index
```

Your `default` environment (created during base protection) is
unaffected by resets.

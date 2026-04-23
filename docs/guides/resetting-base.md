# Resetting the base environment

How to restore your base environment from a snapshot when things go
wrong.

## Auto-detect the best snapshot

```bash
conda self reset
```

conda-self tries snapshots in this order:

1. `base-protection` -- the snapshot saved by [conda doctor base-protection --fix](inv:conda:std:doc#commands/doctor)
2. `installer` -- the snapshot saved by the installer
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
conda self reset --snapshot installer
```

This uses `conda-meta/installer-state.explicit.txt`. Not all
installers provide this file.

### Current essentials

Strip base to only conda, its [plugins](inv:conda:std:doc#dev-guide/plugins/index), and their dependencies,
without using any snapshot file:

```bash
conda self reset --snapshot current
```

## Dry run

Preview what a reset would do:

```bash
conda self reset --dry-run
conda self reset --snapshot installer --dry-run
```

## After a reset

After resetting, your base environment contains only essentials.
[conda info](inv:conda:std:doc#commands/info) lists what is left in base. You may need to reinstall plugins:

```bash
conda self install conda-index
```

Your `default` environment (created during base protection) is
unaffected by resets.

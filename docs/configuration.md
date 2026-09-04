# Configuration

## conda settings

conda-self registers one custom setting via conda's `conda_settings`
[plugin hook](inv:conda:std:doc#dev-guide/plugins/index).

### plugins.self_permanent_packages

A list of package names protected from `conda self remove` and retained by the
`current` and `installer-updated` reset modes. Exact snapshot modes restore the
packages recorded in the snapshot and may remove configured permanent packages
that are absent from it.

Configure in [`.condarc`](inv:conda:std:doc#configuration):

```yaml
plugins:
  self_permanent_packages:
    - pip
    - setuptools
```

The reset modes retain these packages and their dependencies alongside conda,
conda-self, installed [conda plugins](inv:conda:std:doc#dev-guide/plugins/index),
and their dependencies. `conda self remove` refuses to remove a configured
permanent package or one of its dependencies unless `--force` is passed.

## Snapshot files

Snapshots are stored in `conda-meta/` inside the base prefix and use conda's
explicit format. Each file begins with an `@EXPLICIT` header followed by
complete package URLs.

| File | Created by | Purpose |
|------|-----------|---------|
| `base-protection-state.explicit.txt` | `conda doctor base-protection --fix` | Pre-protection state of base |
| `initial-state.explicit.txt` | Installer (e.g. Miniforge) | Original installer state |

These files are used by `conda self reset --snapshot <type>` to
restore base without running the solver. `base-protection`, `installer`, and
`installer-exact` reuse an installed package only when its package URL and any
checksum match the corresponding values in the snapshot. `installer-updated`
uses `initial-state.explicit.txt` only to select the installed package names
to retain.

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `DEFAULT_ENV_NAME` | `"default"` | Name of the environment created when cloning base |
| `RESET_FILE_BASE_PROTECTION` | `"base-protection-state.explicit.txt"` | Snapshot filename for base protection |
| `RESET_FILE_INSTALLER` | `"initial-state.explicit.txt"` | Snapshot filename from installer |
| `SELF_PERMANENT_PACKAGES_SETTING` | `"self_permanent_packages"` | Name of the condarc setting |

## Environment variables

conda-self does not define its own environment variables. It respects
all standard conda environment variables, including:

`CONDA_CHANNELS`
: Override configured channels for plugin installation.

`CONDA_DRY_RUN`
: Enable dry-run mode for all operations.

`CONDA_JSON`
: Enable JSON output for all operations.

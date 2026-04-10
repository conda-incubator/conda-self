# Configuration

## conda settings

conda-self registers one custom setting via conda's `conda_settings`
plugin hook.

### self_permanent_packages

A list of package names that should never be removed by
`conda self remove` or stripped during `conda self reset`.

Configure in `.condarc`:

```yaml
self_permanent_packages:
  - pip
  - setuptools
```

These packages are added to the set of "permanent" dependencies
(alongside conda itself and its plugins) when determining what
can be safely removed.

## Snapshot files

Snapshots are stored in `conda-meta/` inside the base prefix and
use conda's `@EXPLICIT` format (a list of exact package URLs).

| File | Created by | Purpose |
|------|-----------|---------|
| `base-protection-state.explicit.txt` | `conda doctor base-protection --fix` | Pre-protection state of base |
| `installer-state.explicit.txt` | Installer (e.g. Miniforge) | Original installer state |

These files are used by `conda self reset --snapshot <type>` to
restore base to a known state without running the solver.

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `DEFAULT_ENV_NAME` | `"default"` | Name of the environment created when cloning base |
| `SNAPSHOT_FILE_BASE_PROTECTION` | `"base-protection-state.explicit.txt"` | Snapshot filename for base protection |
| `RESET_FILE_INSTALLER` | `"installer-state.explicit.txt"` | Snapshot filename from installer |
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

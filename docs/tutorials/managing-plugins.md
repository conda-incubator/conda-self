# Managing plugins

This tutorial covers the complete lifecycle of
[conda plugins](inv:conda:std:doc#dev-guide/plugins/index) in a protected base
environment: installing, updating, and removing them.

## Prerequisites

- conda-self installed in base (`conda install -n base conda-self`)
- Base environment protected (see {doc}`protecting-base`)

## Install a plugin

![Install plugin demo](../../demos/install-plugin.gif)

```bash
conda self install conda-index
```

conda-self runs [conda install](inv:conda:std:doc#commands/install) as a subprocess with
`--override-frozen`, then validates that the installed package is
a real conda plugin by checking its entry points. If validation
fails, the package is automatically uninstalled.

### Multiple plugins at once

```bash
conda self install conda-index conda-auth
```

## Update plugins

![Update demo](../../demos/update.gif)

Update conda:

```bash
conda self update
```

Update a specific plugin:

```bash
conda self update --plugin conda-index
```

Update all installed packages:

```bash
conda self update --all
```

Force reinstall:

```bash
conda self update --force-reinstall
```

## Remove a plugin

![Remove demo](../../demos/remove.gif)

```bash
conda self remove conda-index
```

Conda-self protects conda, conda-self, configured permanent packages, and their
dependencies from direct removal requests unless `--force` is passed. If you
try without `--force`, you will see a `PluginRemoveError`. Conda's own
transaction checks still apply with `--force`.

## Channel configuration

conda-self uses your configured channels. Use
[conda config](inv:conda:std:doc#commands/config) to add or change channels
before installing. To install plugins from a custom channel:

```bash
# Add the channel first
conda config --add channels my-channel -n base

# Then install
conda self install my-plugin
```

Channel-qualified package specs (`conda-forge::my-plugin`) are not supported
and will produce an error. This keeps channel configuration consistent across
all operations.

## Next steps

- {doc}`../guides/resetting-base` -- Restore base from a snapshot
- {doc}`../guides/custom-channels` -- Use custom channels for plugins
- {doc}`../reference/cli` -- Full CLI reference

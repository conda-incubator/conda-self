# Managing plugins

This tutorial covers the complete lifecycle of [conda plugins](inv:conda:std:doc#dev-guide/plugins/index) in a
protected base environment: installing, updating, and removing them.

## Prerequisites

- conda-self installed in base (included by default in conda 26.1.1+)
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

Update all plugins and conda itself:

```bash
conda self update
```

Update specific packages:

```bash
conda self update conda
```

Force reinstall everything:

```bash
conda self update --force-reinstall
```

The solver finds the latest compatible versions automatically. No
manual version pinning is needed.

## Remove a plugin

![Remove demo](../../demos/remove.gif)

```bash
conda self remove conda-index
```

Essential packages (conda, its core dependencies) cannot be removed.
If you try, you will see a `SpecsCanNotBeRemoved` error.

## Channel configuration

conda-self uses your configured channels. Use [conda config](inv:conda:std:doc#commands/config) to add or change channels before installing. To install plugins from
a custom channel:

```bash
# Add the channel first
conda config --add channels my-channel -n base

# Then install
conda self install my-plugin
```

Inline channel specs (`conda-forge::my-plugin`) are not supported
and will produce an error. This keeps channel configuration
consistent across all operations.

## Verify installed plugins

After installing, you can verify which plugins are registered with
[conda info](inv:conda:std:doc#commands/info):

```bash
conda info
```

The output includes a "plugins" section listing all discovered
conda plugins and their versions.

## Next steps

- {doc}`../guides/resetting-base` -- Restore base from a snapshot
- {doc}`../guides/custom-channels` -- Use custom channels for plugins
- {doc}`../reference/cli` -- Full CLI reference

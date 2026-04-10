# Quick start

This guide walks you through protecting your base environment and
managing plugins with conda-self.

## Prerequisites

- conda 26.1.1 or later (conda-self is included as a default plugin)

## Protect your base environment

![Base protection demo](../demos/base-protection.gif)

Using [conda doctor](inv:conda:std:doc#commands/doctor), check whether base is currently protected:

```bash
conda doctor base-protection
```

If it is not, enable protection:

```bash
conda doctor base-protection --fix
```

This does three things:

1. Clones your current base environment to a new `default` environment
2. Resets base to only conda, its plugins, and their dependencies
3. Freezes base so regular [conda install](inv:conda:std:doc#commands/install) cannot modify it

:::{tip}
You only need to run this once. After protection, use `conda self`
commands to manage plugins in base.
:::

## Install a plugin

![Install plugin demo](../demos/install-plugin.gif)

```bash
conda self install conda-index
```

conda-self installs the package via subprocess, validates that it
registers as a [conda plugin](inv:conda:std:doc#dev-guide/plugins/index) (via entry points), and rolls back if
it does not.

## Update plugins

```bash
conda self update
```

This updates conda itself and all installed plugins to their latest
compatible versions.

## Remove a plugin

![Remove plugin demo](../demos/remove.gif)

```bash
conda self remove conda-index
```

Essential packages (conda itself, its core dependencies) cannot be
removed.

## Reset base

![Reset demo](../demos/reset.gif)

If something goes wrong, reset base to essentials:

```bash
conda self reset
```

## Next steps

- {doc}`tutorials/protecting-base` -- A deeper walkthrough of base
  protection and what happens under the hood
- {doc}`tutorials/managing-plugins` -- Install, update, and remove
  plugins with confidence
- {doc}`features` -- How base protection, snapshots, and plugin
  validation work
- {doc}`reference/cli` -- Every command and flag

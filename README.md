# conda-self

Commands to manage your `base` environment safely.

## `conda self`

Manage your conda 'base' environment safely.

```
$ conda self
usage: conda self [-V] [-h] {install,protect,remove,reset,update} ...

Manage your conda 'base' environment safely.

options:
  -V, --version         Show the 'conda-self' version number and exit.
  -h, --help            Show this help message and exit.

subcommands:
  {install,protect,remove,reset,update}
    install             Add conda plugins to the 'base' environment.
    protect             Protect 'base' environment from any further modifications
    remove              Remove conda plugins from the 'base' environment.
    reset               Reset 'base' environment to essential packages only.
    update              Update 'conda' and/or its plugins in the 'base' environment.
```

## `conda fix base`

The `conda fix` command is provided by conda and offers a framework for
fix tasks. The `conda-self` plugin provides the `base` fix task.

The `base` task helps you transition your conda setup to follow best practices
by creating a duplicate environment for daily use while protecting the base
environment from accidental modifications.

```
$ conda fix --list
Available fix tasks:

  base    Protect the `base` environment from accidental modifications and
          provide a modifiable copy that will be configured as default.
```

### What it does

Running `conda fix base` will:

1. Duplicate your `base` environment to a new environment (default: `default`).
2. Reset the `base` environment to only the essential packages and plugins.
3. Protect the `base` environment, preventing further modifications
   (unless an override flag is used).

This helps prevent issues like:

- Accidental breakage of the conda installation
- Bloated and complex environments that are difficult to update

### Usage

```
$ conda fix base --help
```

To run the migration with a custom name for the new default environment:

```
$ conda fix base --default-env myenv
```

## Installation

1. `conda install -n base conda-self`
2. `conda self --help`
3. `conda fix --list`

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md)

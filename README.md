# conda-self

Commands to manage your `base` environment safely.

## `conda self`

Manage your conda 'base' environment safely.

```
$ conda self
usage: conda self [-V] [-h] {install,remove,reset,update} ...

Manage your conda 'base' environment safely.

options:
  -V, --version         Show the 'conda-self' version number and exit.
  -h, --help            Show this help message and exit.

subcommands:
  {install,remove,reset,update}
    install             Add conda plugins to the 'base' environment.
    remove              Remove conda plugins from the 'base' environment.
    reset               Reset 'base' environment to essential packages only.
    update              Update 'conda' and/or its plugins in the 'base' environment.
```

## Base Environment Protection

To check if your base environment is protected, run:

```
conda doctor
```

To protect your base environment, run:

```
conda doctor --fix base-protection
```

This will:
1. Clone your current base environment to a new "default" environment
2. Reset base to essential packages only
3. Freeze the base environment to prevent modifications

To see all available health checks, run:

```
conda doctor --list
```

## Installation

1. `conda install -n base conda-self`
2. `conda self --help`

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md)

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

## Installation

1. `conda install -n base conda-self`
2. `conda self --help`

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md)

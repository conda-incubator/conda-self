# conda-self

A `self` command to manage your `base` environment safely.

The `conda self` plugin provides two main subcommands, `protect` and `reset`: 

- The `protect` subcommand lets you "freeze" your `base` environment so that you can't accidentally modify it. 
- The `reset` subcommand lets you "reset" your `base` environment to only contain the essential packages. Others are deleted and the `base` environment is returned to an "unbloated" state. 

Both `protect` and `reset` save the current state of the base environment in a `conda-meta/explicit.<time-stamp>.txt` file. 

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

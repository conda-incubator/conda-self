# conda-self

A `self` command to manage your `base` environment safely.

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
    protect             Remove conda plugins from the 'base' environment.
    remove              Protect 'base' environment from any further modifications
    reset               Reset 'base' environment to essential packages only.
    update              Update 'conda' and/or its plugins in the 'base' environment.
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md)

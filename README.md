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

## `conda migrate`

Perform migration tasks for conda environments and configuration.

```
$ conda migrate
Perform migration tasks for conda environments and configuration.

The migrate command helps you transition your conda setup to follow best
practices. Each migration task is a one-time operation that improves your
conda workflow.

Use `conda migrate --list` to see available migration tasks.

Available migration tasks:

  base    Protect `base` from accidental modifications and provide a modifiable
          copy that will be configured as default.

Run 'conda migrate <task> --help' for more information on a specific task.
```

### `conda migrate base`

Migrate your base environment to follow best practices by creating a duplicate
environment for daily use while protecting the base environment from accidental
modifications.

```
$ conda migrate base --help
```

## Installation

1. `conda install -n base conda-self`
2. `conda self --help`
3. `conda migrate --help`

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md)

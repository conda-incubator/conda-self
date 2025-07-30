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
    protect             Protect 'base' environment from any further modifications
    remove              Remove conda plugins from the 'base' environment.
    reset               Reset 'base' environment to essential packages only.
    update              Update 'conda' and/or its plugins in the 'base' environment.
```

## Try it locally

1. Make sure `pixi` and `git` are installed. [Instructions for `pixi`](https://pixi.sh/latest/installation/).
2. Clone this repository: `git clone https://github.com/conda-incubator/conda-self`
3. Change to that directory: `cd conda-self`
4. Run the help message: `pixi run conda self --help`

We _could_ just use the default pixi env to try things, but it doesn't write a good `history` file, so `conda self` will misunderstand what to do and remove everything sometimes. For now, let's use this default conda to create a demo environment to do things with:

1. Create a demo environment with `conda` and `pip`: `pixi run conda create -p .pixi/envs/demo conda pip`
2. Pseudo-activate it: `conda spawn ./.pixi/envs/demo`.
3. Install conda-self in it `pip install -e .`
4. Play with `python -m conda self`
   1. `python -m conda self install numpy`
   2. `python -m conda self install conda-rich`
   3. `python -m conda self update`
   4. `python -m conda self remove conda-rich`

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md)

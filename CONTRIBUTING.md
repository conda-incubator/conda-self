# How to Contribute

## With `pixi`

1. Make sure `pixi` and `git` are installed. [Instructions for `pixi`](https://pixi.sh/latest/installation/).
2. Clone this repository. 
```
git clone https://github.com/conda-incubator/conda-self
```
3. Change to that directory. 
```
cd conda-self
```
4. Run the help message. 
```
pixi run conda self --help
```

We _could_ just use the default pixi env to try things, but it doesn't write a good `history` file, so `conda self` will misunderstand what to do and remove everything sometimes. For now, let's use this default conda to create a demo environment to do things with:

1. Create a demo environment with `conda` and `pip`.
```
pixi run conda create -p .pixi/envs/demo conda pip
```
2. `conda-spawn` is included in the pixi configuration, which you can use to pseudo-activate the environment:
```
pixi run conda spawn ./.pixi/envs/demo
```  
If not, simply activate the environment.
```
conda activate .pixi/envs/demo
```
3. Install `conda-self` in it. 
```
pip install -e .
```
4. Play with `python -m conda self`.
   1. `python -m conda self update`
   2. `python -m conda self install numpy`
   3. `python -m conda self install conda-rich` 
   4. `python -m conda self remove conda-rich`

### Included Tasks

1. `pixi run test` to run the tests. Choose your desired Python version by picking the adequate environment.
2. `pixi run lint` to run the pre-commit linters and formatters.
3. `pixi run docs` to build the docs and `pixi run serve` to serve them in your browser.

## With `conda` only

1. Fork and clone this repository.
```
git clone https://github.com/conda-incubator/conda-self
```
2. Change to that directory. 
```
cd conda-self
```

3. Create a `conda` environment with `python` and `pip` in it.
```
conda create -n conda-self-dev python pip
```
4. Activate the environment and install `conda self`.
```
conda activate conda-self-dev
conda install conda-self --only-deps
```
5. `pip` install the package.
```
python -m pip install -e . --no-deps
```
6. Play with `python -m conda self`
   1. `python -m conda self install numpy`
   2. `python -m conda self install conda-rich`
   3. `python -m conda self update`
   4. `python -m conda self remove conda-rich`
# Protecting your base environment

This tutorial walks through setting up base environment protection
from scratch and understanding what happens at each step.

## Before you start

Verify conda-self is available (install with `conda install -n base conda-self`):

```bash
conda self --version
```

## Check current status

First, see if base is already protected with [conda doctor](inv:conda:std:doc#commands/doctor):

```bash
conda doctor -n base base-protection
```

If base is not protected, you will see a message indicating that the
health check found an issue.

## Enable protection

![Base protection demo](../../demos/base-protection.gif)

Run the fix:

```bash
conda doctor -n base base-protection --fix
```

You will be prompted to confirm. Here is what happens:

### Step 1: Save a snapshot

conda-self tries to save a snapshot of base in conda's explicit format to
`conda-meta/base-protection-state.explicit.txt`. The file contains an
`@EXPLICIT` marker followed by the complete URL for each conda package in the
environment before the reset, enabling exact restoration later. Protection
continues without the snapshot when base cannot be exported in this format.

### Step 2: Clone base to default

Your current base environment is cloned to a new environment called
`default`. All packages, including pip-installed ones, are preserved
in the clone. This is your fallback -- you can activate `default`
and continue working as before.

```bash
conda activate default
```

### Step 3: Reset base

Every conda package is removed except conda, conda-self, configured permanent
packages, their dependencies, and installed conda packages named in the
installer snapshot when that file exists.

### Step 4: Mark base as frozen

The `conda-meta/frozen` environment marker file is written, marking base as
frozen. Regular conda commands refuse to modify it unless `--override-frozen`
is passed. `conda self install`, `update`, and `remove` pass that option to
conda.

## Verify protection

Run the health check again:

```bash
conda doctor -n base base-protection
```

It should now report that base is protected.

Try installing a regular package into base:

```bash
conda install -n base numpy
```

This will fail with a frozen environment error. That is the expected
behavior.

## Use the default environment

Your previous packages are in the `default` environment:

```bash
conda activate default
python -c "import numpy; print(numpy.__version__)"
```

## External packages

If your base environment contains pip-installed packages, you will
see a warning before protection proceeds:

> Warning: Base environment contains N external packages that may no longer
> work in the reset base environment. They are preserved in the cloned
> 'default' environment.

These packages remain usable in `default` but may no longer work in the reset
base environment. Activate `default` to keep using them, or reinstall them in
another environment.

## Next steps

- {doc}`managing-plugins` -- Install plugins safely in the protected base
- {doc}`../guides/resetting-base` -- Restore base from a snapshot
- {doc}`../reference/cli` -- Full CLI reference

# Motivation

## The problem

The conda `base` environment is unique: it contains conda itself and
is always activated. This makes it a tempting target for installing
packages directly, but doing so creates real risks:

- Installing a package with conflicting dependencies can break conda
- A broken base environment means you cannot use conda to fix it
- Over time, base accumulates packages that are difficult to untangle
- There is no built-in way to "undo" what was installed in base

Many users have experienced the frustration of a broken base
environment. The usual advice is "don't install anything in base,"
but conda itself needs plugins (like the solver) installed there.

## Prior art

### Manual discipline

The most common approach is to simply avoid installing packages in
base. This works until you need to install a conda plugin, which
must live in base to be discovered. There is no tooling to enforce
this discipline.

### conda-protect

Earlier experiments explored freezing environments to prevent
accidental modification. conda-self builds on this idea by
integrating protection directly into conda's health check system
and providing safe commands for the operations that do need to
modify base.

## How conda-self fits in

conda-self takes a layered approach:

1. **Protection** -- freeze base so regular `conda install` cannot
   touch it
2. **Safe modification** -- provide `conda self install`, `update`,
   and `remove` commands that bypass the freeze through subprocess
   calls with `--override-frozen`, ensuring all of conda's safety
   checks (including frozen env protection) are respected
3. **Recovery** -- provide `conda self reset` to restore base from
   a snapshot if something goes wrong
4. **Health checks** -- integrate with `conda doctor` so protection
   status is visible alongside other environment health information

## Design choices

Subprocess over in-process API
: `conda self install` uses subprocess calls to `conda install`
  rather than the in-process Solver API. This ensures frozen
  environment protection (which lives in conda's CLI layer) is
  always respected. It is coarser but stays on the supported
  public surface.

Plugin validation after install
: Rather than pre-validating packages (which would require
  maintaining a list of known plugins), conda-self installs first
  and then checks `importlib.metadata` entry points. If the package
  is not a plugin, it is automatically rolled back.

Snapshot-based recovery
: Snapshots use conda's `@EXPLICIT` format -- a list of exact
  package URLs. This is the most reliable way to reproduce an
  environment state, as it bypasses the solver entirely.

Channel configuration over inline specs
: `conda self install conda-forge::pkg` is rejected. Instead,
  channels are configured via `conda config`, keeping channel
  settings consistent across install, update, and dependency
  resolution.

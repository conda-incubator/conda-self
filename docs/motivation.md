# Motivation

## What conda-self is

conda-self is a conda plugin that manages conda installations
themselves -- specifically the `base` environment where conda, its
plugins, and their dependencies live. It provides safe commands to
install, update, and remove plugins in base, and integrates with
[conda doctor](inv:conda:std:doc#commands/doctor) to protect base from accidental modification.

The name `conda self` reflects this purpose: conda managing itself.

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
but conda itself needs [plugins](inv:conda:std:doc#dev-guide/plugins/index) (like the solver, authentication
handlers, or custom subcommands) installed there to be discovered.

## How we got here

conda-self evolved through several iterations, shaped by UX testing
and community feedback:

1. The project started as a way to protect and manage the base
   environment. Early versions had a `conda self protect` command
   that froze base.

2. UX testing showed that "protect" did not communicate what the
   command actually does -- cloning base to a working environment
   and locking down the original. The command was renamed to
   `conda self migrate` (later `conda migrate`).

3. Rather than introducing a new top-level subcommand, the protection
   logic was integrated into conda's existing health check system via
   `conda doctor` and `conda doctor --fix`. This makes base
   protection discoverable alongside other environment health checks.

4. The name `conda self` (rather than `conda base`) was chosen
   because the plugin manages the conda installation, not just
   any environment named "base."

5. Reset functionality evolved from a simple "strip to essentials"
   to supporting multiple snapshot sources: the installer-provided
   state (e.g. from Miniforge), the pre-protection state saved by
   `conda doctor --fix`, and the current essential packages.

## Prior art

### Manual discipline

The most common approach is to simply avoid installing packages in
base. This works until you need to install a conda plugin, which
must live in base to be discovered. There is no tooling to enforce
this discipline.

### conda-protect

An earlier plugin that explored freezing environments to prevent
accidental modification. conda-self builds on this idea by
integrating protection directly into conda's health check system
and providing safe commands for the operations that do need to
modify base.

### Package managers with self-management

Tools like `rustup` (Rust), `pipx` (Python CLI tools), and
`brew` (macOS) separate the tool installation from user packages.
conda-self brings a similar separation to conda: the base
environment is for conda and its plugins, while user packages
live in named environments.

## Design choices

Subprocess over in-process API
: `conda self install` uses subprocess calls to [conda install](inv:conda:std:doc#commands/install)
  rather than the in-process Solver API. This ensures frozen
  environment protection (which lives in conda's CLI layer) is
  always respected. It also means all of conda's safety checks,
  channel resolution, and reporting work exactly as users expect.
  See [issue #15](https://github.com/conda-incubator/conda-self/issues/15)
  for the discussion that led to this decision.

Plugin validation after install
: Rather than pre-validating packages (which would require
  maintaining a list of known plugins), conda-self installs first
  and then checks `importlib.metadata` entry points. If the package
  is not a plugin, it is automatically rolled back. This is
  future-proof and works with any plugin, including third-party ones.

Snapshot-based recovery
: Snapshots use conda's `@EXPLICIT` format -- a list of exact
  package URLs. This is the most reliable way to reproduce an
  environment state, as it bypasses the solver entirely. Multiple
  snapshot sources (installer, base-protection, current) give users
  flexibility in how far back to restore.

Channel configuration over inline specs
: `conda self install conda-forge::pkg` is rejected. Instead,
  channels are configured via [conda config](inv:conda:std:doc#commands/config), keeping channel
  settings consistent across install, update, and dependency
  resolution.

Health checks over custom subcommands
: Base protection is implemented as a `conda doctor` health check
  rather than a standalone `conda self protect` or `conda migrate`
  command. This makes it discoverable via `conda doctor --list` and
  follows the pattern conda already provides for environment
  maintenance.

## What's next

conda-self is on track to graduate from the conda-incubator
organization to the main conda organization, becoming a default
plugin shipped with conda. See
[issue #89](https://github.com/conda-incubator/conda-self/issues/89)
for details.

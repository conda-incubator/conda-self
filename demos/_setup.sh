#!/usr/bin/env bash
# Sourced by VHS tapes to create a fresh Miniforge with conda-self installed.

MINIFORGE_DIR="/tmp/miniforge-demo"
INSTALLER="/tmp/miniforge.sh"
INSTALLER_URL="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname -s)-$(uname -m).sh"
CONDA_SELF_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_SHLVL CONDA_PROMPT_MODIFIER
unset PIXI_HOME PIXI_PROJECT_MANIFEST

if [[ ! -f "$INSTALLER" ]]; then
    curl -fsSL -o "$INSTALLER" "$INSTALLER_URL"
fi

rm -rf "$MINIFORGE_DIR"
bash "$INSTALLER" -b -p "$MINIFORGE_DIR" > /dev/null 2>&1
"$MINIFORGE_DIR/bin/pip" install -q -e "$CONDA_SELF_SRC" > /dev/null 2>&1

eval "$("$MINIFORGE_DIR/bin/conda" shell.bash hook)"
conda activate base

export PS1="\[\e[1;38;2;67;176;42m\]\$\[\e[0m\] "
export CONDA_CHANNELS=conda-forge

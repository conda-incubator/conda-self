#!/bin/bash
# Run linting for conda-self

set -e

echo "Running conda-self linting..."

# Check if we're in the right conda environment
if [[ "$CONDA_DEFAULT_ENV" != "conda-self-dev" ]] && [[ -z "$CI" ]]; then
    echo "Warning: Not in conda-self-dev environment. Consider running:"
    echo "conda activate conda-self-dev"
    echo "Continuing anyway..."
fi

# Run pre-commit on all files
pre-commit run --all-files

echo "Linting completed!"

#!/bin/bash
# Run tests for conda-self

set -e

echo "Running conda-self tests..."

# Check if we're in the right conda environment
if [[ "$CONDA_DEFAULT_ENV" != "conda-self-dev" ]] && [[ -z "$CI" ]]; then
    echo "Warning: Not in conda-self-dev environment. Consider running:"
    echo "conda activate conda-self-dev"
    echo "Continuing anyway..."
fi

# Run pytest with coverage
python -m pytest -xvs --cov=conda_self --cov-report=term-missing tests/

echo "Tests completed!"

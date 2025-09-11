#!/bin/bash
# Build documentation for conda-self

set -e

echo "Building conda-self documentation..."

# Setup docs environment if needed
if ! conda env list | grep -q conda-self-docs; then
    echo "Creating conda-self-docs environment..."
    conda env create -f environment-docs.yml
fi

# Activate docs environment and build
echo "Activating docs environment and building..."
eval "$(conda shell.bash hook)"
conda activate conda-self-docs

# Build docs
cd docs
python -m sphinx.cmd.build -M dirhtml . _build
cd ..

echo "Documentation build completed!"
echo "To serve docs: python -m http.server --directory docs/_build/dirhtml"

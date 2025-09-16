#!/bin/bash
# Setup development environment for conda-self

set -e

echo "Setting up conda-self development environment..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "Error: conda is not available. Please install conda first."
    exit 1
fi

# Create development environment
echo "Creating conda-self-dev environment..."
if conda env list | grep -q conda-self-dev; then
    echo "Environment already exists, updating..."
    conda env update -f environment-dev.yml
else
    conda env create -f environment-dev.yml
fi

echo "Environment setup complete!"
echo "To activate: conda activate conda-self-dev"

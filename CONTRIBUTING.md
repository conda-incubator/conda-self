# How to Contribute

## Setup Development Environment

This project uses conda's native capabilities for development and testing. Follow these steps to get started:

### Prerequisites

**You must have conda installed before proceeding.**

- **conda** - Install [Miniforge](https://conda-forge.org/download/) (recommended) or [Miniconda](https://www.anaconda.com/docs/getting-started/miniconda/main)
- git

> 💡 **Note**: All setup commands below require `conda` to be available in your PATH. If you just installed conda, you may need to restart your terminal or run `conda init` first.

### Quick Setup

1. Fork and clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/conda-self
cd conda-self
```

2. Set up the development environment:
```bash
# Unix/Linux/macOS
./scripts/setup.sh

# Windows
scripts\setup.bat
```

3. Activate the environment:
```bash
conda activate conda-self-dev
```

4. Verify the installation works by testing the plugin:
```bash
python -m conda self --help
```

### Manual Setup (Alternative)

If you prefer to set up manually:

1. Create and activate the conda environment:
```bash
conda env create -f environment-dev.yml
conda activate conda-self-dev
```

2. The environment automatically installs the package in editable mode via pip.

### Development Workflow

#### Running Tests
```bash
# Unix/Linux/macOS
./scripts/test.sh

# Windows
scripts\test.bat

# Or manually:
python -m pytest -xvs --cov=conda_self tests/
```

#### Running Linting
```bash
# Unix/Linux/macOS
./scripts/lint.sh

# Windows
scripts\lint.bat

# Or manually:
pre-commit run --all-files
```

#### Building Documentation
```bash
# Unix/Linux/macOS
./scripts/docs.sh

# Windows
scripts\docs.bat
```

#### Testing Your Changes

**Method 1: Testing within development environment**
```bash
conda activate conda-self-dev

# Test the module directly
python -m conda self --help
python -c "import conda_self; print('Version:', conda_self.__version__)"
```

**Method 2: Testing as a real conda plugin (recommended for full testing)**
```bash
# Install your development version in base environment
conda activate base
pip install -e /path/to/your/conda-self

# Now you can use it as a real conda plugin
conda self --help
conda self update  # Update conda itself
conda self install conda-auth  # Install a conda plugin (for private channel auth)
conda self remove conda-auth   # Remove the plugin when done testing

# When done testing, uninstall from base
pip uninstall conda-self
```

**Method 3: Testing in isolated environment**
```bash
# Create a clean test environment with conda
conda create -n test-env python conda pip
conda activate test-env

# Install your development version
pip install -e /path/to/your/conda-self

# Test using that environment's conda
python -m conda self --help
```

### Environment Files

- `environment-dev.yml` - Main development environment with testing tools
- `environment-docs.yml` - Documentation building environment

## Code Standards

This project follows these standards:
- Code formatting with `ruff`
- Type checking with `mypy`
- Testing with `pytest`
- Pre-commit hooks for code quality

All checks run automatically in CI, but please run them locally:
```bash
pre-commit run --all-files
```

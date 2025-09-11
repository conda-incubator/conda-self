@echo off
REM Run tests for conda-self

echo Running conda-self tests...

REM Check if we're in the right conda environment
if not "%CONDA_DEFAULT_ENV%"=="conda-self-dev" (
    if not defined CI (
        echo Warning: Not in conda-self-dev environment. Consider running:
        echo conda activate conda-self-dev
        echo Continuing anyway...
    )
)

REM Run pytest with coverage
python -m pytest -xvs --cov=conda_self --cov-report=term-missing tests/

echo Tests completed!

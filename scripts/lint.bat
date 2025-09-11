@echo off
REM Run linting for conda-self

echo Running conda-self linting...

REM Check if we're in the right conda environment
if not "%CONDA_DEFAULT_ENV%"=="conda-self-dev" (
    if not defined CI (
        echo Warning: Not in conda-self-dev environment. Consider running:
        echo conda activate conda-self-dev
        echo Continuing anyway...
    )
)

REM Run pre-commit on all files
pre-commit run --all-files

echo Linting completed!

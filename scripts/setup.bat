@echo off
REM Setup development environment for conda-self

echo Setting up conda-self development environment...

REM Check if conda is available
conda --version >nul 2>&1
if errorlevel 1 (
    echo Error: conda is not available. Please install conda first.
    exit /b 1
)

REM Create development environment
echo Creating conda-self-dev environment...
conda env list | findstr /C:"conda-self-dev" >nul
if errorlevel 1 (
    conda env create -f environment-dev.yml
) else (
    echo Environment already exists, updating...
    conda env update -f environment-dev.yml
)

echo Environment setup complete!
echo To activate: conda activate conda-self-dev

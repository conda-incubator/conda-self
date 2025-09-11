@echo off
REM Build documentation for conda-self

echo Building conda-self documentation...

REM Setup docs environment if needed
conda env list | findstr /C:"conda-self-docs" >nul
if errorlevel 1 (
    echo Creating conda-self-docs environment...
    conda env create -f environment-docs.yml
)

REM Activate docs environment and build
echo Activating docs environment and building...
call conda activate conda-self-docs

REM Build docs
cd docs
python -m sphinx.cmd.build -M dirhtml . _build
cd ..

echo Documentation build completed!
echo To serve docs: python -m http.server --directory docs/_build/dirhtml

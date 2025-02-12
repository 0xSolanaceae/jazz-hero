@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

cd /d "%~dp0"

where python >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install it from https://www.python.org/downloads/
    exit /b 1
)

python -m ensurepip --default-pip

IF EXIST requirements.txt (
    echo Installing required dependencies...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt || (
        echo Failed to install dependencies.
        exit /b 1
    )
)

IF EXIST src\main.py (
    echo Running src\main.py...
    python src\main.py
) ELSE (
    echo Error: src\main.py not found. Make sure the script is in the correct location.
    exit /b 1
)

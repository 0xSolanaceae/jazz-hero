#!/bin/bash

cd "$(dirname "$0")"

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Installing via Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "Homebrew is not installed. Please install Homebrew first: https://brew.sh/"
        exit 1
    fi
    brew install python3
fi

if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Installing..."
    python3 -m ensurepip --default-pip
fi

if [ -f "requirements.txt" ]; then
    echo "Installing required dependencies..."
    pip3 install -r requirements.txt || { echo "Failed to install dependencies."; exit 1; }
fi

if [ -f "src/main.py" ]; then
    echo "Running src/main.py..."
    python3 src/main.py
else
    echo "Error: src/main.py not found. Make sure the script is in the correct location."
    exit 1
fi

exit
#!/bin/bash
set -e

echo "--- Removing existing .venv ---"
rm -rf .venv

echo "--- Creating new .venv with Python 3.13 ---"
if ! command -v python3.13 &> /dev/null; then
    echo "Error: python3.13 is not installed or not in PATH."
    exit 1
fi

python3.13 -m venv .venv

echo "--- Activating .venv and installing dependencies ---"
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

echo "--- Rebuild complete ---"
echo "Run 'source .venv/bin/activate' to start using the new environment."
source .venv/bin/activate
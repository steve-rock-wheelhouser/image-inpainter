#!/bin/bash
set -e

echo "--- Setting up PyInstaller Environment ---"
source .venv/bin/activate
pip install pyinstaller

echo "--- Cleaning previous builds ---"
rm -rf build dist

echo "--- Building with PyInstaller ---"
# --onefile: Create a single executable
# --windowed: Do not show a console window when running
# --add-data: Bundle the assets folder (format is source:dest)
# --collect-all: Aggressively collect all files for cairo libraries to prevent missing imports
pyinstaller --noconfirm --onefile --windowed \
    --name "image_inpainter" \
    --icon "assets/icons/icon.png" \
    --add-data "assets:assets" \
    --hidden-import "cairosvg" \
    --hidden-import "cairocffi" \
    --collect-all "cairosvg" \
    --collect-all "cairocffi" \
    image_inpainter.py

echo "--- Success! Binary created: dist/image_inpainter ---"
# PowerShell script to build a Windows executable for image-inpainter

# Stay in the packaging-windows directory
Set-Location -Path $PSScriptRoot

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

# Activate virtual environment
& ".\.venv\Scripts\Activate.ps1"

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
python -m pip install PySide6 opencv-python numpy Pillow cairosvg nuitka zstandard ordered-set pyinstaller

# Add Python Scripts to PATH
$pythonScripts = ".venv\Scripts"
$env:Path += ";$pythonScripts"

# Build the executable with PyInstaller
pyinstaller --onefile --windowed --add-data "../assets;assets" --icon "../assets/icons/icon.ico" "../image_inpainter.py"

Write-Host "Executable built successfully. Check the 'dist' folder for image_inpainter.exe"
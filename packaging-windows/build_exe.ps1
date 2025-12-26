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

# Clean previous build artifacts to ensure fresh icon embedding
if (Test-Path "build") { Remove-Item -Path "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item -Path "dist" -Recurse -Force }

# Build the executable with PyInstaller
pyinstaller --name "Image Inpainter" --onefile --windowed --add-data "../assets;assets" --icon "../assets/icons/icon.ico" --clean "../image_inpainter.py"

Write-Host "Executable built successfully. Check the 'dist' folder for Image Inpainter.exe"
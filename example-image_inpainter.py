#!/usr/bin/python3
# -*- coding: utf-8 -*-
# This script generates icon files for various platforms (Linux, Windows, macOS, etc.)
# from a source image. It supports PNG, JPG, SVG, and other formats.
# It uses the Pillow library for image processing and PySide6 for the GUI.
#
#
# Copyright (C) 2025 steve.rock@wheelhouser.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# --- Setup Instructions ---
# Active the venv on linux/macOS:
# python -m venv .venv
# source .venv/bin/activate
# pip install --upgrade pip
#
# Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
# pip install -r requirements.txt
# pip install --force-reinstall -r requirements.txt
#
#===========================================================================================

import os
import sys
import faulthandler
import ctypes

# Enable crash logging immediately for compiled binary
if getattr(sys, 'frozen', False):
    if os.environ.get("DEBUG_MODE"):
        print("DEBUG_MODE enabled: Logging to stderr", flush=True)
        faulthandler.enable()
    else:
        print("Application starting...", flush=True)
        try:
            log_file = open('crash.log', 'w', buffering=1)
            os.dup2(log_file.fileno(), 2)
            sys.stderr = log_file
            faulthandler.enable(file=log_file)
        except Exception:
            pass

# Fix for Nuitka/CairoSVG: Explicitly load the bundled libcairo.so.2
# This must run before cairosvg is imported or used.
if "__compiled__" in globals():
    try:
        # In standalone mode, the binary is in the root of the .dist folder
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cairo_path = os.path.join(base_dir, "libcairo.so.2")
        if os.path.exists(cairo_path):
            ctypes.CDLL(cairo_path)
    except Exception:
        pass

import json
from PIL import Image
import io
import argparse
import shutil
import tempfile
import base64
import traceback

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                               QMessageBox, QSizePolicy, QTreeWidget, QTreeWidgetItem, 
                               QStyle, QCheckBox, QGroupBox)
from PySide6.QtGui import QPixmap, QImage, QIcon, QDesktopServices
from PySide6.QtCore import Qt, QSize, QUrl

#============================================================================================
#--- Resource Path Helper ---
#============================================================================================
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev, PyInstaller, and Nuitka """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    
    # For py2app, the resources are in a 'Resources' directory
    if 'py2app' in sys.argv:
        return os.path.join(os.path.dirname(sys.executable), '..', 'Resources', relative_path)

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

#============================================================================================
#--- Background Remover Class ---
#============================================================================================
class CreateIconFilesApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window setup
        self.setWindowTitle("Create Icon Files")
        self.resize(900, 600)

        # Set Window Icon
        # Prefer SVG for crisp rendering at any scale
        icon_svg = resource_path(os.path.join("assets", "icons", "icon.svg"))
        icon_png = resource_path(os.path.join("assets", "icons", "icon.png"))
        
        if os.path.exists(icon_svg):
            self.setWindowIcon(QIcon(icon_svg))
        elif os.path.exists(icon_png):
            self.setWindowIcon(QIcon(icon_png))

        icon_path = resource_path(os.path.join("assets", "icons", "custom_checkmark.png"))
        # CSS requires forward slashes for URL paths, even on Windows
        css_icon_path = icon_path.replace(os.sep, '/')

        # Apply Dark Theme to the whole Application
        # This ensures dialogs (like File Browser) inherit the style
        QApplication.instance().setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: "Segoe UI", "Arial", sans-serif;
                font-size: 14px;
            }
            #header_widget {
                background-color: #1e1e1e;
                border-bottom: 1px solid #1e1e1e;
            }
            QPushButton {
                background-color: #323232;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
                icon-size: 0px;
            }
            QPushButton:hover {
                background-color: #424242;
                border: 1px solid #2196F3;
                border: 1px solid #007AFF;
            }
            QPushButton:disabled {
                background-color: #1e1e1e;
                color: #555;
                border: 1px solid #333;
            }

            /* Specific style for the 'About' button */
            QPushButton#aboutButton {
                background-color: transparent;
                border: none;
                padding: 4px 8px;
                color: #00BFFF;
            }
            /* Style for the 'About' button on mouse hover */
            QPushButton#aboutButton:hover {
                background-color: #444444;
                border: none;
                border-radius: 4px;
            }
            /* Style for the 'About' button when pressed */
            QPushButton#aboutButton:pressed {
                background-color: #333333;
                border: none;
            }

            /* GroupBox Styling */
            QGroupBox {
                border: 1px solid #1e1e1e;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: normal;
                color: #ddd;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px 0 3px;
            }

            /* CheckBox Styling */
            QCheckBox {
                spacing: 5px;
                color: #ccc;
            }
            /* Style for the checkbox indicator */
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }

            /* Style for the checkbox indicator when unchecked */
            QCheckBox::indicator:unchecked {
                background-color: #3E3E3E;
                border: 1px solid #555555;
                border-radius: 3px;
            }

            /* Style for the unchecked checkbox indicator on mouse hover */
            QCheckBox::indicator:unchecked:hover {
                border: 1px solid #007AFF;
            }

            /* Style for the checkbox indicator when checked */
            QCheckBox::indicator:checked {
                background-color: #007AFF;
                border: 1px solid #007AFF;
                border-radius: 3px;
                image: url("{css_icon_path}");
            }
        """.replace("{css_icon_path}", css_icon_path))

        # Variables
        self.original_image = None
        self.processed_image = None
        self.file_path = None
        self.last_opened_dir = os.path.expanduser("~/Pictures")
        self.settings_file = os.path.expanduser("~/.create_icon_files_config.json")
        self.platform_checks = {}

        self._setup_ui()
        self.load_settings()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout (Edge-to-Edge for Header)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Header Section ---
        header_widget = QWidget()
        header_widget.setObjectName("header_widget")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 5, 10, 5)
        header_layout.setSpacing(10)
        
        btn_width = 150
        btn_height = 36

        self.btn_load = QPushButton("Select Image")
        self.btn_load.setFixedSize(btn_width, btn_height)
        self.btn_load.clicked.connect(self.load_image)
        header_layout.addWidget(self.btn_load)

        header_layout.addStretch()

        self.btn_process = QPushButton("Create Icon Files")
        self.btn_process.setFixedSize(btn_width, btn_height)
        self.btn_process.clicked.connect(self.process_image)
        self.btn_process.setEnabled(False)
        header_layout.addWidget(self.btn_process)

        self.btn_save = QPushButton("Save Results")
        self.btn_save.setFixedSize(btn_width, btn_height)
        self.btn_save.clicked.connect(self.save_image)
        self.btn_save.setEnabled(False)
        header_layout.addWidget(self.btn_save)

        # --- Hamburger Menu ---
        self.btn_menu = QPushButton("About")
        self.btn_menu.setObjectName("aboutButton")
        self.btn_menu.setFixedSize(80, btn_height)
        self.btn_menu.clicked.connect(self.show_about_dialog)
        header_layout.addWidget(self.btn_menu)

        main_layout.addWidget(header_widget)

        # --- Content Section ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(10)

        # --- Platform Selection ---
        self.platforms_group = QGroupBox("Target Platforms")
        self.platforms_layout = QHBoxLayout()
        self.platforms_group.setLayout(self.platforms_layout)
        
        platforms = ["Android", "iOS", "Linux", "Windows", "macOS", "Web", "watchOS", "Unix"]
        for p in platforms:
            chk = QCheckBox(p)
            chk.stateChanged.connect(self.save_settings)
            self.platforms_layout.addWidget(chk)
            self.platform_checks[p.lower()] = chk

        content_layout.addWidget(self.platforms_group)

        # --- Image Display Section ---
        image_layout = QHBoxLayout()

        # Left side: Original
        left_layout = QVBoxLayout()
        lbl_left_title = QLabel("Icon Source Image")
        lbl_left_title.setAlignment(Qt.AlignCenter)
        title_font = lbl_left_title.font()
        title_font.setPointSize(12)
        title_font.setBold(False)
        lbl_left_title.setFont(title_font)
        left_layout.addWidget(lbl_left_title)

        self.lbl_original_img = QLabel("No Image Loaded")
        self.lbl_original_img.setAlignment(Qt.AlignCenter)
        self.lbl_original_img.setStyleSheet("border: 1px solid #444; background-color: #252525; color: #888;")
        self.lbl_original_img.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(self.lbl_original_img)
        
        image_layout.addLayout(left_layout)

        # Right side: Processed
        right_layout = QVBoxLayout()
        lbl_right_title = QLabel("Files Created")
        lbl_right_title.setAlignment(Qt.AlignCenter)
        lbl_right_title.setFont(title_font)
        right_layout.addWidget(lbl_right_title)

        self.tree_files = QTreeWidget()
        self.tree_files.setHeaderLabels(["Name", "Dimensions", "Size"])
        self.tree_files.setColumnWidth(0, 250)
        self.tree_files.setColumnWidth(1, 120)
        self.tree_files.setColumnWidth(2, 100)
        self.tree_files.setStyleSheet("border: 1px solid #444; background-color: #252525; color: #ccc;")
        self.tree_files.setIconSize(QSize(24, 24))
        self.tree_files.itemDoubleClicked.connect(self.open_file_preview)
        right_layout.addWidget(self.tree_files)

        image_layout.addLayout(right_layout)
        content_layout.addLayout(image_layout)
        
        main_layout.addWidget(content_widget)

        # Status Bar
        self.lbl_status = QLabel("Ready")
        self.statusBar().addWidget(self.lbl_status)
        self.statusBar().setSizeGripEnabled(True)

    def load_settings(self):
        # Default: Linux, Windows, macOS = True; others = False
        defaults = {
            "linux": True, "windows": True, "macos": True,
            "web": False, "unix": False, "android": False, "ios": False, "watchos": False
        }
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    saved = json.load(f)
                    defaults.update(saved)
        except Exception as e:
            print(f"Error loading settings: {e}")
            
        for key, chk in self.platform_checks.items():
            chk.blockSignals(True)
            chk.setChecked(defaults.get(key, False))
            chk.blockSignals(False)

    def save_settings(self):
        settings = {key: chk.isChecked() for key, chk in self.platform_checks.items()}
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_image(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image", self.last_opened_dir, 
            "Images (*.png *.jpg *.jpeg *.svg *.webp *.tiff *.bmp *.pdf);;All Files (*)")
        if not file_name:
            return

        self.file_path = file_name
        self.last_opened_dir = os.path.dirname(file_name)
        
        # Display logic
        ext = os.path.splitext(file_name)[1].lower()
        if ext == '.svg':
            # Render to png for display using cairosvg
            try:
                import cairosvg
                png_data = cairosvg.svg2png(url=file_name, output_width=512, output_height=512)
                image = QImage.fromData(png_data)
                pixmap = QPixmap.fromImage(image)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load SVG preview: {e}")
                return
        else:
            pixmap = QPixmap(file_name)
        
        if pixmap.isNull():
             QMessageBox.warning(self, "Error", "Failed to load image.")
             return

        self.original_image = pixmap

        # Check dimensions and aspect ratio (skip for SVG as they are vector/scalable)
        if ext != '.svg':
            w = pixmap.width()
            h = pixmap.height()
            warnings = []
            
            if w < 512 or h < 512:
                warnings.append(f"<span style='color: #ff5555; font-weight: bold;'>Warning:</span> The Image size ({w}x{h}) is smaller than 512x512!")
            
            if w != h:
                warnings.append(f"<span style='color: #ff5555; font-weight: bold;'>Warning:</span> The Image is not square ({w}x{h})!")
                
            if warnings:
                warnings.append("<br>For best results, a square image of at least 1024x1024 is recommended.")
                QMessageBox.warning(self, "Image Recommendation", "<br>".join(warnings))

        self.lbl_original_img.setPixmap(pixmap.scaled(self.lbl_original_img.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        self.btn_process.setEnabled(True)
        self.btn_save.setEnabled(False)
        self.tree_files.clear()
        self.lbl_status.setText(f"Loaded: {os.path.basename(file_name)}")

    def process_image(self):
        if not self.file_path:
            return
        
        self.lbl_status.setText("Generating icons...")
        QApplication.processEvents()

        try:
            # Use a temp dir in the user's home to ensure visibility if running in Flatpak/Sandbox
            # Default /tmp is often isolated in containers, preventing xdg-open from seeing files.
            cache_base = os.path.expanduser("~/.cache")
            if not os.path.exists(cache_base):
                os.makedirs(cache_base, exist_ok=True)
            self.temp_dir = tempfile.mkdtemp(prefix="create_icon_files_", dir=cache_base)
            
            selected_platforms = {key: chk.isChecked() for key, chk in self.platform_checks.items()}
            generate_icons(self.file_path, self.temp_dir, platforms=selected_platforms)
            
            self.tree_files.clear()
            
            # Map relative paths to tree items to build hierarchy
            dir_items = {}

            for root, dirs, files in os.walk(self.temp_dir):
                rel_path = os.path.relpath(root, self.temp_dir)
                
                if rel_path == ".":
                    parent_item = self.tree_files.invisibleRootItem()
                else:
                    parent_item = dir_items.get(rel_path)
                
                if parent_item is None:
                    continue

                # Add Directories
                for d in sorted(dirs):
                    item = QTreeWidgetItem(parent_item)
                    item.setText(0, d)
                    item.setIcon(0, self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon))
                    item.setExpanded(False)
                    
                    key = os.path.join(rel_path, d) if rel_path != "." else d
                    dir_items[key] = item

                # Add Files
                for file in sorted(files):
                    full_path = os.path.abspath(os.path.join(root, file))
                    item = QTreeWidgetItem(parent_item)
                    item.setText(0, file)
                    item.setData(0, Qt.UserRole, full_path)
                    
                    # Details
                    size_kb = os.path.getsize(full_path) / 1024
                    item.setText(2, f"{size_kb:.1f} KB")
                    item.setTextAlignment(2, Qt.AlignRight)

                    if file.lower().endswith(('.png', '.ico', '.icns', '.svg', '.webp', '.xpm', '.bmp')):
                        pix = QPixmap(full_path)
                        if not pix.isNull():
                            item.setIcon(0, QIcon(pix))
                            item.setText(1, f"{pix.width()}x{pix.height()}")
            
            self.btn_save.setEnabled(True)
            self.lbl_status.setText("Icons generated. Ready to save.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate icons: {e}")
            self.lbl_status.setText("Error generating icons.")

    def open_file_preview(self, item, column):
        file_path = item.data(0, Qt.UserRole)
        print(f"DEBUG: Double click detected. Path: {file_path}")
        if file_path and os.path.exists(file_path):
            # Ensure path is absolute and strictly a file URL
            url = QUrl.fromLocalFile(os.path.abspath(file_path))
            print(f"DEBUG: Opening URL via QDesktopServices: {url.toString()}")
            
            # This launches the default system app for the file type
            if not QDesktopServices.openUrl(url):
                print(f"ERROR: QDesktopServices failed to open {url.toString()}")
                QMessageBox.warning(self, "Preview Error", f"Could not launch default application for:\n{file_path}")

    def show_about_dialog(self):
        """Shows the about dialog."""
        about_dlg = QMessageBox(self)
        about_dlg.setWindowTitle("About Create Icon Files")

        # Set the icon
        icon_path = resource_path(os.path.join("assets", "icons", "icon.png"))
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            about_dlg.setIconPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        about_dlg.setTextFormat(Qt.RichText)
        about_dlg.setText("<h3>Create Icon Files</h3>")
        about_dlg.setInformativeText(
            "<div style='font-size: 14px;'>"
            "A powerful tool to generate icon files for Android, iOS, Linux, macOS, Windows, Web, watchOS, and Unix.<br><br>"
            "<span style='color: #00BFFF;'>"
            "Version 0.1.0<br>"
            "Input support for: png, jpg, jpeg, tiff, webp, avif, pdf, svg, and bmp file formats.<br>"
            "</span><br>"
            "© 2025 Wheelhouser LLC<br>"
            "Visit our website: <a href='https://wheelhouser.com' style='color: #00BFFF;'>wheelhouser.com</a>"
            "</div>"
        )
        about_dlg.setStandardButtons(QMessageBox.Ok)
        about_dlg.exec()

    def save_image(self):
        output_dir = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.last_opened_dir)
        if output_dir and hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            try:
                for item in os.listdir(self.temp_dir):
                    s = os.path.join(self.temp_dir, item)
                    d = os.path.join(output_dir, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d)
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)
                
                QMessageBox.information(self, "Success", f"Icons saved to:\n{output_dir}")
                self.lbl_status.setText("Saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save files: {e}")

#============================================================================================
#--- Icon Generation Function ---
#============================================================================================
def save_xpm_manual(img, file_path):
    width, height = img.size
    img = img.convert("RGBA")
    pixels = img.load()
    
    # Map (r,g,b,a) -> color_key
    # We treat alpha < 128 as transparent
    color_map = {}
    colors = []
    
    # Helper to generate code: 2 chars
    # We use printable ascii. 
    chars = " .XoO+@#$%&*=-;:>,<1234567890qwertyuioppasdfghjklzxcvbnmMNBVCZLKJHGFDSAQWERTYUIOP"
    
    def get_code(idx):
        return chars[idx % len(chars)] + chars[(idx // len(chars)) % len(chars)]

    # First pass: collect colors and build pixel grid
    grid = []
    for y in range(height):
        row = []
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a < 128:
                c = "None"
            else:
                c = (r, g, b)
            
            if c not in color_map:
                color_map[c] = len(colors)
                colors.append(c)
            
            row.append(color_map[c])
        grid.append(row)
        
    # Write
    with open(file_path, 'w') as f:
        f.write("/* XPM */\n")
        f.write("static char * icon[] = {\n")
        f.write(f"\"{width} {height} {len(colors)} 2\",\n")
        
        # Colors
        for i, c in enumerate(colors):
            code = get_code(i)
            if c == "None":
                f.write(f"\"{code} c None\",\n")
            else:
                hex_c = f"#{c[0]:02X}{c[1]:02X}{c[2]:02X}"
                f.write(f"\"{code} c {hex_c}\",\n")
        
        # Pixels
        for row in grid:
            line = "".join(get_code(idx) for idx in row)
            f.write(f"\"{line}\",\n")
            
        f.write("};\n")

def generate_icons(source_path, output_dir=None, platforms=None):
    if output_dir is None:
        output_dir = f"{os.path.splitext(source_path)[0]}_icons"

    if platforms is None:
        # Default to all if not specified (e.g. CLI usage)
        platforms = {k: True for k in ["linux", "windows", "macos", "web", "unix", "android", "ios", "watchos"]}

    # 1. Load the Image
    file_ext = os.path.splitext(source_path)[1].lower()
    
    if file_ext == '.svg':
        # Convert SVG to a high-res PNG in memory
        import cairosvg
        png_data = cairosvg.svg2png(url=source_path, output_width=1024, output_height=1024)
        master_img = Image.open(io.BytesIO(png_data))
    else:
        master_img = Image.open(source_path)
    
    # Ensure RGBA for transparency
    master_img = master_img.convert("RGBA")

    if master_img.width < 512 or master_img.height < 512:
        print(f"Warning: Input image is {master_img.width}x{master_img.height}. For best results, use an image at least 512x512.", file=sys.stderr)

    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Define Platform Directories
    linux_dir = os.path.join(output_dir, 'linux')
    windows_dir = os.path.join(output_dir, 'windows')
    macos_dir = os.path.join(output_dir, 'macOS')
    web_dir = os.path.join(output_dir, 'web')
    unix_dir = os.path.join(output_dir, 'unix')
    android_dir = os.path.join(output_dir, 'android')
    ios_dir = os.path.join(output_dir, 'iOS')
    watchos_dir = os.path.join(output_dir, 'watchOS')

    dirs_map = {
        'linux': linux_dir, 'windows': windows_dir, 'macos': macos_dir,
        'web': web_dir, 'unix': unix_dir, 'android': android_dir,
        'ios': ios_dir, 'watchos': watchos_dir
    }

    for key, d in dirs_map.items():
        if platforms.get(key, False):
            os.makedirs(d, exist_ok=True)

    # Prepare Master 1024x1024
    img_1024 = master_img.resize((1024, 1024), Image.Resampling.LANCZOS)

    # --- SVG Handling ---
    svg_content = None
    if file_ext == '.svg':
        with open(source_path, 'r') as f:
            svg_content = f.read()
    else:
        # Generate wrapper SVG from the 1024x1024 PNG data
        with io.BytesIO() as buf:
            img_1024.save(buf, format='PNG')
            b64_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        svg_content = f'<svg version="1.1" width="1024" height="1024" xmlns="http://www.w3.org/2000/svg">\n  <image href="data:image/png;base64,{b64_data}" x="0" y="0" width="1024" height="1024" />\n</svg>'

    def save_svg(target_dir):
        with open(os.path.join(target_dir, 'icon.svg'), 'w') as f:
            f.write(svg_content)

    # Save SVG to all platform directories for convenience
    for key, d in dirs_map.items():
        if platforms.get(key, False):
            save_svg(d)

    # --- LINUX (PNG Set) ---
    if platforms.get('linux', False):
        linux_sizes = [16, 24, 32, 48, 64, 96, 128, 256, 512]
        
        for size in linux_sizes:
            # 1x
            img_resized = master_img.resize((size, size), Image.Resampling.LANCZOS)
            size_dir = os.path.join(linux_dir, f"{size}x{size}")
            os.makedirs(size_dir, exist_ok=True)
            img_resized.save(os.path.join(size_dir, 'icon.png'))

            # 2x
            img_2x = master_img.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
            size_dir_2x = os.path.join(linux_dir, f"{size}x{size}@2x")
            os.makedirs(size_dir_2x, exist_ok=True)
            img_2x.save(os.path.join(size_dir_2x, 'icon.png'))
        
        # Linux Extras
        img_1024.save(os.path.join(linux_dir, 'icon.png'))

        # Create 'scalable' directory for SVG (Freedesktop.org standard)
        scalable_dir = os.path.join(linux_dir, 'scalable')
        os.makedirs(scalable_dir, exist_ok=True)
        save_svg(scalable_dir)

        print(f"Linux icons generated in {linux_dir}")

    # --- UNIX (Legacy XPM) ---
    if platforms.get('unix', False):
        print("DEBUG: Starting XPM generation...")
        try:
            # 1. XPM (Legacy)
            img_xpm = master_img.resize((48, 48), Image.Resampling.LANCZOS)
            print(f"DEBUG: Resized for XPM. Mode: {img_xpm.mode}")

            # Pillow does not support writing XPM. Use manual helper.
            print(f"DEBUG: Saving XPM manually to {os.path.join(unix_dir, 'icon.xpm')}")
            save_xpm_manual(img_xpm, os.path.join(unix_dir, 'icon.xpm'))

            # 2. Modern Unix (PNG)
            img_1024.save(os.path.join(unix_dir, 'icon.png'))
            print(f"Unix (Legacy XPM) icon generated in {unix_dir}")
        except Exception as e:
            print(f"ERROR generating XPM file: {e}", file=sys.stderr)
            traceback.print_exc()

    # --- WINDOWS (.ico) ---
    if platforms.get('windows', False):
        win_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        # Pillow expects a sequence of images to embed in the ICO
        ico_images = []
        for w, h in win_sizes:
            ico_images.append(master_img.resize((w, h), Image.Resampling.LANCZOS))
            
        ico_path = os.path.join(windows_dir, 'icon.ico')
        # Save the first image, appending the rest
        ico_images[0].save(ico_path, format='ICO', sizes=win_sizes, append_images=ico_images[1:])
        
        # Legacy BMP
        img_bmp = master_img.resize((128, 128), Image.Resampling.LANCZOS)
        img_bmp.save(os.path.join(windows_dir, 'icon.bmp'))

        # Windows Store (UWP) Assets
        win_store_dir = os.path.join(windows_dir, 'store')
        os.makedirs(win_store_dir, exist_ok=True)
        
        uwp_assets = {
            'Square44x44Logo.scale-100.png': 44,
            'Square44x44Logo.scale-125.png': 55,
            'Square44x44Logo.scale-150.png': 66,
            'Square44x44Logo.scale-200.png': 88,
            'Square44x44Logo.scale-400.png': 176,
            
            'Square50x50Logo.scale-100.png': 50,
            'Square50x50Logo.scale-200.png': 100,
            
            'Square150x150Logo.scale-100.png': 150,
            'Square150x150Logo.scale-200.png': 300,
            'Square150x150Logo.scale-400.png': 600,
            
            'Square310x310Logo.scale-100.png': 310,
            'Square310x310Logo.scale-200.png': 620,
            
            'StoreLogo.scale-100.png': 50,
            'StoreLogo.scale-125.png': 63,
            'StoreLogo.scale-150.png': 75,
            'StoreLogo.scale-200.png': 100,
            'StoreLogo.scale-400.png': 200,
        }

        for name, size in uwp_assets.items():
            img = master_img.resize((size, size), Image.Resampling.LANCZOS)
            img.save(os.path.join(win_store_dir, name))

        # Store Asset
        img_1024.save(os.path.join(windows_dir, 'icon.png'))
        print(f"Windows icons generated in {windows_dir}")

    # --- MACOS (.icns) ---
    if platforms.get('macos', False):
        # Explicitly generate all standard macOS sizes to ensure high quality at every zoom level
        mac_sizes = [16, 32, 64, 128, 256, 512, 1024]
        mac_images = []
        for s in mac_sizes:
            mac_images.append(master_img.resize((s, s), Image.Resampling.LANCZOS))
        
        icns_path = os.path.join(macos_dir, 'icon.icns')
        # Save using the largest image, appending the smaller ones
        mac_images[-1].save(icns_path, format='ICNS', append_images=mac_images[:-1])
        # App Store Asset
        img_1024.save(os.path.join(macos_dir, 'icon.png'))
        print(f"macOS icons generated in {macos_dir}")

    # --- WEB (PNG & WebP) ---
    if platforms.get('web', False):
        # Standard Web/PWA sizes
        web_sizes = {
            'favicon-16x16.png': 16,
            'favicon-32x32.png': 32,
            'apple-touch-icon.png': 180,
            'android-chrome-192x192.png': 192,
            'android-chrome-512x512.png': 512
        }

        for name, size in web_sizes.items():
            img = master_img.resize((size, size), Image.Resampling.LANCZOS)
            img.save(os.path.join(web_dir, name))
            
            # Generate WebP for larger sizes (modern web support)
            if size >= 192:
                webp_name = os.path.splitext(name)[0] + ".webp"
                img.save(os.path.join(web_dir, webp_name), format="WEBP")

        # Generate favicon.ico (Legacy but essential)
        fav_sizes = [(16, 16), (32, 32), (48, 48)]
        fav_imgs = [master_img.resize(s, Image.Resampling.LANCZOS) for s in fav_sizes]
        fav_imgs[0].save(os.path.join(web_dir, 'favicon.ico'), format='ICO', sizes=fav_sizes, append_images=fav_imgs[1:])
        
        # Web Extras
        img_1024.save(os.path.join(web_dir, 'icon.png'))

        print(f"Web icons generated in {web_dir}")

    # --- ANDROID (Native) ---
    if platforms.get('android', False):
        # Standard mipmap density buckets
        android_map = {
            'mipmap-mdpi': 48,
            'mipmap-hdpi': 72,
            'mipmap-xhdpi': 96,
            'mipmap-xxhdpi': 144,
            'mipmap-xxxhdpi': 192,
            'playstore': 512
        }
        
        for folder, size in android_map.items():
            d = os.path.join(android_dir, folder)
            os.makedirs(d, exist_ok=True)
            img = master_img.resize((size, size), Image.Resampling.LANCZOS)
            img.save(os.path.join(d, 'ic_launcher.png'))
            
        # Android Extras
        img_1024.save(os.path.join(android_dir, 'icon.png'))

        print(f"Android icons generated in {android_dir}")

    # --- iOS (Native) ---
    if platforms.get('ios', False):
        # Standard iOS AppIcon sizes
        ios_sizes = {
            'Icon-20.png': 20, 'Icon-20@2x.png': 40, 'Icon-20@3x.png': 60,
            'Icon-29.png': 29, 'Icon-29@2x.png': 58, 'Icon-29@3x.png': 87,
            'Icon-40.png': 40, 'Icon-40@2x.png': 80, 'Icon-40@3x.png': 120,
            'Icon-60@2x.png': 120, 'Icon-60@3x.png': 180,
            'Icon-76.png': 76, 'Icon-76@2x.png': 152,
            'Icon-83.5@2x.png': 167, 'Icon-1024.png': 1024
        }
        
        for name, size in ios_sizes.items():
            img = master_img.resize((size, size), Image.Resampling.LANCZOS)
            img.save(os.path.join(ios_dir, name))

        # iOS Extras
        img_1024.save(os.path.join(ios_dir, 'icon.png'))

        print(f"iOS icons generated in {ios_dir}")

    # --- WATCHOS (Apple Watch) ---
    if platforms.get('watchos', False):
        watch_sizes = {
            'Icon-24@2x.png': 48,
            'Icon-27.5@2x.png': 55,
            'Icon-29@2x.png': 58,
            'Icon-29@3x.png': 87,
            'Icon-40@2x.png': 80,
            'Icon-44@2x.png': 88,
            'Icon-50@2x.png': 100,
            'Icon-86@2x.png': 172,
            'Icon-98@2x.png': 196,
            'Icon-1024.png': 1024
        }
        
        for name, size in watch_sizes.items():
            img = master_img.resize((size, size), Image.Resampling.LANCZOS)
            img.save(os.path.join(watchos_dir, name))
            
        print(f"watchOS icons generated in {watchos_dir}")

# Example Usage
# generate_icons('my_logo.svg', './output_icons')

#============================================================================================
#--- Main Entry Point ---
#============================================================================================
if __name__ == "__main__":
    # If arguments are passed, run in CLI mode
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Generate icons for Linux, Windows, and macOS.")
        parser.add_argument("source", help="Path to the source image file")
        parser.add_argument("output_dir", nargs='?', help="Directory to save the generated icons")

        args = parser.parse_args()

        if not os.path.exists(args.source):
            print(f"Error: Source file '{args.source}' does not exist.", file=sys.stderr)
            sys.exit(1)

        generate_icons(args.source, args.output_dir)
    else:
        # Otherwise run GUI
        app = QApplication(sys.argv)
        window = CreateIconFilesApp()
        window.show()
        sys.exit(app.exec())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   image_impainter.py
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
# .\.venv\Scripts\Activate.ps1
# Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
# pip install -r requirements.txt
# pip install --force-reinstall -r requirements.txt
#
#===========================================================================================

import sys
import cv2
import numpy as np
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QFileDialog, 
                               QSpinBox, QFormLayout, QFrame, QMessageBox, QSizePolicy)
from PySide6.QtGui import QPixmap, QImage, QIcon
from PySide6.QtCore import Qt, QEvent, QSettings
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller. """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # _MEIPASS not defined, so we are running in a normal Python environment
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

#=====================================================================================================
# --- Dark Mode Stylesheet ---
#=====================================================================================================
DARK_STYLESHEET = """
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: "Segoe UI", "Arial", sans-serif;
                font-size: 14px;
            }
            QLabel {
                font-size: 14px;
                font-weight: bold;
                border: none;
                padding: 5px;
            }
            QLabel#ImageLabel {
                border: 2px dashed #4A4B4C;
                background-color: #252627;
                min-height: 300px;
                min-width: 400px;
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
                border: 1px solid #007AFF;
            }
            QPushButton:disabled {
                background-color: #1e1e1e;
                color: #555;
                border: 1px solid #333;
            }
            QSpinBox {
                min-width: 80px;
                font-size: 14px;
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
"""

#=====================================================================================================
#--- Main Application Class ---
#=====================================================================================================
class InpaintingApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QSettings("Wheelhouser LLC", "Image Inpainting Tool")

        self.active_result_cv_image = None # Tracks the image currently in the result panel
        self.last_used_dir = self.settings.value("last_used_dir", os.path.join(os.path.expanduser("~"), "Pictures"), type=str)

        self.original_alpha = None
        self.result_alpha = None
        self.preview_cv_image = None
        self.preview_alpha = None

        self.setWindowTitle("Image Inpainting Tool")
        self.setGeometry(100, 100, 1000, 750)
        
        # --- Prepare and set stylesheet with correct resource paths ---
        css_icon_path = resource_path(os.path.join("assets", "icons", "custom_checkmark.png")).replace(os.sep, '/')

        QApplication.instance().setStyleSheet(DARK_STYLESHEET.replace("{css_icon_path}", css_icon_path))
        
        # --- Set Window Icon using resource_path ---
        icon_path = resource_path(os.path.join("assets", "icons", "icon.png"))
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.original_cv_image = None
        self.result_cv_image = None

        # --- Main Widget and Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Top Control Bar ---
        top_bar_layout = QHBoxLayout()
        self.load_button = QPushButton("Load Image")
        self.load_button.clicked.connect(self.load_image)
        
        self.image_size_label = QLabel("Dimensions: N/A")
        self.image_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.save_button = QPushButton("Save Result")
        self.save_button.clicked.connect(self.save_image)
        self.save_button.setEnabled(False)

        self.cancel_button = QPushButton("Undo")
        self.cancel_button.clicked.connect(self.cancel_mask)
        self.cancel_button.setEnabled(False)

        self.execute_button = QPushButton("Execute Inpaint")
        self.execute_button.clicked.connect(self.perform_inpainting)
        self.execute_button.setEnabled(False)
        
        self.about_button = QPushButton("About")
        self.about_button.setObjectName("aboutButton")
        self.about_button.clicked.connect(self.show_about_dialog)

        top_bar_layout.addWidget(self.load_button)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.image_size_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.cancel_button)
        top_bar_layout.addWidget(self.execute_button)
        top_bar_layout.addWidget(self.save_button)
        top_bar_layout.addWidget(self.about_button)
        main_layout.addLayout(top_bar_layout)
        
        # --- Image Display Area ---
        image_layout = QHBoxLayout()
        
        self.result_label = QLabel("Image")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setObjectName("ImageLabel")
        self.result_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.result_label.setMouseTracking(True)
        self.result_label.installEventFilter(self)

        image_layout.addWidget(self.result_label)
        main_layout.addLayout(image_layout)
        
        # --- Bottom Control Bar ---
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(2)
        separator.setObjectName("Separator")
        main_layout.addWidget(separator)
        
        mask_and_buttons_layout = QHBoxLayout()
        mask_and_buttons_layout.setContentsMargins(10, 10, 10, 10)
        
        self.mouse_coords_label = QLabel("Mouse: (---, ---)")
        
        # Mask controls
        left_form = QFormLayout()
        right_form = QFormLayout()
        self.x_spinbox = QSpinBox()
        self.y_spinbox = QSpinBox()
        self.w_spinbox = QSpinBox()
        self.h_spinbox = QSpinBox()
        
        for spinbox in [self.x_spinbox, self.y_spinbox, self.w_spinbox, self.h_spinbox]:
            spinbox.setRange(0, 9999)
            spinbox.setEnabled(False)

        # Load persistent settings
        settings = self.settings
        self.w_spinbox.setValue(settings.value("mask_width", 100, type=int))
        self.h_spinbox.setValue(settings.value("mask_height", 100, type=int))

        # Save settings when changed
        self.w_spinbox.valueChanged.connect(lambda: settings.setValue("mask_width", self.w_spinbox.value()))
        self.h_spinbox.valueChanged.connect(lambda: settings.setValue("mask_height", self.h_spinbox.value()))

        # Auto-update mask preview when spinbox values change
        for spinbox in [self.x_spinbox, self.y_spinbox, self.w_spinbox, self.h_spinbox]:
            spinbox.valueChanged.connect(self.apply_mask_preview)

        left_form.addRow("Mask Origin X:", self.x_spinbox)
        left_form.addRow("Mask Origin Y:", self.y_spinbox)
        right_form.addRow("Mask Width:", self.w_spinbox)
        right_form.addRow("Mask Height:", self.h_spinbox)
        
        mask_and_buttons_layout.addLayout(left_form)
        mask_and_buttons_layout.addLayout(right_form)
        mask_and_buttons_layout.addWidget(self.mouse_coords_label)
        mask_and_buttons_layout.addStretch()
        
        main_layout.addLayout(mask_and_buttons_layout)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", self.last_used_dir, "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.gif)")
        if file_path:
            self.last_used_dir = os.path.dirname(file_path)
            self.settings.setValue("last_used_dir", self.last_used_dir)
            self.original_filename = os.path.basename(file_path)
            self.original_cv_image = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
            if self.original_cv_image is None:
                QMessageBox.warning(self, "Error", "Failed to load the image file.")
                return
            
            # Handle alpha channel
            if self.original_cv_image.shape[2] == 4:
                self.original_alpha = self.original_cv_image[:, :, 3]
                self.original_cv_image = self.original_cv_image[:, :, :3]  # Keep BGR
            else:
                self.original_alpha = None
            
            # Display original image
            pixmap = self.convert_cv_to_pixmap(self.original_cv_image, self.original_alpha)
            self.result_label.setPixmap(pixmap.scaled(self.result_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.active_result_cv_image = self.original_cv_image
            
            # Enable controls
            self.save_button.setEnabled(False)
            self.execute_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            
            # Update spinbox ranges and display dimensions
            img_h, img_w = self.original_cv_image.shape[:2]
            self.image_size_label.setText(f"Dimensions: {img_w} x {img_h}")
            self.x_spinbox.setMaximum(img_w - 1)
            self.y_spinbox.setMaximum(img_h - 1)
            self.w_spinbox.setMaximum(img_w)
            self.h_spinbox.setMaximum(img_h)

            for spinbox in [self.x_spinbox, self.y_spinbox, self.w_spinbox, self.h_spinbox]:
                spinbox.setEnabled(True)

    def cancel_mask(self):
        """Undo the inpainting or cancel the mask preview."""
        if self.active_result_cv_image is self.result_cv_image:
            if self.preview_cv_image is not None:
                self.active_result_cv_image = self.preview_cv_image
                alpha = self.preview_alpha
            else:
                self.active_result_cv_image = self.original_cv_image
                alpha = self.original_alpha
        elif self.active_result_cv_image is self.preview_cv_image:
            self.active_result_cv_image = self.original_cv_image
            alpha = self.original_alpha
        else:
            # already original
            alpha = self.original_alpha
        
        pixmap = self.convert_cv_to_pixmap(self.active_result_cv_image, alpha)
        self.result_label.setPixmap(pixmap.scaled(self.result_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def apply_mask_preview(self):
        if self.original_cv_image is None:
            return
        
        image_with_mask = self.original_cv_image.copy()
        x = self.x_spinbox.value()
        y = self.y_spinbox.value()
        w = self.w_spinbox.value()
        h = self.h_spinbox.value()

        # Draw a semi-transparent rectangle for the mask preview
        overlay = image_with_mask.copy()
        cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 0), -1) # Green rectangle
        alpha = 0.5  # Transparency factor.
        image_with_mask = cv2.addWeighted(overlay, alpha, image_with_mask, 1 - alpha, 0)
        
        self.preview_cv_image = image_with_mask
        self.preview_alpha = self.original_alpha
        self.active_result_cv_image = self.preview_cv_image
        pixmap = self.convert_cv_to_pixmap(self.active_result_cv_image, self.preview_alpha)
        self.result_label.setPixmap(pixmap.scaled(self.result_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def perform_inpainting(self):
        if self.original_cv_image is None:
            QMessageBox.warning(self, "No Image", "Please load an image first.")
            return

        x = self.x_spinbox.value()
        y = self.y_spinbox.value()
        w = self.w_spinbox.value()
        h = self.h_spinbox.value()

        if w == 0 or h == 0:
            QMessageBox.warning(self, "Invalid Mask", "Mask width and height must be greater than zero.")
            return

        # Create the mask
        mask = np.zeros(self.original_cv_image.shape[:2], dtype=np.uint8)
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)

        # Perform inpainting
        self.result_cv_image = cv2.inpaint(self.original_cv_image, mask, 5, cv2.INPAINT_NS)
        self.result_alpha = self.original_alpha  # Keep original alpha
        self.active_result_cv_image = self.result_cv_image
        
        # Display the result
        pixmap = self.convert_cv_to_pixmap(self.active_result_cv_image, self.result_alpha)
        self.result_label.setPixmap(pixmap.scaled(self.result_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        self.save_button.setEnabled(True)

    def save_image(self):
        if self.result_cv_image is None:
            QMessageBox.warning(self, "No Result", "There is no inpainted image to save.")
            return
            
        name, ext = os.path.splitext(self.original_filename)
        default_save_path = os.path.join(self.last_used_dir, f"{name}_inpainted{ext}")
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", default_save_path, "PNG Image (*.png);;JPEG Image (*.jpg);;TIFF Image (*.tiff *.tif);;GIF Image (*.gif)")
        if file_path:
            try:
                if self.result_alpha is not None:
                    # Combine RGB and alpha
                    bgra = cv2.cvtColor(self.result_cv_image, cv2.COLOR_BGR2BGRA)
                    bgra[:, :, 3] = self.result_alpha
                    cv2.imwrite(file_path, bgra)
                else:
                    cv2.imwrite(file_path, self.result_cv_image)
                QMessageBox.information(self, "Success", f"Image successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save the image.\nError: {e}")

    def resizeEvent(self, event):
        """Handle window resize to scale images correctly from their source."""
        super().resizeEvent(event)
        if self.active_result_cv_image is not None:
            alpha = self.result_alpha if self.active_result_cv_image is self.result_cv_image else (self.preview_alpha if self.active_result_cv_image is self.preview_cv_image else self.original_alpha)
            pixmap = self.convert_cv_to_pixmap(self.active_result_cv_image, alpha)
            self.result_label.setPixmap(pixmap.scaled(self.result_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def eventFilter(self, source, event):
        """Filters events from the image label to track the mouse."""
        if source is self.result_label and self.original_cv_image is not None:
            # Handle mouse move for coordinate display
            if event.type() == QEvent.Type.MouseMove:
                self.update_mouse_coords(source, event.position())
            
            # Handle mouse leaving the widget
            elif event.type() == QEvent.Type.Leave:
                self.mouse_coords_label.setText("Mouse: (---, ---)")

            # Handle mouse click to set the mask position
            elif event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    coords = self.get_image_coords(source, event.position())
                    if coords:
                        self.x_spinbox.setValue(coords[0])
                        self.y_spinbox.setValue(coords[1])
                        # Automatically preview the new mask
                        self.apply_mask_preview()
        
        return super().eventFilter(source, event)

    def get_image_coords(self, label_widget, widget_pos):
        """Maps a mouse position on a label to the original image coordinates."""
        if self.original_cv_image is None or label_widget.pixmap().isNull():
            return None

        # Get geometries
        label_size = label_widget.size()
        pixmap = label_widget.pixmap()
        scaled_pixmap_size = pixmap.size()

        # Calculate the position of the scaled pixmap within the label (centered)
        offset_x = (label_size.width() - scaled_pixmap_size.width()) / 2
        offset_y = (label_size.height() - scaled_pixmap_size.height()) / 2

        # Calculate mouse position relative to the top-left of the pixmap
        pixmap_x = widget_pos.x() - offset_x
        pixmap_y = widget_pos.y() - offset_y

        # Check if mouse is over the pixmap
        if not (0 <= pixmap_x < scaled_pixmap_size.width() and 0 <= pixmap_y < scaled_pixmap_size.height()):
            return None

        # Get original image dimensions
        original_h, original_w, _ = self.original_cv_image.shape

        # Map pixmap coordinates to original image coordinates
        final_x = int((pixmap_x / scaled_pixmap_size.width()) * original_w)
        final_y = int((pixmap_y / scaled_pixmap_size.height()) * original_h)

        return (final_x, final_y)

    def update_mouse_coords(self, label_widget, widget_pos):
        """Updates the coordinate label with the mapped mouse position."""
        coords = self.get_image_coords(label_widget, widget_pos)
        if coords:
            self.mouse_coords_label.setText(f"Mouse: ({coords[0]}, {coords[1]})")
        else:
            self.mouse_coords_label.setText("Mouse: (---, ---)")

    def show_about_dialog(self):
        """Shows the about dialog."""
        about_dlg = QMessageBox(self)
        about_dlg.setWindowTitle("About Image Inpainting Tool")

        # Set the icon
        icon_path = resource_path(os.path.join("assets", "icons", "icon.png"))
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            about_dlg.setIconPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        about_dlg.setTextFormat(Qt.RichText)
        about_dlg.setText("<h3>Image Inpainting Tool</h3>")
        about_dlg.setInformativeText(
            "<div style='font-size: 14px; font-weight: normal;'>"
            "This application uses OpenCV to remove and reconstruct selected portions of an image.<br><br>"
            "Supported input/output formats: PNG, JPEG, BMP, TIFF, GIF<br><br>"
            "<span style='color: #00BFFF;'>"
            "Version 0.1.0<br>"
            "</span><br>"
            "© 2025 Wheelhouser LLC<br>"
            "Visit our website: <a href='https://wheelhouser.com' style='color: #00BFFF;'>wheelhouser.com</a>"
            "</div>"
        )
        about_dlg.setStandardButtons(QMessageBox.Ok)
        about_dlg.exec()

    def convert_cv_to_pixmap(self, cv_img, alpha=None):
        """Convert an OpenCV image to a QPixmap."""
        if alpha is not None:
            # Combine RGB and alpha
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            rgba_image = np.dstack((rgb_image, alpha))
            h, w, ch = rgba_image.shape
            bytes_per_line = ch * w
            q_image = QImage(rgba_image.data, w, h, bytes_per_line, QImage.Format.Format_RGBA8888)
        else:
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(q_image)

#=====================================================================================================
#--- Application Entry Point ---
#=====================================================================================================
if __name__ == '__main__':
    # Set AppUserModelID to ensure the taskbar icon is displayed correctly on Windows
    if sys.platform == 'win32':
        import ctypes
        myappid = 'wheelhouser.imageinpainter.tool.0.1.0' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    window = InpaintingApp()
    window.show()
    sys.exit(app.exec())


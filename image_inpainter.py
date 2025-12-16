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
                               QSpinBox, QFormLayout, QFrame, QMessageBox, QGridLayout, QSizePolicy)
from PySide6.QtGui import QPixmap, QImage, QIcon
from PySide6.QtCore import Qt, QEvent
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

        self.active_result_cv_image = None # Tracks the image currently in the result panel
        self.last_used_dir = os.path.join(os.path.expanduser("~"), "Pictures")

        self.setWindowTitle("Image Inpainting Tool")
        self.setGeometry(100, 100, 1200, 700)
        
        # --- Prepare and set stylesheet with correct resource paths ---
        css_icon_path = resource_path(os.path.join("assets", "icons", "custom_checkmark.png")).replace(os.sep, '/')

        QApplication.instance().setStyleSheet(DARK_STYLESHEET.replace("{css_icon_path}", css_icon_path))
        
        # --- Set Window Icon using resource_path ---
        icon_path = resource_path(os.path.join("assets", "icons", "icon-image-inpainter.ico"))
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
        
        self.about_button = QPushButton("About")
        self.about_button.setObjectName("aboutButton")
        self.about_button.clicked.connect(self.show_about_dialog)

        top_bar_layout.addWidget(self.load_button)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.image_size_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.save_button)
        top_bar_layout.addWidget(self.about_button)
        main_layout.addLayout(top_bar_layout)
        
        # --- Image Display Area ---
        image_layout = QHBoxLayout()
        
        self.original_label = QLabel("Original Image")
        self.original_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.original_label.setObjectName("ImageLabel")
        self.original_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.original_label.setMouseTracking(True)
        self.original_label.installEventFilter(self)
        
        self.result_label = QLabel("Preview / Result")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setObjectName("ImageLabel")
        self.result_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.result_label.setMouseTracking(True)
        self.result_label.installEventFilter(self)

        image_layout.addWidget(self.original_label)
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
        
        # Mask controls
        form_layout = QFormLayout()
        self.x_spinbox = QSpinBox()
        self.y_spinbox = QSpinBox()
        self.w_spinbox = QSpinBox()
        self.h_spinbox = QSpinBox()
        
        for spinbox in [self.x_spinbox, self.y_spinbox, self.w_spinbox, self.h_spinbox]:
            spinbox.setRange(0, 9999)
            spinbox.setEnabled(False)

        form_layout.addRow("Mask Origin X:", self.x_spinbox)
        form_layout.addRow("Mask Origin Y:", self.y_spinbox)
        form_layout.addRow("Mask Width:", self.w_spinbox)
        form_layout.addRow("Mask Height:", self.h_spinbox)
        
        self.apply_mask_button = QPushButton("Apply Mask")
        self.apply_mask_button.clicked.connect(self.apply_mask_preview)
        self.apply_mask_button.setEnabled(False)

        self.execute_button = QPushButton("Execute Inpaint")
        self.execute_button.clicked.connect(self.perform_inpainting)
        self.execute_button.setEnabled(False)

        # --- Create a button container with a grid layout to enforce equal size ---
        button_container = QWidget()
        button_grid = QGridLayout(button_container)
        button_grid.setContentsMargins(0,0,0,0)
        button_grid.addWidget(self.apply_mask_button, 0, 0)
        button_grid.addWidget(self.execute_button, 0, 1)

        mask_and_buttons_layout.addLayout(form_layout)
        mask_and_buttons_layout.addStretch()
        mask_and_buttons_layout.addWidget(button_container)
        
        main_layout.addLayout(mask_and_buttons_layout)

        # --- Status Bar ---
        status_bar_layout = QHBoxLayout()
        status_bar_layout.setContentsMargins(10, 0, 10, 5)
        self.mouse_coords_label = QLabel("Mouse: (---, ---)")
        
        status_bar_layout.addWidget(self.mouse_coords_label)
        status_bar_layout.addStretch()
        main_layout.addLayout(status_bar_layout)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", self.last_used_dir, "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.last_used_dir = os.path.dirname(file_path)
            self.original_cv_image = cv2.imread(file_path)
            if self.original_cv_image is None:
                QMessageBox.warning(self, "Error", "Failed to load the image file.")
                return
            
            # Display original image
            pixmap = self.convert_cv_to_pixmap(self.original_cv_image)
            self.original_label.setPixmap(pixmap.scaled(self.original_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            
            # Reset result label and enable controls
            self.result_label.setText("Preview / Result")
            self.active_result_cv_image = None
            self.save_button.setEnabled(False)
            self.execute_button.setEnabled(True)
            self.apply_mask_button.setEnabled(True)
            
            # Update spinbox ranges and display dimensions
            img_h, img_w, _ = self.original_cv_image.shape
            self.image_size_label.setText(f"Dimensions: {img_w} x {img_h}")
            self.x_spinbox.setMaximum(img_w - 1)
            self.y_spinbox.setMaximum(img_h - 1)
            self.w_spinbox.setMaximum(img_w)
            self.h_spinbox.setMaximum(img_h)

            for spinbox in [self.x_spinbox, self.y_spinbox, self.w_spinbox, self.h_spinbox]:
                spinbox.setEnabled(True)

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
        
        self.active_result_cv_image = image_with_mask
        pixmap = self.convert_cv_to_pixmap(self.active_result_cv_image)
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
        self.active_result_cv_image = self.result_cv_image
        
        # Display the result
        pixmap = self.convert_cv_to_pixmap(self.active_result_cv_image)
        self.result_label.setPixmap(pixmap.scaled(self.result_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        self.save_button.setEnabled(True)

    def save_image(self):
        if self.result_cv_image is None:
            QMessageBox.warning(self, "No Result", "There is no inpainted image to save.")
            return
            
        default_save_path = os.path.join(self.last_used_dir, "inpainted_result.png")
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", default_save_path, "PNG Image (*.png);;JPEG Image (*.jpg)")
        if file_path:
            try:
                cv2.imwrite(file_path, self.result_cv_image)
                QMessageBox.information(self, "Success", f"Image successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save the image.\nError: {e}")

    def resizeEvent(self, event):
        """Handle window resize to scale images correctly from their source."""
        super().resizeEvent(event)
        if self.original_cv_image is not None:
            pixmap = self.convert_cv_to_pixmap(self.original_cv_image)
            self.original_label.setPixmap(pixmap.scaled(self.original_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        if self.active_result_cv_image is not None:
            pixmap = self.convert_cv_to_pixmap(self.active_result_cv_image)
            self.result_label.setPixmap(pixmap.scaled(self.result_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    def eventFilter(self, source, event):
        """Filters events from the image labels to track the mouse."""
        if source in [self.original_label, self.result_label] and self.original_cv_image is not None:
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
                        self.w_spinbox.setValue(100)
                        self.h_spinbox.setValue(100)
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
            "<div style='font-size: 14px;'>"
            "This application uses OpenCV to remove and reconstruct selected portions of an image.<br><br>"
            "<span style='color: #00BFFF;'>"
            "Version 1.0<br>"
            "</span><br>"
            "© 2025 Wheelhouser LLC<br>"
            "Part of the <a href='http://www.marquee-magic.com' style='color: #00BFFF;'>Marquee-Magic Designer</a> suite."
            "</div>"
        )
        about_dlg.setStandardButtons(QMessageBox.Ok)
        about_dlg.exec()

    def convert_cv_to_pixmap(self, cv_img):
        """Convert an OpenCV image to a QPixmap."""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(q_image)

#=====================================================================================================
#--- Application Entry Point ---
#=====================================================================================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = InpaintingApp()
    window.show()
    sys.exit(app.exec())


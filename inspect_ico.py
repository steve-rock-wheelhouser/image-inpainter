#!/usr/bin/env python3
"""
Quick script to inspect the contents of an ICO file.
Shows all resolutions contained within the file.
"""

import sys
import struct
import os

def parse_ico_sizes(file_path):
    """Parse ICO file to extract all image sizes."""
    try:
        with open(file_path, 'rb') as f:
            # Read ICO header
            # Reserved (2 bytes), Type (2 bytes), Count (2 bytes)
            header = f.read(6)
            if len(header) != 6:
                return None
            reserved, ico_type, count = struct.unpack('<HHH', header)
            if ico_type != 1:  # Not an ICO file
                return None
            
            sizes = []
            for i in range(count):
                # Read directory entry: Width (1), Height (1), ColorCount (1), Reserved (1), Planes (2), BitCount (2), BytesInRes (4), ImageOffset (4)
                entry = f.read(16)
                if len(entry) != 16:
                    break
                width, height = struct.unpack('<BB', entry[:2])
                # Width and height are 0 for >255, but for standard, width is actual if <256
                if width == 0:
                    width = 256
                if height == 0:
                    height = 256
                # For ICO, height includes AND mask, so actual height is height // 2, but for size, it's the icon size
                sizes.append((width, height))
            
            return sizes
    except Exception as e:
        print(f"Error parsing ICO: {e}")
        return None

def inspect_ico(file_path):
    file_size = os.path.getsize(file_path)
    print(f"ICO file: {file_path}")
    print(f"File size: {file_size} bytes")
    
    try:
        # First, try manual parsing
        manual_sizes = parse_ico_sizes(file_path)
        if manual_sizes:
            print(f"Manually parsed sizes: {manual_sizes}")
            print(f"Number of images: {len(manual_sizes)}")
        else:
            print("Failed to parse ICO manually.")
        
        # Then, try Pillow
        from PIL import Image
        with Image.open(file_path) as img:
            print("\nPillow inspection:")
            print(f"Format: {img.format}")
            print(f"Mode: {img.mode}")
            if hasattr(img, 'ico_sizes'):
                print(f"ICO sizes available: {img.ico_sizes}")
                print(f"Number of sizes: {len(img.ico_sizes)}")
            print("\nAttempting to seek through frames:")
            
            i = 0
            try:
                while True:
                    img.seek(i)
                    print(f"  Frame {i}: {img.size[0]}x{img.size[1]}")
                    i += 1
            except EOFError:
                print(f"Total frames accessible: {i}")
                
    except Exception as e:
        print(f"Error opening ICO file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python inspect_ico.py <path_to_ico_file>")
        sys.exit(1)
    
    inspect_ico(sys.argv[1])
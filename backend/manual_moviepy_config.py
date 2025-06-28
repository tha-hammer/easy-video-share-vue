#!/usr/bin/env python3
"""
Manual MoviePy Configuration
Run this if the automatic configuration fails
"""

# Find MoviePy installation
import moviepy
import os

moviepy_dir = os.path.dirname(moviepy.__file__)
print(f"MoviePy directory: {moviepy_dir}")

# Create config file
config_content = '''
# MoviePy Configuration
# Set ImageMagick binary path for Windows

# Replace this path with your ImageMagick installation
IMAGEMAGICK_BINARY = r"C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"

# Common paths (uncomment the correct one):
# IMAGEMAGICK_BINARY = r"C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"
# IMAGEMAGICK_BINARY = r"C:\\Program Files (x86)\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"
'''

config_file = os.path.join(moviepy_dir, "config_defaults.py")

print(f"\nManual configuration steps:")
print(f"1. Edit this file: {config_file}")
print(f"2. Add the ImageMagick path configuration")
print(f"3. Set IMAGEMAGICK_BINARY to your magick.exe path")

print(f"\nExample content to add:")
print(config_content)

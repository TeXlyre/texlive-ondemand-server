import subprocess
import os
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FontManager:
    def __init__(self, fontlist_path='xetexfontlist.txt'):
        self.fontlist_path = fontlist_path
        self.existing_fonts = set()
        self.load_existing_fonts()

    def load_existing_fonts(self):
        """Load existing fonts from xetexfontlist.txt"""
        if os.path.exists(self.fontlist_path):
            try:
                with open(self.fontlist_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract font names (lines that don't start with numbers)
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.isdigit() and not line.startswith(
                                ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')):
                            # Clean font name
                            font_name = line.split('.')[0]  # Remove extension
                            self.existing_fonts.add(font_name.lower())
                logger.info(f"Loaded {len(self.existing_fonts)} existing fonts")
            except Exception as e:
                logger.error(f"Error loading existing fonts: {e}")

    def get_system_fonts(self):
        """Get all available system fonts using fc-list"""
        try:
            result = subprocess.run(['fc-list', ':', 'family', 'file', 'style'],
                                    capture_output=True, text=True, check=True)

            fonts = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        font_file = parts[0].strip()
                        family = parts[1].strip()
                        style = parts[2].strip() if len(parts) > 2 else 'Regular'

                        if family and os.path.exists(font_file):
                            font_key = f"{family}-{style}".lower()
                            if font_key not in self.existing_fonts:
                                fonts[font_key] = {
                                    'family': family,
                                    'style': style,
                                    'file': font_file,
                                    'filename': os.path.basename(font_file)
                                }

            logger.info(f"Found {len(fonts)} new system fonts")
            return fonts

        except subprocess.CalledProcessError as e:
            logger.error(f"Error running fc-list: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error getting system fonts: {e}")
            return {}

    def generate_font_entry(self, font_data, font_id):
        """Generate XeTeX font list entry for a font"""
        family = font_data['family']
        style = font_data['style']
        filename = font_data['filename']

        # Determine weight and slant from style
        weight = 400  # Regular
        slant = 0  # Not italic

        style_lower = style.lower()
        if 'bold' in style_lower or 'black' in style_lower:
            if 'extra' in style_lower or 'ultra' in style_lower:
                weight = 800
            else:
                weight = 700
        elif 'light' in style_lower:
            weight = 300
        elif 'thin' in style_lower:
            weight = 200
        elif 'medium' in style_lower:
            weight = 500
        elif 'semibold' in style_lower:
            weight = 600

        if 'italic' in style_lower or 'oblique' in style_lower:
            slant = 212

        # Basic font entry format (simplified version)
        entry = f"""{filename}
0
1
{family}
1
{style}
1
{family} {style}
{family}-{style.replace(' ', '')}

{weight}
5
{slant}
{'1' if 'bold' in style_lower else '0'}
{'1' if 'italic' in style_lower or 'oblique' in style_lower else '0'}
{'1' if 'italic' in style_lower or 'oblique' in style_lower else '0'}
10.000000
0.000000
0.000000
0
0"""

        return entry

    def append_fonts_to_list(self):
        """Append new fonts to xetexfontlist.txt"""
        new_fonts = self.get_system_fonts()

        if not new_fonts:
            logger.info("No new fonts to add")
            return

        try:
            # Read existing content
            existing_content = ""
            font_count = 0

            if os.path.exists(self.fontlist_path):
                with open(self.fontlist_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read().strip()
                    # Get the last font ID
                    lines = existing_content.split('\n')
                    if lines and lines[0].isdigit():
                        font_count = int(lines[0])

            # Generate new entries
            new_entries = []
            for font_key, font_data in new_fonts.items():
                font_count += 1
                entry = self.generate_font_entry(font_data, font_count)
                new_entries.append(f"{font_count}\n{entry}")

            # Write updated file
            with open(self.fontlist_path, 'w', encoding='utf-8') as f:
                # Write updated font count
                f.write(f"{font_count}\n")

                # Write existing content (skip first line if it was count)
                if existing_content:
                    lines = existing_content.split('\n')
                    if lines and lines[0].isdigit():
                        existing_content = '\n'.join(lines[1:])
                    f.write(existing_content)
                    if not existing_content.endswith('\n'):
                        f.write('\n')

                # Write new entries
                for entry in new_entries:
                    f.write(entry + '\n')

            logger.info(f"Added {len(new_entries)} new fonts to {self.fontlist_path}")

        except Exception as e:
            logger.error(f"Error updating font list: {e}")

    def update_font_cache(self):
        """Update system font cache"""
        try:
            subprocess.run(['fc-cache', '-fv'], check=True)
            logger.info("Font cache updated successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error updating font cache: {e}")
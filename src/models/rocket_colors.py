"""
Rocket Color Constants (STORY-004-05)

Shared constants for rocket customization feature.
Placed in a separate module to avoid circular imports.
"""

# Preset color palette for rocket customization
ROCKET_COLOR_PRESETS = [
    {"hex": "#FF4444", "name": "Red", "rgb": (255, 68, 68)},
    {"hex": "#4488FF", "name": "Blue", "rgb": (68, 136, 255)},
    {"hex": "#44FF44", "name": "Green", "rgb": (68, 255, 68)},
    {"hex": "#FFD700", "name": "Yellow", "rgb": (255, 215, 0)},
    {"hex": "#AA44FF", "name": "Purple", "rgb": (170, 68, 255)},
    {"hex": "#FF8844", "name": "Orange", "rgb": (255, 136, 68)},
    {"hex": "#FF44AA", "name": "Pink", "rgb": (255, 68, 170)},
    {"hex": "#44FFFF", "name": "Cyan", "rgb": (68, 255, 255)},
]

DEFAULT_ROCKET_COLOR = "#4488FF"  # Blue - neutral, pleasing to most users


def hex_to_rgb(hex_color: str) -> tuple:
    """
    Convert hex color string to RGB tuple.
    
    Args:
        hex_color: Hex color string (e.g., "#FF4444")
        
    Returns:
        RGB tuple (r, g, b) with values 0-255
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: tuple) -> str:
    """
    Convert RGB tuple to hex color string.
    
    Args:
        rgb: RGB tuple (r, g, b) with values 0-255
        
    Returns:
        Hex color string (e.g., "#FF4444")
    """
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
"""
Theme management for Word Quest space-themed visuals.

Provides centralized color management, theme configuration, and utilities
for applying the space theme across all game screens.
"""

import json
import os
from typing import Dict, Tuple, Optional
import pygame


# Color constants for space theme
SPACE_BLUE = (26, 26, 62)  # #1a1a3e - Deep space blue background
STAR_WHITE = (255, 255, 255)  # White stars
STAR_PALE_YELLOW = (255, 255, 224)  # #FFFFE0 - Pale yellow stars

# Planet colors (color-blind safe palette)
PLANET_1 = (255, 152, 0)   # Orange
PLANET_2 = (33, 150, 243)  # Blue
PLANET_3 = (156, 39, 176)  # Purple
PLANET_4 = (76, 175, 80)   # Green
PLANET_5 = (244, 67, 54)   # Red (color-blind safe alternative)

# UI Element colors
UI_TEXT_NORMAL = (255, 255, 255)  # White text
UI_TEXT_MUTED = (189, 189, 189)   # Grey text
UI_ACCENT = (255, 152, 0)         # Orange accent
UI_SUCCESS = (76, 175, 80)        # Green success
UI_WARNING = (255, 152, 0)        # Orange warning
UI_ERROR = (244, 67, 54)          # Red error
UI_BG_LIGHT = (42, 42, 80)        # Slightly lighter blue for panels
UI_BG_DARK = (26, 26, 62)         # Deep blue for backgrounds
UI_BORDER = (100, 100, 150)       # Muted purple-blue for borders

# Font colors
FONT_PRIMARY = (255, 255, 255)
FONT_SECONDARY = (189, 189, 189)
FONT_ACCENT = (255, 200, 100)


class ThemeManager:
    """
    Central configuration for all theme colors and assets.
    Provides colors by name and handles theme switching.
    """
    
    def __init__(self, config_path: str = "data/theme_config.json"):
        """Initialize theme manager with configuration."""
        self.config_path = config_path
        self._colors: Dict[str, Tuple[int, int, int]] = {}
        self._load_default_colors()
        self._load_config()
        
    def _load_default_colors(self) -> None:
        """Load default color palette."""
        self._colors = {
            # Background colors
            "space_blue": SPACE_BLUE,
            "ui_bg_light": UI_BG_LIGHT,
            "ui_bg_dark": UI_BG_DARK,
            
            # Star colors
            "star_white": STAR_WHITE,
            "star_pale_yellow": STAR_PALE_YELLOW,
            
            # Planet colors
            "planet_1": PLANET_1,
            "planet_2": PLANET_2,
            "planet_3": PLANET_3,
            "planet_4": PLANET_4,
            "planet_5": PLANET_5,
            
            # Text colors
            "text_normal": UI_TEXT_NORMAL,
            "text_muted": UI_TEXT_MUTED,
            "font_primary": FONT_PRIMARY,
            "font_secondary": FONT_SECONDARY,
            "font_accent": FONT_ACCENT,
            
            # UI element colors
            "ui_accent": UI_ACCENT,
            "ui_success": UI_SUCCESS,
            "ui_warning": UI_WARNING,
            "ui_error": UI_ERROR,
            "ui_border": UI_BORDER,
        }
    
    def _load_config(self) -> None:
        """Load theme configuration from JSON file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Override default colors with config values
                    for color_name, color_value in config.get("colors", {}).items():
                        if isinstance(color_value, list) and len(color_value) == 3:
                            self._colors[color_name] = tuple(color_value)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load theme config: {e}")
    
    def get_color(self, name: str, default: Optional[Tuple[int, int, int]] = None) -> Tuple[int, int, int]:
        """
        Return RGB tuple for theme color name.
        
        Args:
            name: Color name (e.g., "space_blue", "planet_1")
            default: Default color if name not found
            
        Returns:
            RGB tuple (R, G, B)
        """
        return self._colors.get(name, default or SPACE_BLUE)
    
    def get_planet_color(self, planet_number: int) -> Tuple[int, int, int]:
        """
        Get color for a specific planet.
        
        Args:
            planet_number: Planet number (1-5)
            
        Returns:
            RGB tuple for the planet color
        """
        color_name = f"planet_{planet_number}"
        return self._colors.get(color_name, PLANET_1)
    
    def set_color(self, name: str, color: Tuple[int, int, int]) -> None:
        """
        Set a color in the theme.
        
        Args:
            name: Color name
            color: RGB tuple
        """
        self._colors[name] = color
    
    def get_colors(self) -> Dict[str, Tuple[int, int, int]]:
        """Return all theme colors."""
        return self._colors.copy()
    
    def save_config(self) -> None:
        """Save current theme configuration to file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        config = {"colors": self._colors}
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def get_font(self, size: int) -> pygame.font.Font:
        """
        Return themed font at specified size.
        
        Args:
            size: Font size in pixels
            
        Returns:
            pygame.font.Font object
        """
        # Use default pygame font for MVP
        return pygame.font.Font(None, size)
    
    def get_font_large(self) -> pygame.font.Font:
        """Return large themed font."""
        return self.get_font(48)
    
    def get_font_medium(self) -> pygame.font.Font:
        """Return medium themed font."""
        return self.get_font(32)
    
    def get_font_small(self) -> pygame.font.Font:
        """Return small themed font."""
        return self.get_font(24)


# Global theme instance
_theme_instance: Optional[ThemeManager] = None


def get_theme() -> ThemeManager:
    """Get or create the global theme manager instance."""
    global _theme_instance
    if _theme_instance is None:
        _theme_instance = ThemeManager()
    return _theme_instance


def reset_theme() -> None:
    """Reset the global theme instance."""
    global _theme_instance
    _theme_instance = None
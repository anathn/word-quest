"""
Theme management for Word Quest space-themed visuals.

Provides centralized color management, theme configuration, and utilities
for applying the space theme across all game screens.
Updated with color-blind safe palette for accessibility (STORY-006-01).
"""

import json
import os
from typing import Dict, Tuple, Optional
import pygame

from .color_validator import ColorValidator


# Color constants for space theme - COLOR-BLIND SAFE PALETTE
# Updated to avoid red-green combinations for accessibility

SPACE_BLUE = (26, 26, 62)  # #1a1a3e - Deep space blue background
STAR_WHITE = (255, 255, 255)  # White stars
STAR_PALE_YELLOW = (255, 255, 224)  # #FFFFE0 - Pale yellow stars

# Planet colors (color-blind safe palette)
# Key changes: PLANET_4 is brown (not green), PLANET_5 is yellow-gold (not red/teal)
PLANET_1 = (255, 152, 0)   # Orange
PLANET_2 = (33, 150, 243)  # Blue
PLANET_3 = (156, 39, 176)  # Purple
PLANET_4 = (121, 85, 72)   # Brown (instead of green)
PLANET_5 = (205, 170, 80)  # Gold/Yellow (instead of teal - more distinguishable from blue)

# UI Element colors - color-blind safe
UI_TEXT_NORMAL = (255, 255, 255)  # White text
UI_TEXT_MUTED = (189, 189, 189)   # Grey text
UI_ACCENT = (255, 152, 0)         # Orange accent
UI_SUCCESS = (76, 175, 80)        # Green success (always used with shape indicator)
UI_ERROR = (33, 150, 243)         # Blue error (NOT red - color-blind safe!)
UI_WARNING = (255, 152, 0)        # Orange warning
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
    Color-blind safe palette is the default.
    
    STORY-006-01: Updated to ensure all colors are distinguishable
    for users with deuteranopia, protanopia, and tritanopia.
    """
    
    def __init__(self, config_path: str = "data/theme_config.json"):
        """Initialize theme manager with configuration."""
        self.config_path = config_path
        self._colors: Dict[str, Tuple[int, int, int]] = {}
        self._color_validator = ColorValidator()
        self._load_default_colors()
        self._load_config()
        self._validate_colors()
    
    def _validate_colors(self) -> None:
        """Validate all colors for color-blind accessibility."""
        # Check critical color pairs for distinguishability
        critical_pairs = [
            ("ui_success", "ui_error"),      # Success vs error
            ("planet_1", "planet_2"),        # Adjacent planets
            ("planet_3", "planet_4"),        # Adjacent planets
            ("planet_4", "planet_5"),        # Adjacent planets
        ]
        
        for name1, name2 in critical_pairs:
            color1 = self._colors.get(name1)
            color2 = self._colors.get(name2)
            if color1 and color2:
                passes, reason = self._color_validator.validate_color_pair_with_reason(color1, color2)
                if not passes:
                    print(f"Warning: {name1} vs {name2} may not be distinguishable: {reason}")
    
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
            
            # Planet colors - color-blind safe palette
            "planet_1": PLANET_1,
            "planet_2": PLANET_2,
            "planet_3": PLANET_3,
            "planet_4": PLANET_4,
            "planet_5": PLANET_5,  # Gold/Yellow - distinguishable from all others
            
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
    
    def get_planet_bloom_color(self, planet_number: int) -> Tuple[int, int, int]:
        """
        Get brighter bloom color for a completed planet.
        
        Args:
            planet_number: Planet number (1-5)
            
        Returns:
            RGB tuple for the brighter bloom color
        """
        # Planet bloom colors (brighter versions) - color-blind safe
        PLANET_BLOOM_COLORS = {
            1: (255, 183, 77),   # Bright Orange
            2: (100, 181, 246),  # Bright Blue
            3: (186, 104, 200),  # Bright Purple
            4: (161, 136, 127),  # Lighter Brown (NOT bright green)
            5: (230, 200, 120),  # Light Gold (NOT teal)
        }
        return PLANET_BLOOM_COLORS.get(planet_number, PLANET_1)
    
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
    
    # Color-blind accessibility methods (STORY-006-01)
    
    def validate_color_against_background(self, color: Tuple[int, int, int],
                                           background: Tuple[int, int, int] = None) -> Tuple[bool, float]:
        """
        Validate a color has sufficient contrast against background.
        
        Args:
            color: Color to validate (R, G, B)
            background: Background color (defaults to space_blue)
            
        Returns:
            Tuple of (passes_contrast_check, contrast_ratio)
        """
        if background is None:
            background = self._colors.get("space_blue", SPACE_BLUE)
        
        return self._color_validator.validate_contrast(color, background)
    
    def get_luminance(self, color: Tuple[int, int, int]) -> float:
        """
        Get the luminance of a color.
        
        Args:
            color: Color (R, G, B)
            
        Returns:
            Luminance value (0.0 to 1.0)
        """
        return self._color_validator.get_luminance(color)
    
    def simulate_color_deuteranopia(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Simulate how a color appears to someone with deuteranopia.
        
        Args:
            color: Color (R, G, B)
            
        Returns:
            Simulated color (R, G, B)
        """
        return self._color_validator.simulate_deuteranopia(color)
    
    def simulate_color_protanopia(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Simulate how a color appears to someone with protanopia.
        
        Args:
            color: Color (R, G, B)
            
        Returns:
            Simulated color (R, G, B)
        """
        return self._color_validator.simulate_protanopia(color)
    
    def simulate_color_tritanopia(self, color: Tuple[int, int, int]) -> Tuple[int, int, int]:
        """
        Simulate how a color appears to someone with tritanopia.
        
        Args:
            color: Color (R, G, B)
            
        Returns:
            Simulated color (R, G, B)
        """
        return self._color_validator.simulate_tritanopia(color)
    
    def generate_theme_audit_report(self) -> str:
        """
        Generate an accessibility audit report for the current theme.
        
        Returns:
            Formatted audit report string
        """
        return self._color_validator.generate_audit_report(
            self._colors,
            "Word Quest Theme Color Accessibility Audit"
        )


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
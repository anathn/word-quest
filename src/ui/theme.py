"""
Theme management for Word Quest space-themed visuals.

Provides centralized color management, theme configuration, and utilities
for applying the space theme across all game screens.
Updated with color-blind safe palette for accessibility (STORY-006-01).
Updated with OpenDyslexic font support for accessibility (STORY-006-05).
Updated with high contrast mode for accessibility (STORY-006-06).
"""

import json
import os
import logging
from typing import Dict, Tuple, Optional, Callable
import pygame

from .color_validator import ColorValidator
from .font_manager import FontManager, get_font_manager

# Import high contrast theme
try:
    from .high_contrast_theme import HIGH_CONTRAST_THEME, hex_to_rgb, generate_theme_report
except ImportError:
    # Fallback if high contrast module not available
    HIGH_CONTRAST_THEME = {}
    
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex to RGB (fallback implementation)."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def generate_theme_report() -> str:
        """Generate theme report (fallback)."""
        return "High contrast theme not available"


logger = logging.getLogger(__name__)


# Color constants for space theme - COLOR-BLIND SAFE PALETTE
# Updated to avoid red-green combinations for accessibility

SPACE_BLUE = (26, 26, 62)  # #1a1a3e - Deep space blue background
STAR_WHITE = (255, 255, 255)  # White stars
STAR_PALE_YELLOW = (255, 255, 224)  # #FFFFE0 - Pale yellow stars

# Planet colors (color-blind safe palette)
# Key changes: PLANET_4 is brown (not green), PLANET_5 is gold (not red/teal)
PLANET_1 = (255, 152, 0)   # Orange
PLANET_2 = (33, 150, 243)  # Blue
PLANET_3 = (156, 39, 176)  # Purple
PLANET_4 = (121, 85, 72)   # Brown (instead of green)
PLANET_5 = (205, 170, 80)  # Gold (instead of red - distinguishable from blue for color-blind users)

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

# Planet state colors (for space map) - color-blind safe palette
PLANET_LOCKED = (80, 80, 100)        # Dark gray-blue
PLANET_VISITED = (100, 149, 237)      # Cornflower blue
PLANET_COMPLETED = (255, 215, 0)      # Gold
PLANET_CURRENT = (0, 191, 255)        # Deep sky blue


class ThemeManager:
    """
    Central configuration for all theme colors and assets.
    Provides colors by name and handles theme switching.
    Color-blind safe palette is the default.
    
    STORY-006-01: Updated to ensure all colors are distinguishable
    for users with deuteranopia, protanopia, and tritanopia.
    STORY-006-06: Added high contrast mode support with WCAG AAA compliance.
    """
    
    # Theme constants
    THEME_DEFAULT = "default"
    THEME_HIGH_CONTRAST = "high_contrast"
    
    def __init__(self, config_path: str = "data/theme_config.json"):
        """Initialize theme manager with configuration."""
        # Make path absolute relative to this module if it's a relative path
        if not os.path.isabs(config_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, '..', '..', config_path)
        
        self.config_path = config_path
        self._colors: Dict[str, Tuple[int, int, int]] = {}
        self._color_validator = ColorValidator()
        self._font_manager: Optional[FontManager] = None
        self._current_theme = self.THEME_DEFAULT
        self._high_contrast_colors: Dict[str, Tuple[int, int, int]] = {}
        self._theme_change_callbacks: List[Callable[[str], None]] = []
        self._load_default_colors()
        self._load_config()
        self._load_high_contrast_colors()
        self._validate_colors()
        self._init_font_manager()
    
    def _init_font_manager(self) -> None:
        """Initialize font manager."""
        try:
            self._font_manager = get_font_manager()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Could not initialize font manager: {e}")
            self._font_manager = None
    
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
            # Note: These default values can be overridden by theme_config.json
            "planet_1": PLANET_1,
            "planet_2": PLANET_2,
            "planet_3": PLANET_3,
            "planet_4": PLANET_4,
            "planet_5": PLANET_5,  # Gold - distinguishable from all others (not red/green)
            
            # Planet state colors (for space map)
            "planet_locked": PLANET_LOCKED,
            "planet_visited": PLANET_VISITED,
            "planet_completed": PLANET_COMPLETED,
            "planet_current": PLANET_CURRENT,
            
            # Text colors
            "text_normal": UI_TEXT_NORMAL,
            "text_muted": UI_TEXT_MUTED,
            "text_primary": FONT_PRIMARY,  # Alias for compatibility
            "text_secondary": FONT_SECONDARY,  # Alias for compatibility
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
    
    def _load_high_contrast_colors(self) -> None:
        """Load high contrast color palette from high_contrast_theme module."""
        if not HIGH_CONTRAST_THEME:
            logger.warning("HIGH_CONTRAST_THEME not available")
            return
            
        for name, hex_color in HIGH_CONTRAST_THEME.items():
            if isinstance(hex_color, str):
                try:
                    self._high_contrast_colors[name] = hex_to_rgb(hex_color)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Invalid hex color for {name}: {hex_color} - {e}")
                    # Fallback to white
                    self._high_contrast_colors[name] = (255, 255, 255)
            elif isinstance(hex_color, (list, tuple)) and len(hex_color) == 3:
                self._high_contrast_colors[name] = tuple(hex_color)
    
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
        Return themed font at specified size using current typography settings.
        
        Args:
            size: Font size in pixels
            
        Returns:
            pygame.font.Font object
        """
        if self._font_manager:
            return self._font_manager.get_font(size=size)
        # Fallback if font manager not available
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
    
    # Theme switching methods (STORY-006-06: High Contrast Mode)
    
    def get_current_theme(self) -> str:
        """
        Get the current theme name.
        
        Returns:
            Current theme name ("default" or "high_contrast")
        """
        return self._current_theme
    
    def is_high_contrast(self) -> bool:
        """
        Check if high contrast mode is active.
        
        Returns:
            True if high contrast mode is enabled
        """
        return self._current_theme == self.THEME_HIGH_CONTRAST
    
    def enable_high_contrast(self) -> bool:
        """
        Enable high contrast mode.
        
        Switches all colors to high contrast palette.
        Theme switch should complete in <100ms.
        
        Returns:
            True if successful, False if high contrast theme not available
        """
        if not self._high_contrast_colors:
            logger.warning("High contrast theme not available")
            return False
            
        self._current_theme = self.THEME_HIGH_CONTRAST
        self._colors = self._high_contrast_colors.copy()
        
        # Notify all registered screens/components of theme change
        self._apply_theme()
        
        logger.info("High contrast mode enabled")
        return True
    
    def disable_high_contrast(self) -> bool:
        """
        Disable high contrast mode and return to default theme.
        
        Returns:
            True if successful
        """
        self._current_theme = self.THEME_DEFAULT
        # Reload default colors
        self._load_default_colors()
        self._load_config()  # Re-apply any config overrides
        
        # Notify all registered screens/components of theme change
        self._apply_theme()
        
        logger.info("High contrast mode disabled")
        return True
    
    def toggle_high_contrast(self) -> bool:
        """
        Toggle high contrast mode on/off.
        
        Returns:
            True if successful
        """
        if self.is_high_contrast():
            return self.disable_high_contrast()
        else:
            return self.enable_high_contrast()
    
    def set_theme(self, theme_name: str) -> bool:
        """
        Set theme by name.
        
        Args:
            theme_name: Theme name ("default" or "high_contrast")
            
        Returns:
            True if theme set successfully
        """
        if theme_name == self.THEME_HIGH_CONTRAST:
            return self.enable_high_contrast()
        elif theme_name == self.THEME_DEFAULT:
            return self.disable_high_contrast()
        else:
            logger.warning(f"Unknown theme: {theme_name}")
            return False
    
    # Theme change notification system (STORY-006-06)
    
    def register_theme_change_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register a callback to be called when theme changes.
        
        Args:
            callback: Function to call with new theme name as argument
        """
        if callback not in self._theme_change_callbacks:
            self._theme_change_callbacks.append(callback)
            logger.debug(f"Registered theme change callback: {callback.__name__}")
    
    def unregister_theme_change_callback(self, callback: Callable[[str], None]) -> None:
        """
        Unregister a theme change callback.
        
        Args:
            callback: Function to remove from notification list
        """
        if callback in self._theme_change_callbacks:
            self._theme_change_callbacks.remove(callback)
            logger.debug(f"Unregistered theme change callback: {callback.__name__}")
    
    def _apply_theme(self) -> None:
        """
        Notify all registered screens/components of theme change.
        
        This method is called after theme switching to notify all
        screens that they need to refresh their UI elements with
        the new color scheme.
        
        Screens should register callbacks via register_theme_change_callback()
        to receive theme change notifications and refresh their UI accordingly.
        """
        theme_name = self._current_theme
        
        # Notify all registered callbacks
        for callback in self._theme_change_callbacks:
            try:
                callback(theme_name)
            except Exception as e:
                logger.warning(f"Theme change callback failed: {e}")
        
        # Also post a pygame event for screens that prefer event-driven updates
        theme_event = pygame.USEREVENT + 50  # Arbitrary unique event ID
        pygame.event.post(pygame.event.Event(theme_event, theme=theme_name))
    
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
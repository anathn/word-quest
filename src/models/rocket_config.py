"""
Rocket Configuration Model (STORY-005-02)

Manages rocket color presets and player preferences for rocket customization.
Handles persistence of rocket color choices to player profiles.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
import json
import os

# Color preset definitions matching STORY-005-02 specification
ROCKET_COLOR_PRESETS = [
    {"name": "White", "rgb": (255, 255, 255), "hex": "#FFFFFF"},
    {"name": "Red", "rgb": (244, 67, 54), "hex": "#F44336"},
    {"name": "Blue", "rgb": (33, 150, 243), "hex": "#2196F3"},
    {"name": "Green", "rgb": (76, 175, 80), "hex": "#4CAF50"},
    {"name": "Yellow", "rgb": (255, 235, 59), "hex": "#FFEB3B"},
    {"name": "Purple", "rgb": (156, 39, 176), "hex": "#9C27B0"},
    {"name": "Orange", "rgb": (255, 152, 0), "hex": "#FF9800"},
    {"name": "Pink", "rgb": (233, 30, 99), "hex": "#E91E63"},
]

DEFAULT_ROCKET_COLOR_RGB = (255, 255, 255)  # White - neutral default
DEFAULT_ROCKET_COLOR_HEX = "#FFFFFF"

# Performance targets
MAX_COLOR_CHANGE_TIME_MS = 3  # Maximum time for color change
CACHE_MAX_SIZE = 8  # Cache rendered sprites for each color


@dataclass
class RocketColor:
    """Represents a rocket color preset."""
    name: str
    rgb: tuple
    hex: str
    
    def __post_init__(self):
        """Validate RGB values."""
        if not all(0 <= v <= 255 for v in self.rgb):
            raise ValueError(f"RGB values must be 0-255, got {self.rgb}")


class RocketConfig:
    """
    Configuration manager for rocket colors and preferences.
    
    Provides:
    - Access to color presets
    - Current rocket color management
    - Persistence to player profile
    - Color validation
    
    Attributes:
        player_id: Unique player identifier for persistence
        rocket_colors: List of available RocketColor presets
    """
    
    def __init__(self, player_id: str):
        """
        Initialize rocket configuration for a player.
        
        Args:
            player_id: Unique identifier for the player profile
            
        Example:
            >>> config = RocketConfig("student_123")
            >>> config.get_current_color()
            (255, 255, 255)
        """
        self.player_id = player_id
        self.rocket_colors = [RocketColor(**c) for c in ROCKET_COLOR_PRESETS]
        self._current_color_rgb = DEFAULT_ROCKET_COLOR_RGB
        self._current_color_hex = DEFAULT_ROCKET_COLOR_HEX
        self._load_player_preference()
    
    def _load_player_preference(self):
        """Load saved rocket color preference from player profile."""
        try:
            from src.profiles.student_profile import get_student_profile_path
            
            profile_path = get_student_profile_path(self.player_id)
            if os.path.exists(profile_path):
                with open(profile_path, 'r') as f:
                    profile_data = json.load(f)
                    rocket_color = profile_data.get('rocket_color', DEFAULT_ROCKET_COLOR_HEX)
                    self.set_color_by_hex(rocket_color)
        except (FileNotFoundError, json.JSONDecodeError, KeyError, ImportError):
            # Use default color if profile doesn't exist or has issues
            self._current_color_rgb = DEFAULT_ROCKET_COLOR_RGB
            self._current_color_hex = DEFAULT_ROCKET_COLOR_HEX
    
    def get_current_color(self) -> tuple:
        """
        Return currently selected rocket color as RGB tuple.
        
        Returns:
            RGB tuple (r, g, b) with values 0-255
            
        Example:
            >>> config = RocketConfig("student_123")
            >>> config.get_current_color()
            (255, 255, 255)
        """
        return self._current_color_rgb
    
    def get_current_color_hex(self) -> str:
        """
        Return currently selected rocket color as hex string.
        
        Returns:
            Hex color string (e.g., "#FFFFFF")
        """
        return self._current_color_hex
    
    def set_color(self, rgb: tuple):
        """
        Set rocket color by RGB values.
        
        Args:
            rgb: RGB tuple (r, g, b) with values 0-255
            
        Raises:
            ValueError: If RGB values are out of range or color is not in presets
            
        Example:
            >>> config = RocketConfig("student_123")
            >>> config.set_color((244, 67, 54))  # Red
        """
        # Validate RGB values
        if not all(isinstance(v, int) and 0 <= v <= 255 for v in rgb):
            raise ValueError(f"RGB values must be integers 0-255, got {rgb}")
        
        # Convert to hex for validation against presets
        hex_color = self.rgb_to_hex(rgb)
        
        # Validate against presets
        preset_hex = [c.hex.upper() for c in self.rocket_colors]
        if hex_color.upper() not in preset_hex:
            raise ValueError(f"Color {hex_color} is not in preset list. "
                           f"Available: {preset_hex}")
        
        self._current_color_rgb = rgb
        self._current_color_hex = hex_color.upper()
        self._save_player_preference()
    
    def set_color_by_hex(self, hex_color: str):
        """
        Set rocket color by hex string.
        
        Args:
            hex_color: Hex color string (e.g., "#F44336")
            
        Raises:
            ValueError: If hex color is invalid or not in presets
            
        Example:
            >>> config = RocketConfig("student_123")
            >>> config.set_color_by_hex("#F44336")  # Red
        """
        # Validate hex format
        try:
            rgb = self.hex_to_rgb(hex_color)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid hex color format: {hex_color}") from e
        
        # Validate against presets
        preset_hex = [c.hex for c in self.rocket_colors]
        if hex_color.upper() not in [h.upper() for h in preset_hex]:
            raise ValueError(f"Color {hex_color} is not in preset list. "
                           f"Available: {preset_hex}")
        
        self._current_color_hex = hex_color.upper()
        self._current_color_rgb = rgb
        self._save_player_preference()
    
    def _save_player_preference(self):
        """Save rocket color preference to player profile."""
        try:
            from src.profiles.student_profile import load_student_profile, save_student_profile
            
            profile = load_student_profile(self.player_id)
            if profile:
                profile.rocket_color = self._current_color_hex
                save_student_profile(profile)
        except (FileNotFoundError, ImportError):
            # Profile doesn't exist yet - will be saved when profile is created
            pass
    
    def get_available_colors(self) -> List[tuple]:
        """
        Return list of available preset colors.
        
        Returns:
            List of RGB tuples for all available colors
            
        Example:
            >>> config = RocketConfig("student_123")
            >>> colors = config.get_available_colors()
            >>> len(colors)
            8
        """
        return [color.rgb for color in self.rocket_colors]
    
    def get_available_colors_hex(self) -> List[str]:
        """
        Return list of available preset colors as hex strings.
        
        Returns:
            List of hex color strings
        """
        return [color.hex for color in self.rocket_colors]
    
    def get_color_name(self, rgb: tuple) -> str:
        """
        Get the name of a color from RGB values.
        
        Args:
            rgb: RGB tuple to look up
            
        Returns:
            Color name, or "Unknown" if not in presets
        """
        for color in self.rocket_colors:
            if color.rgb == rgb:
                return color.name
        return "Unknown"
    
    def validate_color(self, rgb: tuple) -> bool:
        """
        Check if a color is in the preset list.
        
        Args:
            rgb: RGB tuple to validate
            
        Returns:
            True if color is valid (in presets)
        """
        return rgb in [color.rgb for color in self.rocket_colors]
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple:
        """
        Convert hex color string to RGB tuple.
        
        Args:
            hex_color: Hex color string (e.g., "#FF4444")
            
        Returns:
            RGB tuple (r, g, b) with values 0-255
            
        Raises:
            ValueError: If hex format is invalid
        """
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color format: {hex_color}")
        
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
        except ValueError as e:
            raise ValueError(f"Invalid hex color format: {hex_color}") from e
        
        return (r, g, b)
    
    @staticmethod
    def rgb_to_hex(rgb: tuple) -> str:
        """
        Convert RGB tuple to hex color string.
        
        Args:
            rgb: RGB tuple (r, g, b) with values 0-255
            
        Returns:
            Hex color string (e.g., "#FF4444")
        """
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def create_rocket_config(player_id: str) -> RocketConfig:
    """
    Factory function to create a RocketConfig instance.
    
    Args:
        player_id: Unique identifier for the player
        
    Returns:
        Configured RocketConfig instance
        
    Example:
        >>> config = create_rocket_config("student_123")
        >>> config.get_current_color()
        (255, 255, 255)
    """
    return RocketConfig(player_id)
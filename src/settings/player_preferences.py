"""
Player Preferences (STORY-005-02)

Wrapper module for player preference management.
This module provides a centralized interface for accessing and managing
player preferences including rocket color, audio settings, and other
personalization options.

Note: This is a wrapper around the profile system to provide a consistent
API for preference management across the application.
"""

from typing import Optional, Tuple, Dict
from dataclasses import dataclass
import json
import os


@dataclass
class PlayerPreferences:
    """Container for player preference data."""
    player_id: str
    rocket_color: str = "#FFFFFF"  # Hex color
    audio_enabled: bool = True
    music_volume: float = 0.3  # 0.0 to 1.0 (default 30% as per story)
    music_muted: bool = False  # Music mute state
    sfx_volume: float = 0.7    # 0.0 to 1.0
    text_size: str = "medium"  # "small", "medium", "large"
    animations_enabled: bool = True
    animation_intensity: str = "full"  # "full", "reduced", "off" (STORY-005-05)


class PlayerPreferencesManager:
    """
    Centralized player preferences management.
    
    Provides a unified interface for:
    - Reading/writing player preferences
    - Rocket color customization
    - Audio settings
    - Display preferences
    
    This class wraps the underlying profile system to provide a clean API
    for preference management throughout the application.
    """
    
    def __init__(self):
        """Initialize the preferences manager."""
        self._current_player_id: Optional[str] = None
        self._preferences: Optional[PlayerPreferences] = None
    
    def set_current_player(self, player_id: str):
        """
        Set the current player and load their preferences.
        
        Args:
            player_id: Unique player identifier
        """
        self._current_player_id = player_id
        self._preferences = self._load_preferences(player_id)
    
    def _load_preferences(self, player_id: str) -> PlayerPreferences:
        """
        Load preferences for a specific player.
        
        Args:
            player_id: Player identifier
            
        Returns:
            PlayerPreferences instance with loaded or default values
        """
        try:
            from src.profiles.student_profile import load_student_profile
            
            profile = load_student_profile(player_id)
            if profile:
                return PlayerPreferences(
                    player_id=player_id,
                    rocket_color=profile.rocket_color,
                    audio_enabled=profile.audio_enabled if hasattr(profile, 'audio_enabled') else True
                )
        except (FileNotFoundError, ImportError, AttributeError):
            pass
        
        # Return defaults if profile not found
        return PlayerPreferences(player_id=player_id)
    
    def _save_preferences(self, preferences: PlayerPreferences):
        """
        Save preferences to player profile.
        
        Args:
            preferences: PlayerPreferences to save
        """
        try:
            from src.profiles.student_profile import load_student_profile, save_student_profile
            
            profile = load_student_profile(preferences.player_id)
            if profile:
                profile.rocket_color = preferences.rocket_color
                if hasattr(profile, 'audio_enabled'):
                    profile.audio_enabled = preferences.audio_enabled
                save_student_profile(profile)
        except (FileNotFoundError, ImportError, AttributeError):
            # Profile doesn't exist - will be created when student logs in
            pass
    
    # Rocket Color Methods
    
    def get_rocket_color(self) -> str:
        """
        Get current rocket color preference.
        
        Returns:
            Hex color string (e.g., "#FFFFFF")
        """
        if self._preferences:
            return self._preferences.rocket_color
        return "#FFFFFF"  # Default white
    
    def set_rocket_color(self, hex_color: str):
        """
        Set rocket color preference.
        
        Args:
            hex_color: Hex color string (e.g., "#F44336" for red)
        """
        if not self._current_player_id:
            raise ValueError("No player set. Call set_current_player() first.")
        
        # Validate color format
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color format: {hex_color}")
        
        if self._preferences:
            self._preferences.rocket_color = f"#{hex_color.upper()}"
            self._save_preferences(self._preferences)
    
    def get_rocket_color_rgb(self) -> Tuple[int, int, int]:
        """
        Get current rocket color as RGB tuple.
        
        Returns:
            RGB tuple (r, g, b) with values 0-255
        """
        hex_color = self.get_rocket_color()
        return self._hex_to_rgb(hex_color)
    
    def set_rocket_color_rgb(self, rgb: Tuple[int, int, int]):
        """
        Set rocket color using RGB values.
        
        Args:
            rgb: RGB tuple (r, g, b) with values 0-255
        """
        hex_color = self._rgb_to_hex(rgb)
        self.set_rocket_color(hex_color)
    
    # Audio Methods
    
    def get_audio_enabled(self) -> bool:
        """Check if audio is enabled."""
        if self._preferences:
            return self._preferences.audio_enabled
        return True
    
    def set_audio_enabled(self, enabled: bool):
        """Enable or disable audio."""
        if self._preferences:
            self._preferences.audio_enabled = enabled
            self._save_preferences(self._preferences)
    
    def get_music_volume(self) -> float:
        """Get music volume (0.0 to 1.0)."""
        if self._preferences:
            return self._preferences.music_volume
        return 0.3  # Default 30% as per story
    
    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)."""
        volume = max(0.0, min(1.0, volume))
        if self._preferences:
            self._preferences.music_volume = volume
            self._save_preferences(self._preferences)
    
    def get_music_muted(self) -> bool:
        """Get music mute state."""
        if self._preferences:
            return self._preferences.music_muted
        return False
    
    def set_music_muted(self, muted: bool):
        """Set music mute state."""
        if self._preferences:
            self._preferences.music_muted = muted
            self._save_preferences(self._preferences)
    
    def toggle_music_muted(self) -> bool:
        """Toggle music mute state. Returns new mute state."""
        if self._preferences:
            self._preferences.music_muted = not self._preferences.music_muted
            self._save_preferences(self._preferences)
            return self._preferences.music_muted
        return False
    
    def get_sfx_volume(self) -> float:
        """Get SFX volume (0.0 to 1.0)."""
        if self._preferences:
            return self._preferences.sfx_volume
        return 0.7
    
    def set_sfx_volume(self, volume: float):
        """Set SFX volume (0.0 to 1.0)."""
        volume = max(0.0, min(1.0, volume))
        if self._preferences:
            self._preferences.sfx_volume = volume
            self._save_preferences(self._preferences)
    
    # Display Methods
    
    def get_text_size(self) -> str:
        """Get text size preference."""
        if self._preferences:
            return self._preferences.text_size
        return "medium"
    
    def set_text_size(self, size: str):
        """Set text size preference."""
        if size not in ["small", "medium", "large"]:
            raise ValueError(f"Invalid text size: {size}. Must be 'small', 'medium', or 'large'")
        
        if self._preferences:
            self._preferences.text_size = size
            self._save_preferences(self._preferences)
    
    def get_animations_enabled(self) -> bool:
        """Check if animations are enabled."""
        if self._preferences:
            return self._preferences.animations_enabled
        return True
    
    def set_animations_enabled(self, enabled: bool):
        """Enable or disable animations."""
        if self._preferences:
            self._preferences.animations_enabled = enabled
            self._save_preferences(self._preferences)
    
    def get_animation_intensity(self) -> str:
        """Get animation intensity level.
        
        Returns:
            Animation intensity: 'full', 'reduced', or 'off'
        """
        if self._preferences:
            return self._preferences.animation_intensity
        return "full"
    
    def set_animation_intensity(self, intensity: str):
        """Set animation intensity level for accessibility.
        
        Args:
            intensity: Animation intensity ('full', 'reduced', or 'off')
        """
        valid_intensities = ["full", "reduced", "off"]
        if intensity not in valid_intensities:
            raise ValueError(f"Invalid animation intensity: {intensity}. Must be one of {valid_intensities}")
        
        if self._preferences:
            self._preferences.animation_intensity = intensity
            self._save_preferences(self._preferences)
    
    # Utility Methods
    
    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """
        Convert hex color to RGB tuple.
        
        Args:
            hex_color: Hex color string (e.g., "#FF4444")
            
        Returns:
            RGB tuple (r, g, b)
        """
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    
    @staticmethod
    def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """
        Convert RGB tuple to hex color string.
        
        Args:
            rgb: RGB tuple (r, g, b)
            
        Returns:
            Hex color string (e.g., "#FF4444")
        """
        return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
    
    def get_all_preferences(self) -> Dict:
        """
        Get all preferences as a dictionary.
        
        Returns:
            Dictionary with all preference values
        """
        if self._preferences:
            return {
                'player_id': self._preferences.player_id,
                'rocket_color': self._preferences.rocket_color,
                'audio_enabled': self._preferences.audio_enabled,
                'music_volume': self._preferences.music_volume,
                'sfx_volume': self._preferences.sfx_volume,
                'text_size': self._preferences.text_size,
                'animations_enabled': self._preferences.animations_enabled,
                'animation_intensity': self._preferences.animation_intensity
            }
        return {}


# Singleton instance for global access
_preferences_manager: Optional[PlayerPreferencesManager] = None


def get_preferences_manager() -> PlayerPreferencesManager:
    """
    Get the global preferences manager instance.
    
    Returns:
        PlayerPreferencesManager singleton
    """
    global _preferences_manager
    if _preferences_manager is None:
        _preferences_manager = PlayerPreferencesManager()
    return _preferences_manager


def set_current_player(player_id: str):
    """
    Set the current player (convenience function).
    
    Args:
        player_id: Player identifier
    """
    get_preferences_manager().set_current_player(player_id)


def get_rocket_color() -> str:
    """
    Get current rocket color (convenience function).
    
    Returns:
        Hex color string
    """
    return get_preferences_manager().get_rocket_color()


def set_rocket_color(hex_color: str):
    """
    Set rocket color (convenience function).
    
    Args:
        hex_color: Hex color string
    """
    get_preferences_manager().set_rocket_color(hex_color)
"""
Accessibility Settings Component (STORY-006-06)

Manages all accessibility feature settings including high contrast mode.
Provides centralized storage and persistence for accessibility preferences.
"""

import json
import os
import logging
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any


logger = logging.getLogger(__name__)


@dataclass
class AccessibilitySettings:
    """
    Combined accessibility feature settings.
    
    Attributes:
        captions_enabled: Whether closed captions are enabled
        caption_font_size: Font size for captions (18-48)
        tts_enabled: Whether text-to-speech is enabled
        tts_speed: Speech speed multiplier (0.5-2.0)
        high_contrast: Whether high contrast mode is enabled
        opendyslexic_font: Whether OpenDyslexic font is enabled
        keyboard_navigation: Whether keyboard navigation is enabled
    """
    captions_enabled: bool = True
    caption_font_size: int = 28
    tts_enabled: bool = True
    tts_speed: float = 1.0
    high_contrast: bool = False
    opendyslexic_font: bool = False
    keyboard_navigation: bool = True
    
    # Validation constants
    MIN_FONT_SIZE = 18
    MAX_FONT_SIZE = 48
    MIN_TTS_SPEED = 0.5
    MAX_TTS_SPEED = 2.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization."""
        return {
            'captions_enabled': self.captions_enabled,
            'caption_font_size': self.caption_font_size,
            'tts_enabled': self.tts_enabled,
            'tts_speed': self.tts_speed,
            'high_contrast': self.high_contrast,
            'opendyslexic_font': self.opendyslexic_font,
            'keyboard_navigation': self.keyboard_navigation,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AccessibilitySettings':
        """Create settings from dictionary."""
        return cls(
            captions_enabled=data.get('captions_enabled', True),
            caption_font_size=cls._validate_font_size(data.get('caption_font_size', 28)),
            tts_enabled=data.get('tts_enabled', True),
            tts_speed=cls._validate_tts_speed(data.get('tts_speed', 1.0)),
            high_contrast=data.get('high_contrast', False),
            opendyslexic_font=data.get('opendyslexic_font', False),
            keyboard_navigation=data.get('keyboard_navigation', True),
        )
    
    @staticmethod
    def _validate_font_size(value: int) -> int:
        """Validate and clamp font size."""
        try:
            size = int(value)
            return max(AccessibilitySettings.MIN_FONT_SIZE, 
                      min(AccessibilitySettings.MAX_FONT_SIZE, size))
        except (ValueError, TypeError):
            return 28
    
    @staticmethod
    def _validate_tts_speed(value: float) -> float:
        """Validate and clamp TTS speed."""
        try:
            speed = float(value)
            return max(AccessibilitySettings.MIN_TTS_SPEED,
                      min(AccessibilitySettings.MAX_TTS_SPEED, speed))
        except (ValueError, TypeError):
            return 1.0
    
    # High contrast mode methods
    
    def toggle_high_contrast(self) -> None:
        """Toggle high contrast mode on/off."""
        self.high_contrast = not self.high_contrast
        logger.info(f"High contrast mode toggled: {self.high_contrast}")
        
    def enable_high_contrast(self) -> None:
        """Enable high contrast mode."""
        self.high_contrast = True
        logger.info("High contrast mode enabled")
        
    def disable_high_contrast(self) -> None:
        """Disable high contrast mode."""
        self.high_contrast = False
        logger.info("High contrast mode disabled")
    
    # Getter methods for individual settings
    
    def get_caption_font_size(self) -> int:
        """Get caption font size."""
        return self.caption_font_size
    
    def get_tts_speed(self) -> float:
        """Get TTS speed."""
        return self.tts_speed
    
    def is_captions_enabled(self) -> bool:
        """Check if captions are enabled."""
        return self.captions_enabled
    
    def is_tts_enabled(self) -> bool:
        """Check if TTS is enabled."""
        return self.tts_enabled
    
    def is_keyboard_navigation_enabled(self) -> bool:
        """Check if keyboard navigation is enabled."""
        return self.keyboard_navigation
    
    def is_opendyslexic_font_enabled(self) -> bool:
        """Check if OpenDyslexic font is enabled."""
        return self.opendyslexic_font
    
    def is_high_contrast_enabled(self) -> bool:
        """Check if high contrast mode is enabled."""
        return self.high_contrast
    
    # Setter methods for individual settings
    
    def set_captions_enabled(self, enabled: bool) -> None:
        """Enable or disable captions."""
        self.captions_enabled = enabled
        logger.info(f"Captions {'enabled' if enabled else 'disabled'}")
    
    def set_caption_font_size(self, size: int) -> None:
        """Set caption font size."""
        self.caption_font_size = self._validate_font_size(size)
        logger.info(f"Caption font size set to {self.caption_font_size}")
    
    def set_tts_enabled(self, enabled: bool) -> None:
        """Enable or disable TTS."""
        self.tts_enabled = enabled
        logger.info(f"TTS {'enabled' if enabled else 'disabled'}")
    
    def set_tts_speed(self, speed: float) -> None:
        """Set TTS speed."""
        self.tts_speed = self._validate_tts_speed(speed)
        logger.info(f"TTS speed set to {self.tts_speed}x")
    
    def set_keyboard_navigation(self, enabled: bool) -> None:
        """Enable or disable keyboard navigation."""
        self.keyboard_navigation = enabled
        logger.info(f"Keyboard navigation {'enabled' if enabled else 'disabled'}")
    
    def set_opendyslexic_font(self, enabled: bool) -> None:
        """Enable or disable OpenDyslexic font."""
        self.opendyslexic_font = enabled
        logger.info(f"OpenDyslexic font {'enabled' if enabled else 'disabled'}")
    
    def set_high_contrast(self, enabled: bool) -> None:
        """Enable or disable high contrast mode."""
        self.high_contrast = enabled
        logger.info(f"High contrast mode {'enabled' if enabled else 'disabled'}")
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self.captions_enabled = True
        self.caption_font_size = 28
        self.tts_enabled = True
        self.tts_speed = 1.0
        self.high_contrast = False
        self.opendyslexic_font = False
        self.keyboard_navigation = True
        logger.info("All accessibility settings reset to defaults")


class AccessibilitySettingsManager:
    """
    Manages accessibility settings persistence and loading.
    
    Features:
    - Save/load settings to/from JSON file
    - Integration with theme manager for high contrast
    - Default fallback if settings file missing
    - Thread-safe operations
    """
    
    # Default file path
    DEFAULT_SETTINGS_FILE = "data/accessibility_settings.json"
    
    def __init__(self, data_dir: Optional[str] = None, 
                 settings_file: Optional[str] = None):
        """
        Initialize settings manager.
        
        Args:
            data_dir: Directory for settings file. Defaults to 'data'.
            settings_file: Path to settings file. If None, uses default.
        """
        # Resolve data directory
        if data_dir is None:
            # Try environment variable first
            data_dir = os.environ.get('WORDQUEST_DATA_DIR')
            if data_dir is None:
                # Default to data directory relative to this file
                base_dir = os.path.dirname(os.path.abspath(__file__))
                data_dir = os.path.join(base_dir, '..', '..', 'data')
        
        self.data_dir = data_dir
        self.settings_file = settings_file or os.path.join(
            self.data_dir, 'accessibility_settings.json'
        )
        
        self.settings = AccessibilitySettings()
        self._theme_manager = None
        
        # Load existing settings
        self.load_settings()
        
        logger.info("AccessibilitySettingsManager initialized")
    
    @property
    def theme_manager(self):
        """Get theme manager (lazily imported to avoid circular imports)."""
        if self._theme_manager is None:
            try:
                from src.ui.theme import get_theme
                self._theme_manager = get_theme()
            except Exception as e:
                logger.warning(f"Could not initialize theme manager: {e}")
                self._theme_manager = None
        return self._theme_manager
    
    def load_settings(self) -> None:
        """Load settings from file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings = AccessibilitySettings.from_dict(data)
                logger.info(f"Loaded accessibility settings from {self.settings_file}")
            else:
                logger.info("No existing accessibility settings found, using defaults")
        except Exception as e:
            logger.error(f"Error loading accessibility settings: {e}")
            self.settings = AccessibilitySettings()
    
    def save_settings(self) -> bool:
        """
        Save current settings to file.
        
        Uses atomic write (temp file + rename) for data integrity.
        
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Ensure data directory exists
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Write to temp file first, then rename for atomicity
            temp_file = self.settings_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings.to_dict(), f, indent=2)
            
            # Atomic rename
            os.replace(temp_file, self.settings_file)
            logger.info(f"Saved accessibility settings to {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving accessibility settings: {e}")
            return False
    
    def get_settings(self) -> AccessibilitySettings:
        """Get current settings."""
        return self.settings
    
    def apply_settings(self) -> None:
        """Apply all settings to the game (e.g., theme, fonts)."""
        # Apply high contrast theme if enabled
        if self.settings.high_contrast:
            if self.theme_manager:
                self.theme_manager.enable_high_contrast()
        else:
            if self.theme_manager:
                self.theme_manager.disable_high_contrast()
        
        logger.info("Applied accessibility settings")
    
    def toggle_high_contrast(self) -> bool:
        """
        Toggle high contrast mode and persist the change.
        
        Returns:
            True if successful, False otherwise
        """
        # Toggle the setting
        self.settings.toggle_high_contrast()
        
        # Apply to theme
        if self.theme_manager:
            success = self.theme_manager.toggle_high_contrast()
            if not success:
                logger.warning("Failed to toggle high contrast in theme manager")
            # Keep setting in sync even if theme toggle fails
            self.settings.high_contrast = self.theme_manager.is_high_contrast()
        
        # Save to file
        saved = self.save_settings()
        
        return saved
    
    def enable_high_contrast(self) -> bool:
        """
        Enable high contrast mode and persist the change.
        
        Returns:
            True if successful, False otherwise
        """
        # Enable the setting
        self.settings.enable_high_contrast()
        
        # Apply to theme
        if self.theme_manager:
            success = self.theme_manager.enable_high_contrast()
            if not success:
                logger.warning("Failed to enable high contrast in theme manager")
            # Keep setting in sync even if theme enable fails
            self.settings.high_contrast = self.theme_manager.is_high_contrast()
        
        # Save to file
        saved = self.save_settings()
        
        return saved
    
    def disable_high_contrast(self) -> bool:
        """
        Disable high contrast mode and persist the change.
        
        Returns:
            True if successful, False otherwise
        """
        # Disable the setting
        self.settings.disable_high_contrast()
        
        # Apply to theme  
        if self.theme_manager:
            success = self.theme_manager.disable_high_contrast()
            if not success:
                logger.warning("Failed to disable high contrast in theme manager")
            # Keep setting in sync even if theme disable fails
            self.settings.high_contrast = self.theme_manager.is_high_contrast()
        
        # Save to file
        saved = self.save_settings()
        
        return saved
    
    def is_high_contrast_enabled(self) -> bool:
        """Check if high contrast mode is enabled."""
        return self.settings.high_contrast
    
    # Convenience methods for other settings
    
    def set_captions_enabled(self, enabled: bool) -> None:
        """Enable or disable captions and save."""
        self.settings.set_captions_enabled(enabled)
        self.save_settings()
    
    def set_caption_font_size(self, size: int) -> None:
        """Set caption font size and save."""
        self.settings.set_caption_font_size(size)
        self.save_settings()
    
    def set_tts_speed(self, speed: float) -> None:
        """Set TTS speed and save."""
        self.settings.set_tts_speed(speed)
        self.save_settings()
    
    def set_keyboard_navigation(self, enabled: bool) -> None:
        """Set keyboard navigation and save."""
        self.settings.set_keyboard_navigation(enabled)
        self.save_settings()
    
    def set_opendyslexic_font(self, enabled: bool) -> None:
        """Set OpenDyslexic font and save."""
        self.settings.set_opendyslexic_font(enabled)
        self.save_settings()
    
    def reset_all_settings(self) -> None:
        """Reset all settings to defaults and save."""
        self.settings.reset_to_defaults()
        self.save_settings()
        # Reset theme to default
        if self.theme_manager:
            self.theme_manager.disable_high_contrast()


# Global settings instance
_settings_instance: Optional[AccessibilitySettingsManager] = None


def get_accessibility_settings() -> AccessibilitySettingsManager:
    """Get or create the global accessibility settings manager."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = AccessibilitySettingsManager()
    return _settings_instance


def reset_accessibility_settings() -> None:
    """Reset the global settings instance."""
    global _settings_instance
    _settings_instance = None
"""
Caption Settings Component (STORY-006-03)

Manages caption appearance and behavior configuration with persistence.
Provides customizable settings for font size, position, colors, and duration.
"""

import json
import os
import logging
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any


logger = logging.getLogger(__name__)


@dataclass
class CaptionSettings:
    """
    Caption appearance and behavior settings.
    
    Attributes:
        enabled: Whether captions are enabled
        font_size: Font size in points (18-48)
        position: Caption position ("bottom" or "middle")
        background_color: Semi-transparent background (RGBA)
        text_color: Caption text color (RGB)
        speaker_color: Speaker name color (RGB)
        duration: Default caption duration in seconds
        high_contrast: Use high contrast color scheme
        show_sfx: Show sound effect descriptions
        intensity_mode: "full", "reduced", or "off"
    """
    enabled: bool = True
    font_size: int = 28
    position: str = "bottom"
    background_color: Tuple[int, int, int, int] = (0, 0, 0, 180)
    text_color: Tuple[int, int, int] = (255, 255, 255)
    speaker_color: Tuple[int, int, int] = (255, 215, 0)  # Gold
    duration: float = 3.0
    high_contrast: bool = False
    show_sfx: bool = True
    intensity_mode: str = "full"
    
    # High contrast defaults
    HIGH_CONTRAST_BG = (255, 255, 255, 230)  # White with slight transparency
    HIGH_CONTRAST_TEXT = (0, 0, 0)  # Black
    HIGH_CONTRAST_SPEAKER = (0, 0, 255)  # Blue
    
    # Color constraints
    MIN_FONT_SIZE = 18
    MAX_FONT_SIZE = 48
    MIN_DURATION = 2.0
    MAX_DURATION = 10.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for serialization."""
        return {
            'enabled': self.enabled,
            'font_size': self.font_size,
            'position': self.position,
            'background_color': list(self.background_color),
            'text_color': list(self.text_color),
            'speaker_color': list(self.speaker_color),
            'duration': self.duration,
            'high_contrast': self.high_contrast,
            'show_sfx': self.show_sfx,
            'intensity_mode': self.intensity_mode
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CaptionSettings':
        """Create settings from dictionary."""
        return cls(
            enabled=data.get('enabled', True),
            font_size=cls._validate_font_size(data.get('font_size', 28)),
            position=data.get('position', 'bottom'),
            background_color=cls._validate_color(data.get('background_color'), (0, 0, 0, 180), 4),
            text_color=cls._validate_color(data.get('text_color'), (255, 255, 255), 3),
            speaker_color=cls._validate_color(data.get('speaker_color'), (255, 215, 0), 3),
            duration=cls._validate_duration(data.get('duration', 3.0)),
            high_contrast=data.get('high_contrast', False),
            show_sfx=data.get('show_sfx', True),
            intensity_mode=data.get('intensity_mode', 'full')
        )
    
    @staticmethod
    def _validate_font_size(value: int) -> int:
        """Validate and clamp font size."""
        try:
            size = int(value)
            return max(CaptionSettings.MIN_FONT_SIZE, 
                      min(CaptionSettings.MAX_FONT_SIZE, size))
        except (ValueError, TypeError):
            return 28
    
    @staticmethod
    def _validate_color(value, default: tuple, channels: int) -> Tuple[int, ...]:
        """Validate and convert color tuple."""
        if value is None:
            return default
        
        try:
            if isinstance(value, list):
                color = tuple(int(x) for x in value[:channels])
            elif isinstance(value, tuple):
                color = tuple(int(x) for x in value[:channels])
            else:
                return default
            
            # Ensure correct number of channels
            while len(color) < channels:
                color = color + (255,)
            
            return color[:channels]
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def _validate_duration(value: float) -> float:
        """Validate and clamp duration."""
        try:
            duration = float(value)
            return max(CaptionSettings.MIN_DURATION,
                      min(CaptionSettings.MAX_DURATION, duration))
        except (ValueError, TypeError):
            return 3.0
    
    def apply_high_contrast(self) -> None:
        """Apply high contrast color scheme."""
        self.high_contrast = True
        self.background_color = CaptionSettings.HIGH_CONTRAST_BG
        self.text_color = CaptionSettings.HIGH_CONTRAST_TEXT
        self.speaker_color = CaptionSettings.HIGH_CONTRAST_SPEAKER
        
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self.enabled = True
        self.font_size = 28
        self.position = "bottom"
        self.background_color = (0, 0, 0, 180)
        self.text_color = (255, 255, 255)
        self.speaker_color = (255, 215, 0)
        self.duration = 3.0
        self.high_contrast = False
        self.show_sfx = True
        self.intensity_mode = "full"


class CaptionSettingsManager:
    """
    Manages caption settings persistence and loading.
    
    Features:
    - Save/load settings to/from JSON file
    - Integration with player preferences
    - Default fallback if settings file missing
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize settings manager.
        
        Args:
            data_dir: Directory for settings file. Defaults to 'data'.
        """
        # Resolve data directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_data_dir = os.path.join(base_dir, '..', '..', 'data')
        self.data_dir = data_dir or os.environ.get('WORDQUEST_DATA_DIR', default_data_dir)
        self.settings_file = os.path.join(self.data_dir, 'caption_settings.json')
        
        self.settings = CaptionSettings()
        
        # Load existing settings
        self.load_settings()
        
        logger.info("CaptionSettingsManager initialized")
    
    def load_settings(self) -> None:
        """Load settings from file."""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings = CaptionSettings.from_dict(data)
                logger.info(f"Loaded caption settings from {self.settings_file}")
            else:
                logger.info("No existing caption settings found, using defaults")
        except Exception as e:
            logger.error(f"Error loading caption settings: {e}")
            self.settings = CaptionSettings()
    
    def save_settings(self) -> bool:
        """
        Save current settings to file.
        
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
            logger.info(f"Saved caption settings to {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving caption settings: {e}")
            return False
    
    def get_settings(self) -> CaptionSettings:
        """Get current settings."""
        return self.settings
    
    def update_settings(self, **kwargs) -> None:
        """
        Update settings with provided values.
        
        Args:
            **kwargs: Settings to update (font_size, position, etc.)
        """
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
                logger.debug(f"Updated caption setting: {key} = {value}")
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable captions."""
        self.settings.enabled = enabled
        self.save_settings()
    
    def set_font_size(self, size: int) -> None:
        """Set caption font size."""
        self.settings.font_size = CaptionSettings._validate_font_size(size)
        self.save_settings()
    
    def set_position(self, position: str) -> None:
        """Set caption position."""
        if position in ("bottom", "middle"):
            self.settings.position = position
            self.save_settings()
    
    def set_duration(self, duration: float) -> None:
        """Set default caption duration."""
        self.settings.duration = CaptionSettings._validate_duration(duration)
        self.save_settings()
    
    def set_high_contrast(self, enabled: bool) -> None:
        """Toggle high contrast mode."""
        if enabled:
            self.settings.apply_high_contrast()
        else:
            self.settings.reset_to_defaults()
        self.save_settings()
    
    def set_sfx_display(self, show: bool) -> None:
        """Toggle sound effect descriptions."""
        self.settings.show_sfx = show
        self.save_settings()
    
    def set_intensity_mode(self, mode: str) -> None:
        """Set caption intensity mode."""
        if mode in ("full", "reduced", "off"):
            self.settings.intensity_mode = mode
            self.save_settings()
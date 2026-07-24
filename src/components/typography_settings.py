"""
Typography settings for Word Quest.

Provides configuration for font choices, sizes, and spacing with persistence
across game sessions. Includes support for OpenDyslexic font accessibility.

STORY-006-05: OpenDyslexic Font Implementation
"""

import json
import os
from dataclasses import dataclass, field
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class TypographySettings:
    """
    Typography configuration for the game.
    
    Attributes:
        font_family: Current font family ("default" or "opendyslexic")
        font_size_base: Base font size in pixels
        font_size_large: Large font size for headers
        font_size_small: Small font size for captions/helper text
        letter_spacing: Letter spacing in pixels
        word_spacing: Word spacing in pixels
        line_height: Line height as multiplier (e.g., 1.5 = 150%)
    """
    
    # Font family constants
    FONT_DEFAULT = "default"
    FONT_OD = "opendyslexic"  # OpenDyslexic alias
    
    # Default values
    DEFAULT_FONT_FAMILY = "default"
    DEFAULT_FONT_SIZE_BASE = 24
    DEFAULT_FONT_SIZE_LARGE = 48
    DEFAULT_FONT_SIZE_SMALL = 18
    DEFAULT_LETTER_SPACING = 2
    DEFAULT_WORD_SPACING = 4
    DEFAULT_LINE_HEIGHT = 1.5
    
    font_family: str = DEFAULT_FONT_FAMILY
    font_size_base: int = DEFAULT_FONT_SIZE_BASE
    font_size_large: int = DEFAULT_FONT_SIZE_LARGE
    font_size_small: int = DEFAULT_FONT_SIZE_SMALL
    letter_spacing: int = DEFAULT_LETTER_SPACING
    word_spacing: int = DEFAULT_WORD_SPACING
    line_height: float = DEFAULT_LINE_HEIGHT
    
    # Config file path
    CONFIG_PATH = "data/typography_config.json"
    
    def to_dict(self) -> dict:
        """
        Serialize settings to dictionary.
        
        Returns:
            Dictionary representation of settings
        """
        return {
            'font_family': self.font_family,
            'font_size_base': self.font_size_base,
            'font_size_large': self.font_size_large,
            'font_size_small': self.font_size_small,
            'letter_spacing': self.letter_spacing,
            'word_spacing': self.word_spacing,
            'line_height': self.line_height
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TypographySettings':
        """
        Create settings from dictionary.
        
        Args:
            data: Dictionary containing settings
            
        Returns:
            TypographySettings instance
        """
        return cls(
            font_family=data.get('font_family', cls.DEFAULT_FONT_FAMILY),
            font_size_base=data.get('font_size_base', cls.DEFAULT_FONT_SIZE_BASE),
            font_size_large=data.get('font_size_large', cls.DEFAULT_FONT_SIZE_LARGE),
            font_size_small=data.get('font_size_small', cls.DEFAULT_FONT_SIZE_SMALL),
            letter_spacing=data.get('letter_spacing', cls.DEFAULT_LETTER_SPACING),
            word_spacing=data.get('word_spacing', cls.DEFAULT_WORD_SPACING),
            line_height=data.get('line_height', cls.DEFAULT_LINE_HEIGHT)
        )
    
    def save(self) -> bool:
        """
        Save settings to configuration file.
        
        Uses atomic write (temp file + rename) to prevent corruption.
        
        Returns:
            True if save successful, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
            
            # Write to temp file first (atomic write)
            temp_path = self.CONFIG_PATH + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
            
            # Rename temp file to actual config file
            os.replace(temp_path, self.CONFIG_PATH)
            
            logger.info(f"Typography settings saved to {self.CONFIG_PATH}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save typography settings: {e}")
            return False
    
    @classmethod
    def load(cls) -> 'TypographySettings':
        """
        Load settings from configuration file.
        
        Returns:
            TypographySettings instance with loaded or default values
        """
        config_path = cls.CONFIG_PATH
        
        # Check if config file exists
        if not os.path.exists(config_path):
            logger.info(f"Typography config not found at {config_path}, using defaults")
            return cls()
        
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                
            # Handle both nested and flat JSON structures
            if 'typography' in data:
                data = data['typography']
            
            settings = cls.from_dict(data)
            logger.info(f"Typography settings loaded from {config_path}")
            return settings
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in typography config: {e}")
            return cls()
        except Exception as e:
            logger.error(f"Failed to load typography settings: {e}")
            return cls()
    
    def set_font_family(self, family: str) -> None:
        """
        Set font family.
        
        Args:
            family: Font family name ("default" or "opendyslexic")
        """
        valid_families = [self.FONT_DEFAULT, self.FONT_OD]
        if family in valid_families:
            self.font_family = family
            logger.info(f"Typography font family set to: {family}")
        else:
            logger.warning(f"Invalid font family '{family}', using default")
            self.font_family = self.FONT_DEFAULT
    
    def is_opendyslexic(self) -> bool:
        """
        Check if OpenDyslexic font is currently selected.
        
        Returns:
            True if OpenDyslexic is selected, False otherwise
        """
        return self.font_family == self.FONT_OD
    
    def validate(self) -> bool:
        """
        Validate settings values.
        
        Returns:
            True if all values are valid, False otherwise
        """
        # Validate font family
        if self.font_family not in [self.FONT_DEFAULT, self.FONT_OD]:
            logger.warning(f"Invalid font family: {self.font_family}")
            return False
        
        # Validate font sizes (positive integers)
        if self.font_size_base <= 0 or self.font_size_base > 100:
            logger.warning(f"Invalid base font size: {self.font_size_base}")
            return False
            
        if self.font_size_large <= 0 or self.font_size_large > 200:
            logger.warning(f"Invalid large font size: {self.font_size_large}")
            return False
            
        if self.font_size_small <= 0 or self.font_size_small > 100:
            logger.warning(f"Invalid small font size: {self.font_size_small}")
            return False
        
        # Validate spacing (non-negative integers)
        if self.letter_spacing < 0 or self.letter_spacing > 20:
            logger.warning(f"Invalid letter spacing: {self.letter_spacing}")
            return False
            
        if self.word_spacing < 0 or self.word_spacing > 40:
            logger.warning(f"Invalid word spacing: {self.word_spacing}")
            return False
        
        # Validate line height (reasonable range)
        if self.line_height < 1.0 or self.line_height > 3.0:
            logger.warning(f"Invalid line height: {self.line_height}")
            return False
        
        return True
    
    def apply_defaults_if_invalid(self) -> None:
        """
        Replace invalid values with defaults.
        """
        if self.font_family not in [self.FONT_DEFAULT, self.FONT_OD]:
            self.font_family = self.FONT_DEFAULT
            
        if not (0 < self.font_size_base <= 100):
            self.font_size_base = self.DEFAULT_FONT_SIZE_BASE
            
        if not (0 < self.font_size_large <= 200):
            self.font_size_large = self.DEFAULT_FONT_SIZE_LARGE
            
        if not (0 < self.font_size_small <= 100):
            self.font_size_small = self.DEFAULT_FONT_SIZE_SMALL
            
        if not (0 <= self.letter_spacing <= 20):
            self.letter_spacing = self.DEFAULT_LETTER_SPACING
            
        if not (0 <= self.word_spacing <= 40):
            self.word_spacing = self.DEFAULT_WORD_SPACING
            
        if not (1.0 <= self.line_height <= 3.0):
            self.line_height = self.DEFAULT_LINE_HEIGHT


# Global settings instance
_typography_settings: Optional[TypographySettings] = None


def get_typography_settings() -> TypographySettings:
    """
    Get or create global typography settings instance.
    
    Returns:
        Global TypographySettings instance
    """
    global _typography_settings
    if _typography_settings is None:
        _typography_settings = TypographySettings.load()
        # Validate and apply defaults if needed
        _typography_settings.apply_defaults_if_invalid()
    return _typography_settings


def reset_typography_settings() -> None:
    """Reset the global typography settings instance."""
    global _typography_settings
    _typography_settings = None
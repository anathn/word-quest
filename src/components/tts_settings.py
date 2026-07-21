"""
TTS Settings Component

Provides configuration management for Text-to-Speech settings,
including persistence to JSON files.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import json
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class TTSSettings:
    """
    TTS configuration settings.
    
    Attributes:
        enabled: Whether TTS is enabled
        speed: Speech speed multiplier (0.5 to 2.0)
        volume: Speech volume (0.0 to 1.0)
        voice_id: Identifier for selected voice
    """
    enabled: bool = True
    speed: float = 1.0  # Default: normal speed
    volume: float = 1.0  # Default: full volume
    voice_id: Optional[str] = None
    
    # Speed presets
    SPEED_SLOW = 0.5
    SPEED_NORMAL = 1.0
    SPEED_FAST = 1.5
    SPEED_VERY_FAST = 2.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary"""
        return {
            'enabled': self.enabled,
            'speed': self.speed,
            'volume': self.volume,
            'voice_id': self.voice_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TTSSettings':
        """Create settings from dictionary"""
        return cls(
            enabled=data.get('enabled', True),
            speed=data.get('speed', 1.0),
            volume=data.get('volume', 1.0),
            voice_id=data.get('voice_id')
        )
    
    def validate(self) -> bool:
        """
        Validate settings are in acceptable ranges.
        
        Returns:
            True if all settings are valid
        """
        return (0.5 <= self.speed <= 2.0 and 
                0.0 <= self.volume <= 1.0)
    
    def validate_speed(self, speed: float) -> bool:
        """
        Validate a speed value.
        
        Args:
            speed: Speed value to validate
            
        Returns:
            True if speed is valid
        """
        return 0.5 <= speed <= 2.0
    
    def validate_volume(self, volume: float) -> bool:
        """
        Validate a volume value.
        
        Args:
            volume: Volume value to validate
            
        Returns:
            True if volume is valid
        """
        return 0.0 <= volume <= 1.0
    
    def clamp_speed(self, speed: float) -> float:
        """
        Clamp speed to valid range.
        
        Args:
            speed: Speed value to clamp
            
        Returns:
            Clamped speed value
        """
        return max(0.5, min(2.0, speed))
    
    def clamp_volume(self, volume: float) -> float:
        """
        Clamp volume to valid range.
        
        Args:
            volume: Volume value to clamp
            
        Returns:
            Clamped volume value
        """
        return max(0.0, min(1.0, volume))
    
    def get_speed_preset_name(self) -> str:
        """
        Get the name of the current speed preset.
        
        Returns:
            Preset name ('Slow', 'Normal', 'Fast', 'Very Fast', or 'Custom')
        """
        if abs(self.speed - self.SPEED_SLOW) < 0.01:
            return 'Slow'
        elif abs(self.speed - self.SPEED_NORMAL) < 0.01:
            return 'Normal'
        elif abs(self.speed - self.SPEED_FAST) < 0.01:
            return 'Fast'
        elif abs(self.speed - self.SPEED_VERY_FAST) < 0.01:
            return 'Very Fast'
        else:
            return 'Custom'
    
    def apply_preset(self, preset: str) -> None:
        """
        Apply a speed preset.
        
        Args:
            preset: Preset name ('slow', 'normal', 'fast', 'very_fast')
        """
        preset_lower = preset.lower()
        if preset_lower in ('slow', 'slowest'):
            self.speed = self.SPEED_SLOW
        elif preset_lower in ('normal', 'default'):
            self.speed = self.SPEED_NORMAL
        elif preset_lower in ('fast', 'faster'):
            self.speed = self.SPEED_FAST
        elif preset_lower in ('very_fast', 'veryfast', 'fastest'):
            self.speed = self.SPEED_VERY_FAST
        else:
            logger.warning(f"Unknown speed preset: {preset}")


class TTSConfigManager:
    """
    Persistence layer for TTS settings.
    
    Loads and saves TTS settings to/from JSON configuration files.
    """
    
    DEFAULT_CONFIG_PATH = "data/tts_config.json"
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize TTS Config Manager.
        
        Args:
            config_path: Path to config file (defaults to data/tts_config.json)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.settings = TTSSettings()
        
        # Ensure data directory exists
        self._ensure_data_dir()
        
        # Load settings on initialization
        self.load()
        
        logger.info(f"TTS Config Manager initialized (config: {self.config_path})")
    
    def _ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist"""
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            logger.debug(f"Created data directory: {config_dir}")
    
    def load(self) -> None:
        """
        Load settings from file.
        
        If file doesn't exist or is invalid, uses default settings.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    tts_data = data.get('tts', {})
                    self.settings = TTSSettings.from_dict(tts_data)
                    logger.info(f"TTS settings loaded from {self.config_path}")
            else:
                logger.info(f"No existing TTS config found, using defaults: {self.config_path}")
        except FileNotFoundError:
            logger.info(f"Config file not found, using defaults: {self.config_path}")
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in config file, using defaults: {e}")
            self.settings = TTSSettings()
        except Exception as e:
            logger.error(f"Error loading TTS settings: {e}")
            self.settings = TTSSettings()
    
    def save(self) -> None:
        """
        Save settings to file.
        
        Creates the file if it doesn't exist, overwrites if it does.
        """
        try:
            # Ensure directory exists
            self._ensure_data_dir()
            
            # Read existing data or create new
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {}
            
            # Update with current settings
            data['tts'] = self.settings.to_dict()
            
            # Write atomically using temp file
            temp_path = self.config_path + '.tmp'
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Rename temp file to final path
            os.replace(temp_path, self.config_path)
            
            logger.info(f"TTS settings saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving TTS settings: {e}")
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable TTS.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.settings.enabled = enabled
        self.save()
    
    def set_speed(self, speed: float) -> None:
        """
        Set speech speed.
        
        Args:
            speed: Speed multiplier (0.5 to 2.0)
        """
        self.settings.speed = self.settings.clamp_speed(speed)
        self.save()
    
    def set_volume(self, volume: float) -> None:
        """
        Set speech volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.settings.volume = self.settings.clamp_volume(volume)
        self.save()
    
    def set_voice(self, voice_id: str) -> None:
        """
        Set the voice identifier.
        
        Args:
            voice_id: Voice identifier
        """
        self.settings.voice_id = voice_id
        self.save()
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults"""
        self.settings = TTSSettings()
        self.save()
        logger.info("TTS settings reset to defaults")


# Convenience function to create a config manager
def create_tts_config() -> TTSConfigManager:
    """
    Create a TTS config manager with default settings.
    
    Returns:
        Configured TTSConfigManager instance
    """
    return TTSConfigManager()
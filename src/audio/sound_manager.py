"""
Sound Manager Module

Centralized sound effect management and playback system.
Handles loading, playing, volume control, and caching of sound effects.
"""

import pygame
from typing import Optional, Dict, List, Callable
from enum import Enum
import threading
import time
import io

from .sfx_config import (
    SoundEvent, 
    SFXConfig, 
    SFX_LIBRARY, 
    get_sound_config, 
    DEFAULT_SFX_VOLUME,
    MIN_VOLUME,
    MAX_VOLUME,
    SOUND_SAMPLE_RATE
)
from .sfx_generator import SFXGenerator


class SoundManager:
    """
    Central sound effect management system.
    
    Features:
    - Pre-cached sound effects for low-latency playback
    - Global volume control with persistence support
    - Mute/unmute functionality
    - Automatic pygame mixer initialization
    - Graceful fallback when audio unavailable
    - Multiple simultaneous sound playback
    """
    
    def __init__(self):
        """Initialize the sound manager."""
        self._sfx_volume = DEFAULT_SFX_VOLUME
        self._is_muted = False
        self._initialized = False
        self._sounds: Dict[SoundEvent, pygame.mixer.Sound] = {}
        self._sfx_generator = SFXGenerator(SOUND_SAMPLE_RATE)
        self._mixer_initialized = False
        self._audio_available = True
        self._last_play_time: Dict[SoundEvent, float] = {}
        self._min_delay = 0.01  # 10ms minimum between same sound
        
        # Load sounds on initialization
        self._initialization_error: Optional[str] = None
    
    def initialize(self) -> bool:
        """
        Initialize pygame mixer and pre-load all sound effects.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
        
        # Initialize pygame mixer
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=SOUND_SAMPLE_RATE,
                    size=-16,  # 16-bit
                    channels=2,  # Stereo support
                    buffer=512   # Small buffer for low latency
                )
                self._mixer_initialized = True
        except Exception as e:
            self._initialization_error = str(e)
            self._audio_available = False
            print(f"Warning: Could not initialize pygame mixer: {e}")
            print("Sound effects will be unavailable.")
            self._initialized = True
            return False
        
        # Pre-generate all sound effects
        try:
            self._preload_sounds()
            self._initialized = True
            return True
        except Exception as e:
            self._initialization_error = str(e)
            print(f"Warning: Error pre-loading sounds: {e}")
            self._initialized = True
            return False
    
    def _preload_sounds(self):
        """Pre-generate and cache all sound effects."""
        for event in SoundEvent:
            try:
                self._generate_and_cache_sound(event)
            except Exception as e:
                print(f"Warning: Could not generate sound for {event}: {e}")
    
    def _generate_and_cache_sound(self, event: SoundEvent):
        """
        Generate a sound effect and cache it.
        
        Args:
            event: SoundEvent to generate
        """
        config = get_sound_config(event)
        sound_bytes = self._generate_sfx_bytes(config)
        
        # Create pygame Sound object from bytes
        sound = pygame.mixer.Sound(buffer=sound_bytes)
        sound.set_volume(config.volume * self._sfx_volume)
        
        self._sounds[event] = sound
    
    def _generate_sfx_bytes(self, config: SFXConfig) -> bytes:
        """
        Generate raw sound bytes based on configuration.
        
        Args:
            config: SFXConfig containing sound parameters
            
        Returns:
            WAV format audio data as bytes
        """
        if len(config.frequencies) == 1 and len(config.durations) == 1:
            # Simple tone
            return self._sfx_generator.generate_tone(
                frequency=config.frequencies[0],
                duration=config.durations[0],
                amplitude=config.volume
            )
        else:
            # Chime or fanfare
            return self._sfx_generator.generate_chime(
                frequencies=config.frequencies,
                durations=config.durations,
                amplitude=config.volume,
                overlap=0.02
            )
    
    def play(self, event: SoundEvent, volume_override: Optional[float] = None) -> bool:
        """
        Play a sound effect.
        
        Args:
            event: SoundEvent to play
            volume_override: Optional volume override (0.0 to 1.0)
            
        Returns:
            True if sound played successfully, False otherwise
        """
        if not self._initialized:
            # Try to initialize on first play
            if not self.initialize():
                return False
        
        if not self._audio_available:
            return False
        
        if self._is_muted:
            return True  # Silently succeed when muted
        
        if event not in self._sounds:
            print(f"Warning: Sound not cached for event: {event}")
            return False
        
        # Check minimum delay to prevent sound spam
        current_time = time.time()
        if event in self._last_play_time:
            if current_time - self._last_play_time[event] < self._min_delay:
                return False  # Too soon, skip
        
        self._last_play_time[event] = current_time
        
        try:
            sound = self._sounds[event]
            
            # Apply volume
            volume = volume_override if volume_override is not None else self._sfx_volume
            if self._is_muted:
                volume = 0.0
            
            sound.set_volume(volume)
            sound.play(maxtime=0)  # 0 = play until finished
            
            return True
        except Exception as e:
            print(f"Error playing sound {event}: {e}")
            return False
    
    def play_multiple(
        self, 
        events: List[SoundEvent],
        delay_between: float = 0.1
    ) -> bool:
        """
        Play multiple sounds in sequence.
        
        Args:
            events: List of SoundEvents to play in order
            delay_between: Delay between sounds in seconds
            
        Returns:
            True if all sounds scheduled successfully
        """
        success = True
        for event in events:
            if not self.play(event):
                success = False
            if delay_between > 0:
                time.sleep(delay_between)
        
        return success
    
    def set_volume(self, volume: float):
        """
        Set the global SFX volume.
        
        Args:
            volume: Volume level from 0.0 (mute) to 1.0 (max)
        """
        volume = max(MIN_VOLUME, min(MAX_VOLUME, volume))
        self._sfx_volume = volume
        
        # Update volume on all cached sounds
        for event, sound in self._sounds.items():
            config = get_sound_config(event)
            sound.set_volume(config.volume * volume)
    
    def get_volume(self) -> float:
        """
        Get the current SFX volume.
        
        Returns:
            Volume level from 0.0 to 1.0
        """
        return self._sfx_volume
    
    def mute(self):
        """Mute all sound effects."""
        self._is_muted = True
    
    def unmute(self):
        """Unmute sound effects."""
        self._is_muted = False
    
    def toggle_mute(self) -> bool:
        """
        Toggle mute state.
        
        Returns:
            New mute state (True = muted, False = unmuted)
        """
        self._is_muted = not self._is_muted
        return self._is_muted
    
    def is_muted(self) -> bool:
        """
        Check if sound effects are muted.
        
        Returns:
            True if muted, False otherwise
        """
        return self._is_muted
    
    def is_initialized(self) -> bool:
        """
        Check if sound manager is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self._initialized
    
    def is_audio_available(self) -> bool:
        """
        Check if audio system is available.
        
        Returns:
            True if audio works, False if disabled/unavailable
        """
        return self._audio_available
    
    def get_initialization_error(self) -> Optional[str]:
        """
        Get initialization error message if any.
        
        Returns:
            Error message string or None
        """
        return self._initialization_error
    
    def stop_all(self):
        """Stop all playing sounds."""
        if self._mixer_initialized and pygame.mixer.get_init():
            pygame.mixer.stop()
    
    def reload_sounds(self):
        """
        Reload all sound effects from config.
        
        Useful for testing or dynamic config changes.
        """
        self._sounds.clear()
        self._preload_sounds()
    
    def clear_cache(self):
        """Clear cached sounds (will regenerate on next play)."""
        self._sounds.clear()
    
    def get_sound_info(self, event: SoundEvent) -> Optional[Dict]:
        """
        Get information about a sound effect.
        
        Args:
            event: SoundEvent to get info for
            
        Returns:
            Dict with sound information or None if not found
        """
        if event not in SFX_LIBRARY:
            return None
        
        config = get_sound_config(event)
        return {
            'event': event.value,
            'frequencies': config.frequencies,
            'total_duration': config.duration_total,
            'volume': config.volume,
            'is_loaded': event in self._sounds
        }


# Global singleton instance
_sound_manager: Optional[SoundManager] = None
_sound_manager_lock = threading.Lock()


def get_sound_manager() -> SoundManager:
    """
    Get or create the global sound manager instance.
    
    Returns:
        SoundManager singleton
    """
    global _sound_manager
    if _sound_manager is None:
        with _sound_manager_lock:
            if _sound_manager is None:
                _sound_manager = SoundManager()
    return _sound_manager


def reset_sound_manager():
    """Reset the global sound manager (useful for testing)."""
    global _sound_manager
    with _sound_manager_lock:
        _sound_manager = None


# Convenience functions for common sounds

def play_correct_answer(volume: Optional[float] = None) -> bool:
    """Play correct answer chime."""
    return get_sound_manager().play(SoundEvent.CORRECT_ANSWER, volume)

def play_incorrect_answer(volume: Optional[float] = None) -> bool:
    """Play incorrect answer tone."""
    return get_sound_manager().play(SoundEvent.INCORRECT_ANSWER, volume)

def play_streak_3(volume: Optional[float] = None) -> bool:
    """Play 3-word streak celebration."""
    return get_sound_manager().play(SoundEvent.STREAK_3, volume)

def play_streak_5(volume: Optional[float] = None) -> bool:
    """Play 5-word streak fanfare."""
    return get_sound_manager().play(SoundEvent.STREAK_5, volume)

def play_planet_complete(volume: Optional[float] = None) -> bool:
    """Play planet completion victory fanfare."""
    return get_sound_manager().play(SoundEvent.PLANET_COMPLETE, volume)

def play_button_click(volume: Optional[float] = None) -> bool:
    """Play button click sound."""
    return get_sound_manager().play(SoundEvent.BUTTON_CLICK, volume)

def play_rocket_bonus(volume: Optional[float] = None) -> bool:
    """Play rocket bonus sound."""
    return get_sound_manager().play(SoundEvent.ROCKET_BONUS, volume)
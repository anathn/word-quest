"""
SFX Configuration Module

Defines sound effect configurations for all game events.
Contains frequency mappings, durations, and volume levels for procedural sound generation.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict


class SoundEvent(Enum):
    """Enum of all sound events in the game."""
    CORRECT_ANSWER = "correct_answer"
    INCORRECT_ANSWER = "incorrect_answer"
    STREAK_3 = "streak_3"
    STREAK_5 = "streak_5"
    PLANET_COMPLETE = "planet_complete"
    BUTTON_CLICK = "button_click"
    PLANET_APPROACH = "planet_approach"
    ROCKET_BONUS = "rocket_bonus"


@dataclass
class SFXConfig:
    """Configuration for a single sound effect."""
    event: SoundEvent
    frequencies: List[float]  # Frequencies in Hz
    durations: List[float]    # Duration per frequency in seconds
    volume: float             # Volume 0.0 to 1.0
    duration_total: float     # Total duration for reference
    
    def __post_init__(self):
        """Calculate total duration if not provided."""
        if self.duration_total is None:
            self.duration_total = sum(self.durations)


# Sound effect configurations
# Based on musical principles:
# - Major chords for positive events (C-E-G = 523.25Hz, 659.25Hz, 783.99Hz)
# - Descending whole steps for gentle corrections
# - Layered sounds for milestones

SFX_LIBRARY: Dict[SoundEvent, SFXConfig] = {
    SoundEvent.CORRECT_ANSWER: SFXConfig(
        event=SoundEvent.CORRECT_ANSWER,
        frequencies=[523.25, 659.25, 783.99],  # C5, E5, G5 (major chord)
        durations=[0.1, 0.1, 0.1],
        volume=0.5,
        duration_total=0.3
    ),
    
    SoundEvent.INCORRECT_ANSWER: SFXConfig(
        event=SoundEvent.INCORRECT_ANSWER,
        frequencies=[392.00, 349.23],  # G4, F4 (descending whole step)
        durations=[0.1, 0.1],
        volume=0.3,
        duration_total=0.2
    ),
    
    SoundEvent.STREAK_3: SFXConfig(
        event=SoundEvent.STREAK_3,
        frequencies=[523.25, 659.25, 783.99, 880.00],  # C-E-G-A ascending
        durations=[0.08, 0.08, 0.08, 0.16],
        volume=0.6,
        duration_total=0.4
    ),
    
    SoundEvent.STREAK_5: SFXConfig(
        event=SoundEvent.STREAK_5,
        frequencies=[523.25, 659.25, 783.99, 1046.50],  # C-E-G-C (octave)
        durations=[0.1, 0.1, 0.1, 0.2],
        volume=0.7,
        duration_total=0.5
    ),
    
    SoundEvent.PLANET_COMPLETE: SFXConfig(
        event=SoundEvent.PLANET_COMPLETE,
        frequencies=[523.25, 659.25, 783.99, 1046.50, 1318.51],  # C-E-G-C-E arpeggio
        durations=[0.12, 0.12, 0.12, 0.12, 0.12],
        volume=0.8,
        duration_total=0.6
    ),
    
    SoundEvent.BUTTON_CLICK: SFXConfig(
        event=SoundEvent.BUTTON_CLICK,
        frequencies=[440.00],  # A4 simple tone
        durations=[0.05],
        volume=0.3,
        duration_total=0.05
    ),
    
    SoundEvent.PLANET_APPROACH: SFXConfig(
        event=SoundEvent.PLANET_APPROACH,
        frequencies=[261.63, 293.66, 329.63],  # C4-D4-E4 ascending
        durations=[0.15, 0.15, 0.2],
        volume=0.4,
        duration_total=0.5
    ),
    
    SoundEvent.ROCKET_BONUS: SFXConfig(
        event=SoundEvent.ROCKET_BONUS,
        frequencies=[392.00, 440.00, 493.88, 523.25],  # G4-A4-B4-C5 rising
        durations=[0.08, 0.08, 0.08, 0.16],
        volume=0.6,
        duration_total=0.4
    ),
}


def get_sound_config(event: SoundEvent) -> SFXConfig:
    """
    Get configuration for a sound event.
    
    Args:
        event: SoundEvent to get config for
        
    Returns:
        SFXConfig for the event
        
    Raises:
        ValueError: If event not found
    """
    config = SFX_LIBRARY.get(event)
    if config is None:
        raise ValueError(f"Unknown sound event: {event}")
    return config


def get_all_events() -> List[SoundEvent]:
    """Get list of all defined sound events."""
    return list(SFX_LIBRARY.keys())


# Default global settings
DEFAULT_SFX_VOLUME = 0.5  # 50% volume
MIN_VOLUME = 0.0
MAX_VOLUME = 1.0
SOUND_SAMPLE_RATE = 44100  # Hz
SOUND_CHANNELS = 1  # Mono to save memory
"""
Audio Package

Sound effect management and generation for Word Quest.

Modules:
- sound_manager: Centralized SFX playback and control
- sfx_generator: Procedural sound generation
- sfx_config: Sound configuration and mappings
"""

from .sound_manager import (
    SoundManager,
    get_sound_manager,
    reset_sound_manager,
    play_correct_answer,
    play_incorrect_answer,
    play_streak_3,
    play_streak_5,
    play_planet_complete,
    play_button_click,
    play_rocket_bonus,
)

from .sfx_config import (
    SoundEvent,
    SFXConfig,
    SFX_LIBRARY,
    get_sound_config,
    get_all_events,
    DEFAULT_SFX_VOLUME,
    MIN_VOLUME,
    MAX_VOLUME,
    SOUND_SAMPLE_RATE,
)

from .sfx_generator import SFXGenerator


__all__ = [
    # Sound Manager
    'SoundManager',
    'get_sound_manager',
    'reset_sound_manager',
    'play_correct_answer',
    'play_incorrect_answer',
    'play_streak_3',
    'play_streak_5',
    'play_planet_complete',
    'play_button_click',
    'play_rocket_bonus',
    
    # SFX Configuration
    'SoundEvent',
    'SFXConfig',
    'SFX_LIBRARY',
    'get_sound_config',
    'get_all_events',
    'DEFAULT_SFX_VOLUME',
    'MIN_VOLUME',
    'MAX_VOLUME',
    'SOUND_SAMPLE_RATE',
    
    # SFX Generation
    'SFXGenerator',
]
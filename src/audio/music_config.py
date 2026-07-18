"""
Music Configuration Module

Configuration for background music tracks, volumes, and playback settings.
Defines music states, track configurations, and procedural music generation parameters.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, List


class MusicState(Enum):
    """
    Enumeration of game states with corresponding music tracks.
    
    Each state represents a different game screen or activity
    that requires distinct ambient music.
    """
    MAIN_MENU = "main_menu"
    GAMEPLAY = "gameplay"
    CELEBRATION = "celebration"
    PARENT_DASHBOARD = "parent_dashboard"
    PAUSED = "paused"
    TRANSITION = "transition"


@dataclass
class MusicTrack:
    """
    Container for music track configuration.
    
    Attributes:
        name: Human-readable track name
        state: Associated MusicState
        file_path: Path to audio file (if using external files)
        default_volume: Default playback volume (0.0-1.0)
        fade_ms: Fade transition duration in milliseconds
        should_loop: Whether track should loop
        duration: Estimated track duration in seconds
        bpm: Beats per minute for procedural generation
        key: Musical key for procedural generation
        instruments: List of instrument types for procedural generation
    """
    name: str
    state: MusicState
    file_path: Optional[str] = None
    default_volume: float = 0.3
    fade_ms: int = 500
    should_loop: bool = True
    duration: float = 120.0
    bpm: int = 60
    key: str = "C major"
    instruments: List[str] = None
    
    def __post_init__(self):
        if self.instruments is None:
            self.instruments = ["synth_pad"]


# Default music configuration for each state
MUSIC_CONFIG: Dict[MusicState, MusicTrack] = {
    MusicState.MAIN_MENU: MusicTrack(
        name="Exploration",
        state=MusicState.MAIN_MENU,
        file_path="sounds/music/main_menu.ogg",
        default_volume=0.4,
        fade_ms=500,
        should_loop=True,
        duration=180.0,
        bpm=65,
        key="C major",
        instruments=["synth_pad", "ambient_pad", "gentle_melody"]
    ),
    
    MusicState.GAMEPLAY: MusicTrack(
        name="Ambient Space",
        state=MusicState.GAMEPLAY,
        file_path="sounds/music/gameplay.ogg",
        default_volume=0.3,
        fade_ms=500,
        should_loop=True,
        duration=300.0,
        bpm=55,
        key="D minor",
        instruments=["synth_pad", "ambient_pad"]
    ),
    
    MusicState.CELEBRATION: MusicTrack(
        name="Victory",
        state=MusicState.CELEBRATION,
        file_path="sounds/music/celebration.ogg",
        default_volume=0.5,
        fade_ms=500,
        should_loop=False,
        duration=25.0,
        bpm=85,
        key="C major",
        instruments=["bright synth", "orchestral_hit", "celebration_melody"]
    ),
    
    MusicState.PARENT_DASHBOARD: MusicTrack(
        name="Neutral",
        state=MusicState.PARENT_DASHBOARD,
        file_path="sounds/music/dashboard.ogg",
        default_volume=0.2,
        fade_ms=500,
        should_loop=True,
        duration=120.0,
        bpm=60,
        key="F major",
        instruments=["subtle_ambient", "professional_pad"]
    ),
    
    MusicState.PAUSED: MusicTrack(
        name="Suspension",
        state=MusicState.PAUSED,
        file_path=None,
        default_volume=0.15,
        fade_ms=500,
        should_loop=True,
        duration=60.0,
        bpm=40,
        key="C minor",
        instruments=["slow_pad", "distant_ambient"]
    ),
    
    MusicState.TRANSITION: MusicTrack(
        name="Transition",
        state=MusicState.TRANSITION,
        file_path=None,
        default_volume=0.25,
        fade_ms=300,
        should_loop=False,
        duration=10.0,
        bpm=70,
        key="C major",
        instruments=["upward_arpeggio", "whoosh"]
    ),
}


# Procedural music generation parameters
PROCEDURAL_CONFIG = {
    "sample_rate": 44100,
    "channels": 2,
    "buffer_size": 1024,
    
    # Ambient pad settings
    "ambient_pad": {
        "frequency_range": [110.0, 440.0],  # A2 to A4
        "amplitude": 0.3,
        "decay": 0.98,
        "reverb_amount": 0.7,
    },
    
    # Melody settings
    "melody": {
        "scale": [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88],  # C major scale
        "rhythm": [0.5, 0.25, 0.25, 0.5, 0.5, 0.25, 0.25],  # Note durations
        "amplitude": 0.2,
    },
    
    # Bass settings
    "bass": {
        "frequency_range": [55.0, 110.0],  # A1 to A2
        "amplitude": 0.25,
        "decay": 0.95,
    },
    
    # Effects
    "reverb": {
        "decay_time": 3.0,
        "mix": 0.4,
    },
    
    # Master settings
    "master_volume": 0.8,
    "fade_in_ms": 500,
    "fade_out_ms": 500,
}


# Volume default settings
class AudioDefaults:
    """Default audio volume settings."""
    MUSIC_VOLUME = 0.3  # 30% default
    SFX_VOLUME = 0.5    # 50% default
    OVERALL_MUTE = False
    
    # Volume constraints
    MIN_VOLUME = 0.0
    MAX_VOLUME = 1.0


# File paths for external audio (if used)
class AudioPaths:
    """Paths to audio files."""
    MUSIC_DIR = "data/sounds/music"
    
    # Track file names
    MAIN_MENU = "main_menu.ogg"
    GAMEPLAY = "gameplay.ogg"
    CELEBRATION = "celebration.ogg"
    DASHBOARD = "dashboard.ogg"
    PAUSED = "paused.ogg"
    TRANSITION = "transition.ogg"
    
    @classmethod
    def get_track_path(cls, state: MusicState) -> str:
        """
        Get the file path for a music track.
        
        Args:
            state: MusicState to get path for
            
        Returns:
            Full path to the audio file
        """
        return f"{cls.MUSIC_DIR}/{state.value}.ogg"


def get_music_track(state: MusicState) -> MusicTrack:
    """
    Get the music track configuration for a game state.
    
    Args:
        state: MusicState to get track for
        
    Returns:
        MusicTrack configuration
        
    Raises:
        KeyError: If state not found in configuration
    """
    return MUSIC_CONFIG[state]


def get_all_music_states() -> List[MusicState]:
    """
    Get all available music states.
    
    Returns:
        List of all MusicState values
    """
    return list(MUSIC_STATE.value for MUSIC_STATE in MusicState)
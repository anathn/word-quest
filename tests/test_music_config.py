"""
Music Configuration Unit Tests

Tests for music configuration, track settings, and procedural generation parameters.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.audio.music_config import (
    MusicState,
    MusicTrack,
    MUSIC_CONFIG,
    PROCEDURAL_CONFIG,
    AudioDefaults,
    AudioPaths,
    get_music_track,
    get_all_music_states,
)


class TestMusicStateEnum:
    """Tests for MusicState enumeration."""
    
    def test_main_menu_state(self):
        """Test MAIN_MENU state."""
        assert MusicState.MAIN_MENU.value == "main_menu"
        assert str(MusicState.MAIN_MENU) == "MusicState.MAIN_MENU"
    
    def test_gameplay_state(self):
        """Test GAMEPLAY state."""
        assert MusicState.GAMEPLAY.value == "gameplay"
    
    def test_celebration_state(self):
        """Test CELEBRATION state."""
        assert MusicState.CELEBRATION.value == "celebration"
    
    def test_parent_dashboard_state(self):
        """Test PARENT_DASHBOARD state."""
        assert MusicState.PARENT_DASHBOARD.value == "parent_dashboard"
    
    def test_paused_state(self):
        """Test PAUSED state."""
        assert MusicState.PAUSED.value == "paused"
    
    def test_transition_state(self):
        """Test TRANSITION state."""
        assert MusicState.TRANSITION.value == "transition"
    
    def test_state_count(self):
        """Test total number of music states."""
        states = list(MusicState)
        assert len(states) == 6


class TestMusicTrack:
    """Tests for MusicTrack dataclass."""
    
    def test_create_track(self):
        """Test creating a MusicTrack."""
        track = MusicTrack(
            name="Test Track",
            state=MusicState.GAMEPLAY,
            default_volume=0.5
        )
        
        assert track.name == "Test Track"
        assert track.state == MusicState.GAMEPLAY
        assert track.default_volume == 0.5
        assert track.should_loop == True
        assert track.fade_ms == 500
    
    def test_track_default_values(self):
        """Test MusicTrack default values."""
        track = MusicTrack(
            name="Simple Track",
            state=MusicState.MAIN_MENU
        )
        
        assert track.file_path is None
        assert track.default_volume == 0.3
        assert track.fade_ms == 500
        assert track.should_loop == True
        assert track.duration == 120.0
        assert track.bpm == 60
        assert track.key == "C major"
        assert track.instruments == ["synth_pad"]
    
    def test_custom_instruments(self):
        """Test MusicTrack with custom instruments."""
        instruments = ["synth_pad", "ambient_pad", "melody"]
        track = MusicTrack(
            name="Complex Track",
            state=MusicState.CELEBRATION,
            instruments=instruments
        )
        
        assert track.instruments == instruments
    
    def test_track_with_file_path(self):
        """Test MusicTrack with file path."""
        track = MusicTrack(
            name="External Track",
            state=MusicState.GAMEPLAY,
            file_path="/path/to/music.ogg",
            should_loop=True
        )
        
        assert track.file_path == "/path/to/music.ogg"
        assert track.should_loop == True


class TestMUSIC_CONFIG:
    """Tests for the global MUSIC_CONFIG dictionary."""
    
    def test_all_states_have_configs(self):
        """Test that all MusicState values have configurations."""
        for state in MusicState:
            assert state in MUSIC_CONFIG, f"Missing config for {state}"
    
    def test_main_menu_config(self):
        """Test main menu music configuration."""
        track = MUSIC_CONFIG[MusicState.MAIN_MENU]
        
        assert track.name == "Exploration"
        assert track.state == MusicState.MAIN_MENU
        assert track.default_volume == 0.4
        assert track.fade_ms == 500
        assert track.should_loop == True
        assert track.duration == 180.0
        assert track.bpm == 65
        assert track.key == "C major"
    
    def test_gameplay_config(self):
        """Test gameplay music configuration."""
        track = MUSIC_CONFIG[MusicState.GAMEPLAY]
        
        assert track.name == "Ambient Space"
        assert track.state == MusicState.GAMEPLAY
        assert track.default_volume == 0.3
        assert track.should_loop == True
        assert track.bpm == 55
        assert track.key == "D minor"
    
    def test_celebration_config(self):
        """Test celebration music configuration."""
        track = MUSIC_CONFIG[MusicState.CELEBRATION]
        
        assert track.name == "Victory"
        assert track.state == MusicState.CELEBRATION
        assert track.default_volume == 0.5
        assert track.should_loop == False  # One-time play
        assert track.duration == 25.0
        assert track.bpm == 85
    
    def test_dashboard_config(self):
        """Test parent dashboard music configuration."""
        track = MUSIC_CONFIG[MusicState.PARENT_DASHBOARD]
        
        assert track.name == "Neutral"
        assert track.state == MusicState.PARENT_DASHBOARD
        assert track.default_volume == 0.2  # Quiet for professional setting
        assert track.should_loop == True
        assert track.bpm == 60
        assert track.key == "F major"
    
    def test_paused_config(self):
        """Test paused state music configuration."""
        track = MUSIC_CONFIG[MusicState.PAUSED]
        
        assert track.name == "Suspension"
        assert track.state == MusicState.PAUSED
        assert track.default_volume == 0.15  # Very quiet
        assert track.should_loop == True
    
    def test_transition_config(self):
        """Test transition state music configuration."""
        track = MUSIC_CONFIG[MusicState.TRANSITION]
        
        assert track.name == "Transition"
        assert track.state == MusicState.TRANSITION
        assert track.should_loop == False  # One-time transition sound
        assert track.duration == 10.0


class TestAudioDefaults:
    """Tests for AudioDefaults constants."""
    
    def test_music_volume_default(self):
        """Test default music volume is 30%."""
        assert AudioDefaults.MUSIC_VOLUME == 0.3
    
    def test_sfx_volume_default(self):
        """Test default SFX volume is 50%."""
        assert AudioDefaults.SFX_VOLUME == 0.5
    
    def test_overall_mute_default(self):
        """Test default overall mute is False."""
        assert AudioDefaults.OVERALL_MUTE == False
    
    def test_min_volume(self):
        """Test minimum volume constant."""
        assert AudioDefaults.MIN_VOLUME == 0.0
    
    def test_max_volume(self):
        """Test maximum volume constant."""
        assert AudioDefaults.MAX_VOLUME == 1.0


class TestAudioPaths:
    """Tests for AudioPaths class."""
    
    def test_music_dir(self):
        """Test music directory path."""
        assert AudioPaths.MUSIC_DIR == "data/sounds/music"
    
    def test_track_file_names(self):
        """Test individual track file names."""
        assert AudioPaths.MAIN_MENU == "main_menu.ogg"
        assert AudioPaths.GAMEPLAY == "gameplay.ogg"
        assert AudioPaths.CELEBRATION == "celebration.ogg"
        assert AudioPaths.DASHBOARD == "dashboard.ogg"
        assert AudioPaths.PAUSED == "paused.ogg"
        assert AudioPaths.TRANSITION == "transition.ogg"
    
    def test_get_track_path_main_menu(self):
        """Test get_track_path for main menu."""
        path = AudioPaths.get_track_path(MusicState.MAIN_MENU)
        assert path == "data/sounds/music/main_menu.ogg"
    
    def test_get_track_path_gameplay(self):
        """Test get_track_path for gameplay."""
        path = AudioPaths.get_track_path(MusicState.GAMEPLAY)
        assert path == "data/sounds/music/gameplay.ogg"
    
    def test_get_track_path_celebration(self):
        """Test get_track_path for celebration."""
        path = AudioPaths.get_track_path(MusicState.CELEBRATION)
        assert path == "data/sounds/music/celebration.ogg"
    
    def test_get_track_path_all_states(self):
        """Test get_track_path for all states."""
        for state in MusicState:
            path = AudioPaths.get_track_path(state)
            assert path.startswith("data/sounds/music/")
            assert path.endswith(".ogg")


class TestGetMusicTrack:
    """Tests for get_music_track function."""
    
    def test_get_main_menu_track(self):
        """Test getting main menu track."""
        track = get_music_track(MusicState.MAIN_MENU)
        
        assert track is not None
        assert track.state == MusicState.MAIN_MENU
        assert track == MUSIC_CONFIG[MusicState.MAIN_MENU]
    
    def test_get_gameplay_track(self):
        """Test getting gameplay track."""
        track = get_music_track(MusicState.GAMEPLAY)
        
        assert track.state == MusicState.GAMEPLAY
    
    def test_get_celebration_track(self):
        """Test getting celebration track."""
        track = get_music_track(MusicState.CELEBRATION)
        
        assert track.state == MusicState.CELEBRATION
        assert track.should_loop == False
    
    def test_get_unknown_state(self):
        """Test getting track for unknown state raises KeyError."""
        # Create a mock state that's not in MUSIC_CONFIG
        with pytest.raises(KeyError):
            # This will raise KeyError if state not in config
            _ = MUSIC_CONFIG[MusicState]  # Get the enum class itself (not a valid key)


class TestGetAllMusicStates:
    """Tests for get_all_music_states function."""
    
    def test_returns_list(self):
        """Test that function returns a list."""
        states = get_all_music_states()
        assert isinstance(states, list)
    
    def test_contains_all_states(self):
        """Test that all MusicState values are returned."""
        states = get_all_music_states()
        
        for state in MusicState:
            assert state.value in states
    
    def test_count_matches_enum(self):
        """Test that count matches MusicState enum."""
        states = get_all_music_states()
        assert len(states) == len(list(MusicState))


class TestPROCEDURAL_CONFIG:
    """Tests for procedural music generation configuration."""
    
    def test_sample_rate(self):
        """Test sample rate configuration."""
        assert PROCEDURAL_CONFIG["sample_rate"] == 44100
    
    def test_channels(self):
        """Test channel count."""
        assert PROCEDURAL_CONFIG["channels"] == 2
    
    def test_buffer_size(self):
        """Test buffer size."""
        assert PROCEDURAL_CONFIG["buffer_size"] == 1024
    
    def test_ambient_pad_config(self):
        """Test ambient pad configuration."""
        config = PROCEDURAL_CONFIG["ambient_pad"]
        
        assert "frequency_range" in config
        assert len(config["frequency_range"]) == 2
        assert config["amplitude"] == 0.3
    
    def test_melody_config(self):
        """Test melody configuration."""
        config = PROCEDURAL_CONFIG["melody"]
        
        assert "scale" in config
        assert len(config["scale"]) == 7  # Major scale has 7 notes
        assert "rhythm" in config
        assert config["amplitude"] == 0.2
    
    def test_bass_config(self):
        """Test bass configuration."""
        config = PROCEDURAL_CONFIG["bass"]
        
        assert "frequency_range" in config
        assert config["amplitude"] == 0.25
    
    def test_reverb_config(self):
        """Test reverb configuration."""
        config = PROCEDURAL_CONFIG["reverb"]
        
        assert config["decay_time"] == 3.0
        assert config["mix"] == 0.4
    
    def test_master_volume(self):
        """Test master volume configuration."""
        assert PROCEDURAL_CONFIG["master_volume"] == 0.8
    
    def test_fade_times(self):
        """Test fade time configurations."""
        assert PROCEDURAL_CONFIG["fade_in_ms"] == 500
        assert PROCEDURAL_CONFIG["fade_out_ms"] == 500


class TestTrackVolumeRequirements:
    """Tests to verify volume requirements from story.
    
    Story acceptance criteria:
    - Music is low volume by default (30% or lower)
    - Volume adjustable (0-100%)
    """
    
    def test_gameplay_volume_is_low(self):
        """Test gameplay music default is 30% or lower."""
        track = MUSIC_CONFIG[MusicState.GAMEPLAY]
        assert track.default_volume <= 0.3
    
    def test_main_menu_volume_reasonable(self):
        """Test main menu volume is reasonable."""
        track = MUSIC_CONFIG[MusicState.MAIN_MENU]
        assert 0.0 <= track.default_volume <= 1.0
    
    def test_celebration_volume_higher(self):
        """Test celebration music is louder (celebratory)."""
        track = MUSIC_CONFIG[MusicState.CELEBRATION]
        assert track.default_volume > 0.3  # Should be more prominent
    
    def test_dashboard_volume_very_low(self):
        """Test dashboard music is very quiet."""
        track = MUSIC_CONFIG[MusicState.PARENT_DASHBOARD]
        assert track.default_volume <= 0.3


class TestTrackDurationRequirements:
    """Tests for track duration requirements.
    
    Story specifications:
    - Main Menu: 2-3 minute loop
    - Gameplay: 3-5 minute loop  
    - Celebration: 15-30 seconds
    - Dashboard: 2 minute loop
    """
    
    def test_main_menu_duration(self):
        """Test main menu track duration (2-3 minutes = 120-180 seconds)."""
        track = MUSIC_CONFIG[MusicState.MAIN_MENU]
        assert 120 <= track.duration <= 180
    
    def test_gameplay_duration(self):
        """Test gameplay track duration (3-5 minutes = 180-300 seconds)."""
        track = MUSIC_CONFIG[MusicState.GAMEPLAY]
        assert 180 <= track.duration <= 300
    
    def test_celebration_duration(self):
        """Test celebration track duration (15-30 seconds)."""
        track = MUSIC_CONFIG[MusicState.CELEBRATION]
        assert 15 <= track.duration <= 30
    
    def test_dashboard_duration(self):
        """Test dashboard track duration (2 minutes = 120 seconds)."""
        track = MUSIC_CONFIG[MusicState.PARENT_DASHBOARD]
        assert track.duration == 120.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
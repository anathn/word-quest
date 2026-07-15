"""
Unit tests for sound manager module (STORY-005-03).

Tests cover:
- Sound manager initialization
- Sound playback
- Volume control
- Mute/unmute functionality
- Sound event configurations
"""

import pytest
import sys
import os
import time

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import numpy as np


class TestSoundEvent:
    """Test SoundEvent enum."""
    
    def test_sound_event_values(self):
        """Test that all sound events have valid values."""
        from audio.sfx_config import SoundEvent
        
        events = [
            SoundEvent.CORRECT_ANSWER,
            SoundEvent.INCORRECT_ANSWER,
            SoundEvent.STREAK_3,
            SoundEvent.STREAK_5,
            SoundEvent.PLANET_COMPLETE,
            SoundEvent.BUTTON_CLICK,
            SoundEvent.PLANET_APPROACH,
            SoundEvent.ROCKET_BONUS,
        ]
        
        for event in events:
            assert isinstance(event.value, str)
            assert len(event.value) > 0
    
    def test_sound_event_count(self):
        """Test that we have all expected events."""
        from audio.sfx_config import SoundEvent, get_all_events
        
        all_events = get_all_events()
        assert len(all_events) == 8, "Should have 8 sound events"


class TestSFXConfig:
    """Test SFX configuration."""
    
    def test_correct_answer_config(self):
        """Test correct answer sound configuration."""
        from audio.sfx_config import SoundEvent, get_sound_config
        
        config = get_sound_config(SoundEvent.CORRECT_ANSWER)
        
        # Check frequencies: C5, E5, G5 (major chord)
        assert len(config.frequencies) == 3
        assert config.frequencies[0] == 523.25  # C5
        assert config.frequencies[1] == 659.25  # E5
        assert config.frequencies[2] == 783.99  # G5
        
        # Check volume and duration
        assert config.volume == 0.5
        assert config.duration_total == 0.3
    
    def test_incorrect_answer_config(self):
        """Test incorrect answer sound configuration."""
        from audio.sfx_config import SoundEvent, get_sound_config
        
        config = get_sound_config(SoundEvent.INCORRECT_ANSWER)
        
        # Check frequencies: G4, F4 (descending whole step)
        assert len(config.frequencies) == 2
        assert config.frequencies[0] == 392.00  # G4
        assert config.frequencies[1] == 349.23  # F4
        
        # Check volume and duration
        assert config.volume == 0.3
        assert config.duration_total == 0.2
    
    def test_streak_3_config(self):
        """Test 3-word streak sound configuration."""
        from audio.sfx_config import SoundEvent, get_sound_config
        
        config = get_sound_config(SoundEvent.STREAK_3)
        
        # Check frequencies: C-E-G-A ascending
        assert len(config.frequencies) == 4
        assert config.volume == 0.6
        assert config.duration_total == 0.4
    
    def test_streak_5_config(self):
        """Test 5-word streak sound configuration."""
        from audio.sfx_config import SoundEvent, get_sound_config
        
        config = get_sound_config(SoundEvent.STREAK_5)
        
        # Check frequencies: C-E-G-C (octave)
        assert len(config.frequencies) == 4
        assert config.volume == 0.7
        assert config.duration_total == 0.5
    
    def test_planet_complete_config(self):
        """Test planet complete sound configuration."""
        from audio.sfx_config import SoundEvent, get_sound_config
        
        config = get_sound_config(SoundEvent.PLANET_COMPLETE)
        
        # Check frequencies: C-E-G-C-E arpeggio
        assert len(config.frequencies) == 5
        assert config.volume == 0.8
        assert config.duration_total == 0.6
    
    def test_get_sound_config_invalid(self):
        """Test that invalid events raise ValueError."""
        from audio.sfx_config import get_sound_config
        
        with pytest.raises(ValueError):
            # Create a mock invalid event
            class FakeEvent:
                value = "invalid"
            get_sound_config(FakeEvent())  # type: ignore


class TestSFXLibrary:
    """Test SFX library configurations."""
    
    def test_all_events_have_config(self):
        """Test that all sound events have configurations."""
        from audio.sfx_config import SFX_LIBRARY, SoundEvent
        
        for event in SoundEvent:
            assert event in SFX_LIBRARY, f"Missing config for {event}"
    
    def test_frequencies_positive(self):
        """Test that all frequencies are positive."""
        from audio.sfx_config import SFX_LIBRARY
        
        for event, config in SFX_LIBRARY.items():
            for freq in config.frequencies:
                assert freq > 0, f"Invalid frequency for {event}: {freq}"
    
    def test_volumes_in_range(self):
        """Test that all volumes are in valid range."""
        from audio.sfx_config import SFX_LIBRARY
        
        for event, config in SFX_LIBRARY.items():
            assert 0.0 <= config.volume <= 1.0, f"Invalid volume for {event}: {config.volume}"
    
    def test_durations_positive(self):
        """Test that all durations are positive."""
        from audio.sfx_config import SFX_LIBRARY
        
        for event, config in SFX_LIBRARY.items():
            for duration in config.durations:
                assert duration > 0, f"Invalid duration for {event}: {duration}"


class TestSFXGenerator:
    """Test SFXGenerator class."""
    
    def test_generate_tone(self):
        """Test single tone generation."""
        from audio.sfx_generator import SFXGenerator
        
        generator = SFXGenerator()
        
        # Generate a 440 Hz tone for 0.1 seconds
        sound_data = generator.generate_tone(
            frequency=440.0,
            duration=0.1,
            amplitude=0.5
        )
        
        # Check that we got some data
        assert len(sound_data) > 0
        
        # Basic sanity check on WAV header
        assert sound_data[:4] == b'RIFF'  # RIFF header
    
    def test_generate_chime(self):
        """Test chime generation with multiple frequencies."""
        from audio.sfx_generator import SFXGenerator
        
        generator = SFXGenerator()
        
        # Generate C-E-G major chord
        sound_data = generator.generate_chime(
            frequencies=[523.25, 659.25, 783.99],
            durations=[0.1, 0.1, 0.1],
            amplitude=0.4
        )
        
        assert len(sound_data) > 0
        assert sound_data[:4] == b'RIFF'  # RIFF header
    
    def test_generate_fanfare(self):
        """Test fanfare generation."""
        from audio.sfx_generator import SFXGenerator
        
        generator = SFXGenerator()
        
        # Generate ascending fanfare
        sound_data = generator.generate_fanfare(
            frequencies=[523.25, 659.25, 783.99, 1046.50],
            durations=[0.1, 0.1, 0.1, 0.2]
        )
        
        assert len(sound_data) > 0
    
    def test_generate_silence(self):
        """Test silence generation."""
        from audio.sfx_generator import SFXGenerator
        
        generator = SFXGenerator()
        
        sound_data = generator.generate_silence(0.5)
        
        assert len(sound_data) > 0
        assert sound_data[:4] == b'RIFF'
    
    def test_sample_rate(self):
        """Test custom sample rate."""
        from audio.sfx_generator import SFXGenerator
        
        generator = SFXGenerator(sample_rate=22050)  # Half of standard
        
        sound_data = generator.generate_tone(440.0, 0.1)
        
        assert len(sound_data) > 0


class TestSoundManager:
    """Test SoundManager class."""
    
    @pytest.fixture
    def sound_manager(self):
        """Create a sound manager instance."""
        from audio.sound_manager import SoundManager
        # Mock pygame to avoid needing actual audio hardware
        import sys
        from unittest.mock import MagicMock
        
        # Create mock pygame module
        mock_pygame = MagicMock()
        mock_pygame.mixer.get_init.return_value = None
        mock_pygame.mixer.init.return_value = None
        
        # Mock Sound object
        mock_sound_class = MagicMock()
        mock_sound_instance = MagicMock()
        mock_sound_class.return_value = mock_sound_instance
        mock_pygame.mixer.Sound = mock_sound_class
        
        sys.modules['pygame'] = mock_pygame
        
        manager = SoundManager()
        yield manager
        
        # Cleanup
        del sys.modules['pygame']
    
    def test_create_sound_manager(self):
        """Test sound manager creation."""
        from audio.sound_manager import SoundManager
        
        manager = SoundManager()
        assert manager is not None
        assert not manager.is_initialized()
    
    def test_initialization(self, sound_manager):
        """Test sound manager initialization."""
        result = sound_manager.initialize()
        
        # Should succeed or fail gracefully
        assert sound_manager.is_initialized()
    
    def test_get_volume(self, sound_manager):
        """Test default volume retrieval."""
        from audio.sfx_config import DEFAULT_SFX_VOLUME
        
        volume = sound_manager.get_volume()
        assert volume == DEFAULT_SFX_VOLUME
    
    def test_set_volume(self, sound_manager):
        """Test volume setting."""
        sound_manager.set_volume(0.75)
        assert sound_manager.get_volume() == 0.75
    
    def test_volume_bounds(self, sound_manager):
        """Test volume bounds checking."""
        sound_manager.set_volume(1.5)  # Above max
        assert sound_manager.get_volume() == 1.0
        
        sound_manager.set_volume(-0.1)  # Below min
        assert sound_manager.get_volume() == 0.0
    
    def test_mute_unmute(self, sound_manager):
        """Test mute/unmute functionality."""
        assert not sound_manager.is_muted()
        
        sound_manager.mute()
        assert sound_manager.is_muted()
        
        sound_manager.unmute()
        assert not sound_manager.is_muted()
    
    def test_toggle_mute(self, sound_manager):
        """Test mute toggle."""
        # toggle_mute returns the NEW state
        assert sound_manager.toggle_mute()  # First toggle: now muted (returns True)
        assert not sound_manager.toggle_mute()  # Second toggle: now unmuted (returns False)


class TestConvenienceFunctions:
    """Test convenience functions for playing sounds."""
    
    def test_convenience_functions_exist(self):
        """Test that convenience functions are exported."""
        from audio.sound_manager import (
            play_correct_answer,
            play_incorrect_answer,
            play_streak_3,
            play_streak_5,
            play_planet_complete,
            play_button_click,
            play_rocket_bonus,
        )
        
        assert callable(play_correct_answer)
        assert callable(play_incorrect_answer)
        assert callable(play_streak_3)
        assert callable(play_streak_5)
        assert callable(play_planet_complete)
        assert callable(play_button_click)
        assert callable(play_rocket_bonus)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
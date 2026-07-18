"""
Music Manager Unit Tests

Tests for music volume defaults, mute functionality, and basic manager behavior.
Uses mocking to avoid pygame/audio initialization issues.
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import config (no pygame dependency)
from src.audio.music_config import MusicState, AudioDefaults


class TestMusicVolumeDefaults:
    """Test that volume defaults match story requirements."""
    
    def test_default_music_volume_is_30_percent(self):
        """Story requires music to be low volume by default (30% or lower)."""
        assert AudioDefaults.MUSIC_VOLUME == 0.3
    
    def test_sfx_volume_default(self):
        """Test default SFX volume."""
        assert AudioDefaults.SFX_VOLUME == 0.5
    
    def test_overall_mute_default_is_false(self):
        """Audio should not be muted by default."""
        assert AudioDefaults.OVERALL_MUTE == False
    
    def test_volume_range_valid(self):
        """Test volume constraints."""
        assert AudioDefaults.MIN_VOLUME == 0.0
        assert AudioDefaults.MAX_VOLUME == 1.0


class TestMusicStateEnum:
    """Test MusicState enum values."""
    
    def test_states_exist(self):
        """Test all expected states exist."""
        states = [s.value for s in MusicState]
        assert "main_menu" in states
        assert "gameplay" in states
        assert "celebration" in states
        assert "parent_dashboard" in states
        assert "paused" in states
        assert "transition" in states


class TestMusicManagerImports:
    """Test that MusicManager can be imported without issues."""
    
    def test_music_manager_imports(self):
        """Test MusicManager module imports correctly."""
        with patch('pygame.mixer.get_init', return_value=None):
            from src.audio.music_manager import MusicManager
            assert MusicManager is not None
    
    def test_music_manager_singleton_functions_import(self):
        """Test singleton functions are available."""
        with patch('pygame.mixer.get_init', return_value=None):
            from src.audio.music_manager import (
                get_music_manager,
                reset_music_manager,
                play_music,
                stop_music,
                set_music_volume,
                toggle_music_mute,
            )
            assert callable(get_music_manager)
            assert callable(reset_music_manager)
            assert callable(play_music)
            assert callable(stop_music)
            assert callable(set_music_volume)
            assert callable(toggle_music_mute)


class TestMusicManagerBasicBehavior:
    """Test basic MusicManager behavior with mocking."""
    
    def test_music_manager_creation(self):
        """Test MusicManager can be created."""
        with patch('pygame.mixer.get_init', return_value=None):
            from src.audio.music_manager import MusicManager
            manager = MusicManager()
            assert manager is not None
    
    def test_get_default_volume(self):
        """Test get_volume returns default."""
        with patch('pygame.mixer.get_init', return_value=None):
            from src.audio.music_manager import MusicManager
            manager = MusicManager()
            # Should return AudioDefaults.MUSIC_VOLUME
            assert manager.get_volume() == AudioDefaults.MUSIC_VOLUME
    
    def test_set_volume_clamps_values(self):
        """Test volume clamping."""
        with patch('pygame.mixer.get_init', return_value=None), \
             patch('pygame.mixer.music.set_volume'):
            from src.audio.music_manager import MusicManager
            manager = MusicManager()
            
            # Test below minimum
            manager.set_volume(-0.5)
            assert manager.get_volume() == 0.0
            
            # Test above maximum
            manager.set_volume(1.5)
            assert manager.get_volume() == 1.0
    
    def test_mute_functionality(self):
        """Test mute methods."""
        with patch('pygame.mixer.get_init', return_value=(44100, -16, 2, 1024)), \
             patch('pygame.mixer.music.set_volume'):
            from src.audio.music_manager import MusicManager
            manager = MusicManager()
            
            # Initialize the manager (sets up internal state)
            manager.initialize()
            
            assert not manager.is_muted()
            manager.mute()
            assert manager.is_muted()
            manager.unmute()
            assert not manager.is_muted()
    
    def test_toggle_mute(self):
        """Test mute toggle."""
        with patch('pygame.mixer.get_init', return_value=(44100, -16, 2, 1024)), \
             patch('pygame.mixer.music.set_volume'):
            from src.audio.music_manager import MusicManager
            manager = MusicManager()
            
            # Initialize the manager
            manager.initialize()
            
            result = manager.toggle_mute()
            assert result == True
            result = manager.toggle_mute()
            assert result == False
    
    def test_singleton_pattern(self):
        """Test MusicManager is a singleton."""
        with patch('pygame.mixer.get_init', return_value=None):
            from src.audio.music_manager import get_music_manager, reset_music_manager
            reset_music_manager()
            
            manager1 = get_music_manager()
            manager2 = get_music_manager()
            assert manager1 is manager2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
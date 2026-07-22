"""
Unit tests for TTS Engine and Manager components (STORY-006-02)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.components.tts_engine import FallbackTTSEngine, create_tts_engine
from src.components.tts_manager import TTSManager
from src.components.tts_settings import TTSSettings


class TestFallbackTTSEngine:
    """Tests for fallback TTS engine (when pyttsx3 unavailable)"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FallbackTTSEngine()
    
    def test_initialization_returns_false(self):
        """Test that fallback initialize returns False"""
        assert self.engine.initialize() is False
    
    def test_speak_does_nothing(self):
        """Test that fallback speak doesn't raise exceptions"""
        # Should not raise
        self.engine.speak("test text")
        self.engine.speak("")
        self.engine.speak("test", speed=1.5, volume=0.5)
    
    def test_stop_does_nothing(self):
        """Test that fallback stop doesn't raise exceptions"""
        self.engine.stop()
    
    def test_is_speaking_returns_false(self):
        """Test that fallback always returns False for is_speaking"""
        assert self.engine.is_speaking() is False
    
    def test_get_available_voices_returns_empty_list(self):
        """Test that fallback returns empty voice list"""
        voices = self.engine.get_available_voices()
        assert voices == []
    
    def test_set_voice_returns_false(self):
        """Test that fallback set_voice returns False"""
        assert self.engine.set_voice("voice1") is False


class TestCreateTtsEngine:
    """Tests for factory function"""
    
    def test_returns_fallback_when_not_available(self):
        """Test that factory returns FallbackTTSEngine when pyttsx3 unavailable"""
        with patch.dict('sys.modules', {'pyttsx3': None}):
            engine = create_tts_engine()
            assert isinstance(engine, FallbackTTSEngine)


class TestTTSManagerBasic:
    """Basic tests for TTS Manager that don't require threading"""
    
    def test_settings_getter(self):
        """Test that get_settings returns current settings"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create, \
             patch('src.components.tts_manager.TTSConfigManager') as mock_config_mgr:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_create.return_value = mock_engine
            
            # Mock config manager to return fresh default settings
            mock_config = MagicMock()
            mock_config.settings = TTSSettings(enabled=True, speed=1.0, volume=1.0, voice_id=None)
            mock_config_mgr.return_value = mock_config
            
            manager = TTSManager()
            settings = manager.get_settings()
            
            assert isinstance(settings, TTSSettings)
            assert settings.enabled is True
            assert settings.speed == 1.0
            assert settings.volume == 1.0
    
    def test_set_enabled_updates_setting(self):
        """Test that set_enabled updates settings"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_create.return_value = mock_engine
            
            manager = TTSManager()
            manager.set_enabled(False)
            
            assert manager.settings.enabled is False
    
    def test_set_speed_updates_setting_with_clamping(self):
        """Test that set_speed updates setting and clamps values"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_create.return_value = mock_engine
            
            manager = TTSManager()
            manager.set_speed(0.3)  # Below minimum
            assert manager.settings.speed == 0.5
            
            manager.set_speed(2.5)  # Above maximum
            assert manager.settings.speed == 2.0
            
            manager.set_speed(1.5)
            assert manager.settings.speed == 1.5
    
    def test_set_volume_updates_setting_with_clamping(self):
        """Test that set_volume updates setting and clamps values"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_create.return_value = mock_engine
            
            manager = TTSManager()
            manager.set_volume(-0.5)  # Below minimum
            assert manager.settings.volume == 0.0
            
            manager.set_volume(1.5)  # Above maximum
            assert manager.settings.volume == 1.0
            
            manager.set_volume(0.7)
            assert manager.settings.volume == 0.7
    
    def test_is_speaking_returns_current_state(self):
        """Test that is_speaking returns correct state"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_create.return_value = mock_engine
            
            manager = TTSManager()
            assert manager.is_speaking() is False
            
            manager._is_speaking = True
            assert manager.is_speaking() is True
    
    def test_get_current_text_returns_text_being_spoken(self):
        """Test that get_current_text returns current text"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_create.return_value = mock_engine
            
            manager = TTSManager()
            assert manager.get_current_text() is None
            
            manager._current_text = "Hello"
            assert manager.get_current_text() == "Hello"
    
    def test_enabled_property_checks_both_conditions(self):
        """Test that is_enabled checks both enabled flag and initialization"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_create.return_value = mock_engine
            
            manager = TTSManager()
            
            # Both conditions True
            manager.settings.enabled = True
            assert manager.is_enabled is True
            
            # Flag False
            manager.settings.enabled = False
            assert manager.is_enabled is False
            
            # Not initialized
            manager.settings.enabled = True
            manager._initialized = False
            assert manager.is_enabled is False
    
    def test_can_set_speech_start_callback(self):
        """Test that on_speech_start callback can be set"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_create.return_value = mock_engine
            
            mock_callback = MagicMock()
            
            manager = TTSManager()
            manager.on_speech_start(mock_callback)
            
            assert manager._on_speech_start == mock_callback
    
    def test_can_set_speech_end_callback(self):
        """Test that on_speech_end callback can be set"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_create.return_value = mock_engine
            
            mock_callback = MagicMock()
            
            manager = TTSManager()
            manager.on_speech_end(mock_callback)
            
            assert manager._on_speech_end == mock_callback
    
    def test_clear_queue_removes_all_items(self):
        """Test that clear_queue empties the queue"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_create.return_value = mock_engine
            
            manager = TTSManager()
            manager.speech_queue.put("first")
            manager.speech_queue.put("second")
            manager.clear_queue()
            
            assert manager.speech_queue.empty()
    
    def test_clear_queue_does_not_stop_speech(self):
        """Test that clear_queue doesn't stop ongoing speech"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_create.return_value = mock_engine
            
            manager = TTSManager()
            manager._is_speaking = True
            manager.clear_queue()
            
            # Engine.stop should NOT be called by clear_queue
            mock_engine.stop.assert_not_called()
            assert manager._is_speaking is True
    
    def test_speak_word_empty_string_ignored(self):
        """Test that empty string doesn't queue anything"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_create.return_value = mock_engine
            
            manager = TTSManager()
            manager.speak_word("")
            manager.speak_word("   ")
            
            assert manager.speech_queue.empty()
    
    def test_get_available_voices_delegates_to_engine(self):
        """Test that get_available_voices uses engine"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_engine.get_available_voices.return_value = [
                {'id': 'v1', 'name': 'Voice 1'},
                {'id': 'v2', 'name': 'Voice 2'}
            ]
            mock_create.return_value = mock_engine
            
            manager = TTSManager()
            voices = manager.get_available_voices()
            
            assert len(voices) == 2
            mock_engine.get_available_voices.assert_called_once()
    
    def test_set_voice_updates_setting(self):
        """Test that set_voice updates settings"""
        with patch('src.components.tts_manager.create_tts_engine') as mock_create:
            mock_engine = MagicMock()
            mock_engine.initialize.return_value = True
            mock_engine.set_voice.return_value = True
            mock_create.return_value = mock_engine
            
            manager = TTSManager()
            result = manager.set_voice("voice123")
            
            assert result is True
            assert manager.settings.voice_id == "voice123"
            mock_engine.set_voice.assert_called_with("voice123")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
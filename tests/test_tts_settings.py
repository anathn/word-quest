"""
Unit tests for TTS Settings component (STORY-006-02)
"""

import pytest
import json
import os
import tempfile
from src.components.tts_settings import TTSSettings, TTSConfigManager


class TestTTSSettings:
    """Tests for TTSSettings dataclass"""
    
    def test_default_values(self):
        """Test that default settings have correct values"""
        settings = TTSSettings()
        assert settings.enabled is True
        assert settings.speed == 1.0
        assert settings.volume == 1.0
        assert settings.voice_id is None
    
    def test_to_dict(self):
        """Test serialization to dictionary"""
        settings = TTSSettings(
            enabled=True,
            speed=1.5,
            volume=0.8,
            voice_id="voice1"
        )
        result = settings.to_dict()
        
        assert result['enabled'] is True
        assert result['speed'] == 1.5
        assert result['volume'] == 0.8
        assert result['voice_id'] == "voice1"
    
    def test_from_dict(self):
        """Test deserialization from dictionary"""
        data = {
            'enabled': False,
            'speed': 0.5,
            'volume': 0.0,
            'voice_id': "voice2"
        }
        settings = TTSSettings.from_dict(data)
        
        assert settings.enabled is False
        assert settings.speed == 0.5
        assert settings.volume == 0.0
        assert settings.voice_id == "voice2"
    
    def test_from_dict_partial_data(self):
        """Test deserialization with partial data uses defaults"""
        data = {'enabled': False}
        settings = TTSSettings.from_dict(data)
        
        assert settings.enabled is False
        assert settings.speed == 1.0  # Default
        assert settings.volume == 1.0  # Default
        assert settings.voice_id is None  # Default
    
    def test_validate_valid_settings(self):
        """Test validation of valid settings"""
        settings = TTSSettings()
        assert settings.validate() is True
        
        settings.speed = 1.5
        settings.volume = 0.5
        assert settings.validate() is True
    
    def test_validate_invalid_speed(self):
        """Test validation rejects invalid speed"""
        settings = TTSSettings(speed=0.3)  # Too slow
        assert settings.validate() is False
        
        settings.speed = 2.5  # Too fast
        assert settings.validate() is False
    
    def test_validate_invalid_volume(self):
        """Test validation rejects invalid volume"""
        settings = TTSSettings(volume=-0.1)  # Negative
        assert settings.validate() is False
        
        settings.volume = 1.5  # Over max
        assert settings.validate() is False
    
    def test_clamp_speed(self):
        """Test speed clamping to valid range"""
        settings = TTSSettings()
        
        assert settings.clamp_speed(0.2) == 0.5
        assert settings.clamp_speed(0.5) == 0.5
        assert settings.clamp_speed(1.0) == 1.0
        assert settings.clamp_speed(1.5) == 1.5
        assert settings.clamp_speed(2.0) == 2.0
        assert settings.clamp_speed(3.0) == 2.0
    
    def test_clamp_volume(self):
        """Test volume clamping to valid range"""
        settings = TTSSettings()
        
        assert settings.clamp_volume(-0.5) == 0.0
        assert settings.clamp_volume(0.0) == 0.0
        assert settings.clamp_volume(0.5) == 0.5
        assert settings.clamp_volume(1.0) == 1.0
        assert settings.clamp_volume(1.5) == 1.0
    
    def test_validate_speed(self):
        """Test speed validation method"""
        settings = TTSSettings()
        
        assert settings.validate_speed(0.5) is True
        assert settings.validate_speed(1.0) is True
        assert settings.validate_speed(2.0) is True
        assert settings.validate_speed(0.4) is False
        assert settings.validate_speed(2.1) is False
    
    def test_validate_volume(self):
        """Test volume validation method"""
        settings = TTSSettings()
        
        assert settings.validate_volume(0.0) is True
        assert settings.validate_volume(0.5) is True
        assert settings.validate_volume(1.0) is True
        assert settings.validate_volume(-0.1) is False
        assert settings.validate_volume(1.1) is False
    
    def test_get_speed_preset_name_default(self):
        """Test preset name for default speed"""
        settings = TTSSettings()
        assert settings.get_speed_preset_name() == "Normal"
    
    def test_get_speed_preset_name_slow(self):
        """Test preset name for slow speed"""
        settings = TTSSettings(speed=0.5)
        assert settings.get_speed_preset_name() == "Slow"
    
    def test_get_speed_preset_name_fast(self):
        """Test preset name for fast speed"""
        settings = TTSSettings(speed=1.5)
        assert settings.get_speed_preset_name() == "Fast"
    
    def test_get_speed_preset_name_very_fast(self):
        """Test preset name for very fast speed"""
        settings = TTSSettings(speed=2.0)
        assert settings.get_speed_preset_name() == "Very Fast"
    
    def test_get_speed_preset_name_custom(self):
        """Test preset name for custom speed"""
        settings = TTSSettings(speed=1.2)
        assert settings.get_speed_preset_name() == "Custom"
    
    def test_apply_preset_slow(self):
        """Test applying slow preset"""
        settings = TTSSettings()
        settings.apply_preset('slow')
        assert settings.speed == 0.5
    
    def test_apply_preset_normal(self):
        """Test applying normal preset"""
        settings = TTSSettings(speed=2.0)
        settings.apply_preset('normal')
        assert settings.speed == 1.0
    
    def test_apply_preset_fast(self):
        """Test applying fast preset"""
        settings = TTSSettings()
        settings.apply_preset('fast')
        assert settings.speed == 1.5
    
    def test_apply_preset_very_fast(self):
        """Test applying very fast preset"""
        settings = TTSSettings()
        settings.apply_preset('very_fast')
        assert settings.speed == 2.0
    
    def test_apply_preset_invalid(self):
        """Test applying invalid preset keeps current speed"""
        settings = TTSSettings(speed=1.0)
        settings.apply_preset('invalid_preset')
        # Speed should remain unchanged (or log warning)
        assert settings.speed == 1.0


class TestTTSConfigManager:
    """Tests for TTSConfigManager class"""
    
    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file path (file doesn't exist)"""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        os.remove(path)  # Remove the file so it doesn't exist for the test
        yield path
        # Cleanup
        if os.path.exists(path):
            os.remove(path)
    
    def test_load_missing_file_uses_defaults(self, temp_config_file):
        """Test that missing file results in default settings"""
        config = TTSConfigManager(temp_config_file)
        assert config.settings.enabled is True
        assert config.settings.speed == 1.0
        assert config.settings.volume == 1.0
    
    def test_save_creates_file(self, temp_config_file):
        """Test that save creates the config file"""
        config = TTSConfigManager(temp_config_file)
        assert not os.path.exists(temp_config_file)
        
        config.save()
        assert os.path.exists(temp_config_file)
    
    def test_save_and_load_persists_settings(self, temp_config_file):
        """Test that settings persist through save and load"""
        config = TTSConfigManager(temp_config_file)
        config.settings.enabled = False
        config.settings.speed = 1.5
        config.settings.volume = 0.7
        config.save()
        
        # Create new config manager (simulating restart)
        config2 = TTSConfigManager(temp_config_file)
        
        assert config2.settings.enabled is False
        assert config2.settings.speed == 1.5
        assert config2.settings.volume == 0.7
    
    def test_save_adds_to_existing_data(self, temp_config_file):
        """Test that save preserves other data in file"""
        # Create file with existing data
        existing_data = {'other_section': {'key': 'value'}}
        with open(temp_config_file, 'w') as f:
            json.dump(existing_data, f)
        
        config = TTSConfigManager(temp_config_file)
        config.settings.speed = 1.5
        config.save()
        
        # Verify both old and new data exist
        with open(temp_config_file, 'r') as f:
            data = json.load(f)
        
        assert data['other_section']['key'] == 'value'
        assert 'tts' in data
        assert data['tts']['speed'] == 1.5
    
    def test_load_invalid_json_uses_defaults(self, temp_config_file):
        """Test that invalid JSON results in default settings"""
        with open(temp_config_file, 'w') as f:
            f.write('invalid json {')
        
        config = TTSConfigManager(temp_config_file)
        assert config.settings.speed == 1.0  # Default
    
    def test_set_enabled(self, temp_config_file):
        """Test set_enabled method"""
        config = TTSConfigManager(temp_config_file)
        config.set_enabled(False)
        assert config.settings.enabled is False
    
    def test_set_speed(self, temp_config_file):
        """Test set_speed method"""
        config = TTSConfigManager(temp_config_file)
        config.set_speed(1.5)
        assert config.settings.speed == 1.5
        
        # Test clamping
        config.set_speed(0.1)  # Below minimum
        assert config.settings.speed == 0.5
        
        config.set_speed(3.0)  # Above maximum
        assert config.settings.speed == 2.0
    
    def test_set_volume(self, temp_config_file):
        """Test set_volume method"""
        config = TTSConfigManager(temp_config_file)
        config.set_volume(0.7)
        assert config.settings.volume == 0.7
        
        # Test clamping
        config.set_volume(-0.5)  # Below minimum
        assert config.settings.volume == 0.0
        
        config.set_volume(1.5)  # Above maximum
        assert config.settings.volume == 1.0
    
    def test_set_voice(self, temp_config_file):
        """Test set_voice method"""
        config = TTSConfigManager(temp_config_file)
        config.set_voice("voice123")
        assert config.settings.voice_id == "voice123"
    
    def test_reset_to_defaults(self, temp_config_file):
        """Test reset_to_defaults method"""
        config = TTSConfigManager(temp_config_file)
        config.settings.enabled = False
        config.settings.speed = 1.5
        config.settings.volume = 0.0
        config.save()
        
        config.reset_to_defaults()
        
        assert config.settings.enabled is True
        assert config.settings.speed == 1.0
        assert config.settings.volume == 1.0
    
    def test_creates_data_directory(self, temp_config_file):
        """Test that save creates parent directory if needed"""
        # Use a path in a non-existent directory
        temp_dir = tempfile.mkdtemp()
        nested_path = os.path.join(temp_dir, 'subdir', 'config.json')
        
        config = TTSConfigManager(nested_path)
        config.save()
        
        assert os.path.exists(nested_path)
        
        # Cleanup
        os.remove(nested_path)
        os.rmdir(os.path.join(temp_dir, 'subdir'))
        os.rmdir(temp_dir)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
"""
Unit Tests for Caption Settings Component (STORY-006-03)

Tests for caption settings data model, validation, and persistence.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch

from src.components.caption_settings import (
    CaptionSettings, CaptionSettingsManager
)


class TestCaptionSettings:
    """Tests for CaptionSettings dataclass."""
    
    def test_default_values(self):
        """Test default settings values."""
        settings = CaptionSettings()
        
        assert settings.enabled == True
        assert settings.font_size == 28
        assert settings.position == "bottom"
        assert settings.background_color == (0, 0, 0, 180)
        assert settings.text_color == (255, 255, 255)
        assert settings.speaker_color == (255, 215, 0)
        assert settings.duration == 3.0
        assert settings.high_contrast == False
        assert settings.show_sfx == True
        assert settings.intensity_mode == "full"
    
    def test_to_dict(self):
        """Test settings serialization."""
        settings = CaptionSettings(
            font_size=36,
            position="middle",
            duration=4.5
        )
        
        result = settings.to_dict()
        
        assert result['font_size'] == 36
        assert result['position'] == "middle"
        assert result['duration'] == 4.5
        assert isinstance(result['background_color'], list)
    
    def test_from_dict(self):
        """Test settings deserialization."""
        data = {
            'enabled': False,
            'font_size': 32,
            'position': 'middle',
            'background_color': [0, 0, 0, 200],
            'text_color': [255, 255, 0],
            'speaker_color': [255, 0, 0],
            'duration': 5.0,
            'high_contrast': True,
            'show_sfx': False,
            'intensity_mode': 'reduced'
        }
        
        settings = CaptionSettings.from_dict(data)
        
        assert settings.enabled == False
        assert settings.font_size == 32
        assert settings.position == "middle"
        assert settings.duration == 5.0
        assert settings.high_contrast == True
        assert settings.show_sfx == False
        assert settings.intensity_mode == "reduced"
    
    def test_from_dict_missing_fields(self):
        """Test deserialization with missing fields uses defaults."""
        data = {
            'font_size': 36
        }
        
        settings = CaptionSettings.from_dict(data)
        
        assert settings.font_size == 36
        assert settings.enabled == True  # Default
        assert settings.position == "bottom"  # Default
    
    def test_from_dict_invalid_font_size(self):
        """Test font size validation."""
        data = {
            'font_size': "invalid"
        }
        
        settings = CaptionSettings.from_dict(data)
        
        assert settings.font_size == 28  # Default
    
    def test_from_dict_font_size_clamped(self):
        """Test font size is clamped to valid range."""
        data = {
            'font_size': 100  # Too large
        }
        
        settings = CaptionSettings.from_dict(data)
        
        assert settings.font_size <= CaptionSettings.MAX_FONT_SIZE
    
    def test_from_dict_invalid_duration(self):
        """Test duration validation."""
        data = {
            'duration': "invalid"
        }
        
        settings = CaptionSettings.from_dict(data)
        
        assert settings.duration == 3.0  # Default
    
    def test_from_dict_duration_clamped(self):
        """Test duration is clamped to valid range."""
        data = {
            'duration': 20.0  # Too long
        }
        
        settings = CaptionSettings.from_dict(data)
        
        assert settings.duration <= CaptionSettings.MAX_DURATION
    
    def test_from_dict_color_as_list(self):
        """Test color as list is converted to tuple."""
        data = {
            'background_color': [0, 0, 0, 200],
            'text_color': [255, 255, 255]
        }
        
        settings = CaptionSettings.from_dict(data)
        
        assert isinstance(settings.background_color, tuple)
        assert isinstance(settings.text_color, tuple)
    
    def test_from_dict_color_wrong_channels(self):
        """Test color with wrong number of channels is fixed."""
        data = {
            'text_color': [255, 255]  # Only 2 channels
        }
        
        settings = CaptionSettings.from_dict(data)
        
        # Should have 3 channels
        assert len(settings.text_color) == 3
    
    def test_apply_high_contrast(self):
        """Test high contrast mode application."""
        settings = CaptionSettings()
        
        settings.apply_high_contrast()
        
        assert settings.high_contrast == True
        assert settings.text_color == (0, 0, 0)
        assert settings.background_color == (255, 255, 255, 230)
    
    def test_reset_to_defaults(self):
        """Test resetting to defaults."""
        settings = CaptionSettings(
            font_size=36,
            enabled=False,
            high_contrast=True
        )
        
        settings.reset_to_defaults()
        
        assert settings.font_size == 28
        assert settings.enabled == True
        assert settings.high_contrast == False


class TestCaptionSettingsManager:
    """Tests for CaptionSettingsManager."""
    
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary data directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return str(data_dir)
    
    def test_initialization_default(self, temp_data_dir):
        """Test manager initializes with defaults."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        assert manager.settings is not None
        assert manager.settings.enabled == True
    
    def test_initialization_loads_existing(self, temp_data_dir):
        """Test manager loads existing settings file."""
        # Create settings file
        settings_file = os.path.join(temp_data_dir, 'caption_settings.json')
        data = {
            'enabled': False,
            'font_size': 36,
            'position': 'middle'
        }
        with open(settings_file, 'w') as f:
            json.dump(data, f)
        
        # Load settings
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        assert manager.settings.enabled == False
        assert manager.settings.font_size == 36
        assert manager.settings.position == "middle"
    
    def test_save_settings(self, temp_data_dir):
        """Test saving settings to file."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        manager.update_settings(font_size=36, position="middle")
        
        result = manager.save_settings()
        
        assert result == True
        
        # Verify file exists
        settings_file = os.path.join(temp_data_dir, 'caption_settings.json')
        assert os.path.exists(settings_file)
        
        # Verify content
        with open(settings_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['font_size'] == 36
        assert saved_data['position'] == "middle"
    
    def test_load_settings_missing_file(self, temp_data_dir):
        """Test loading when settings file doesn't exist."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        manager.load_settings()
        
        # Should use defaults
        assert manager.settings.enabled == True
    
    def test_get_settings(self, temp_data_dir):
        """Test getting current settings."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        settings = manager.get_settings()
        
        assert settings is manager.settings
    
    def test_update_settings(self, temp_data_dir):
        """Test updating settings."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        manager.update_settings(font_size=36, position="middle")
        
        assert manager.settings.font_size == 36
        assert manager.settings.position == "middle"
    
    def test_set_enabled(self, temp_data_dir):
        """Test enabling/disabling captions."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        manager.set_enabled(False)
        
        assert manager.settings.enabled == False
    
    def test_set_font_size(self, temp_data_dir):
        """Test setting font size."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        manager.set_font_size(36)
        
        assert manager.settings.font_size == 36
    
    def test_set_position(self, temp_data_dir):
        """Test setting position."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        manager.set_position("middle")
        
        assert manager.settings.position == "middle"
    
    def test_set_position_invalid(self, temp_data_dir):
        """Test setting invalid position doesn't change."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        manager.set_position("invalid")
        
        assert manager.settings.position == "bottom"  # Default
    
    def test_set_duration(self, temp_data_dir):
        """Test setting duration."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        manager.set_duration(5.0)
        
        assert manager.settings.duration == 5.0
    
    def test_set_high_contrast(self, temp_data_dir):
        """Test toggling high contrast."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        manager.set_high_contrast(True)
        
        assert manager.settings.high_contrast == True
        assert manager.settings.text_color == (0, 0, 0)
    
    def test_set_sfx_display(self, temp_data_dir):
        """Test toggling SFX display."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        manager.set_sfx_display(False)
        
        assert manager.settings.show_sfx == False
    
    def test_set_intensity_mode(self, temp_data_dir):
        """Test setting intensity mode."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        manager.set_intensity_mode("reduced")
        
        assert manager.settings.intensity_mode == "reduced"
    
    def test_set_intensity_mode_invalid(self, temp_data_dir):
        """Test setting invalid intensity mode doesn't change."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        manager.set_intensity_mode("invalid")
        
        assert manager.settings.intensity_mode == "full"  # Default
    
    def test_save_creates_directory(self, tmp_path):
        """Test that save creates data directory if not exists."""
        data_dir = tmp_path / "new_data"
        
        manager = CaptionSettingsManager(data_dir=str(data_dir))
        
        result = manager.save_settings()
        
        assert result == True
        assert data_dir.exists()
    
    def test_persistence_roundtrip(self, temp_data_dir):
        """Test settings persist through save and load."""
        # Create and configure manager
        manager1 = CaptionSettingsManager(data_dir=temp_data_dir)
        manager1.update_settings(
            font_size=36,
            position="middle",
            show_sfx=False,
            duration=4.5
        )
        
        # Save
        manager1.save_settings()
        
        # Create new manager (simulates restart)
        manager2 = CaptionSettingsManager(data_dir=temp_data_dir)
        
        # Should have same settings
        assert manager2.settings.font_size == 36
        assert manager2.settings.position == "middle"
        assert manager2.settings.show_sfx == False
        assert manager2.settings.duration == 4.5


class TestCaptionSettingsEdgeCases:
    """Edge case tests for caption settings."""
    
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        return str(data_dir)
    
    def test_corrupt_settings_file(self, temp_data_dir):
        """Test handling corrupt settings file."""
        # Create corrupt JSON
        settings_file = os.path.join(temp_data_dir, 'caption_settings.json')
        with open(settings_file, 'w') as f:
            f.write("{ invalid json }")
        
        # Should use defaults without crashing
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        assert manager.settings.enabled == True  # Default
    
    def test_empty_settings_file(self, temp_data_dir):
        """Test handling empty settings file."""
        settings_file = os.path.join(temp_data_dir, 'caption_settings.json')
        with open(settings_file, 'w') as f:
            f.write("{}")
        
        # Should use defaults for all fields
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        assert manager.settings.enabled == True
    
    def test_negative_font_size(self, temp_data_dir):
        """Test negative font size is clamped."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        manager.set_font_size(-10)
        
        assert manager.settings.font_size >= CaptionSettings.MIN_FONT_SIZE
    
    def test_zero_duration(self, temp_data_dir):
        """Test zero duration is clamped."""
        manager = CaptionSettingsManager(data_dir=temp_data_dir)
        
        manager.set_duration(0)
        
        assert manager.settings.duration >= CaptionSettings.MIN_DURATION
    
    def test_none_in_dict(self, temp_data_dir):
        """Test None values in dict use defaults."""
        data = {
            'font_size': None,
            'duration': None
        }
        
        settings = CaptionSettings.from_dict(data)
        
        assert settings.font_size == 28  # Default
        assert settings.duration == 3.0  # Default


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
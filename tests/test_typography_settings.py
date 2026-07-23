"""
Tests for TypographySettings component.

STORY-006-05: OpenDyslexic Font Implementation
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from components.typography_settings import TypographySettings


class TestTypographySettingsDataclass:
    """Test cases for TypographySettings dataclass."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        settings = TypographySettings()
        
        assert settings.font_family == TypographySettings.FONT_DEFAULT
        assert settings.font_size_base == TypographySettings.DEFAULT_FONT_SIZE_BASE
        assert settings.font_size_large == TypographySettings.DEFAULT_FONT_SIZE_LARGE
        assert settings.font_size_small == TypographySettings.DEFAULT_FONT_SIZE_SMALL
        assert settings.letter_spacing == TypographySettings.DEFAULT_LETTER_SPACING
        assert settings.word_spacing == TypographySettings.DEFAULT_WORD_SPACING
        assert settings.line_height == TypographySettings.DEFAULT_LINE_HEIGHT
    
    def test_custom_values(self):
        """Test custom values can be set."""
        settings = TypographySettings(
            font_family="opendyslexic",
            font_size_base=28,
            font_size_large=52,
            letter_spacing=4
        )
        
        assert settings.font_family == "opendyslexic"
        assert settings.font_size_base == 28
        assert settings.font_size_large == 52
        assert settings.letter_spacing == 4
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        settings = TypographySettings(
            font_family="opendyslexic",
            font_size_base=28
        )
        
        data = settings.to_dict()
        
        assert data['font_family'] == "opendyslexic"
        assert data['font_size_base'] == 28
        assert 'font_size_large' in data
        assert 'font_size_small' in data
        assert 'letter_spacing' in data
        assert 'word_spacing' in data
        assert 'line_height' in data
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'font_family': 'opendyslexic',
            'font_size_base': 28,
            'font_size_large': 52,
            'font_size_small': 20,
            'letter_spacing': 4,
            'word_spacing': 6,
            'line_height': 1.6
        }
        
        settings = TypographySettings.from_dict(data)
        
        assert settings.font_family == 'opendyslexic'
        assert settings.font_size_base == 28
        assert settings.font_size_large == 52
        assert settings.letter_spacing == 4
    
    def test_from_dict_defaults(self):
        """Test that missing values use defaults."""
        data = {
            'font_family': 'opendyslexic'
            # Missing other fields
        }
        
        settings = TypographySettings.from_dict(data)
        
        assert settings.font_family == 'opendyslexic'
        assert settings.font_size_base == TypographySettings.DEFAULT_FONT_SIZE_BASE
        assert settings.line_height == TypographySettings.DEFAULT_LINE_HEIGHT
    
    def test_is_opendyslexic_true(self):
        """Test is_opendyslexic returns True when OD selected."""
        settings = TypographySettings(font_family=TypographySettings.FONT_OD)
        
        assert settings.is_opendyslexic() is True
    
    def test_is_opendyslexic_false(self):
        """Test is_opendyslexic returns False when default selected."""
        settings = TypographySettings(font_family=TypographySettings.FONT_DEFAULT)
        
        assert settings.is_opendyslexic() is False
    
    def test_set_font_family_valid(self):
        """Test setting valid font family."""
        settings = TypographySettings(font_family=TypographySettings.FONT_DEFAULT)
        
        settings.set_font_family(TypographySettings.FONT_OD)
        
        assert settings.font_family == TypographySettings.FONT_OD
    
    def test_set_font_family_invalid(self):
        """Test setting invalid font family falls back to default."""
        settings = TypographySettings()
        
        settings.set_font_family("invalid_font")
        
        assert settings.font_family == TypographySettings.FONT_DEFAULT
    
    def test_validate_valid_settings(self):
        """Test validation of valid settings."""
        settings = TypographySettings()
        
        assert settings.validate() is True
    
    def test_validate_invalid_font_family(self):
        """Test validation with invalid font family."""
        settings = TypographySettings(font_family="invalid")
        
        assert settings.validate() is False
    
    def test_validate_invalid_font_size_base(self):
        """Test validation with invalid base font size."""
        settings = TypographySettings(font_size_base=0)
        
        assert settings.validate() is False
        
        settings = TypographySettings(font_size_base=150)
        
        assert settings.validate() is False
    
    def test_validate_invalid_letter_spacing(self):
        """Test validation with invalid letter spacing."""
        settings = TypographySettings(letter_spacing=-1)
        
        assert settings.validate() is False
        
        settings = TypographySettings(letter_spacing=25)
        
        assert settings.validate() is False
    
    def test_apply_defaults_if_invalid(self):
        """Test that invalid values are replaced with defaults."""
        settings = TypographySettings(
            font_family="invalid",
            font_size_base=0,
            letter_spacing=-5,
            line_height=5.0
        )
        
        settings.apply_defaults_if_invalid()
        
        assert settings.font_family == TypographySettings.FONT_DEFAULT
        assert settings.font_size_base == TypographySettings.DEFAULT_FONT_SIZE_BASE
        assert settings.letter_spacing == TypographySettings.DEFAULT_LETTER_SPACING
        assert settings.line_height == TypographySettings.DEFAULT_LINE_HEIGHT


class TestTypographySettingsPersistence:
    """Test cases for TypographySettings persistence."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temp directory for test config
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.temp_dir, 'test_typography.json')
    
    def teardown_method(self):
        """Clean up after tests."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load(self):
        """Test saving and loading settings."""
        # Create settings and save to temp file
        original_path = TypographySettings.CONFIG_PATH
        TypographySettings.CONFIG_PATH = self.test_config_path
        
        settings = TypographySettings(
            font_family="opendyslexic",
            font_size_base=28,
            letter_spacing=4
        )
        
        # Save
        result = settings.save()
        assert result is True
        assert os.path.exists(self.test_config_path)
        
        # Load
        loaded_settings = TypographySettings.load()
        
        # Restore original path
        TypographySettings.CONFIG_PATH = original_path
        
        # Verify loaded settings
        assert loaded_settings.font_family == "opendyslexic"
        assert loaded_settings.font_size_base == 28
        assert loaded_settings.letter_spacing == 4
    
    def test_save_creates_directory(self):
        """Test that save creates directory if needed."""
        settings = TypographySettings()
        
        # Use a nested path that doesn't exist
        nested_path = os.path.join(self.temp_dir, 'nested', 'config.json')
        settings.CONFIG_PATH = nested_path
        
        result = settings.save()
        
        assert result is True
        assert os.path.exists(nested_path)
    
    def test_load_nonexistent_file(self):
        """Test loading when config file doesn't exist."""
        # Use non-existent path
        settings = TypographySettings()
        settings.CONFIG_PATH = os.path.join(self.temp_dir, 'nonexistent.json')
        
        loaded = TypographySettings.load()
        
        # Should return default settings
        assert loaded.font_family == TypographySettings.FONT_DEFAULT
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON file."""
        # Create invalid JSON file
        with open(self.test_config_path, 'w') as f:
            f.write('{ invalid json }')
        
        settings = TypographySettings()
        settings.CONFIG_PATH = self.test_config_path
        
        loaded = TypographySettings.load()
        
        # Should return default settings
        assert loaded.font_family == TypographySettings.FONT_DEFAULT
    
    def test_load_nested_json(self):
        """Test loading nested JSON structure."""
        data = {
            'typography': {
                'font_family': 'opendyslexic',
                'font_size_base': 28
            }
        }
        
        with open(self.test_config_path, 'w') as f:
            json.dump(data, f)
        
        # Load with custom path by overriding in class
        original_path = TypographySettings.CONFIG_PATH
        TypographySettings.CONFIG_PATH = self.test_config_path
        
        loaded = TypographySettings.load()
        
        # Restore
        TypographySettings.CONFIG_PATH = original_path
        
        assert loaded.font_family == 'opendyslexic'
        assert loaded.font_size_base == 28
    
    def test_atomic_write(self):
        """Test that save uses atomic write (temp file + rename)."""
        settings = TypographySettings()
        settings.CONFIG_PATH = self.test_config_path
        
        # Save
        settings.save()
        
        # Temp file should not exist after successful save
        temp_path = self.test_config_path + ".tmp"
        assert not os.path.exists(temp_path)


class TestTypographySettingsIntegration:
    """Integration tests for TypographySettings."""
    
    def test_full_workflow(self):
        """Test complete workflow of save, load, modify, save."""
        temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(temp_dir, 'workflow_test.json')
        
        try:
            # Save initial settings
            settings1 = TypographySettings(
                font_family="default",
                font_size_base=24
            )
            settings1.CONFIG_PATH = config_path
            settings1.save()
            
            # Load settings
            original_path = TypographySettings.CONFIG_PATH
            TypographySettings.CONFIG_PATH = config_path
            settings2 = TypographySettings.load()
            assert settings2.font_family == "default"
            
            # Modify and save
            settings2.set_font_family("opendyslexic")
            settings2.save()
            
            # Load again and verify
            settings3 = TypographySettings.load()
            
            # Restore original path
            TypographySettings.CONFIG_PATH = original_path
            
            assert settings3.font_family == "opendyslexic"
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
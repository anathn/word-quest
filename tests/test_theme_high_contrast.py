"""
Theme Manager High Contrast Integration Tests (STORY-006-06)

Tests for ThemeManager's high contrast theme switching functionality.
"""

import pytest
import sys
import os
import json
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestThemeManagerHighContrastIntegration:
    """Test ThemeManager high contrast integration."""
    
    @pytest.fixture
    def temp_theme_config(self):
        """Create a temporary theme config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'theme.json')
            # Create empty config
            with open(config_path, 'w') as f:
                json.dump({}, f)
            yield config_path
            
    def test_theme_manager_initialization(self, temp_theme_config):
        """Test that ThemeManager initializes correctly."""
        from src.ui.theme import ThemeManager
        
        theme = ThemeManager(temp_theme_config)
        assert theme is not None
        assert theme.get_current_theme() == "default"
        assert theme.is_high_contrast() is False
    
    def test_enable_high_contrast(self, temp_theme_config):
        """Test enabling high contrast mode."""
        from src.ui.theme import ThemeManager
        
        theme = ThemeManager(temp_theme_config)
        result = theme.enable_high_contrast()
        
        assert result is True
        assert theme.get_current_theme() == "high_contrast"
        assert theme.is_high_contrast() is True
    
    def test_disable_high_contrast(self, temp_theme_config):
        """Test disabling high contrast mode."""
        from src.ui.theme import ThemeManager
        
        theme = ThemeManager(temp_theme_config)
        theme.enable_high_contrast()
        
        result = theme.disable_high_contrast()
        
        assert result is True
        assert theme.get_current_theme() == "default"
        assert theme.is_high_contrast() is False
    
    def test_toggle_high_contrast(self, temp_theme_config):
        """Test toggling high contrast mode."""
        from src.ui.theme import ThemeManager
        
        theme = ThemeManager(temp_theme_config)
        
        # Initially disabled
        assert theme.is_high_contrast() is False
        
        # Toggle on
        result = theme.toggle_high_contrast()
        assert result is True
        assert theme.is_high_contrast() is True
        
        # Toggle off
        result = theme.toggle_high_contrast()
        assert result is True
        assert theme.is_high_contrast() is False
    
    def test_set_theme_by_name(self, temp_theme_config):
        """Test setting theme by name."""
        from src.ui.theme import ThemeManager
        
        theme = ThemeManager(temp_theme_config)
        
        # Set to high contrast
        result = theme.set_theme("high_contrast")
        assert result is True
        assert theme.get_current_theme() == "high_contrast"
        
        # Set back to default
        result = theme.set_theme("default")
        assert result is True
        assert theme.get_current_theme() == "default"
    
    def test_set_unknown_theme(self, temp_theme_config):
        """Test setting unknown theme name."""
        from src.ui.theme import ThemeManager
        
        theme = ThemeManager(temp_theme_config)
        
        result = theme.set_theme("unknown_theme")
        assert result is False
        assert theme.get_current_theme() == "default"  # Should stay on default
    
    def test_get_color_high_contrast(self, temp_theme_config):
        """Test getting colors in high contrast mode."""
        from src.ui.theme import ThemeManager
        
        theme = ThemeManager(temp_theme_config)
        
        # In default mode, get a color
        default_color = theme.get_color("text_normal")
        
        # Switch to high contrast
        theme.enable_high_contrast()
        hc_color = theme.get_color("text_normal")
        
        # High contrast should have different (whiter) text color
        assert hc_color is not None
        assert len(hc_color) == 3  # RGB
        
        # Switch back
        theme.disable_high_contrast()
        restored_color = theme.get_color("text_normal")
        assert restored_color == default_color
    
    def test_high_contrast_text_is_white(self, temp_theme_config):
        """Test that high contrast text color is white."""
        from src.ui.theme import ThemeManager
        
        theme = ThemeManager(temp_theme_config)
        theme.enable_high_contrast()
        
        # Primary text should be white in high contrast
        text_color = theme.get_color("text_normal")
        assert text_color == (255, 255, 255), \
            f"High contrast text should be white, got {text_color}"
    
    def test_high_contrast_background_is_black(self, temp_theme_config):
        """Test that high contrast background is black."""
        from src.ui.theme import ThemeManager
        
        theme = ThemeManager(temp_theme_config)
        theme.enable_high_contrast()
        
        # Primary background should be black
        bg_color = theme.get_color("space_blue")
        assert bg_color == (0, 0, 0), \
            f"High contrast background should be black, got {bg_color}"
    
    def test_theme_switch_performance(self, temp_theme_config):
        """Test that theme switch is fast (<100ms)."""
        from src.ui.theme import ThemeManager
        import time
        
        theme = ThemeManager(temp_theme_config)
        
        # Measure time to switch themes
        start = time.perf_counter()
        theme.enable_high_contrast()
        theme.disable_high_contrast()
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        assert elapsed < 100, f"Theme switch should be <100ms, took {elapsed}ms"
    
    def test_multiple_enable_calls(self, temp_theme_config):
        """Test multiple enable_high_contrast calls."""
        from src.ui.theme import ThemeManager
        
        theme = ThemeManager(temp_theme_config)
        
        # Call enable multiple times
        assert theme.enable_high_contrast() is True
        assert theme.enable_high_contrast() is True
        assert theme.enable_high_contrast() is True
        
        assert theme.is_high_contrast() is True
    
    def test_multiple_disable_calls(self, temp_theme_config):
        """Test multiple disable_high_contrast calls."""
        from src.ui.theme import ThemeManager
        
        theme = ThemeManager(temp_theme_config)
        
        # Call disable multiple times (even when already disabled)
        assert theme.disable_high_contrast() is True
        assert theme.disable_high_contrast() is True
        assert theme.disable_high_contrast() is True
        
        assert theme.is_high_contrast() is False


class TestAccessibilitySettingsIntegration:
    """Test AccessibilitySettings integration with theme."""
    
    @pytest.fixture
    def temp_settings_dir(self):
        """Create a temporary directory for settings."""
        return tempfile.mkdtemp()
    
    def test_settings_manager_import(self):
        """Test that AccessibilitySettingsManager can be imported."""
        from src.components.accessibility_settings import AccessibilitySettingsManager
        assert AccessibilitySettingsManager is not None
    
    def test_settings_manager_creation(self, temp_settings_dir):
        """Test that settings manager can be created."""
        from src.components.accessibility_settings import AccessibilitySettingsManager
        
        manager = AccessibilitySettingsManager(data_dir=temp_settings_dir)
        assert manager is not None
        assert manager.settings is not None
    
    def test_settings_high_contrast_property(self, temp_settings_dir):
        """Test high contrast property on settings."""
        from src.components.accessibility_settings import AccessibilitySettingsManager
        
        manager = AccessibilitySettingsManager(data_dir=temp_settings_dir)
        
        # Initially disabled
        assert manager.is_high_contrast_enabled() is False
        assert manager.settings.high_contrast is False
    
    def test_settings_enable_high_contrast(self, temp_settings_dir):
        """Test enabling high contrast via settings manager."""
        from src.components.accessibility_settings import AccessibilitySettingsManager
        
        manager = AccessibilitySettingsManager(data_dir=temp_settings_dir)
        manager.enable_high_contrast()
        
        assert manager.is_high_contrast_enabled() is True
        assert manager.settings.high_contrast is True
    
    def test_settings_disable_high_contrast(self, temp_settings_dir):
        """Test disabling high contrast via settings manager."""
        from src.components.accessibility_settings import AccessibilitySettingsManager
        
        manager = AccessibilitySettingsManager(data_dir=temp_settings_dir)
        manager.enable_high_contrast()
        manager.disable_high_contrast()
        
        assert manager.is_high_contrast_enabled() is False
        assert manager.settings.high_contrast is False
    
    def test_settings_toggle_high_contrast(self, temp_settings_dir):
        """Test toggling high contrast via settings manager."""
        from src.components.accessibility_settings import AccessibilitySettingsManager
        
        manager = AccessibilitySettingsManager(data_dir=temp_settings_dir)
        
        # Toggle on
        manager.toggle_high_contrast()
        assert manager.is_high_contrast_enabled() is True
        
        # Toggle off
        manager.toggle_high_contrast()
        assert manager.is_high_contrast_enabled() is False
    
    def test_settings_serialization_with_high_contrast(self, temp_settings_dir):
        """Test settings serialization includes high contrast."""
        from src.components.accessibility_settings import AccessibilitySettingsManager
        
        manager = AccessibilitySettingsManager(data_dir=temp_settings_dir)
        manager.enable_high_contrast()
        
        # Get settings dict
        settings_dict = manager.settings.to_dict()
        
        assert 'high_contrast' in settings_dict
        assert settings_dict['high_contrast'] is True
    
    def test_settings_from_dict_with_high_contrast(self, temp_settings_dir):
        """Test settings deserialization handles high contrast."""
        from src.components.accessibility_settings import AccessibilitySettingsManager, AccessibilitySettings
        
        # Create settings from dict with high contrast enabled
        data = {
            'high_contrast': True,
            'captions_enabled': True,
            'tts_enabled': False,
        }
        
        settings = AccessibilitySettings.from_dict(data)
        assert settings.high_contrast is True


class TestHighContrastThemeColors:
    """Test that high contrast theme colors are valid."""
    
    def test_high_contrast_theme_import(self):
        """Test that high contrast theme module can be imported."""
        from src.ui import high_contrast_theme
        assert high_contrast_theme is not None
    
    def test_high_contrast_colors_exist(self):
        """Test that HIGH_CONTRAST_COLORS is defined."""
        from src.ui.high_contrast_theme import HIGH_CONTRAST_COLORS
        
        assert HIGH_CONTRAST_COLORS is not None
        assert len(HIGH_CONTRAST_COLORS) > 0
    
    def test_high_contrast_theme_mapping_exists(self):
        """Test that HIGH_CONTRAST_THEME mapping exists."""
        from src.ui.high_contrast_theme import HIGH_CONTRAST_THEME
        
        assert HIGH_CONTRAST_THEME is not None
        assert len(HIGH_CONTRAST_THEME) > 0
    
    def test_required_colors_present(self):
        """Test that required colors are present in high contrast theme."""
        from src.ui.high_contrast_theme import HIGH_CONTRAST_THEME
        
        required = [
            'space_blue',
            'text_normal',
            'text_muted',
            'ui_accent',
            'ui_success',
            'ui_error',
            'ui_border',
        ]
        
        for name in required:
            assert name in HIGH_CONTRAST_THEME, f"Missing color: {name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
High Contrast Theme Tests (STORY-006-06)

Tests for high contrast theme implementation including:
- Color definition validation
- Contrast ratio calculations  
- WCAG AAA compliance verification
- Theme switching functionality
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestHighContrastColors:
    """Test high contrast color definitions."""
    
    def test_high_contrast_colors_defined(self):
        """Test that all high contrast colors are defined."""
        from src.ui.high_contrast_theme import HIGH_CONTRAST_COLORS
        
        required_colors = [
            'background_primary',
            'background_secondary', 
            'background_tertiary',
            'text_primary',
            'text_secondary',
            'text_disabled',
            'button_default',
            'button_border',
            'button_hover',
            'button_pressed',
            'focus_indicator',
            'focus_glow',
            'correct',
            'incorrect',
            'warning',
            'error',
            'accent_primary',
            'accent_secondary',
            'highlight',
            'streak',
            'progress_fill',
            'progress_background',
            'progress_border',
            'border_default',
            'border_dim',
        ]
        
        for color_name in required_colors:
            assert color_name in HIGH_CONTRAST_COLORS, f"Missing color: {color_name}"
            assert HIGH_CONTRAST_COLORS[color_name].startswith('#'), \
                f"Color {color_name} should be hex string"
    
    def test_background_colors_are_dark(self):
        """Test that background colors are very dark."""
        from src.ui.high_contrast_theme import HIGH_CONTRAST_COLORS, hex_to_rgb
        
        # Primary background should be pure black
        bg_primary = HIGH_CONTRAST_COLORS['background_primary']
        rgb = hex_to_rgb(bg_primary)
        assert rgb == (0, 0, 0), "Primary background should be pure black"
        
        # Secondary and tertiary should be very dark
        bg_secondary = HIGH_CONTRAST_COLORS['background_secondary']
        rgb = hex_to_rgb(bg_secondary)
        assert all(c < 50 for c in rgb), "Secondary background should be very dark"
    
    def test_text_colors_are_light(self):
        """Test that text colors are light."""
        from src.ui.high_contrast_theme import HIGH_CONTRAST_COLORS, hex_to_rgb
        
        # Primary text should be white
        text_primary = HIGH_CONTRAST_COLORS['text_primary']
        rgb = hex_to_rgb(text_primary)
        assert rgb == (255, 255, 255), "Primary text should be white"
        
        # Secondary text should be very light
        text_secondary = HIGH_CONTRAST_COLORS['text_secondary']
        rgb = hex_to_rgb(text_secondary)
        assert all(c > 200 for c in rgb), "Secondary text should be very light"


class TestContrastRatios:
    """Test contrast ratio calculations."""
    
    def test_white_on_black_max_contrast(self):
        """Test that white on black has maximum contrast (21:1)."""
        from src.ui.high_contrast_theme import get_contrast_ratio
        
        ratio = get_contrast_ratio("#FFFFFF", "#000000")
        assert ratio == 21.0, f"White on black should be 21:1, got {ratio}"
    
    def test_contrast_ratio_calculation(self):
        """Test contrast ratio calculation is correct."""
        from src.ui.high_contrast_theme import get_contrast_ratio
        
        # White on #333333 should be ~12.6:1 (verified calculation)
        ratio = get_contrast_ratio("#FFFFFF", "#333333")
        assert 12.0 < ratio < 13.5, f"White on #333333 should be ~12.6:1, got {ratio}"
        
        # White on #1a1a1a should be ~17.4:1  
        ratio = get_contrast_ratio("#FFFFFF", "#1a1a1a")
        assert 16.0 < ratio < 18.5, f"White on #1a1a1a should be ~17.4:1, got {ratio}"
    
    def test_validate_contrast_function(self):
        """Test contrast validation function."""
        from src.ui.high_contrast_theme import validate_contrast
        
        # White on black passes AAA
        assert validate_contrast("#FFFFFF", "#000000") is True
        
        # Light yellow on black passes AAA  
        assert validate_contrast("#FFFFE0", "#000000") is True
        
        # Medium gray on black still passes AAA (999999 is ~5.9:1, needs < 999999)
        assert validate_contrast("#999999", "#000000") is True
        
        # Dark gray on black does NOT pass AAA
        assert validate_contrast("#555555", "#000000") is False


class TestWCAGAAACompliance:
    """Test WCAG 2.1 AAA compliance."""
    
    def test_all_text_colors_pass_aaa(self):
        """Test that all text colors pass AAA on primary background."""
        from src.ui.high_contrast_theme import HIGH_CONTRAST_COLORS, validate_contrast
        
        background = HIGH_CONTRAST_COLORS['background_primary']  # Black
        
        # Test text colors
        text_colors = ['text_primary', 'text_secondary']
        
        for color_name in text_colors:
            color = HIGH_CONTRAST_COLORS[color_name]
            passes = validate_contrast(color, background)
            assert passes, f"{color_name} should pass AAA on background"
    
    def test_primary_contrast_ratio(self):
        """Test primary text contrast ratio."""
        from src.ui.high_contrast_theme import get_contrast_ratio, HIGH_CONTRAST_COLORS
        
        text = HIGH_CONTRAST_COLORS['text_primary']
        bg = HIGH_CONTRAST_COLORS['background_primary']
        
        ratio = get_contrast_ratio(text, bg)
        assert ratio >= 7.0, f"Primary text should meet AAA (7:1), got {ratio}:1"
        assert ratio == 21.0, f"White on black should be 21:1, got {ratio}"
    
    def test_secondary_contrast_ratio(self):
        """Test secondary text contrast ratio."""
        from src.ui.high_contrast_theme import get_contrast_ratio, HIGH_CONTRAST_COLORS
        
        text = HIGH_CONTRAST_COLORS['text_secondary']
        bg = HIGH_CONTRAST_COLORS['background_primary']
        
        ratio = get_contrast_ratio(text, bg)
        assert ratio >= 7.0, f"Secondary text should meet AAA (7:1), got {ratio}:1"


class TestHexToRgb:
    """Test hex to RGB conversion."""
    
    def test_hex_to_rgb_white(self):
        """Test white color conversion."""
        from src.ui.high_contrast_theme import hex_to_rgb
        
        rgb = hex_to_rgb("#FFFFFF")
        assert rgb == (255, 255, 255)
    
    def test_hex_to_rgb_black(self):
        """Test black color conversion."""
        from src.ui.high_contrast_theme import hex_to_rgb
        
        rgb = hex_to_rgb("#000000")
        assert rgb == (0, 0, 0)
    
    def test_hex_to_rgb_various(self):
        """Test various color conversions."""
        from src.ui.high_contrast_theme import hex_to_rgb
        
        test_cases = [
            ("#FF0000", (255, 0, 0)),
            ("#00FF00", (0, 255, 0)),
            ("#0000FF", (0, 0, 255)),
            ("#FFFF00", (255, 255, 0)),
            ("#FFA500", (255, 165, 0)),
        ]
        
        for hex_color, expected_rgb in test_cases:
            rgb = hex_to_rgb(hex_color)
            assert rgb == expected_rgb, f"{hex_color} should be {expected_rgb}, got {rgb}"
    
    def test_hex_to_rgb_case_insensitive(self):
        """Test that hex conversion is case insensitive."""
        from src.ui.high_contrast_theme import hex_to_rgb
        
        assert hex_to_rgb("#FF0000") == hex_to_rgb("#ff0000")
        assert hex_to_rgb("#aabbcc") == hex_to_rgb("#AABBCC")


class TestHighContrastThemeIntegration:
    """Test high contrast theme integration."""
    
    def test_high_contrast_theme_exists(self):
        """Test that HIGH_CONTRAST_THEME mapping exists."""
        from src.ui.high_contrast_theme import HIGH_CONTRAST_THEME
        
        assert HIGH_CONTRAST_THEME is not None
        assert len(HIGH_CONTRAST_THEME) > 0
    
    def test_theme_mapping_compatibility(self):
        """Test that theme mapping includes required names."""
        from src.ui.high_contrast_theme import HIGH_CONTRAST_THEME
        
        # Check for compatibility with ThemeManager color names
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
            assert name in HIGH_CONTRAST_THEME, f"Missing theme mapping: {name}"


class TestThemeManagerHighContrast:
    """Test ThemeManager high contrast functionality."""
    
    def test_theme_manager_imports(self):
        """Test that ThemeManager can be imported."""
        from src.ui.theme import ThemeManager
        assert ThemeManager is not None
    
    def test_theme_manager_constants(self):
        """Test that theme constants are defined."""
        from src.ui.theme import ThemeManager
        
        assert hasattr(ThemeManager, 'THEME_DEFAULT')
        assert hasattr(ThemeManager, 'THEME_HIGH_CONTRAST')
        assert ThemeManager.THEME_DEFAULT == "default"
        assert ThemeManager.THEME_HIGH_CONTRAST == "high_contrast"
    
    def test_theme_creation(self):
        """Test that ThemeManager can be created."""
        from src.ui.theme import ThemeManager
        
        # Create with unique path to avoid conflicts
        import tempfile
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, 'theme.json')
            
            # Create empty config
            with open(config_path, 'w') as f:
                json.dump({}, f)
            
            theme = ThemeManager(config_path)
            assert theme is not None
            assert theme.get_current_theme() == "default"
    
    def test_high_contrast_methods_exist(self):
        """Test that high contrast methods exist on ThemeManager."""
        from src.ui.theme import ThemeManager
        
        # Check methods exist (don't actually call them to avoid init overhead)
        assert hasattr(ThemeManager, 'enable_high_contrast')
        assert hasattr(ThemeManager, 'disable_high_contrast')
        assert hasattr(ThemeManager, 'toggle_high_contrast')
        assert hasattr(ThemeManager, 'is_high_contrast')
        assert hasattr(ThemeManager, 'get_current_theme')


class TestAccessibilitySettings:
    """Test AccessibilitySettings dataclass."""
    
    def test_settings_creation(self):
        """Test creation of accessibility settings."""
        from src.components.accessibility_settings import AccessibilitySettings
        
        settings = AccessibilitySettings()
        assert settings.high_contrast is False
        assert settings.captions_enabled is True
        assert settings.tts_enabled is True
    
    def test_settings_default_values(self):
        """Test default values."""
        from src.components.accessibility_settings import AccessibilitySettings
        
        settings = AccessibilitySettings()
        
        # Check defaults
        assert settings.caption_font_size == 28
        assert settings.tts_speed == 1.0
        assert settings.keyboard_navigation is True
        assert settings.opendyslexic_font is False
    
    def test_settings_toggle_high_contrast(self):
        """Test high contrast toggle."""
        from src.components.accessibility_settings import AccessibilitySettings
        
        settings = AccessibilitySettings()
        
        # Initially false
        assert settings.high_contrast is False
        
        # Toggle on
        settings.toggle_high_contrast()
        assert settings.high_contrast is True
        
        # Toggle off
        settings.toggle_high_contrast()
        assert settings.high_contrast is False
    
    def test_settings_enable_disable_high_contrast(self):
        """Test enable/disable high contrast."""
        from src.components.accessibility_settings import AccessibilitySettings
        
        settings = AccessibilitySettings()
        
        settings.enable_high_contrast()
        assert settings.high_contrast is True
        
        settings.disable_high_contrast()
        assert settings.high_contrast is False
    
    def test_settings_serialization(self):
        """Test serialization to/from dict."""
        from src.components.accessibility_settings import AccessibilitySettings
        
        settings = AccessibilitySettings()
        settings.high_contrast = True
        settings.caption_font_size = 32
        
        # Serialize
        data = settings.to_dict()
        assert data['high_contrast'] is True
        assert data['caption_font_size'] == 32
        
        # Deserialize
        new_settings = AccessibilitySettings.from_dict(data)
        assert new_settings.high_contrast is True
        assert new_settings.caption_font_size == 32
    
    def test_settings_validation(self):
        """Test setting validation."""
        from src.components.accessibility_settings import AccessibilitySettings
        
        # Font size out of range
        settings = AccessibilitySettings.from_dict({
            'caption_font_size': 100
        })
        assert settings.caption_font_size == 48  # Clamped to max
        
        settings = AccessibilitySettings.from_dict({
            'caption_font_size': 10
        })
        assert settings.caption_font_size == 18  # Clamped to min
        
        # TTS speed out of range
        settings = AccessibilitySettings.from_dict({
            'tts_speed': 3.0
        })
        assert settings.tts_speed == 2.0  # Clamped to max
        
        settings = AccessibilitySettings.from_dict({
            'tts_speed': 0.2
        })
        assert settings.tts_speed == 0.5  # Clamped to min


class TestAccessibilitySettingsManager:
    """Test AccessibilitySettingsManager."""
    
    def test_manager_creation(self):
        """Test settings manager creation."""
        from src.components.accessibility_settings import AccessibilitySettingsManager
        
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AccessibilitySettingsManager(data_dir=tmpdir)
            assert manager is not None
            assert manager.settings is not None
    
    def test_high_contrast_toggle_manager(self):
        """Test high contrast toggle via manager."""
        from src.components.accessibility_settings import AccessibilitySettingsManager
        
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AccessibilitySettingsManager(data_dir=tmpdir)
            
            # Initially disabled
            assert manager.is_high_contrast_enabled() is False
            
            # Enable
            manager.enable_high_contrast()
            assert manager.is_high_contrast_enabled() is True
            
            # Disable
            manager.disable_high_contrast()
            assert manager.is_high_contrast_enabled() is False
    
    def test_settings_persistence(self):
        """Test that settings are persisted to file."""
        from src.components.accessibility_settings import AccessibilitySettingsManager
        
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = AccessibilitySettingsManager(data_dir=tmpdir)
            manager.enable_high_contrast()
            
            # Save settings
            result = manager.save_settings()
            assert result is True
            
            # Verify file exists
            assert os.path.exists(manager.settings_file)
            
            # Create new manager and load
            manager2 = AccessibilitySettingsManager(data_dir=tmpdir)
            assert manager2.is_high_contrast_enabled() is True


class TestContrastRatiosReference:
    """Test contrast ratio reference values."""
    
    def test_contrast_ratios_defined(self):
        """Test that contrast ratios are defined."""
        from src.ui.high_contrast_theme import CONTRAST_RATIOS
        
        assert 'white_on_black' in CONTRAST_RATIOS
        assert CONTRAST_RATIOS['white_on_black'] == 21.0
    
    def test_wcag_compliance_defined(self):
        """Test that WCAG compliance info is defined."""
        from src.ui.high_contrast_theme import WCAG_COMPLIANCE
        
        assert 'normal_text_minimum' in WCAG_COMPLIANCE
        assert 'actual_text_contrast' in WCAG_COMPLIANCE


class TestGenerationFunctions:
    """Test theme generation functions."""
    
    def test_get_color_rgb(self):
        """Test get_color_rgb function."""
        from src.ui.high_contrast_theme import get_color_rgb
        
        rgb = get_color_rgb('text_primary')
        assert rgb == (255, 255, 255)
        
        rgb = get_color_rgb('background_primary')
        assert rgb == (0, 0, 0)
    
    def test_generate_theme_report(self):
        """Test theme report generation."""
        from src.ui.high_contrast_theme import generate_theme_report
        
        report = generate_theme_report()
        assert "HIGH CONTRAST THEME" in report
        assert "WCAG" in report
        assert "AAA" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
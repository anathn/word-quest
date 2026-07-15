"""
Unit tests for theme manager.

Tests for src/ui/theme.py
"""

import pytest
import os
import json
import pygame
from src.ui.theme import (
    ThemeManager, get_theme, reset_theme,
    SPACE_BLUE, STAR_WHITE, STAR_PALE_YELLOW,
    PLANET_1, PLANET_2, PLANET_3, PLANET_4, PLANET_5
)


class TestThemeManager:
    """Test cases for ThemeManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        reset_theme()
        self.test_config_path = "data/test_theme_config.json"
        self.theme = ThemeManager(self.test_config_path)
    
    def teardown_method(self):
        """Clean up after tests."""
        reset_theme()
        # Clean up test config file
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
    
    def test_initialization_with_default_config(self):
        """Test that theme manager initializes with default colors."""
        assert self.theme is not None
        assert self.theme.get_color("space_blue") == SPACE_BLUE
    
    def test_color_retrieval_returns_correct_rgb_values(self):
        """Test that color retrieval returns correct RGB tuples."""
        assert self.theme.get_color("space_blue") == (26, 26, 62)
        assert self.theme.get_color("star_white") == (255, 255, 255)
        assert self.theme.get_color("planet_1") == (255, 152, 0)
    
    def test_default_colors_exist_for_all_required_elements(self):
        """Test that all required theme colors are defined."""
        required_colors = [
            "space_blue", "star_white", "star_pale_yellow",
            "planet_1", "planet_2", "planet_3", "planet_4", "planet_5",
            "text_normal", "text_muted", "ui_accent", "ui_success",
            "ui_warning", "ui_error", "ui_border"
        ]
        
        for color_name in required_colors:
            color = self.theme.get_color(color_name)
            assert isinstance(color, tuple)
            assert len(color) == 3
            assert all(0 <= c <= 255 for c in color)
    
    def test_config_loading_from_json(self):
        """Test that theme config can be loaded from JSON file."""
        # Create test config with custom colors
        custom_config = {
            "colors": {
                "space_blue": [30, 30, 70]
            }
        }
        
        os.makedirs("data", exist_ok=True)
        with open(self.test_config_path, 'w') as f:
            json.dump(custom_config, f)
        
        theme = ThemeManager(self.test_config_path)
        assert theme.get_color("space_blue") == (30, 30, 70)
    
    def test_set_color_updates_theme(self):
        """Test that setting a color updates the theme."""
        new_color = (100, 150, 200)
        self.theme.set_color("custom_color", new_color)
        assert self.theme.get_color("custom_color") == new_color
    
    def test_get_planet_color_returns_correct_color(self):
        """Test planet color retrieval for all planet types."""
        assert self.theme.get_planet_color(1) == PLANET_1
        assert self.theme.get_planet_color(2) == PLANET_2
        assert self.theme.get_planet_color(3) == PLANET_3
        assert self.theme.get_planet_color(4) == PLANET_4
        assert self.theme.get_planet_color(5) == PLANET_5
    
    def test_get_planet_color_handles_invalid_number(self):
        """Test that invalid planet numbers return default color."""
        # Should not raise exception
        color = self.theme.get_planet_color(0)
        assert isinstance(color, tuple)
        
        color = self.theme.get_planet_color(6)
        assert isinstance(color, tuple)
    
    def test_get_colors_returns_all_colors(self):
        """Test that get_colors returns all theme colors."""
        colors = self.theme.get_colors()
        assert isinstance(colors, dict)
        assert "space_blue" in colors
        assert "planet_1" in colors
    
    def test_font_creation(self):
        """Test that fonts are created correctly."""
        pygame.init()
        
        font = self.theme.get_font(24)
        assert font is not None
        
        large_font = self.theme.get_font_large()
        assert large_font is not None
        
        medium_font = self.theme.get_font_medium()
        assert medium_font is not None
        
        small_font = self.theme.get_font_small()
        assert small_font is not None
        
        pygame.quit()
    
    def test_save_config_creates_file(self):
        """Test that save_config creates the config file."""
        self.theme.save_config()
        assert os.path.exists(self.test_config_path)
    
    def test_save_config_saves_valid_json(self):
        """Test that save_config saves valid JSON."""
        self.theme.save_config()
        
        with open(self.test_config_path, 'r') as f:
            config = json.load(f)
        
        assert "colors" in config
        assert isinstance(config["colors"], dict)


class TestGetTheme:
    """Test cases for global theme functions."""
    
    def teardown_method(self):
        """Clean up after tests."""
        reset_theme()
    
    def test_get_theme_returns_manager(self):
        """Test that get_theme returns a ThemeManager instance."""
        theme = get_theme()
        assert theme is not None
        assert isinstance(theme, ThemeManager)
    
    def test_get_theme_returns_singleton(self):
        """Test that get_theme returns the same instance."""
        theme1 = get_theme()
        theme2 = get_theme()
        assert theme1 is theme2
    
    def test_reset_theme_clears_instance(self):
        """Test that reset_theme clears the global instance."""
        theme1 = get_theme()
        reset_theme()
        theme2 = get_theme()
        assert theme1 is not theme2


class TestColorConstants:
    """Test cases for color constant definitions."""
    
    def test_space_blue_is_deep_blue(self):
        """Test that space blue is the correct deep blue color."""
        assert SPACE_BLUE == (26, 26, 62)
    
    def test_star_colors_are_correct(self):
        """Test that star colors are white and pale yellow."""
        assert STAR_WHITE == (255, 255, 255)
        assert STAR_PALE_YELLOW == (255, 255, 224)
    
    def test_planet_colors_are_color_blind_safe(self):
        """Test that planet colors use a color-blind safe palette."""
        # Orange
        assert PLANET_1 == (255, 152, 0)
        # Blue
        assert PLANET_2 == (33, 150, 243)
        # Purple
        assert PLANET_3 == (156, 39, 176)
        # Green
        assert PLANET_4 == (76, 175, 80)
        # Red (color-blind safe alternative)
        assert PLANET_5 == (244, 67, 54)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
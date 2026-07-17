"""
Unit Tests for Color Picker (STORY-004-05)

Tests for color selection UI component and rocket color functionality.
"""

import pytest
import pygame
import os
import sys

# Set TESTING environment variable and headless display before importing project code
os.environ["TESTING"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.ui.color_picker import (
    ColorPicker,
    ROCKET_COLOR_PRESETS,
    DEFAULT_ROCKET_COLOR,
    hex_to_rgb,
    rgb_to_hex,
    create_color_picker
)


class TestHexToRgb:
    """Tests for hex_to_rgb conversion function."""
    
    def test_full_red(self):
        assert hex_to_rgb("#FF0000") == (255, 0, 0)
    
    def test_full_green(self):
        assert hex_to_rgb("#00FF00") == (0, 255, 0)
    
    def test_full_blue(self):
        assert hex_to_rgb("#0000FF") == (0, 0, 255)
    
    def test_white(self):
        assert hex_to_rgb("#FFFFFF") == (255, 255, 255)
    
    def test_black(self):
        assert hex_to_rgb("#000000") == (0, 0, 0)
    
    def test_presets(self):
        """Test all preset colors."""
        expected = [
            ("#FF4444", (255, 68, 68)),
            ("#4488FF", (68, 136, 255)),
            ("#44FF44", (68, 255, 68)),
            ("#FFD700", (255, 215, 0)),
            ("#AA44FF", (170, 68, 255)),
            ("#FF8844", (255, 136, 68)),
            ("#FF44AA", (255, 68, 170)),
            ("#44FFFF", (68, 255, 255)),
        ]
        for hex_color, expected_rgb in expected:
            assert hex_to_rgb(hex_color) == expected_rgb


class TestRgbToHex:
    """Tests for rgb_to_hex conversion function."""
    
    def test_full_red(self):
        assert rgb_to_hex((255, 0, 0)) == "#ff0000"
    
    def test_full_green(self):
        assert rgb_to_hex((0, 255, 0)) == "#00ff00"
    
    def test_full_blue(self):
        assert rgb_to_hex((0, 0, 255)) == "#0000ff"
    
    def test_white(self):
        assert rgb_to_hex((255, 255, 255)) == "#ffffff"
    
    def test_black(self):
        assert rgb_to_hex((0, 0, 0)) == "#000000"
    
    def test_roundtrip(self):
        """Test that hex -> rgb -> hex produces same result."""
        test_colors = ["#FF4444", "#4488FF", "#FFD700", "#AA44FF"]
        for hex_color in test_colors:
            rgb = hex_to_rgb(hex_color)
            result_hex = rgb_to_hex(rgb)
            assert result_hex.upper() == hex_color.upper()


class TestColorPicker:
    """Tests for ColorPicker component."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame for testing."""
        pygame.init()
        yield
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create a test screen."""
        return pygame.display.set_mode((800, 600))
    
    @pytest.fixture
    def color_picker(self, screen):
        """Create a ColorPicker instance."""
        return ColorPicker(screen, 100, 100)
    
    def test_initialization(self, color_picker):
        """Test that ColorPicker initializes with default state."""
        assert color_picker.selected_color == DEFAULT_ROCKET_COLOR
        assert len(color_picker.colors) == 8
        assert color_picker.position == (100, 100)
    
    def test_initial_default_color(self):
        """Test that default color is blue."""
        assert DEFAULT_ROCKET_COLOR == "#4488FF"
    
    def test_preset_count(self):
        """Test that there are 8 preset colors."""
        assert len(ROCKET_COLOR_PRESETS) == 8
    
    def test_select_color(self, color_picker):
        """Test color selection."""
        new_color = "#FF4444"
        color_picker.select_color(new_color)
        assert color_picker.selected_color == new_color
    
    def test_select_color_triggers_callback(self, color_picker):
        """Test that callback is triggered on color selection."""
        selected_colors = []
        color_picker.on_color_selected = lambda c: selected_colors.append(c)
        
        color_picker.select_color("#FF0000")
        
        assert len(selected_colors) == 1
        assert selected_colors[0] == "#FF0000"
    
    def test_get_selected_color(self, color_picker):
        """Test getting selected color."""
        assert color_picker.get_selected_color() == DEFAULT_ROCKET_COLOR
        
        color_picker.select_color("#FF0000")
        assert color_picker.get_selected_color() == "#FF0000"
    
    def test_get_swatch_rect(self, color_picker):
        """Test swatch positioning calculations."""
        # First swatch (index 0)
        rect0 = color_picker._get_swatch_rect(0)
        assert rect0.x == 100
        assert rect0.y == 100
        
        # Second swatch (index 1)
        rect1 = color_picker._get_swatch_rect(1)
        assert rect1.x == 170  # 100 + 60 + 10
        assert rect1.y == 100
        
        # Fifth swatch (index 4, second row)
        rect4 = color_picker._get_swatch_rect(4)
        assert rect4.x == 100  # Back to first column
        assert rect4.y == 170  # 100 + 60 + 10
    
    def test_get_bounds(self, color_picker):
        """Test bounding rectangle calculation."""
        bounds = color_picker.get_bounds()
        
        # 4 columns * (60 width + 10 spacing) - 10 = 230 total width
        expected_width = 4 * (60 + 10) - 10
        assert bounds.width == expected_width
        
        # 2 rows * (60 height + 10 spacing) - 10 = 130 total height
        expected_height = 2 * (60 + 10) - 10
        assert bounds.height == expected_height
    
    def test_hover_detection(self, color_picker, screen):
        """Test mouse hover detection."""
        # Position on first swatch
        pos_on_first = (130, 130)  # Inside first swatch
        
        # Create fake mouse motion event
        event = pygame.event.Event(pygame.MOUSEMOTION, pos=pos_on_first, rel=(0, 0))
        color_picker.handle_event(event)
        
        # Check hover index
        assert color_picker._get_hover_index(pos_on_first) == 0
        
        # Position outside all swatches
        pos_outside = (500, 500)
        assert color_picker._get_hover_index(pos_outside) is None
    
    def test_click_selection(self, color_picker, screen):
        """Test mouse click color selection."""
        # Position on second swatch (index 1)
        pos_on_second = (200, 130)
        
        # Create fake mouse click event
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos_on_second, button=1)
        result = color_picker.handle_event(event)
        
        # Event should be handled
        assert result is True
        
        # Color should be updated to second preset
        expected_color = ROCKET_COLOR_PRESETS[1]["hex"]
        assert color_picker.selected_color == expected_color
    
    def test_all_colors_selectable(self, color_picker):
        """Test that all preset colors can be selected programmatically."""
        for color_data in ROCKET_COLOR_PRESETS:
            color_picker.select_color(color_data["hex"])
            assert color_picker.selected_color == color_data["hex"]
    
    def test_color_has_name(self):
        """Test that all color presets have names."""
        for color_data in ROCKET_COLOR_PRESETS:
            assert "name" in color_data
            assert len(color_data["name"]) > 0
            assert "hex" in color_data
            assert "rgb" in color_data
    
    def test_rgb_values_valid(self):
        """Test that RGB values are in valid range."""
        for color_data in ROCKET_COLOR_PRESETS:
            rgb = color_data["rgb"]
            assert 0 <= rgb[0] <= 255
            assert 0 <= rgb[1] <= 255
            assert 0 <= rgb[2] <= 255


class TestCreateColorPicker:
    """Tests for factory function."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame for testing."""
        pygame.init()
        yield
    
    def test_factory_creates_instance(self, pygame_init):
        """Test that factory function creates ColorPicker."""
        screen = pygame.display.set_mode((800, 600))
        picker = create_color_picker(screen, 50, 50)
        
        assert isinstance(picker, ColorPicker)
        assert picker.position == (50, 50)


class TestRocketColorPersistence:
    """Test rocket color in profile context."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame for testing."""
        pygame.init()
        yield
    
    @pytest.fixture
    def temp_profiles_file(self, tmp_path):
        """Create temporary profiles file."""
        import json
        profiles_file = tmp_path / "profiles.json"
        profiles_file.write_text(json.dumps({"profiles": []}))
        return str(profiles_file)
    
    def test_default_color_valid_format(self):
        """Test that default color is valid hex format."""
        import re
        assert re.match(r'^#[A-Fa-f0-9]{6}$', DEFAULT_ROCKET_COLOR)
    
    def test_preset_colors_valid_format(self):
        """Test that all preset colors are valid hex format."""
        import re
        for color_data in ROCKET_COLOR_PRESETS:
            assert re.match(r'^#[A-Fa-f0-9]{6}$', color_data["hex"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Unit Tests for Rocket Renderer (STORY-004-05)

Tests for rocket color tinting functionality.
"""

import pytest
import pygame
import os
import sys

# Set TESTING environment variable
os.environ["TESTING"] = "1"

from src.components.rocket_renderer import (
    RocketRenderer,
    DEFAULT_ROCKET_COLOR,
    create_rocket_renderer
)


class TestHexToRgb:
    """Tests for hex to RGB conversion in rocket renderer."""
    
    @pytest.fixture
    def renderer(self):
        """Create a RocketRenderer instance for testing."""
        pygame.init()
        screen = pygame.display.set_mode((100, 100))
        renderer = RocketRenderer(screen)
        yield renderer
        pygame.quit()
    
    def test_hex_to_rgb_basic(self, renderer):
        """Test hex to RGB conversion."""
        assert renderer._hex_to_rgb("#FF0000") == (255, 0, 0)
        assert renderer._hex_to_rgb("#00FF00") == (0, 255, 0)
        assert renderer._hex_to_rgb("#0000FF") == (0, 0, 255)
    
    def test_hex_to_rgb_preset_colors(self, renderer):
        """Test conversion of preset colors."""
        test_cases = [
            ("#FF4444", (255, 68, 68)),
            ("#4488FF", (68, 136, 255)),
            ("#FFD700", (255, 215, 0)),
        ]
        for hex_color, expected_rgb in test_cases:
            assert renderer._hex_to_rgb(hex_color) == expected_rgb


class TestRocketRenderer:
    """Tests for RocketRenderer component."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame for testing."""
        pygame.init()
        yield
        pygame.quit()
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create test screen."""
        return pygame.display.set_mode((800, 600))
    
    @pytest.fixture
    def renderer(self, screen):
        """Create RocketRenderer instance."""
        return RocketRenderer(screen)
    
    def test_initialization(self, renderer):
        """Test that renderer initializes with default color."""
        assert renderer.current_color == DEFAULT_ROCKET_COLOR
        assert renderer.base_sprite is not None
        assert renderer.tinted_sprite is not None
    
    def test_default_color(self):
        """Test default color is blue."""
        assert DEFAULT_ROCKET_COLOR == "#4488FF"
    
    def test_set_color(self, renderer):
        """Test changing rocket color."""
        new_color = "#FF4444"
        renderer.set_color(new_color)
        assert renderer.current_color == new_color
    
    def test_set_color_updates_sprite_cache(self, renderer):
        """Test that changing color updates the sprite cache."""
        original_sprite = renderer.tinted_sprite
        renderer.set_color("#FF0000")
        assert renderer.tinted_sprite is not None
        assert renderer.tinted_sprite != original_sprite
        
    def test_get_color(self, renderer):
        """Test getting current color."""
        assert renderer.get_color() == DEFAULT_ROCKET_COLOR
        
        renderer.set_color("#FF0000")
        assert renderer.get_color() == "#FF0000"
    
    def test_set_color_idempotent(self, renderer):
        """Test setting same color doesn't cause errors."""
        renderer.set_color("#FF4444")
        assert renderer.get_color() == "#FF4444"
        
        renderer.set_color("#FF4444")  # Same color
        assert renderer.get_color() == "#FF4444"
    
    def test_all_presets_colors(self, renderer):
        """Test all preset colors can be applied."""
        from src.ui.color_picker import ROCKET_COLOR_PRESETS
        
        for color_data in ROCKET_COLOR_PRESETS:
            renderer.set_color(color_data["hex"])
            assert renderer.get_color() == color_data["hex"]
            assert renderer.tinted_sprite is not None
    
    def test_render(self, renderer):
        """Test rendering doesn't crash."""
        screen = renderer.screen
        screen.fill((0, 0, 0))  # Clear screen
        
        renderer.render((100, 100))
        
        # Just verify no crash occurred
        assert True
    
    def test_render_with_position(self, renderer):
        """Test render_with_position."""
        renderer.render_with_position(200, 300)
        assert True
    
    def test_get_sprite_bounds(self, renderer):
        """Test getting sprite dimensions."""
        width, height = renderer.get_sprite_bounds()
        assert width > 0
        assert height > 0
    
    def test_get_width(self, renderer):
        """Test getting sprite width."""
        width = renderer.get_width()
        assert width > 0
    
    def test_get_height(self, renderer):
        """Test getting sprite height."""
        height = renderer.get_height()
        assert height > 0
    
    def test_tint_preserves_transparency(self, renderer):
        """Test that tinting preserves alpha channel."""
        original_transparent = renderer.base_sprite.get_at((0, 0)).a
        
        renderer.set_color("#FF4444")
        tinted_transparent = renderer.tinted_sprite.get_at((0, 0)).a
        
        # Both should have same transparency at corner (likely transparent)
        assert original_transparent == tinted_transparent
    
    def test_color_change_performance(self, renderer):
        """Test that color change is fast enough."""
        import time
        
        start = time.time()
        for _ in range(10):
            renderer.set_color("#FF4444")
        elapsed = time.time() - start
        
        # 10 color changes should take < 100ms (average <10ms each)
        assert elapsed < 0.1


class TestTinting:
    """Tests for color tinting logic."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame."""
        pygame.init()
        yield
        pygame.quit()
    
    @pytest.fixture
    def renderer(self):
        """Create renderer with small test screen."""
        pygame.init()
        screen = pygame.display.set_mode((100, 100))
        return RocketRenderer(screen)
    
    def test_white_tint_unchanged(self, renderer):
        """Test that white tint doesn't change sprite."""
        # Create original sprite
        original_pixel = renderer.base_sprite.get_at((10, 10))
        
        # Apply white tint
        renderer.set_color("#FFFFFF")
        white_tinted = renderer.tinted_sprite.get_at((10, 10))
        
        # Should be very similar (might have slight rounding differences)
        assert abs(original_pixel.r - white_tinted.r) <= 1
        assert abs(original_pixel.g - white_tinted.g) <= 1
        assert abs(original_pixel.b - white_tinted.b) <= 1
    
    def test_dark_tint_reduces_brightness(self, renderer):
        """Test that dark tint reduces brightness."""
        renderer.set_color("#000000")  # Black
        
        # Any non-transparent pixel should become dark
        for x in range(renderer.base_sprite.get_width()):
            for y in range(renderer.base_sprite.get_height()):
                pixel = renderer.tinted_sprite.get_at((x, y))
                if pixel.a > 0:
                    # With black tint, all RGB should be near 0
                    assert pixel.r < 10
                    assert pixel.g < 10
                    assert pixel.b < 10
                    break
            else:
                continue
            break


class TestCreateRocketRenderer:
    """Tests for factory function."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame."""
        pygame.init()
        yield
        pygame.quit()
    
    def test_factory_creates_instance(self, pygame_init):
        """Test factory function creates renderer."""
        screen = pygame.display.set_mode((200, 200))
        renderer = create_rocket_renderer(screen)
        
        assert isinstance(renderer, RocketRenderer)
    
    def test_factory_with_color(self, pygame_init):
        """Test factory function with initial color."""
        screen = pygame.display.set_mode((200, 200))
        renderer = create_rocket_renderer(screen, color="#FF4444")
        
        assert renderer.get_color() == "#FF4444"
    
    def test_integration_with_profile(self, tmp_path):
        """Test integration with student profile flow."""
        import json
        import sys
        from datetime import datetime
        sys.path.insert(0, os.getcwd())
        
        from src.models.student_profile import StudentProfile
        from src.ui.color_picker import DEFAULT_ROCKET_COLOR
        
        # Test that profile can store rocket color
        profile = StudentProfile(
            id="test-id",
            name="Test Student",
            avatar_id="astronaut",
            created_date=datetime.now(),
            rocket_color="#FF4444"
        )
        
        # Serialize and deserialize
        data = profile.to_dict()
        assert data["rocket_color"] == "#FF4444"
        
        # Test default when not specified
        profile2_dict = {
            "id": "test-id-2",
            "name": "Test 2",
            "avatar_id": "rocket",
            "created_date": "2026-01-01T00:00:00",
        }
        profile2 = StudentProfile.from_dict(profile2_dict)
        assert profile2.rocket_color == DEFAULT_ROCKET_COLOR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
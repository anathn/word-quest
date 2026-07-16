"""
Unit Tests for Rocket Sprite (STORY-005-02)

Tests for rocket rendering, color customization, and rotation.
"""

import pytest
import pygame
import os
import sys

# Set TESTING environment variable and headless display before importing
os.environ["TESTING"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.ui.rocket_sprite import RocketSprite, create_rocket_sprite
from src.models.rocket_config import ROCKET_COLOR_PRESETS


class TestRocketSprite:
    """Tests for RocketSprite class."""
    
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
    def rocket(self):
        """Create default rocket sprite."""
        return RocketSprite()
    
    def test_initialization(self):
        """Test rocket initializes with default values."""
        rocket = RocketSprite()
        assert rocket.get_color() == (255, 255, 255)  # White default
        assert rocket.get_width() == 64
        assert rocket.get_height() == 96
        assert rocket.cached_surface is not None
    
    def test_custom_color_initialization(self):
        """Test rocket with custom color."""
        rocket = RocketSprite(color=(244, 67, 54))  # Red
        assert rocket.get_color() == (244, 67, 54)
    
    def test_custom_size_initialization(self):
        """Test rocket with custom size."""
        rocket = RocketSprite(size=128)
        assert rocket.get_width() == 128
        assert rocket.get_height() == 192  # Proportional scaling
    
    def test_set_color(self, rocket):
        """Test changing rocket color."""
        rocket.set_color((244, 67, 54))
        assert rocket.get_color() == (244, 67, 54)
    
    def test_set_color_all_presets(self, rocket):
        """Test all preset colors can be applied."""
        for color_data in ROCKET_COLOR_PRESETS:
            rocket.set_color(color_data["rgb"])
            assert rocket.get_color() == color_data["rgb"]
    
    def test_get_color(self, rocket):
        """Test getting current color."""
        assert rocket.get_color() == (255, 255, 255)
        rocket.set_color((255, 0, 0))
        assert rocket.get_color() == (255, 0, 0)
    
    def test_get_dimensions(self, rocket):
        """Test getting rocket dimensions."""
        width, height = rocket.get_size()
        assert width == 64
        assert height == 96
    
    def test_get_bounds(self, rocket):
        """Test getting bounding box."""
        bounds = rocket.get_bounds()
        assert len(bounds) == 4
        assert bounds[2] == 64  # width
        assert bounds[3] == 96  # height
    
    def test_get_rect(self, rocket):
        """Test getting bounding rectangle."""
        rect = rocket.get_rect()
        assert isinstance(rect, pygame.Rect)
        assert rect.width == 64
        assert rect.height == 96
    
    def test_render_no_crash(self, rocket, screen):
        """Test rendering doesn't crash."""
        rocket.render(screen, (100, 100), angle=0)
        assert True
    
    def test_render_with_rotation(self, rocket, screen):
        """Test rendering with rotation."""
        rocket.render(screen, (100, 100), angle=45)
        rocket.render(screen, (100, 100), angle=90)
        rocket.render(screen, (100, 100), angle=-45)
        assert True
    
    def test_render_at_corner(self, rocket, screen):
        """Test render_at_corner method."""
        rocket.render_at_corner(screen, (100, 100))
        assert True
    
    def test_render_with_rotation_45_degrees(self, rocket, screen):
        """Test rendering rotated rocket at 45 degrees."""
        rocket.render(screen, (400, 300), angle=45.0)
        # Just verify no crash
        assert True
    
    def test_render_with_rotation_90_degrees(self, rocket, screen):
        """Test rendering rotated rocket at 90 degrees."""
        rocket.render(screen, (400, 300), angle=90.0)
        assert True
    
    def test_color_change_updates_surface(self, rocket):
        """Test that color change updates the cached surface."""
        original_surface = rocket.cached_surface
        rocket.set_color((255, 0, 0))
        assert rocket.cached_surface is not None
        assert rocket.cached_surface != original_surface
    
    def test_size_scaling(self):
        """Test proportional size scaling."""
        rocket_small = RocketSprite(size=32)
        rocket_large = RocketSprite(size=128)
        
        assert rocket_small.get_width() == 32
        assert rocket_small.get_height() == 48  # 32 * 1.5
        
        assert rocket_large.get_width() == 128
        assert rocket_large.get_height() == 192  # 128 * 1.5


class TestRocketCreation:
    """Tests for rocket creation factory function."""
    
    def test_create_rocket_sprite_default(self):
        """Test factory function with defaults."""
        rocket = create_rocket_sprite()
        assert rocket.get_color() == (255, 255, 255)
        assert rocket.get_width() == 64
    
    def test_create_rocket_sprite_custom(self):
        """Test factory function with custom parameters."""
        rocket = create_rocket_sprite(color=(255, 0, 0), size=128)
        assert rocket.get_color() == (255, 0, 0)
        assert rocket.get_width() == 128


class TestRocketRendering:
    """Tests for rocket rendering behavior."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame."""
        pygame.init()
        yield
        pygame.quit()
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create test screen."""
        return pygame.display.set_mode((400, 300))
    
    @pytest.fixture
    def rocket(self):
        """Create rocket sprite."""
        return RocketSprite()
    
    def test_render_preserves_transparency(self, rocket, screen):
        """Test that rendering preserves alpha channel."""
        rocket.render(screen, (100, 100))
        # Verify screen surface is valid
        assert screen.get_at((0, 0))[3] == 255  # Should be opaque at corner
    
    def test_render_multiple_times(self, rocket, screen):
        """Test rendering rocket multiple times."""
        for i in range(10):
            rocket.render(screen, (i * 10, i * 10))
        assert True
    
    def test_render_offscreen(self, rocket, screen):
        """Test rendering rocket offscreen doesn't crash."""
        rocket.render(screen, (1000, 1000))
        rocket.render(screen, (-100, -100))
        assert True


class TestRocketBoundaries:
    """Tests for rocket collision and boundary detection."""
    
    def test_get_rect_returns_valid_rect(self):
        """Test that get_rect returns valid pygame.Rect."""
        rocket = RocketSprite()
        rect = rocket.get_rect()
        
        assert isinstance(rect, pygame.Rect)
        assert rect.width == 64
        assert rect.height == 96
    
    def test_contains_point(self):
        """Test point containment check."""
        rocket = RocketSprite()
        
        # Test center point (rocket is centered at its origin)
        # This is a simplified test - real usage would pass position
        assert rocket.contains_point(rocket.get_width() // 2, rocket.get_height() // 2)
    
    def test_dimensions_consistency(self):
        """Test that dimensions are consistent after color changes."""
        rocket = RocketSprite()
        original_width = rocket.get_width()
        original_height = rocket.get_height()
        
        rocket.set_color((255, 0, 0))
        rocket.set_color((0, 255, 0))
        rocket.set_color((0, 0, 255))
        
        assert rocket.get_width() == original_width
        assert rocket.get_height() == original_height


@pytest.mark.performance
class TestRocketPerformance:
    """Performance tests for rocket sprite."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame."""
        pygame.init()
        yield
        pygame.quit()
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create test screen."""
        return pygame.display.set_mode((800, 600))
    
    @pytest.fixture
    def rocket(self):
        """Create rocket sprite."""
        return RocketSprite()
    
    def test_color_change_performance(self):
        """Test that color changes are fast."""
        rocket = RocketSprite()
        
        import time
        start = time.time()
        for _ in range(100):
            rocket.set_color((255, 0, 0))
        elapsed = time.time() - start
        
        # 100 color changes should take < 1 second
        assert elapsed < 1.0
    
    def test_render_performance(self, screen):
        """Test that rendering is fast."""
        rocket = RocketSprite()
        import time
        start = time.time()
        for _ in range(100):
            rocket.render(screen, (100, 100), angle=0)
        elapsed = time.time() - start
        
        # 100 renders should take < 0.1 second (1ms per render)
        assert elapsed < 0.1
    
    def test_rotation_performance(self, screen):
        """Test that rotation rendering is fast."""
        rocket = RocketSprite()
        import time
        start = time.time()
        for angle in range(0, 360, 10):
            rocket.render(screen, (100, 100), angle=angle)
        elapsed = time.time() - start
        
        # 36 rotations should take < 0.1 second
        assert elapsed < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
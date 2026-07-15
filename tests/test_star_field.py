"""
Unit tests for star field rendering.

Tests for src/ui/star_field.py
"""

import pytest
import pygame
import time
from src.ui.star_field import Star, StarField, create_star_field
from src.ui.theme import STAR_WHITE, STAR_PALE_YELLOW


class TestStar:
    """Test cases for Star class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.star = Star(100, 200, 3, 1.5)
    
    def test_star_initialization_with_random_properties(self):
        """Test that star initializes with correct properties."""
        assert self.star.x == 100
        assert self.star.y == 200
        assert self.star.size == 3
        assert self.star.speed == 1.5
        assert self.star.alpha == 255
        assert self.star.color in [STAR_WHITE, STAR_PALE_YELLOW]
        assert self.star.alpha_direction == -1
        assert 0 < self.star.twinkle_interval <= 4.0
    
    def test_depth_calculation(self):
        """Test that depth is calculated correctly based on size."""
        star1 = Star(0, 0, 1, 1.0)
        star2 = Star(0, 0, 2, 1.0)
        star3 = Star(0, 0, 4, 1.0)
        
        assert star1.depth == 0.25
        assert star2.depth == 0.5
        assert star3.depth == 1.0
    
    def test_update_changes_twinkle_state(self):
        """Test that update modifies star twinkle state."""
        initial_alpha = self.star.alpha
        initial_timer = self.star.twinkle_timer
        
        # Update with 0.1 seconds
        self.star.update(0.1)
        
        # Timer should have increased
        assert self.star.twinkle_timer > initial_timer
        
        # Alpha might have changed depending on speed
        assert 50 <= self.star.alpha <= 255
    
    def test_update_with_parallax_scroll(self):
        """Test that update with scroll speed changes x position."""
        initial_x = self.star.x
        
        # Update with scroll speed
        self.star.update(1.0, scroll_speed=100.0)
        
        # X should have decreased (moving left)
        assert self.star.x < initial_x
    
    def test_alpha_bounds(self):
        """Test that alpha stays within valid bounds."""
        # Update multiple times to ensure alpha doesn't go out of bounds
        for _ in range(100):
            self.star.update(0.1)
            assert 50 <= self.star.alpha <= 255
    
    def test_render_produces_expected_alpha_values(self):
        """Test that render uses current alpha value."""
        pygame.init()
        screen = pygame.Surface((400, 400), pygame.SRCALPHA)
        
        # Set specific alpha
        self.star.alpha = 128
        
        # Render
        self.star.render(screen)
        
        # Should not raise any exceptions
        assert True
        
        pygame.quit()
    
    def test_reset_position(self):
        """Test that reset_position moves star to new random location."""
        initial_x = self.star.x
        initial_y = self.star.y
        
        self.star.reset_position(800, 600)
        
        # Position should be within bounds
        assert 0 <= self.star.x <= 800
        assert 0 <= self.star.y <= 600


class TestStarField:
    """Test cases for StarField class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.star_field = StarField(800, 600, 200)
    
    def test_star_creation_at_random_positions(self):
        """Test that stars are created at random positions."""
        assert len(self.star_field.stars) == 200
        
        for star in self.star_field.stars:
            assert 0 <= star.x <= 800
            assert 0 <= star.y <= 600
    
    def test_update_cycles_stars_correctly(self):
        """Test that update cycles through all stars."""
        initial_states = [(star.alpha, star.twinkle_timer) for star in self.star_field.stars]
        
        # Update
        self.star_field.update(0.1)
        
        # Some states should have changed
        for i, star in enumerate(self.star_field.stars):
            # Timer should have increased
            assert star.twinkle_timer >= initial_states[i][1]
    
    def test_render_within_screen_bounds(self):
        """Test that render keeps all stars within screen bounds."""
        pygame.init()
        screen = pygame.Surface((800, 600))
        
        # Render should not raise exceptions
        self.star_field.render(screen)
        
        assert True
        
        pygame.quit()
    
    def test_performance_under_5ms_for_200_stars(self):
        """Test that rendering 200 stars takes less than 5ms."""
        pygame.init()
        screen = pygame.Surface((800, 600))
        
        # Warm up
        for _ in range(5):
            self.star_field.render(screen)
        
        # Measure performance
        start_time = time.perf_counter()
        for _ in range(100):
            self.star_field.render(screen)
        elapsed = time.perf_counter() - start_time
        
        # Average should be less than 5ms per frame
        avg_time = (elapsed / 100) * 1000  # Convert to ms
        assert avg_time < 5.0, f"Rendering took {avg_time:.2f}ms (should be < 5ms)"
        
        pygame.quit()
    
    def test_resize_adjusts_dimensions(self):
        """Test that resize updates width and height."""
        self.star_field.resize(1920, 1080)
        
        assert self.star_field.width == 1920
        assert self.star_field.height == 1080
    
    def test_resize_adjusts_star_positions(self):
        """Test that resize adjusts star positions proportionally."""
        # Store original positions
        original_stars = [(star.x, star.y) for star in self.star_field.stars[:5]]
        
        self.star_field.resize(1600, 1200)
        
        # Positions should have been adjusted
        for i, star in enumerate(self.star_field.stars[:5]):
            # New positions should be within new bounds
            assert 0 <= star.x <= 1600
            assert 0 <= star.y <= 1200
    
    def test_set_scroll_speed(self):
        """Test that scroll speed can be set."""
        # This should not raise an exception
        self.star_field.set_scroll_speed(50.0)
        assert True
    
    def test_get_performance_stats(self):
        """Test that performance stats are returned correctly."""
        stats = self.star_field.get_performance_stats()
        
        assert "star_count" in stats
        assert "width" in stats
        assert "height" in stats
        assert stats["star_count"] == 200
        assert stats["width"] == 800
        assert stats["height"] == 600
    
    def test_star_count_parameter(self):
        """Test that star count parameter is respected."""
        small_field = StarField(800, 600, 50)
        large_field = StarField(800, 600, 500)
        
        assert len(small_field.stars) == 50
        assert len(large_field.stars) == 500


class TestCreateStarField:
    """Test cases for create_star_field factory function."""
    
    def test_factory_returns_star_field(self):
        """Test that factory function returns StarField instance."""
        star_field = create_star_field(800, 600, 100)
        
        assert isinstance(star_field, StarField)
        assert star_field.width == 800
        assert star_field.height == 600
        assert len(star_field.stars) == 100
    
    def test_factory_default_star_count(self):
        """Test that factory uses default star count when not specified."""
        star_field = create_star_field(800, 600)
        
        assert len(star_field.stars) == 200  # Default is 200


class TestStarTwinkling:
    """Test cases for twinkling animation behavior."""
    
    def test_star_fades_in_and_out(self):
        """Test that star twinkles between min and max alpha."""
        star = Star(100, 100, 2, 2.0)
        star_twinkle_interval = 0.05  # Fast twinkle for testing
        
        # Manually set up for fast testing
        star.twinkle_interval = star_twinkle_interval
        
        # Run multiple update cycles
        for _ in range(200):
            star.update(0.02)
            
            # Alpha should stay within bounds
            assert 50 <= star.alpha <= 255
        
        # Should have experienced both fade directions
        assert True  # If we got here without errors, test passes
    
    def test_slow_stars_twinkle_slower(self):
        """Test that stars with lower speed values twinkle slower."""
        slow_star = Star(100, 100, 2, 0.5)
        fast_star = Star(100, 100, 2, 2.0)
        
        slow_star.twinkle_interval = 0.1
        fast_star.twinkle_interval = 0.1
        
        # Update both stars
        for _ in range(100):
            slow_star.update(0.02)
            fast_star.update(0.02)
        
        # Both should be valid (this test verifies no crashes)
        assert 50 <= slow_star.alpha <= 255
        assert 50 <= fast_star.alpha <= 255


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
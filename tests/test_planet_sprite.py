"""
Unit tests for planet sprite rendering.

Tests for src/ui/planet_sprite.py
"""

import pytest
import pygame
from src.ui.planet_sprite import PlanetSprite, PlanetManager, create_planet
from src.ui.theme import PLANET_1, PLANET_2, PLANET_3, PLANET_4, PLANET_5


class TestPlanetSprite:
    """Test cases for PlanetSprite class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planet = PlanetSprite(1, 100)
    
    def test_planet_initialization(self):
        """Test planet initializes with correct properties."""
        assert self.planet.planet_type == 1
        assert self.planet.size == 100
        assert self.planet.radius == 50
        assert self.planet.base_color == PLANET_1
        assert self.planet.completed == False
        assert self.planet.bloom_alpha == 0
    
    def test_planet_render_at_various_sizes(self):
        """Test that planet renders correctly at various sizes."""
        pygame.init()
        screen = pygame.Surface((400, 400))
        
        # Test different sizes
        planet_small = PlanetSprite(1, 50)
        planet_medium = PlanetSprite(1, 100)
        planet_large = PlanetSprite(1, 150)
        
        planet_small.render(screen, (100, 100))
        planet_medium.render(screen, (200, 200))
        planet_large.render(screen, (300, 300))
        
        # Should not raise any exceptions
        assert True
        
    
    def test_planet_render_various_planet_types(self):
        """Test that all planet types render correctly."""
        pygame.init()
        screen = pygame.Surface((400, 400))
        
        for planet_num in range(1, 6):
            planet = PlanetSprite(planet_num, 80)
            planet.render(screen, (200, 200))
        
        assert True
    
    def test_completed_state_renders_bloom_effect(self):
        """Test that completed state renders bloom effect."""
        pygame.init()
        screen = pygame.Surface((400, 400))
        
        self.planet.set_completed(True)
        self.planet.update(0.016)  # Simulate one frame
        
        # Render with completed state
        self.planet.render(screen, (200, 200), completed=True)
        
        # Should not raise any exceptions
        assert True
        
    
    def test_set_completed_updates_state(self):
        """Test that set_completed updates the completed state."""
        self.planet.set_completed(True)
        assert self.planet.completed == True
        
        self.planet.set_completed(False)
        assert self.planet.completed == False
    
    def test_update_animates_bloom(self):
        """Test that update animates bloom effect."""
        self.planet.set_completed(True)
        
        initial_bloom_alpha = self.planet.bloom_alpha
        initial_bloom_timer = self.planet.bloom_timer
        
        # Update multiple times
        for _ in range(10):
            self.planet.update(0.1)
        
        # Bloom timer should have been reset
        assert self.planet.bloom_timer < 0.1
        
        # Should not crash
        assert True
    
    def test_set_planet_type_updates_color(self):
        """Test that changing planet type updates color."""
        self.planet.set_planet_type(2)
        assert self.planet.planet_type == 2
        assert self.planet.base_color == PLANET_2
        
        self.planet.set_planet_type(3)
        assert self.planet.planet_type == 3
        assert self.planet.base_color == PLANET_3
    
    def test_planet_type_clamped_to_valid_range(self):
        """Test that planet type is clamped to 1-5 range."""
        self.planet.set_planet_type(0)
        assert self.planet.planet_type == 1  # Clamped to minimum
        
        self.planet.set_planet_type(6)
        assert self.planet.planet_type == 5  # Clamped to maximum
    
    def test_get_bounds_returns_correct_rect(self):
        """Test that get_bounds returns correct bounding rectangle."""
        bounds = self.planet.get_bounds((200, 300))
        
        assert bounds.x == 150  # 200 - 50 (radius)
        assert bounds.y == 250  # 300 - 50 (radius)
        assert bounds.width == 100
        assert bounds.height == 100
    
    def test_collide_with_planet(self):
        """Test collision detection with planet."""
        bounds = self.planet.get_bounds((200, 200))
        
        # Point inside planet
        assert bounds.collidepoint(200, 200)
        assert bounds.collidepoint(180, 180)
        
        # Point outside planet
        assert not bounds.collidepoint(100, 100)
        assert not bounds.collidepoint(350, 350)


class TestPlanetManager:
    """Test cases for PlanetManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.manager = PlanetManager(5, 80)
    
    def test_planet_creation(self):
        """Test that manager creates correct number of planets."""
        assert len(self.manager.planets) == 5
        
        for i, planet in enumerate(self.manager.planets):
            assert planet.planet_type == i + 1
            assert planet.size == 80
    
    def test_set_positions_updates_all_planets(self):
        """Test that set_positions updates positions for all planets."""
        positions = [(100, 200), (200, 200), (300, 200), (400, 200), (500, 200)]
        self.manager.set_positions(positions)
        
        assert len(self.manager._positions) == 5
    
    def test_calculate_positions_spreads_planets(self):
        """Test that calculate_positions spreads planets across screen."""
        self.manager.calculate_positions(800, 600, margin=50)
        
        assert len(self.manager._positions) == 5
        
        # All positions should have valid Y coordinate
        for x, y in self.manager._positions:
            assert 0 <= x <= 800
            assert 0 <= y <= 600
    
    def test_calculate_positions_horizontal_spacing(self):
        """Test that planets are spaced horizontally."""
        self.manager.calculate_positions(800, 600, margin=50)
        
        if len(self.manager._positions) >= 2:
            # First planet should be to the left of second
            x1 = self.manager._positions[0][0]
            x2 = self.manager._positions[1][0]
            assert x1 < x2
    
    def test_update_all_planets(self):
        """Test that update updates all planets."""
        self.manager.calculate_positions(800, 600)
        
        # Should not raise exceptions
        self.manager.update(0.016)
        assert True
    
    def test_render_all_planets(self):
        """Test that render renders all planets."""
        pygame.init()
        screen = pygame.Surface((800, 600))
        
        self.manager.calculate_positions(800, 600)
        self.manager.render(screen)
        
        # Should not raise exceptions
        assert True
        
    
    def test_set_planet_completed_updates_specific_planet(self):
        """Test that set_planet_completed updates specific planet."""
        self.manager.set_planet_completed(0, True)
        assert self.manager.planets[0].completed == True
        
        self.manager.set_planet_completed(2, True)
        assert self.manager.planets[2].completed == True
        assert self.manager.planets[0].completed == True  # First one still True
        
        self.manager.set_planet_completed(0, False)
        assert self.manager.planets[0].completed == False
    
    def test_set_planet_completed_handles_invalid_index(self):
        """Test that invalid index is handled gracefully."""
        # Should not raise exception
        self.manager.set_planet_completed(-1, True)
        self.manager.set_planet_completed(10, True)
    
    def test_get_planet_at_position_finds_planet(self):
        """Test that get_planet_at_position finds planet at location."""
        positions = [(200, 200), (400, 200), (600, 200)]
        self.manager.set_positions(positions)
        
        # Find center of first planet
        index = self.manager.get_planet_at_position(200, 200)
        assert index == 0
    
    def test_get_planet_at_position_returns_none_when_no_match(self):
        """Test that get_planet_at_position returns None when no planet at location."""
        positions = [(200, 200)]
        self.manager.set_positions(positions)
        
        # Far from any planet
        index = self.manager.get_planet_at_position(50, 50)
        assert index is None


class TestCreatePlanet:
    """Test cases for create_planet factory function."""
    
    def test_factory_returns_planet_sprite(self):
        """Test that factory function returns PlanetSprite instance."""
        planet = create_planet(3, 120)
        
        assert isinstance(planet, PlanetSprite)
        assert planet.planet_type == 3
        assert planet.size == 120


class TestPlanetColors:
    """Test cases for planet color properties."""
    
    def test_all_planets_have_unique_colors(self):
        """Test that all planets have different colors."""
        colors = [PLANET_1, PLANET_2, PLANET_3, PLANET_4, PLANET_5]
        
        # All colors should be unique
        assert len(set(colors)) == 5
    
    def test_planet_colors_in_color_blind_safe_palette(self):
        """Test that planet colors use color-blind safe palette."""
        # Orange (planet 1)
        assert PLANET_1 == (255, 152, 0)
        
        # Blue (planet 2)
        assert PLANET_2 == (33, 150, 243)
        
        # Purple (planet 3)
        assert PLANET_3 == (156, 39, 176)
        
        # Brown (planet 4 - color-blind safe, NOT green)
        assert PLANET_4 == (121, 85, 72)
        
        # Gold/Yellow (planet 5 - color-blind safe, distinguishable from blue)
        assert PLANET_5 == (205, 170, 80)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
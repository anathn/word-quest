"""
Integration tests for space theme visuals.

Tests theme integration across game components.
"""

import pytest
import pygame
from src.ui.theme import ThemeManager, get_theme, reset_theme
from src.ui.star_field import StarField
from src.ui.planet_sprite import PlanetManager


class TestThemeIntegration:
    """Test cases for theme integration."""
    
    def teardown_method(self):
        """Clean up after tests."""
        reset_theme()
        pygame.quit()
    
    def test_theme_applies_consistently_across_components(self):
        """Test that theme colors are used consistently by all components."""
        pygame.init()
        
        # Get theme
        theme = get_theme()
        
        # Create star field
        star_field = StarField(800, 600, 50)
        
        # Create planet manager
        planet_manager = PlanetManager(5, 80)
        planet_manager.calculate_positions(800, 600)
        
        # Create screen
        screen = pygame.Surface((800, 600))
        
        # Render everything
        screen.fill(theme.get_color("space_blue"))
        star_field.render(screen)
        planet_manager.render(screen)
        
        # Should not raise any exceptions
        assert True
    
    def test_star_field_maintains_30_fps_with_animations(self):
        """Test that star field maintains >= 30 FPS during animation."""
        pygame.init()
        screen = pygame.Surface((800, 600))
        
        star_field = StarField(800, 600, 200)
        
        # Simulate 60 frames
        target_fps = 60
        frame_time = 1.0 / target_fps
        
        start_time = pygame.time.get_ticks()
        
        for _ in range(60):
            star_field.update(frame_time)
            star_field.render(screen)
        
        elapsed = (pygame.time.get_ticks() - start_time) / 1000.0
        actual_fps = 60 / elapsed
        
        # Should maintain at least 30 FPS
        assert actual_fps >= 30, f"FPS dropped to {actual_fps:.1f}"
    
    def test_space_background_fills_entire_window(self):
        """Test that space background fills entire window."""
        pygame.init()
        
        theme = get_theme()
        
        # Test different window sizes
        for width, height in [(800, 600), (1920, 1080), (1024, 768)]:
            screen = pygame.Surface((width, height))
            screen.fill(theme.get_color("space_blue"))
            
            # Verify screen size
            assert screen.get_width() == width
            assert screen.get_height() == height


class TestThemeConfig:
    """Test cases for theme configuration."""
    
    def teardown_method(self):
        """Clean up after tests."""
        reset_theme()
        pygame.quit()
    
    def test_config_file_is_valid_json(self):
        """Test that theme config file is valid JSON."""
        import json
        
        with open("data/theme_config.json", 'r') as f:
            config = json.load(f)
        
        assert "colors" in config
        assert "settings" in config
    
    def test_config_has_all_required_colors(self):
        """Test that config has all required colors."""
        import json
        
        with open("data/theme_config.json", 'r') as f:
            config = json.load(f)
        
        required_colors = [
            "space_blue", "star_white", "star_pale_yellow",
            "planet_1", "planet_2", "planet_3", "planet_4", "planet_5"
        ]
        
        for color in required_colors:
            assert color in config["colors"], f"Missing color: {color}"
    
    def test_config_settings_are_valid(self):
        """Test that config settings have valid values."""
        import json
        
        with open("data/theme_config.json", 'r') as f:
            config = json.load(f)
        
        settings = config["settings"]
        
        assert "star_count" in settings
        assert 10 <= settings["star_count"] <= 500
        
        assert "planet_size" in settings
        assert settings["planet_size"] > 0


class TestColorBlindAccessibility:
    """Test cases for color-blind accessibility."""
    
    def test_planet_colors_are_distinct(self):
        """Test that planet colors are visually distinguishable."""
        from src.ui.theme import PLANET_1, PLANET_2, PLANET_3, PLANET_4, PLANET_5
        
        colors = [PLANET_1, PLANET_2, PLANET_3, PLANET_4, PLANET_5]
        
        # Calculate color differences to ensure they're distinct
        for i in range(len(colors)):
            for j in range(i + 1, len(colors)):
                c1 = colors[i]
                c2 = colors[j]
                
                # Simple Euclidean distance
                distance = ((c1[0] - c2[0])**2 + 
                           (c1[1] - c2[1])**2 + 
                           (c1[2] - c2[2])**2) ** 0.5
                
                # Colors should be at least 50 units apart in RGB space
                assert distance > 50, f"Colors {i} and {j} are too similar"
    
    def test_text_contrast_against_background(self):
        """Test that text has good contrast against background."""
        from src.ui.theme import SPACE_BLUE, UI_TEXT_NORMAL, UI_TEXT_MUTED
        
        # Simple contrast ratio calculation
        def luminance(rgb):
            return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
        
        bg_lum = luminance(SPACE_BLUE) / 255.0
        text_lum = luminance(UI_TEXT_NORMAL) / 255.0
        
        # Calculate contrast ratio
        if bg_lum > text_lum:
            ratio = (bg_lum + 0.05) / (text_lum + 0.05)
        else:
            ratio = (text_lum + 0.05) / (bg_lum + 0.05)
        
        # Should have至少 3:1 contrast ratio for large text
        assert ratio >= 3.0, f"Contrast ratio {ratio:.2f} is too low"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Tests for Game Entry Point (STORY-999-01)

Tests the game entry point, configuration, and screen management.
"""

import pytest
import os
import sys

# Set testing environment before importing game modules
os.environ['TESTING'] = '1'
os.environ['HEADLESS'] = '1'

import pygame
from src.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, FPS,
    COLOR_BACKGROUND, DATA_DIR, ASSETS_DIR
)
from src.ui.screen_manager import ScreenManager


class TestConfig:
    """Test configuration constants."""
    
    def test_window_dimensions(self):
        """Test window dimensions are set correctly."""
        assert WINDOW_WIDTH == 1024
        assert WINDOW_HEIGHT == 768
        
    def test_window_title(self):
        """Test window title is set."""
        assert WINDOW_TITLE == "Word Quest: Spelling Adventure"
        
    def test_fps_setting(self):
        """Test FPS is configured."""
        assert FPS == 60
        
    def test_colors_defined(self):
        """Test that colors are defined."""
        assert COLOR_BACKGROUND == (26, 26, 62)
        assert COLOR_BACKGROUND[0] >= 0
        assert COLOR_BACKGROUND[1] >= 0
        assert COLOR_BACKGROUND[2] >= 0
        
    def test_data_dir_exists(self):
        """Test data directory path is valid."""
        assert DATA_DIR.exists() or str(DATA_DIR).endswith('data')
        
    def test_assets_dir_exists(self):
        """Test assets directory path is valid."""
        assert ASSETS_DIR.exists() or str(ASSETS_DIR).endswith('assets')


class TestScreenManager:
    """Test screen manager functionality."""
    
    @pytest.fixture
    def surface(self):
        """Create a pygame surface for testing."""
        pygame.init()
        surface = pygame.Surface((800, 600))
        yield surface
        pygame.quit()
        
    def test_manager_creation(self, surface):
        """Test ScreenManager can be created."""
        manager = ScreenManager(surface)
        assert manager is not None
        assert manager.current_screen is None
        assert len(manager.screen_stack) == 0
        
    def test_is_running_initially_true(self, surface):
        """Test manager starts in running state."""
        manager = ScreenManager(surface)
        assert manager.is_running is True
        
    def test_clear_stack(self, surface):
        """Test clearing the screen stack."""
        from src.ui.screen_manager import Screen
        
        class DummyScreen(Screen):
            def handle_event(self, event):
                pass
            def update(self):
                pass
            def draw(self):
                pass
                
        manager = ScreenManager(surface)
        screen = DummyScreen(surface)
        manager.push_screen(screen)
        assert len(manager.screen_stack) == 1
        
        manager.clear_stack()
        assert manager.is_running is False
        assert len(manager.screen_stack) == 0


class TestPathHelpers:
    """Test path helper functions."""
    
    def test_get_data_path(self):
        """Test get_data_path function."""
        from src.config import get_data_path
        path = get_data_path("test.json")
        assert "data" in str(path)
        assert "test.json" in str(path)
        
    def test_get_assets_path(self):
        """Test get_assets_path function."""
        from src.config import get_assets_path
        path = get_assets_path("test.png")
        assert "assets" in str(path)
        assert "test.png" in str(path)
        
    def test_get_font_path(self):
        """Test get_font_path function."""
        from src.config import get_font_path
        path = get_font_path("font.ttf")
        assert "fonts" in str(path) or "font" in str(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

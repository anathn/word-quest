"""
Tests for Game Loop and Initialization (STORY-999-01)

Tests the game initialization, game loop, and cleanup.
"""

import pytest
import os
import sys

# Set testing environment before importing game modules
os.environ['TESTING'] = '1'
os.environ['HEADLESS'] = '1'

import pygame
from src.game import Game, create_display, initialize_pygame, cleanup_pygame
from src.config import WINDOW_WIDTH, WINDOW_HEIGHT


class TestGameInitialization:
    """Test game initialization."""
    
    def test_initialize_pygame(self):
        """Test pygame can be initialized."""
        # Note: pygame might already be initialized
        result = initialize_pygame()
        assert result is True
        
    def test_create_display(self):
        """Test display creation."""
        # pygame should already be initialized
        screen = create_display(WINDOW_WIDTH, WINDOW_HEIGHT)
        assert screen is not None
        assert screen.get_width() == WINDOW_WIDTH
        assert screen.get_height() == WINDOW_HEIGHT
        
    def test_display_title(self):
        """Test display caption is set."""
        from src.config import WINDOW_TITLE
        screen = create_display(WINDOW_WIDTH, WINDOW_HEIGHT)
        title = pygame.display.get_caption()[0]
        assert WINDOW_TITLE in title


class TestGame:
    """Test Game class functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_pygame(self):
        """Setup pygame for tests."""
        pygame.init()
        pygame.mixer.init()
        yield
        pygame.quit()
        
    def test_game_creation(self):
        """Test Game can be created."""
        screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        game = Game(screen)
        assert game is not None
        assert game.screen_manager is not None
        assert game.data_store is not None
        assert game._running is True
        
    def test_game_has_music_manager(self):
        """Test game provides music manager."""
        screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        game = Game(screen)
        # Should be lazy loaded
        assert game._music_manager is None
        # Accessing property should load it
        music_mgr = game.music_manager
        assert music_mgr is not None
        
    def test_game_quit(self):
        """Test game cleanup."""
        screen = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        game = Game(screen)
        
        # Should be running
        assert game._running is True
        
        # Quit should stop the game
        game.quit()
        assert game._running is False


class TestEntryPoint:
    """Test main entry point."""
    
    def test_main_module_runnable(self):
        """Test that __main__ module can be imported."""
        import importlib
        # The module should be importable
        # We don't actually run main() because it would start the game loop
        from src import __main__
        assert hasattr(__main__, 'main')
        
        
class TestConfigConstants:
    """Test configuration constants used by game entry."""
    
    def test_window_settings(self):
        """Test window configuration."""
        from src.config import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, FPS
        assert WINDOW_WIDTH > 0
        assert WINDOW_HEIGHT > 0
        assert len(WINDOW_TITLE) > 0
        assert FPS > 0
        
    def test_directory_paths(self):
        """Test directory paths are configured."""
        from src.config import DATA_DIR, ASSETS_DIR, BASE_DIR
        assert DATA_DIR is not None
        assert ASSETS_DIR is not None
        assert BASE_DIR is not None
        # Paths should be pathlib.Path objects
        assert hasattr(DATA_DIR, 'exists')
        
    def test_color_constants(self):
        """Test color constants."""
        from src.config import COLOR_BACKGROUND, COLOR_WHITE, COLOR_GOLD
        assert len(COLOR_BACKGROUND) == 3  # RGB
        assert len(COLOR_WHITE) == 3
        assert len(COLOR_GOLD) == 3
        # All values should be 0-255
        for color in [COLOR_BACKGROUND, COLOR_WHITE, COLOR_GOLD]:
            for value in color:
                assert 0 <= value <= 255


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

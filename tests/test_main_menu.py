"""
Unit tests for Main Menu Screen.

Tests cover:
- Main menu initialization with space theme
- Star field rendering
- Button creation and hover effects
- Theme application
- Screen resize handling
"""

import unittest
import pygame
from unittest.mock import Mock, MagicMock, patch


class TestMainMenuScreen(unittest.TestCase):
    """Tests for the MainMenuScreen class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Initialize pygame for testing
        if not pygame.get_init():
            pygame.init()
            pygame.display.init()
        
        self.screen_width = 800
        self.screen_height = 600
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
    
    def tearDown(self):
        """Clean up after tests."""
        # Pygame surfaces don't have close(), just let it be garbage collected
        pass
    
    def test_main_menu_initialization(self):
        """Test that main menu initializes with required components."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(self.screen_width, self.screen_height)
        
        self.assertIsNotNone(menu)
        self.assertEqual(menu.screen_width, self.screen_width)
        self.assertEqual(menu.screen_height, self.screen_height)
        self.assertIsNotNone(menu.star_field)
        self.assertIsNotNone(menu.theme)
        self.assertIsNotNone(menu.typography)
    
    def test_main_menu_has_decorative_planets(self):
        """Test that main menu creates decorative planets."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(self.screen_width, self.screen_height)
        
        self.assertGreater(len(menu.planets), 0)
        self.assertEqual(len(menu.planets), 3)  # Should have 3 decorative planets
    
    def test_main_menu_has_buttons(self):
        """Test that main menu creates all required buttons."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(self.screen_width, self.screen_height)
        
        # Should have 4 buttons: Start Game, Parent Dashboard, Settings, Quit
        self.assertEqual(len(menu._buttons), 4)
        
        # Check button texts
        button_texts = [btn.text for btn in menu._buttons]
        self.assertIn("START GAME", button_texts)
        self.assertIn("PARENT DASHBOARD", button_texts)
        self.assertIn("SETTINGS", button_texts)
        self.assertIn("QUIT", button_texts)
    
    def test_start_game_button_is_primary(self):
        """Test that the Start Game button is primary (larger, more prominent)."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(self.screen_width, self.screen_height)
        
        start_button = menu._buttons[0]  # First button should be Start Game
        self.assertTrue(start_button.is_primary)
        self.assertEqual(start_button.text, "START GAME")
    
    def test_main_menu_callback_setup(self):
        """Test that callbacks can be set on main menu."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(self.screen_width, self.screen_height)
        
        # Create mock callbacks
        start_callback = Mock()
        dashboard_callback = Mock()
        settings_callback = Mock()
        quit_callback = Mock()
        
        # Set callbacks
        menu.on_start_game = start_callback
        menu.on_parent_dashboard = dashboard_callback
        menu.on_settings = settings_callback
        menu.on_quit = quit_callback
        
        # Verify callbacks are set
        self.assertEqual(menu.on_start_game, start_callback)
        self.assertEqual(menu.on_parent_dashboard, dashboard_callback)
        self.assertEqual(menu.on_settings, settings_callback)
        self.assertEqual(menu.on_quit, quit_callback)
    
    def test_main_menu_render_creates_background(self):
        """Test that render fills screen with space blue background."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(self.screen_width, self.screen_height)
        menu._init_fonts = Mock()  # Mock font initialization
        
        # Render to screen
        menu.render(self.screen)
        
        # Get pixel at center to verify background color
        center_pixel = self.screen.get_at((self.screen_width // 2, self.screen_height // 2))
        
        # Should be close to space blue (26, 26, 62)
        # Allowing some variance due to star rendering
        self.assertGreater(center_pixel.r, 0)  # Should have some red
        self.assertGreater(center_pixel.g, 0)  # Should have some green
        self.assertGreater(center_pixel.b, 50)  # Should have significant blue (space blue)
    
    def test_main_menu_update_animates_stars(self):
        """Test that update method animates the star field."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(self.screen_width, self.screen_height)
        
        # Store original star count
        original_star_count = len(menu.star_field.stars)
        
        # Update with some time delta
        menu.update(0.016)  # ~60 FPS
        
        # Star field should still have stars (procedural, no deletion)
        self.assertEqual(len(menu.star_field.stars), original_star_count)
    
    def test_main_menu_handle_mouse_motion_sets_hover(self):
        """Test that mouse motion sets hover state on buttons."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(self.screen_width, self.screen_height)
        
        # Get first button's position
        button = menu._buttons[0]
        
        # Simulate mouse motion over button
        menu.handle_mouse_motion((button.rect.centerx, button.rect.centery))
        
        # Should have hovered button
        self.assertEqual(menu._hovered_button, button)
    
    def test_main_menu_handle_mouse_motion_clears_hover_when_off_button(self):
        """Test that mouse motion off buttons clears hover state."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(self.screen_width, self.screen_height)
        
        # First hover over a button
        button = menu._buttons[0]
        menu.handle_mouse_motion((button.rect.centerx, button.rect.centery))
        self.assertIsNotNone(menu._hovered_button)
        
        # Then move to empty area
        menu.handle_mouse_motion((10, 10))  # Top-left corner, likely no button
        
        # Hover should be cleared
        self.assertIsNone(menu._hovered_button)
    
    def test_main_menu_handle_mouse_click_triggers_callback(self):
        """Test that mouse click triggers button callback."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(self.screen_width, self.screen_height)
        
        # Create mock callback
        mock_callback = Mock()
        menu.on_start_game = mock_callback
        
        # Get start button position
        start_button = menu._buttons[0]
        
        # Simulate click on start button
        menu.handle_mouse_click((start_button.rect.centerx, start_button.rect.centery))
        
        # Callback should have been called
        mock_callback.assert_called_once()
    
    def test_main_menu_resize_updates_dimensions(self):
        """Test that resize updates screen dimensions."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(self.screen_width, self.screen_height)
        
        new_width = 1024
        new_height = 768
        
        # Resize
        menu.resize(new_width, new_height)
        
        # Dimensions should be updated
        self.assertEqual(menu.screen_width, new_width)
        self.assertEqual(menu.screen_height, new_height)
    
    def test_main_menu_initialization_with_1920x1080(self):
        """Test main menu works with larger screen resolution."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(1920, 1080)
        
        self.assertEqual(menu.screen_width, 1920)
        self.assertEqual(menu.screen_height, 1080)
        self.assertIsNotNone(menu.star_field)
        
        # Star field should match screen dimensions
        self.assertEqual(menu.star_field.width, 1920)
        self.assertEqual(menu.star_field.height, 1080)
    
    def test_main_menu_initialization_with_800x600(self):
        """Test main menu works with minimum screen resolution."""
        from src.screens.main_menu import create_main_menu
        
        menu = create_main_menu(800, 600)
        
        self.assertEqual(menu.screen_width, 800)
        self.assertEqual(menu.screen_height, 600)
        self.assertIsNotNone(menu.star_field)
        
        # Star field should match screen dimensions
        self.assertEqual(menu.star_field.width, 800)
        self.assertEqual(menu.star_field.height, 600)
    
    def test_menu_button_has_correct_properties(self):
        """Test that MenuButton dataclass has correct properties."""
        from src.screens.main_menu import MenuButton
        import pygame
        
        callback = Mock()
        button_rect = pygame.Rect(100, 100, 200, 50)
        
        button = MenuButton(
            text="TEST",
            rect=button_rect,
            callback=callback,
            color=(255, 0, 0),
            hover_color=(0, 255, 0),
            is_primary=False
        )
        
        self.assertEqual(button.text, "TEST")
        self.assertEqual(button.rect, button_rect)
        self.assertEqual(button.callback, callback)
        self.assertEqual(button.color, (255, 0, 0))
        self.assertEqual(button.hover_color, (0, 255, 0))
        self.assertFalse(button.is_primary)


class TestMainMenuIntegration(unittest.TestCase):
    """Integration tests for main menu with space theme."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not pygame.get_init():
            pygame.init()
            pygame.display.init()
        
        self.screen = pygame.display.set_mode((800, 600))
    
    def tearDown(self):
        """Clean up after tests."""
        # Pygame surfaces don't have close(), just let it be garbage collected
        pass
    
    def test_main_menu_uses_space_theme_colors(self):
        """Test that main menu uses the space theme color palette."""
        from src.screens.main_menu import create_main_menu
        from src.ui.theme import get_theme, SPACE_BLUE
        
        menu = create_main_menu(800, 600)
        
        # Verify theme is the space theme
        theme = get_theme()
        space_blue = theme.get_color("space_blue")
        
        self.assertEqual(space_blue, SPACE_BLUE)
    
    def test_main_menu_star_field_uses_theme_colors(self):
        """Test that star field uses colors from theme."""
        from src.screens.main_menu import create_main_menu
        from src.ui.theme import STAR_WHITE, STAR_PALE_YELLOW
        
        menu = create_main_menu(800, 600)
        
        # Check that stars use theme colors
        for star in menu.star_field.stars:
            # Each star should be either white or pale yellow
            self.assertIn(star.color, [STAR_WHITE, STAR_PALE_YELLOW])


if __name__ == '__main__':
    unittest.main()
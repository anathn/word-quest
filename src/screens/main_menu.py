"""
Main Menu Screen

The starting screen for Word Quest, providing navigation to all game modes.
Features the space-themed background with star field animation.
"""

import pygame
from typing import Optional, Callable, List, Dict
from dataclasses import dataclass

from src.ui.star_field import StarField
from src.ui.theme import get_theme, SPACE_BLUE
from src.ui.planet_sprite import PlanetSprite, PlanetManager
from src.ui.typography import get_typography
from src.components.audio_system import get_audio_system
from src.ui.rocket_sprite import RocketSprite
from src.ui.rocket_animator import RocketAnimator, create_rocket_animator
from src.models.rocket_config import RocketConfig
from src.audio.music_manager import get_music_manager, MusicState
from src.ui.screen_manager import Screen

import logging

logger = logging.getLogger(__name__)


@dataclass
class MenuButton:
    """Represents an interactive button on the main menu."""
    text: str
    rect: pygame.Rect
    callback: Optional[Callable] = None
    color: tuple = (76, 175, 80)
    hover_color: tuple = (100, 189, 100)
    is_primary: bool = False  # Primary buttons Larger and more prominent


class MainMenuScreen(Screen):
    """
    Main menu screen for Word Quest.
    
    Features:
    - Space-themed background with star field
    - Navigation buttons for game modes
    - Animated rocket and planet elements
    - Welcome message with Captain Cosmos
    
    Provides entry points to:
    - Spelling Challenge (Start Game)
    - Parent Dashboard
    - Student Settings
    """
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize the main menu.
        
        Args:
            screen: The main pygame display surface
        """
        super().__init__(screen)
        
        self.screen_width = screen.get_width()
        self.screen_height = screen.get_height()
        
        # Space theme initialization (STORY-005-01)
        self.theme = get_theme()
        self.star_field = StarField(self.screen_width, self.screen_height)
        
        # Typography
        self.typography = get_typography()
        
        # Audio system
        self.audio_system = get_audio_system()
        
        # Planet decoration (for visual interest)
        self.planets: List[PlanetSprite] = []
        self._setup_decorative_planets()
        
        # UI elements
        self._buttons: List[MenuButton] = []
        self._hovered_button: Optional[MenuButton] = None
        self._welcome_y_offset: float = 0  # For floating animation
        
        # Animation state
        self._menu_start_time: float = 0
        self._animation_phase: str = "intro"
        
        # Callbacks for navigation
        self.on_start_game: Optional[Callable] = None
        self.on_parent_dashboard: Optional[Callable] = None
        self.on_settings: Optional[Callable] = None
        self.on_quit: Optional[Callable] = None
        
        # Rocket animation (STORY-005-02)
        self.rocket_sprite: Optional[RocketSprite] = None
        self.rocket_animator: Optional[RocketAnimator] = None
        
        # Music manager (STORY-005-04)
        self.music_manager = get_music_manager()
        
        # Initialize buttons
        self._setup_buttons()
        
        # Initialize rocket
        self._setup_rocket()
    
    def on_enter(self):
        """Called when screen becomes active - play main menu music."""
        try:
            self.music_manager.initialize()
            self.music_manager.play(MusicState.MAIN_MENU)
        except Exception as e:
            # Music initialization failed - continue without music
            logger.warning(f"Could not initialize music in main menu: {e}")
    
    def _setup_rocket(self):
        """Set up the animated rocket (STORY-005-02)."""
        try:
            # Get player ID from current session (fallback to default)
            from src.profiles.student_profile import get_current_student_id
            player_id = get_current_student_id()
        except Exception:
            # Use default player ID if no student is logged in
            player_id = "default_student"
        
        # Create rocket config to get current color preference
        self.rocket_config = RocketConfig(player_id)
        rocket_color = self.rocket_config.get_current_color()
        
        # Create rocket sprite with configured color
        self.rocket_sprite = RocketSprite(color=rocket_color, size=64)
        
        # Create animator and start hover animation in center of screen
        self.rocket_animator = create_rocket_animator(
            self.rocket_sprite,
            initial_position=(self.screen_width // 2, self.screen_height // 2)
        )
        # Start hover animation around center position
        self.rocket_animator.animate_hover(
            (self.screen_width // 2, self.screen_height // 2)
        )
    
    def _setup_decorative_planets(self):
        """Set up decorative planets for visual interest."""
        # Create 3 decorative planets at different positions
        planet_configs = [
            {"x": 100, "y": self.screen_height - 150, "size": 60, "planet_num": 1},
            {"x": self.screen_width - 120, "y": self.screen_height - 120, "size": 80, "planet_num": 3},
            {"x": self.screen_width // 2, "y": self.screen_height - 180, "size": 40, "planet_num": 5},
        ]
        
        for config in planet_configs:
            planet = PlanetSprite("space", config["size"])
            planet.x = config["x"]
            planet.y = config["y"]
            self.planets.append(planet)
    
    def _setup_buttons(self):
        """Set up menu buttons."""
        button_y = self.screen_height // 2
        button_spacing = 70
        
        # Primary "Start Game" button
        start_button = MenuButton(
            text="START GAME",
            rect=pygame.Rect(
                self.screen_width // 2 - 120,
                button_y,
                240, 50
            ),
            callback=self._start_game,
            color=(255, 152, 0),  # Orange accent
            hover_color=(255, 172, 60),
            is_primary=True
        )
        
        # Secondary buttons
        dashboard_button = MenuButton(
            text="PARENT DASHBOARD",
            rect=pygame.Rect(
                self.screen_width // 2 - 120,
                button_y + button_spacing,
                240, 45
            ),
            callback=self._parent_dashboard,
            color=(76, 175, 80)  # Green
        )
        
        settings_button = MenuButton(
            text="SETTINGS",
            rect=pygame.Rect(
                self.screen_width // 2 - 120,
                button_y + button_spacing * 2,
                240, 45
            ),
            callback=self._settings,
            color=(33, 150, 243)  # Blue
        )
        
        quit_button = MenuButton(
            text="QUIT",
            rect=pygame.Rect(
                self.screen_width // 2 - 120,
                button_y + button_spacing * 3,
                240, 40
            ),
            callback=self._quit,
            color=(244, 67, 54)  # Red
        )
        
        self._buttons = [start_button, dashboard_button, settings_button, quit_button]
    
    def _start_game(self):
        """Handle start game button click."""
        if self.on_start_game:
            self.on_start_game()
    
    def _parent_dashboard(self):
        """Handle parent dashboard button click."""
        if self.on_parent_dashboard:
            self.on_parent_dashboard()
    
    def _settings(self):
        """Handle settings button click."""
        if self.on_settings:
            self.on_settings()
    
    def _quit(self):
        """Handle quit button click."""
        if self.on_quit:
            self.on_quit()
        else:
            # Default: quit pygame
            pygame.quit()
            exit()
    
    def draw(self) -> None:
        """
        Draw the main menu to the screen.
        """
        # Fill with deep space blue background
        self.screen.fill(self.theme.get_color("space_blue"))
        
        # Render star field (twinkling animation)
        self.star_field.render(self.screen)
        
        # Render decorative planets
        for planet in self.planets:
            planet.render(self.screen, (planet.x, planet.y), completed=False)
        
        # Render title, welcome, buttons, and footer
        self._render_title()
        self._render_welcome()
        self._render_buttons()
        self._render_footer()
        
        # Render rocket (STORY-005-02)
        if self.rocket_animator:
            self.rocket_animator.render(self.screen)
    
    def _render_title(self) -> None:
        """Render the game title."""
        title_text = "WORD QUEST"
        title_font = self.theme.get_font_large()
        title_color = self.theme.get_color("font_accent")
        title_surface = title_font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(
            centerx=self.screen_width // 2,
            top=60
        )
        self.screen.blit(title_surface, title_rect)
        
        subtitle_font = self.theme.get_font_medium()
        subtitle_text = "Spelling Adventure"
        subtitle_color = self.theme.get_color("font_secondary")
        subtitle_surface = subtitle_font.render(subtitle_text, True, subtitle_color)
        subtitle_rect = subtitle_surface.get_rect(
            centerx=self.screen_width // 2,
            top=title_rect.bottom + 10
        )
        self.screen.blit(subtitle_surface, subtitle_rect)
    
    def _render_welcome(self) -> None:
        """Render welcome message with Captain Cosmos reference."""
        import math
        current_time = pygame.time.get_ticks() / 1000
        if self._menu_start_time == 0:
            self._menu_start_time = current_time
        
        elapsed = current_time - self._menu_start_time
        self._welcome_y_offset = math.sin(elapsed * 1.5) * 5
        
        welcome_font = self.theme.get_font_small()
        welcome_text = "Welcome, Space Explorer!"
        welcome_color = self.theme.get_color("font_primary")
        
        welcome_surface = welcome_font.render(welcome_text, True, welcome_color)
        welcome_rect = welcome_surface.get_rect(
            centerx=self.screen_width // 2,
            top=self.screen_height // 2 - 120 + self._welcome_y_offset
        )
        self.screen.blit(welcome_surface, welcome_rect)
    
    def _render_buttons(self) -> None:
        """Render all menu buttons."""
        for button in self._buttons:
            color = button.hover_color if button == self._hovered_button else button.color
            pygame.draw.rect(self.screen, color, button.rect, border_radius=8)
            
            border_width = 3 if button.is_primary else 2
            border_color = (255, 255, 255) if button == self._hovered_button else self.theme.get_color("ui_border")
            pygame.draw.rect(self.screen, border_color, button.rect, border_width, border_radius=8)
            
            button_font = self.theme.get_font_medium() if button.is_primary else self.theme.get_font_small()
            text_color = (255, 255, 255)
            text_surface = button_font.render(button.text, True, text_color)
            text_rect = text_surface.get_rect(center=button.rect.center)
            self.screen.blit(text_surface, text_rect)
    
    def _render_footer(self) -> None:
        """Render footer with version and credits."""
        from src import __version__
        
        footer_font = self.theme.get_font(14)
        footer_text = f"Word Quest v{__version__} | Captain Cosmos Guide"
        footer_color = self.theme.get_color("font_secondary")
        
        footer_surface = footer_font.render(footer_text, True, footer_color)
        footer_rect = footer_surface.get_rect(
            centerx=self.screen_width // 2,
            bottom=self.screen_height - 15
        )
        self.screen.blit(footer_surface, footer_rect)
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle pygame events."""
        if event.type == pygame.MOUSEMOTION:
            self.handle_mouse_motion(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.handle_mouse_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.request_exit()
    
    def on_enter(self) -> None:
        """Called when screen becomes active."""
        self._welcome_y_offset = 0
        try:
            if self.music_manager:
                self.music_manager.play(MusicState.MAIN_MENU)
        except Exception as e:
            logger.warning(f"Could not play menu music: {e}")
    
    def on_exit(self) -> None:
        """Called when screen is deactivated."""
        try:
            if self.music_manager:
                self.music_manager.stop()
        except Exception as e:
            logger.warning(f"Could not stop menu music: {e}")
    
    def update(self) -> None:
        """Update main menu state (call each frame)."""
        delta_time = 1.0 / 60.0
        if self.star_field:
            self.star_field.update(delta_time)
        for planet in self.planets:
            if hasattr(planet, 'update'):
                planet.update(delta_time)
        if self.rocket_animator:
            self.rocket_animator.update(delta_time)
    
    def handle_mouse_motion(self, pos: tuple):
        """
        Handle mouse movement for hover effects.
        
        Args:
            pos: Mouse position (x, y)
        """
        self._hovered_button = None
        
        # Check buttons
        for button in self._buttons:
            if button.rect.collidepoint(pos):
                self._hovered_button = button
                break
    
    def handle_mouse_click(self, pos: tuple):
        """
        Handle mouse click.
        
        Args:
            pos: Mouse position (x, y)
        """
        for button in self._buttons:
            if button.rect.collidepoint(pos) and button.callback:
                # Play click sound if audio available
                if self.audio_system and self.audio_system.is_audio_available():
                    self.audio_system.play_sfx("click")
                
                button.callback()
                return
    
    def handle_event(self, event: pygame.event.Event):
        """
        Handle pygame events.
        
        Args:
            event: Pygame event
        """
        if event.type == pygame.MOUSEMOTION:
            self.handle_mouse_motion(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.handle_mouse_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            self._handle_keydown(event.key)
    
    def _handle_keydown(self, key: int):
        """
        Handle keyboard input for navigation.
        
        Args:
            key: Pygame key constant
        """
        # Keyboard navigation (optional enhancement)
        # For now, just support Escape to quit
        if key == pygame.K_ESCAPE:
            self._quit()
    
    def resize(self, new_width: int, new_height: int):
        """
        Resize menu for new window dimensions.
        
        Args:
            new_width: New screen width
            new_height: New screen height
        """
        self.screen_width = new_width
        self.screen_height = new_height
        
        # Resize star field
        self.star_field.resize(new_width, new_height)
        
        # Reposition decorative planets
        self._setup_decorative_planets()
        
        # Reposition buttons
        self._setup_buttons()
        
        # Reposition rocket
        if self.rocket_animator:
            # Reset rocket position and animation
            self.rocket_animator.position = (self.screen_width // 2, self.screen_height // 2)
            self.rocket_animator.animate_hover(
                (self.screen_width // 2, self.screen_height // 2)
            )


def create_main_menu(screen: pygame.Surface) -> MainMenuScreen:
    """
    Factory function to create a MainMenuScreen.
    
    Args:
        screen: The main pygame display surface
        
    Returns:
        Configured MainMenuScreen instance
    """
    return MainMenuScreen(screen)
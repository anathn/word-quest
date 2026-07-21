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


class MainMenuScreen:
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
    
    def __init__(self, screen_width: int = 800, screen_height: int = 600):
        """
        Initialize the main menu.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Space theme initialization (STORY-005-01)
        self.theme = get_theme()
        self.star_field = StarField(screen_width, screen_height)
        
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
    
    def render(self, screen: pygame.Surface):
        """
        Render the main menu to the screen.
        
        Args:
            screen: Pygame surface to render to
        """
        # Fill with deep space blue background
        screen.fill(self.theme.get_color("space_blue"))
        
        # Render star field (twinkling animation)
        self.star_field.render(screen)
        
        # Render decorative planets
        for planet in self.planets:
            planet.render(screen, (planet.x, planet.y), completed=False)
        
        # Render title
        self._render_title(screen)
        
        # Render welcome message
        self._render_welcome(screen)
        
        # Render menu buttons
        self._render_buttons(screen)
        
        # Render footer with version
        self._render_footer(screen)
        
        # Render rocket (STORY-005-02)
        if self.rocket_animator:
            self.rocket_animator.render(screen)
    
    def _render_title(self, screen: pygame.Surface):
        """Render the game title."""
        title_text = "WORD QUEST"
        
        # Get large font
        title_font = self.theme.get_font_large()
        
        # Main title in bright color
        title_color = self.theme.get_color("font_accent")
        title_surface = title_font.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(
            centerx=self.screen_width // 2,
            top=60
        )
        screen.blit(title_surface, title_rect)
        
        # Subtitle
        subtitle_font = self.theme.get_font_medium()
        subtitle_text = "Spelling Adventure"
        subtitle_color = self.theme.get_color("font_secondary")
        subtitle_surface = subtitle_font.render(subtitle_text, True, subtitle_color)
        subtitle_rect = subtitle_surface.get_rect(
            centerx=self.screen_width // 2,
            top=title_rect.bottom + 10
        )
        screen.blit(subtitle_surface, subtitle_rect)
    
    def _render_welcome(self, screen: pygame.Surface):
        """Render welcome message with Captain Cosmos reference."""
        # Calculate floating animation
        import math
        current_time = pygame.time.get_ticks() / 1000
        if self._menu_start_time == 0:
            self._menu_start_time = current_time
        
        elapsed = current_time - self._menu_start_time
        self._welcome_y_offset = math.sin(elapsed * 1.5) * 5  # Gentle float
        
        welcome_font = self.theme.get_font_small()
        welcome_text = "Welcome, Space Explorer!"
        welcome_color = self.theme.get_color("font_primary")
        
        welcome_surface = welcome_font.render(welcome_text, True, welcome_color)
        welcome_rect = welcome_surface.get_rect(
            centerx=self.screen_width // 2,
            top=self.screen_height // 2 - 120 + self._welcome_y_offset
        )
        screen.blit(welcome_surface, welcome_rect)
    
    def _render_buttons(self, screen: pygame.Surface):
        """Render all menu buttons."""
        for button in self._buttons:
            # Determine color based on hover state
            color = button.hover_color if button == self._hovered_button else button.color
            
            # Draw button background
            pygame.draw.rect(screen, color, button.rect, border_radius=8)
            
            # Draw button border
            border_width = 3 if button.is_primary else 2
            border_color = (255, 255, 255) if button == self._hovered_button else self.theme.get_color("ui_border")
            pygame.draw.rect(screen, border_color, button.rect, border_width, border_radius=8)
            
            # Draw button text
            button_font = self.theme.get_font_medium() if button.is_primary else self.theme.get_font_small()
            text_color = (255, 255, 255)
            text_surface = button_font.render(button.text, True, text_color)
            text_rect = text_surface.get_rect(center=button.rect.center)
            screen.blit(text_surface, text_rect)
    
    def _render_footer(self, screen: pygame.Surface):
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
        screen.blit(footer_surface, footer_rect)
    
    def update(self, delta_time: float):
        """
        Update main menu state (call each frame).
        
        Args:
            delta_time: Time since last update in seconds
        """
        # Update star field twinkling animation
        if self.star_field:
            self.star_field.update(delta_time)
        
        # Update planets (if they have animations)
        for planet in self.planets:
            if hasattr(planet, 'update'):
                planet.update(delta_time)
        
        # Update rocket animation (STORY-005-02)
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
                    self.audio_system.play_sound("click")
                
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


def create_main_menu(screen_width: int = 800, screen_height: int = 600) -> MainMenuScreen:
    """
    Factory function to create a MainMenuScreen.
    
    Args:
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        
    Returns:
        Configured MainMenuScreen instance
    """
    return MainMenuScreen(screen_width, screen_height)
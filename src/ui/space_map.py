"""
Space Map Display Component

Main component for rendering the student's personal space map.
Displays planets, navigation paths, and current position indicator.
"""

from typing import Optional, Callable, Tuple, List
import pygame

from src.models.map_state import SpaceMapState, PlanetNode, PlanetState
from src.ui.map_elements import (
    PlanetSprite, PathRenderer, RocketIndicator,
    create_planet_sprite, create_path_renderer, create_rocket_indicator
)
from src.ui.theme import ThemeManager
from src.components.audio_system import AudioSystem


class SpaceMapDisplay:
    """
    Renders the space map with planets, paths, and navigation.
    
    Features:
    - Visual space map with planet nodes
    - Progress-based planet states (locked/visited/completed/current)
    - Animated transitions and effects
    - Click and keyboard navigation
    - Planet details on selection
    """
    
    # Constants
    MIN_TOUCH_SIZE = 64  # Minimum touch target size for accessibility
    FONT_SIZE_TITLE = 28
    FONT_SIZE_LABEL = 20
    LABEL_PADDING = 10
    
    def __init__(
        self,
        screen: pygame.Surface,
        map_state: SpaceMapState,
        audio_system: Optional[AudioSystem] = None
    ):
        """
        Initialize space map display.
        
        Args:
            screen: Pygame surface to render to
            map_state: SpaceMapState with planet data
            audio_system: Optional AudioSystem for feedback
        """
        self.screen = screen
        self.map_state = map_state
        self.audio_system = audio_system
        
        # Theme
        self.theme = ThemeManager()
        
        # Map rendering
        self.planet_sprites: dict[str, PlanetSprite] = {}
        self.path_renderer: Optional[PathRenderer] = None
        self.rocket_indicator: Optional[RocketIndicator] = None
        
        # Selection and focus
        self.selected_planet_id: Optional[str] = None
        self.keyboard_focus_id: Optional[str] = None
        
        # UI callbacks
        self.on_planet_selected: Optional[Callable[[PlanetNode], None]] = None
        self.on_return: Optional[Callable[[], None]] = None
        
        # Title rendering
        self._title_surface: Optional[pygame.Surface] = None
        self._instructions_surface: Optional[pygame.Surface] = None
        
        # Animation state
        self._update_surfaces()
    
    def _update_surfaces(self):
        """Update all cached surfaces."""
        self._render_title()
        self._render_instructions()
        self._update_planet_sprites()
        self._update_path()
        self._update_rocket()
    
    def _render_title(self):
        """Render the map title."""
        try:
            font = self.theme.get_font('title', self.FONT_SIZE_TITLE)
            self._title_surface = font.render("SPACE MAP", True, self.theme.colors['text_primary'])
            
            font_small = self.theme.get_font('body', self.FONT_SIZE_LABEL)
            self._instructions_surface = font_small.render(
                "Arrow keys or click to navigate",
                True, self.theme.colors['text_secondary']
            )
        except KeyError as e:
            # Theme configuration issue
            raise RuntimeError(f"Missing theme configuration: {e}") from e
        except Exception as e:
            # Log the actual error for debugging
            print(f"Warning: Failed to render title: {e}")
            # Create minimal fallback
            self._title_surface = pygame.Surface((200, 30))
            self._instructions_surface = pygame.Surface((250, 25))
    
    def _update_planet_sprites(self):
        """Update planet sprite instances."""
        self.planet_sprites.clear()
        
        for planet in self.map_state.planets:
            # Ensure minimum touch target size (diameter, not radius)
            # MIN_TOUCH_SIZE = 64px is the minimum diameter for accessibility
            # Planet size is radius, so divide by 2
            min_radius = self.MIN_TOUCH_SIZE // 2  # 32px radius = 64px diameter
            base_size = PlanetSprite.SIZES.get(planet.state, 50)
            size = max(base_size, min_radius)
            
            self.planet_sprites[planet.planet_id] = create_planet_sprite(planet, size, self.theme)
    
    def _update_path(self):
        """Update the path renderer."""
        visible_planets = self.map_state.get_visible_planets()
        if visible_planets:
            self.path_renderer = create_path_renderer(visible_planets)
    
    def _update_rocket(self):
        """Update the rocket indicator."""
        current = self.map_state.get_current_planet()
        if current:
            self.rocket_indicator = create_rocket_indicator(current.position)
    
    def update(self, delta_time: float):
        """
        Update animation and state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        # Update planet sprites
        for sprite in self.planet_sprites.values():
            sprite.update(delta_time)
        
        # Update path animation
        if self.path_renderer:
            self.path_renderer.update(delta_time)
        
        # Update rocket animation
        if self.rocket_indicator:
            self.rocket_indicator.update(delta_time)
    
    def draw(self):
        """Render the complete space map."""
        # Draw background starfield
        self._draw_starfield()
        
        # Draw connection path
        if self.path_renderer:
            self.path_renderer.draw(self.screen)
        
        # Draw planets
        for sprite in self.planet_sprites.values():
            self.screen.blit(sprite.get_surface(), sprite.get_rect())
        
        # Draw rocket indicator
        if self.rocket_indicator:
            self.rocket_indicator.draw(self.screen)
        
        # Draw UI overlay
        self._draw_ui_overlay()
    
    def _draw_starfield(self):
        """Draw a simple starfield background."""
        import random
        # Use deterministic seed for consistent stars
        random.seed(42)
        
        screen_rect = self.screen.get_rect()
        for _ in range(100):
            x = random.randint(0, screen_rect.width)
            y = random.randint(0, screen_rect.height)
            size = random.choice([1, 1, 1, 2])  # mostly small stars
            brightness = random.randint(150, 255)
            color = (brightness, brightness, min(200, brightness + 50))
            pygame.draw.circle(self.screen, color, (x, y), size)
    
    def _draw_ui_overlay(self):
        """Draw title and instructions overlay."""
        # Draw title
        if self._title_surface:
            title_pos = (
                (self.screen.get_width() - self._title_surface.get_width()) // 2,
                20
            )
            self.screen.blit(self._title_surface, title_pos)
        
        # Draw instructions
        if self._instructions_surface:
            instr_pos = (
                (self.screen.get_width() - self._instructions_surface.get_width()) // 2,
                self.screen.get_height() - 40
            )
            self.screen.blit(self._instructions_surface, instr_pos)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle input events.
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                return self._handle_click(event.pos)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self._handle_activate()
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                return self._move_focus_next()
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                return self._move_focus_previous()
            elif event.key == pygame.K_ESCAPE:
                return self._handle_escape()
        
        return False
    
    def _handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click."""
        # Check planets in reverse order (topmost first)
        for planet_id in reversed(list(self.planet_sprites.keys())):
            sprite = self.planet_sprites[planet_id]
            if sprite.is_point_inside(pos):
                return self._select_planet(sprite.planet)
        
        return False
    
    def _handle_activate(self) -> bool:
        """Handle enter/space key."""
        if self.keyboard_focus_id:
            planet = self.map_state.get_planet(self.keyboard_focus_id)
            if planet:
                return self._select_planet(planet)
        
        if self.selected_planet_id:
            # Return from details view
            self._deselect_planet()
            return True
        
        return False
    
    def _handle_escape(self) -> bool:
        """Handle escape key."""
        if self.selected_planet_id:
            self._deselect_planet()
            return True
        return False
    
    def _move_focus_next(self) -> bool:
        """Move keyboard focus to next planet."""
        visible = self.map_state.get_visible_planets()
        if not visible:
            return False
        
        if self.keyboard_focus_id:
            current_idx = next(
                (i for i, p in enumerate(visible) if p.planet_id == self.keyboard_focus_id),
                -1
            )
            next_idx = (current_idx + 1) % len(visible)
            self.keyboard_focus_id = visible[next_idx].planet_id
        else:
            self.keyboard_focus_id = visible[0].planet_id
        
        # Audio feedback
        if self.audio_system:
            self.audio_system.play_sfx('focus_change')
        
        return True
    
    def _move_focus_previous(self) -> bool:
        """Move keyboard focus to previous planet."""
        visible = self.map_state.get_visible_planets()
        if not visible:
            return False
        
        if self.keyboard_focus_id:
            current_idx = next(
                (i for i, p in enumerate(visible) if p.planet_id == self.keyboard_focus_id),
                0
            )
            prev_idx = (current_idx - 1) % len(visible)
            self.keyboard_focus_id = visible[prev_idx].planet_id
        
        # Audio feedback
        if self.audio_system:
            self.audio_system.play_sfx('focus_change')
        
        return True
    
    def _select_planet(self, planet: PlanetNode) -> bool:
        """Select a planet for details view."""
        if planet.state == PlanetState.LOCKED:
            return False
        
        if self.selected_planet_id != planet.planet_id:
            self.selected_planet_id = planet.planet_id
            self.keyboard_focus_id = planet.planet_id
            
            # Audio feedback
            if self.audio_system:
                self.audio_system.play_sfx('focus_change')
            
            # Callback
            if self.on_planet_selected:
                self.on_planet_selected(planet)
            
            return True
        
        return False
    
    def _deselect_planet(self):
        """Deselect current planet."""
        if self.selected_planet_id:
            self.selected_planet_id = None
            if self.on_return:
                self.on_return()
    
    def get_selected_planet(self) -> Optional[PlanetNode]:
        """Get the currently selected planet."""
        if self.selected_planet_id:
            return self.map_state.get_planet(self.selected_planet_id)
        return None
    
    def is_showing_details(self) -> bool:
        """Check if details view is showing."""
        return self.selected_planet_id is not None


def create_space_map_display(
    screen: pygame.Surface,
    map_state: SpaceMapState,
    audio_system: Optional[AudioSystem] = None
) -> SpaceMapDisplay:
    """Create a SpaceMapDisplay instance."""
    return SpaceMapDisplay(screen, map_state, audio_system)
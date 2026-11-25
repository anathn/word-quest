"""
Space Map Screen

Full-screen space map for students to view their progress through the galaxy.
Shows planets visited, completed, and current position with navigation.
"""

from typing import Optional, Callable, Dict, List, Tuple
import logging
import pygame

from src.models.map_state import SpaceMapState, PlanetNode, PlanetState
from src.ui.space_map import SpaceMapDisplay, create_space_map_display
from src.ui.planet_details import PlanetDetailsPanel, create_planet_details_panel
from src.components.audio_system import AudioSystem
from src.components.progress_tracker import ProgressTracker
from src.ui.typography import Typography

logger = logging.getLogger(__name__)


class SpaceMapScreen:
    """
    Full-screen space map display.
    
    Features:
    - Visual map of all planets in the galaxy
    - Planet states: locked, visited, completed, current
    - Click or keyboard navigation to explore planets
    - Planet details panel showing stats
    - Return to main menu or start game from current planet
    """
    
    def __init__(
        self,
        screen: pygame.Surface,
        progress_tracker: ProgressTracker,
        audio_system: Optional[AudioSystem],
        typography: Typography
    ):
        """
        Initialize space map screen.
        
        Args:
            screen: Pygame display surface
            progress_tracker: ProgressTracker with student progress
            audio_system: AudioSystem for sound feedback (optional)
            typography: Typography for text rendering
        """
        self.screen = screen
        self.progress_tracker = progress_tracker
        self.audio_system = audio_system
        self.typography = typography
        
        # Screen state
        self.active = False
        self.showing_details = False
        
        # Map state
        self.map_state: Optional[SpaceMapState] = None
        self.map_display: Optional[SpaceMapDisplay] = None
        self.details_panel: Optional[PlanetDetailsPanel] = None
        
        # Planet configuration
        self.planet_config = self._load_planet_config()
        self._initialize_map()
        
        # Callbacks
        self.on_return_to_menu: Optional[Callable[[], None]] = None
        self.on_start_game: Optional[Callable[[], None]] = None
        
        # Timing
        self._fade_alpha = 255  # For transition effects

        # Visible exit control
        self._back_button = pygame.Rect(24, 24, 140, 40)
        self._back_hover = False
    
    def _load_planet_config(self) -> Dict:
        """Load planet configuration (positions, names, colors)."""
        # Match the 12-planet galaxy used by word lists / ProgressTracker.
        palette = [
            (169, 169, 169), (255, 223, 186), (70, 130, 180), (205, 92, 92),
            (210, 180, 140), (238, 232, 170), (175, 238, 238), (100, 149, 237),
            (186, 104, 200), (255, 167, 38), (129, 199, 132), (79, 195, 247),
        ]
        names = [
            "Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn",
            "Uranus", "Neptune", "Planet 9", "Planet 10", "Planet 11", "Planet 12",
        ]
        planets = []
        for i, name in enumerate(names, start=1):
            planets.append({
                "id": f"planet_{i}",
                "name": name,
                "number": i,
                "color": palette[(i - 1) % len(palette)],
            })
        return {
            "planets": planets,
            "position_pattern": {
                "screen_width": 1024,
                "screen_height": 768,
                "center_x": 512,
                "center_y": 384,
                "horizontal_spacing": 78,
                "vertical_amplitude": 70,
                "starting_y": 450,
            },
        }
    
    def _initialize_map(self):
        """Initialize the space map with planets."""
        self.map_state = SpaceMapState()
        
        # Calculate positions based on pattern
        config = self.planet_config['position_pattern']
        
        for planet_data in self.planet_config['planets']:
            # Calculate position in arc pattern
            idx = planet_data['number'] - 1
            x = config['center_x'] + (idx - 5.5) * config['horizontal_spacing']
            
            # Gentle wave across the path
            y = config['starting_y'] + int(
                config['vertical_amplitude'] * ((idx % 3) - 1) * 0.45
            )
            
            # Create planet node
            planet = PlanetNode(
                planet_id=planet_data['id'],
                planet_name=planet_data['name'],
                planet_number=planet_data['number'],
                position=(x, y),
                state=PlanetState.LOCKED
            )
            
            self.map_state.planets.append(planet)
        
        # Generate positions for game window size
        screen_width, screen_height = self.screen.get_size()
        self._recalculate_positions(screen_width, screen_height)
        
        # Update from progress tracker
        self._update_from_progress()
    
    def _recalculate_positions(self, screen_width: int, screen_height: int):
        """Recalculate planet positions for current screen size."""
        # Scale factor based on screen size
        scale_x = screen_width / 1024
        scale_y = screen_height / 768
        scale = min(scale_x, scale_y)
        
        # Recalculate based on new screen size
        center_x = screen_width // 2
        horizontal_spacing = int(78 * scale)
        vertical_amplitude = int(70 * scale)
        starting_y = int(450 * scale_y)
        count = max(len(self.map_state.planets), 1)
        mid = (count - 1) / 2.0
        
        for i, planet in enumerate(self.map_state.planets):
            idx = planet.planet_number - 1
            x = center_x + (idx - mid) * horizontal_spacing
            y = starting_y + int(vertical_amplitude * ((idx % 3) - 1) * 0.45)
            planet.position = (x, y)
    
    def _update_from_progress(self):
        """Update planet states from progress tracker data."""
        completed_planets: List[str] = []
        visited_planets: List[str] = []
        current_planet_id = (
            self.map_state.planets[0].planet_id if self.map_state.planets else "planet_1"
        )
        
        # Safely extract progress data with robust defaults
        if hasattr(self.progress_tracker, 'galaxy_progress') and self.progress_tracker.galaxy_progress:
            galaxy = self.progress_tracker.galaxy_progress
            completed_count = max(0, int(getattr(galaxy, "completed_planets", 0) or 0))
            unlocked_count = max(1, int(getattr(galaxy, "unlocked_planets", 1) or 1))
            current_num = max(1, int(getattr(galaxy, "current_planet_number", 1) or 1))

            for planet in self.map_state.planets:
                if planet.planet_number <= completed_count:
                    completed_planets.append(planet.planet_id)
                elif planet.planet_number <= unlocked_count:
                    visited_planets.append(planet.planet_id)

            match = self.map_state.get_planet_by_number(
                min(current_num, len(self.map_state.planets) or 1)
            )
            if match:
                current_planet_id = match.planet_id
        
        # Always ensure at least first planet is current if no progress
        if not current_planet_id and self.map_state.planets:
            current_planet_id = self.map_state.planets[0].planet_id
        
        # Update map state
        self.map_state.update_from_progress(
            completed_planets=completed_planets,
            visited_planets=visited_planets,
            current_planet_id=current_planet_id
        )
        
        # Reinitialize display with updated state
        self._initialize_display()
    
    def _initialize_display(self):
        """Initialize the map display components."""
        # Create map display
        self.map_display = create_space_map_display(
            screen=self.screen,
            map_state=self.map_state,
            audio_system=self.audio_system
        )
        
        # Set up callbacks
        self.map_display.on_planet_selected = self._show_planet_details
        self.map_display.on_return = self._hide_planet_details
        
        # Set up planet details panel
        self.details_panel = create_planet_details_panel(
            screen=self.screen,
            typography=self.typography,
            audio_system=self.audio_system
        )
        
        self.details_panel.on_close = self._hide_planet_details
    
    def on_enter(self):
        """Called when screen becomes active."""
        self.active = True
        self.showing_details = False
        self._fade_alpha = 255
        
        # Recalculate positions for current screen size
        self._recalculate_positions(self.screen.get_width(), self.screen.get_height())
        
        # Update from current progress
        self._update_from_progress()
        
        # Initialize display
        self._initialize_display()
        
        # Optional ambient music (AudioSystem may not expose play_music)
        if self.audio_system and hasattr(self.audio_system, "play_music"):
            try:
                self.audio_system.play_music("GAMEPLAY")
            except Exception as e:
                logger.debug("Space map music unavailable: %s", e)
    
    def on_exit(self):
        """Called when screen becomes inactive."""
        self.active = False
        self.showing_details = False
        
        if self.audio_system and hasattr(self.audio_system, "stop_music"):
            try:
                self.audio_system.stop_music()
            except Exception as e:
                logger.debug("Space map stop_music unavailable: %s", e)
    
    def update(self, delta_time: float = 1.0 / 60.0):
        """
        Update screen state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        if self.map_display:
            self.map_display.update(delta_time)
        
        if self.details_panel:
            self.details_panel.update(delta_time)
        
        # Fade effect
        if self._fade_alpha > 0:
            self._fade_alpha = max(0, self._fade_alpha - 255 * delta_time)

        mouse_pos = pygame.mouse.get_pos()
        self._back_hover = self._back_button.collidepoint(mouse_pos)
    
    def draw(self):
        """Render the space map screen."""
        # Draw dark background
        self.screen.fill((10, 10, 30))
        
        # Draw map
        if self.map_display:
            self.map_display.draw()
        
        # Draw planet details panel if showing
        if self.showing_details and self.details_panel:
            self.details_panel.draw()

        self._draw_back_button()
        
        # Fade overlay for transitions
        if self._fade_alpha > 0:
            fade_surface = pygame.Surface(self.screen.get_size())
            fade_surface.set_alpha(int(self._fade_alpha))
            fade_surface.fill((0, 0, 0))
            self.screen.blit(fade_surface, (0, 0))

    def _draw_back_button(self) -> None:
        """Draw the Main Menu exit button."""
        color = (120, 144, 156) if self._back_hover else (96, 125, 139)
        pygame.draw.rect(self.screen, color, self._back_button, border_radius=6)
        pygame.draw.rect(self.screen, (255, 255, 255), self._back_button, 2, border_radius=6)
        font = pygame.font.Font(None, 28)
        label = font.render("Main Menu", True, (255, 255, 255))
        self.screen.blit(label, label.get_rect(center=self._back_button.center))
    
    def handle_event(self, event: pygame.event.Event):
        """
        Handle input events.
        
        Args:
            event: Pygame event
        """
        if event.type == pygame.MOUSEMOTION:
            self._back_hover = self._back_button.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._back_button.collidepoint(event.pos):
                self._return_to_menu()
                return

        if self.showing_details and self.details_panel:
            self.details_panel.handle_event(event)
            return
        
        if self.map_display:
            if self.map_display.handle_event(event):
                return
        
        # Global key handling
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.showing_details:
                    self._hide_planet_details()
                else:
                    self._return_to_menu()

    def _return_to_menu(self) -> None:
        """Leave the space map and return to the main menu."""
        if self.on_return_to_menu:
            self.on_return_to_menu()
    
    def _show_planet_details(self, planet: PlanetNode):
        """Show planet details panel."""
        if self.details_panel:
            self.details_panel.set_planet(planet)
            self.showing_details = True
    
    def _hide_planet_details(self):
        """Hide planet details panel."""
        self.showing_details = False


def create_space_map_screen(
    screen: pygame.Surface,
    progress_tracker: ProgressTracker,
    audio_system: Optional[AudioSystem],
    typography: Typography
) -> SpaceMapScreen:
    """Create a SpaceMapScreen instance."""
    return SpaceMapScreen(screen, progress_tracker, audio_system, typography)

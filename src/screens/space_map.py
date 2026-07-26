"""
Space Map Screen

Full-screen space map for students to view their progress through the galaxy.
Shows planets visited, completed, and current position with navigation.
"""

from typing import Optional, Callable, Dict, List, Tuple
import pygame

from src.models.map_state import SpaceMapState, PlanetNode, PlanetState
from src.ui.space_map import SpaceMapDisplay, create_space_map_display
from src.ui.planet_details import PlanetDetailsPanel, create_planet_details_panel
from src.components.audio_system import AudioSystem
from src.components.progress_tracker import ProgressTracker
from src.ui.typography import Typography


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
        audio_system: AudioSystem,
        typography: Typography
    ):
        """
        Initialize space map screen.
        
        Args:
            screen: Pygame display surface
            progress_tracker: ProgressTracker with student progress
            audio_system: AudioSystem for sound feedback
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
    
    def _load_planet_config(self) -> Dict:
        """Load planet configuration (positions, names, colors)."""
        # Configuration for 8 planets in the solar system
        # Positions arranged in a gentle arc across screen
        return {
            'planets': [
                {'id': 'planet_1', 'name': 'Mercury', 'number': 1, 'color': (169, 169, 169)},
                {'id': 'planet_2', 'name': 'Venus', 'number': 2, 'color': (255, 223, 186)},
                {'id': 'planet_3', 'name': 'Earth', 'number': 3, 'color': (70, 130, 180)},
                {'id': 'planet_4', 'name': 'Mars', 'number': 4, 'color': (205, 92, 92)},
                {'id': 'planet_5', 'name': 'Jupiter', 'number': 5, 'color': (210, 180, 140)},
                {'id': 'planet_6', 'name': 'Saturn', 'number': 6, 'color': (238, 232, 170)},
                {'id': 'planet_7', 'name': 'Uranus', 'number': 7, 'color': (175, 238, 238)},
                {'id': 'planet_8', 'name': 'Neptune', 'number': 8, 'color': (100, 149, 237)},
            ],
            'position_pattern': {
                'screen_width': 1024,
                'screen_height': 768,
                'center_x': 512,
                'center_y': 384,
                'horizontal_spacing': 110,
                'vertical_amplitude': 80,
                'starting_y': 450
            }
        }
    
    def _initialize_map(self):
        """Initialize the space map with planets."""
        self.map_state = SpaceMapState()
        
        # Calculate positions based on pattern
        config = self.planet_config['position_pattern']
        
        for planet_data in self.planet_config['planets']:
            # Calculate position in弧形 pattern
            idx = planet_data['number'] - 1
            x = config['center_x'] + (idx - 3.5) * config['horizontal_spacing']
            
            # Arc pattern - planets 1-4 curve down, 5-8 curve up
            if idx < 4:
                y = config['starting_y'] + int(
                    config['vertical_amplitude'] * (1 - abs(idx - 1.5) / 2.5)
                )
            else:
                y = config['center_y'] + int(
                    config['vertical_amplitude'] * abs(idx - 5.5) / 3
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
        center_y = screen_height // 2
        horizontal_spacing = int(110 * scale)
        vertical_amplitude = int(80 * scale)
        starting_y = int(450 * scale_y)
        
        for i, planet in enumerate(self.map_state.planets):
            idx = planet.planet_number - 1
            x = center_x + (idx - 3.5) * horizontal_spacing
            
            # Arc pattern
            if idx < 4:
                y = starting_y + int(vertical_amplitude * (1 - abs(idx - 1.5) / 2.5))
            else:
                y = center_y + int(vertical_amplitude * abs(idx - 5.5) / 3)
            
            planet.position = (x, y)
    
    def _update_from_progress(self):
        """Update planet states from progress tracker data."""
        completed_planets = []
        visited_planets = []
        current_planet_id = 'planet_1'  # Default to first planet
        
        # Safely extract progress data with robust defaults
        if hasattr(self.progress_tracker, 'galaxy_progress') and self.progress_tracker.galaxy_progress:
            galaxy = self.progress_tracker.galaxy_progress
            if hasattr(galaxy, 'current_planet_number'):
                current_num = galaxy.current_planet_number
                current_planet_id = f'planet_{current_num}'
                
                # All planets before current are completed
                for planet in self.map_state.planets:
                    if planet.planet_number < current_num:
                        completed_planets.append(planet.planet_id)
        
        # Fallback: check breadcrumb tracking if available
        if hasattr(self.progress_tracker, '_completed_planet_ids') and self.progress_tracker._completed_planet_ids:
            # Filter to only valid planet IDs
            valid_ids = {p.planet_id for p in self.map_state.planets}
            completed_planets = list(set(completed_planets) & valid_ids)
        
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
        
        # Play ambient space music
        if self.audio_system:
            self.audio_system.play_music('GAMEPLAY')
    
    def on_exit(self):
        """Called when screen becomes inactive."""
        self.active = False
        self.showing_details = False
        
        # Stop music
        if self.audio_system:
            self.audio_system.stop_music()
    
    def update(self, delta_time: float):
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
        
        # Fade overlay for transitions
        if self._fade_alpha > 0:
            fade_surface = pygame.Surface(self.screen.get_size())
            fade_surface.set_alpha(self._fade_alpha)
            fade_surface.fill((0, 0, 0))
            self.screen.blit(fade_surface, (0, 0))
    
    def handle_event(self, event: pygame.event.Event):
        """
        Handle input events.
        
        Args:
            event: Pygame event
        """
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
                elif self.on_return_to_menu:
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
    audio_system: AudioSystem,
    typography: Typography
) -> SpaceMapScreen:
    """Create a SpaceMapScreen instance."""
    return SpaceMapScreen(screen, progress_tracker, audio_system, typography)
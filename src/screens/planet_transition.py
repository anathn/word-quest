"""
Planet Transition Screen

Handles animation of rocket traveling between planets with:
- Rocket travel animation across star field
- Planet name/number display during transition
- Progress bar showing galaxy progress
- Skip animation functionality
- Transition sound effects
"""

from typing import Optional, Callable, Tuple
from dataclasses import dataclass
import math
import time

import pygame

from src.components.audio_system import AudioSystem
from src.ui.typography import Typography
from src.ui.star_field import StarField
from src.ui.rocket_animator import RocketAnimator
from src.ui.rocket_sprite import RocketSprite
from src.ui.animations import ProgressBarAnimator
from src.ui.theme import get_theme


@dataclass
class PlanetInfo:
    """Information about a planet for display."""
    planet_id: str
    planet_name: str
    planet_number: int
    total_planets: int


class PlanetTransitionScreen:
    """
    Animation screen for planet travel transitions.
    
    Features:
    - Rocket flies from departure to destination planet
    - Planet names displayed on screen edges
    - Progress bar shows galaxy completion percentage
    - Can skip animation with space key or click
    - Plays transition sound effect
    """
    
    def __init__(self, typography: Typography, audio_system: AudioSystem):
        """
        Initialize the transition screen.
        
        Args:
            typography: Typography instance for text rendering
            audio_system: AudioSystem instance for audio
        """
        self.typography = typography
        self.audio_system = audio_system
        
        # State
        self.is_running = False
        self.animation_progress = 0.0  # 0.0 to 1.0
        self.skip_requested = False
        self._skip_lock = False  # Prevents multiple skip triggers until animation completes
        self.start_time = 0

        # Planets
        self.from_planet: Optional[PlanetInfo] = None
        self.to_planet: Optional[PlanetInfo] = None
        
        # Progress tracking
        self.galaxy_progress = 0.0  # 0.0 to 1.0
        
        # Components
        self.star_field: Optional[StarField] = None
        self.rocket_animator: Optional[RocketAnimator] = None
        self.progress_bar_animator: Optional[ProgressBarAnimator] = None
        
        # Configuration
        self.animation_duration = 2.0  # 2 seconds (can be configured via game settings)
        self.width = 800
        self.height = 600
        
        # Callbacks
        self.on_transition_complete: Optional[Callable[[], None]] = None
        
        # Colors
        self.space_blue = (26, 26, 62)
        self.white = (255, 255, 255)
        self.green = (0, 200, 83)
        self.yellow = (255, 215, 0)
    
    def start_transition(
        self,
        from_planet: PlanetInfo,
        to_planet: PlanetInfo,
        galaxy_progress: float,
        skip: bool = False
    ):
        """
        Start the transition animation.
        
        Args:
            from_planet: Departure planet info
            to_planet: Destination planet info
            galaxy_progress: Overall galaxy completion (0.0 to 1.0)
            skip: If True, skip animation and go directly to end
        """
        # Validate destination planet exists
        if to_planet.planet_number > to_planet.total_planets:
            # Galaxy is complete - no next planet available
            self._handle_galaxy_complete()
            return
        
        self.from_planet = from_planet
        self.to_planet = to_planet
        self.galaxy_progress = galaxy_progress
        self.skip_requested = skip
        self.is_running = True
        self.animation_progress = 0.0
        self.start_time = time.time()
        
        # Initialize components
        self.star_field = StarField(self.width, self.height)
        
        # Create rocket sprite with current color from RocketConfig
        try:
            from src.profiles.student_profile import get_current_student_id
            from src.models.rocket_config import RocketConfig
            player_id = get_current_student_id()
            rocket_config = RocketConfig(player_id)
            rocket_color = rocket_config.get_current_color()
        except Exception:
            # Default to white rocket if no student logged in
            rocket_color = (255, 255, 255)
        
        rocket_sprite = RocketSprite(color=rocket_color, size=64)
        self.rocket_animator = RocketAnimator(rocket_sprite)
        
        self.progress_bar_animator = ProgressBarAnimator()
        
        # Reset skip lock for new transition
        self._skip_lock = False
        
        # Play transition sound
        self._play_transition_audio()
    
    def _play_transition_audio(self):
        """Play transition sound effects."""
        # Try to play transition SFX
        if self.audio_system:
            # Play whoosh sound at start
            try:
                self.audio_system.play_sfx("transition")
            except Exception as e:
                print(f"Transition SFX not available: {e}")
            
            # Speak destination planet name
            if self.to_planet:
                self.audio_system.speak(
                    f"Traveling to Planet {self.to_planet.planet_name}"
                )
    
    def _handle_galaxy_complete(self):
        """Handle the case where galaxy is complete and no next planet exists."""
        # Notify callback that galaxy is complete
        if self.on_transition_complete:
            # Pass a flag or special data to indicate galaxy complete
            # For now, just call the callback - the parent screen can handle it
            self.on_transition_complete()
        
        # Reset state
        self.is_running = False
        self.animation_progress = 1.0
    
    def handle_events(self, events):
        """
        Handle pygame events.
        
        Args:
            events: List of pygame events
        """
        # Only handle skip events if lock is not active
        if self._skip_lock:
            return
            
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.skip_requested = True
                    self._skip_lock = True  # Lock until animation completes
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Click to skip
                self.skip_requested = True
                self._skip_lock = True  # Lock until animation completes
    
    def update(self, delta_time: float):
        """
        Update transition animation.
        
        Args:
            delta_time: Time since last update in seconds
        """
        if not self.is_running:
            return
        
        # Handle skip
        if self.skip_requested:
            self.animation_progress = 1.0
            self._complete_transition()
            return
        
        # Check if skip was requested
        if self.skip_requested:
            self.animation_progress = 1.0
            self._complete_transition()
            return
        
        # Update animation progress
        self.animation_progress += delta_time / self.animation_duration
        self.animation_progress = min(1.0, self.animation_progress)
        
        if self.animation_progress >= 1.0:
            self._complete_transition()
        
        # Update components
        if self.star_field:
            self.star_field.update(self.animation_progress, delta_time)
        if self.rocket_animator:
            self.rocket_animator.update(self.start_time + delta_time)
        if self.progress_bar_animator:
            self.progress_bar_animator.set_target(self.galaxy_progress)
            self.progress_bar_animator.update(delta_time)
    
    def _complete_transition(self):
        """Complete the transition and notify callback."""
        self.is_running = False
        self._skip_lock = False  # Release skip lock when complete
        if self.on_transition_complete:
            self.on_transition_complete()
    
    def render(self, screen):
        """
        Render the transition screen.
        
        Args:
            screen: Pygame screen surface
        """
        if not self.is_running:
            return
        
        # Draw star field background
        if self.star_field:
            self.star_field.draw(screen)
        
        # Draw departure planet (left side)
        if self.from_planet:
            self._draw_planet_indicator(
                screen, self.from_planet, "left", is_departure=True
            )
        
        # Draw destination planet (right side)
        if self.to_planet:
            self._draw_planet_indicator(
                screen, self.to_planet, "right", is_departure=False
            )
        
        # Draw rocket
        if self.rocket_animator:
            rocket_x = int(self.width * 0.5)
            rocket_y = int(self.height * 0.5)
            
            # Calculate trajectory (slight arc)
            arc_offset = math.sin(self.animation_progress * math.pi) * 50
            rocket_y = int(self.height * 0.5 - arc_offset)
            
            # Calculate rotation angle based on trajectory
            # Rocket tilts up in the middle of the arc, levels out at start/end
            # Use derivative of the arc function to get angle
            angle = math.cos(self.animation_progress * math.pi) * 0.3  # ~17 degrees max tilt
            
            self.rocket_animator.draw(screen, rocket_x, rocket_y, angle)
        
        # Draw traveling text
        self._draw_traveling_text(screen)
        
        # Draw progress bar
        self._draw_progress_bar(screen)
        
        # Draw skip hint
        self._draw_skip_hint(screen)
    
    def _draw_planet_indicator(
        self, screen, planet: PlanetInfo, side: str, is_departure: bool
    ):
        """
        Draw a planet indicator on the screen edge.
        
        Args:
            screen: Pygame screen surface
            planet: Planet info to display
            side: "left" or "right"
            is_departure: Whether this is the departure planet
        """
        margin = 60
        x = margin if side == "left" else self.width - margin
        
        # Draw planet circle
        planet_radius = 40
        color = (100, 100, 200) if is_departure else self.yellow
        if planet.planet_number == self.to_planet.planet_number if self.to_planet else False:
            color = self.green  # Destination highlighted
        
        pygame.draw.circle(screen, color, (x, margin + planet_radius), planet_radius)
        
        # Draw planet name
        font = self.typography.get_font(
            self.typography.style_default,
            size=self.typography.FONT_MEDIUM
        )
        if font:
            name_text = planet.planet_name
            name_surface = font.render(name_text, True, self.white)
            name_rect = name_surface.get_rect(centerx=x, top=margin + planet_radius + 15)
            screen.blit(name_surface, name_rect)
    
    def _draw_traveling_text(self, screen):
        """Draw the traveling message."""
        if not self.to_planet:
            return
        
        font = self.typography.get_font(
            self.typography.style_header,
            size=self.typography.FONT_XLARGE
        )
        
        if font:
            message = f"Traveling to Planet {self.to_planet.planet_name}..."
            text_surface = font.render(message, True, self.white)
            text_rect = text_surface.get_rect(
                centerx=self.width // 2,
                top=self.height // 2 - 100
            )
            screen.blit(text_surface, text_rect)
    
    def _draw_progress_bar(self, screen):
        """Draw the galaxy progress bar."""
        bar_width = 400
        bar_height = 20
        bar_x = (self.width - bar_width) // 2
        bar_y = self.height - 80
        
        # Use the ProgressBarAnimator for smooth animation
        if self.progress_bar_animator:
            self.progress_bar_animator.draw(screen, bar_x, bar_y, bar_width, bar_height)
        
        # Progress text
        font = self.typography.get_font(
            self.typography.style_default,
            size=self.typography.FONT_SMALL
        )
        
        if font:
            if self.to_planet:
                progress_text = f"{self.to_planet.planet_number}/{self.to_planet.total_planets} planets"
            else:
                progress_text = f"Progress: {int(self.galaxy_progress * 100)}%"
            
            text_surface = font.render(progress_text, True, self.white)
            text_rect = text_surface.get_rect(centerx=self.width // 2, bottom=bar_y - 10)
            screen.blit(text_surface, text_rect)
    
    def _draw_skip_hint(self, screen):
        """Draw the skip animation hint."""
        font = self.typography.get_font(
            self.typography.style_caption,
            size=self.typography.FONT_TINY
        )
        
        if font:
            skip_text = "Press SPACE or click to skip"
            text_surface = font.render(skip_text, True, (200, 200, 200))
            text_rect = text_surface.get_rect(
                centerx=self.width // 2,
                bottom=self.height - 20
            )
            screen.blit(text_surface, text_rect)
    
    def is_complete(self) -> bool:
        """Check if transition animation is complete."""
        return not self.is_running or self.animation_progress >= 1.0
    
    def get_progress(self) -> float:
        """Get current animation progress (0.0 to 1.0)."""
        return self.animation_progress
    
    def set_animation_duration(self, duration: float):
        """
        Set the animation duration.
        
        Args:
            duration: Duration in seconds
        """
        self.animation_duration = max(0.5, min(5.0, duration))  # Clamp between 0.5 and 5 seconds
    
    def reset(self):
        """Reset the transition screen to initial state."""
        self.is_running = False
        self.animation_progress = 0.0
        self.skip_requested = False
        self._skip_lock = False
        self.from_planet = None
        self.to_planet = None
        self.galaxy_progress = 0.0
        self.star_field = None
        self.rocket_animator = None
        self.progress_bar_animator = None


# Factory function
def create_planet_transition_screen(
    typography: Typography,
    audio_system: AudioSystem
) -> PlanetTransitionScreen:
    """
    Create a PlanetTransitionScreen instance.
    
    Args:
        typography: Typography instance
        audio_system: AudioSystem instance
        
    Returns:
        Configured PlanetTransitionScreen instance
    """
    return PlanetTransitionScreen(typography, audio_system)

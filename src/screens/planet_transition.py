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


@dataclass
class PlanetInfo:
    """Information about a planet for display."""
    planet_id: str
    planet_name: str
    planet_number: int
    total_planets: int


class RocketAnimator:
    """
    Handles rocket sprite movement and visual effects.
    
    Creates a simple rocket ship with engine flame animation
    using pygame drawing primitives.
    """
    
    def __init__(self, color: Tuple[int, int, int] = (200, 200, 200)):
        """
        Initialize the rocket animator.
        
        Args:
            color: Rocket body color (RGB tuple)
        """
        self.color = color
        self.flame_offset = 0.0
        self.flame_direction = 1
        self.rocket_width = 60
        self.rocket_height = 120
        
        # Animation timing
        self.last_frame_time = 0
        self.frame_interval = 0.1  # 100ms per frame
    
    def update(self, current_time: float):
        """
        Update animation state.
        
        Args:
            current_time: Current time in seconds
        """
        # Animate flame
        if current_time - self.last_frame_time >= self.frame_interval:
            self.flame_offset += 0.5 * self.flame_direction
            if self.flame_offset >= 1.0 or self.flame_offset <= 0.0:
                self.flame_direction *= -1
            self.last_frame_time = current_time
    
    def draw(self, screen, x: int, y: int, angle: float = 0):
        """
        Draw the rocket at the given position.
        
        Args:
            screen: Pygame screen surface
            x: X position (center)
            y: Y position (center)
            angle: Rotation angle in radians (optional)
        """
        # Create a surface for the rocket
        rocket_surface = pygame.Surface((self.rocket_width, self.rocket_height), pygame.SRCALPHA)
        
        # Rocket body (ellipse)
        body_color = self.color
        pygame.draw.ellipse(rocket_surface, body_color, (5, 20, 50, 80))
        
        # Rocket nose cone
        nose_points = [
            (30, 0),   # Top center
            (55, 35),  # Right base
            (5, 35)    # Left base
        ]
        pygame.draw.polygon(rocket_surface, (220, 220, 220), nose_points)
        
        # Rocket fins
        left_fin_points = [
            (5, 60),
            (0, 90),
            (15, 70)
        ]
        right_fin_points = [
            (55, 60),
            (60, 90),
            (45, 70)
        ]
        pygame.draw.polygon(rocket_surface, (180, 180, 180), left_fin_points)
        pygame.draw.polygon(rocket_surface, (180, 180, 180), right_fin_points)
        
        # Window
        window_color = (135, 206, 235)  # Sky blue
        pygame.draw.circle(rocket_surface, window_color, (30, 50), 15)
        pygame.draw.circle(rocket_surface, (200, 200, 200), (30, 50), 15, 3)
        
        # Engine flame
        flame_width = 20
        flame_height = int(30 * (0.5 + 0.5 * (1 - abs(self.flame_offset))))
        flame_points = [
            (30 - flame_width // 2, 100),
            (30, 100 + flame_height),
            (30 + flame_width // 2, 100)
        ]
        flame_color = (255, int(100 * self.flame_offset + 100), 0)
        pygame.draw.polygon(rocket_surface, flame_color, flame_points)
        
        # Rotate if needed
        if angle != 0:
            rotated_surface = pygame.transform.rotate(rocket_surface, math.degrees(angle))
            rect = rotated_surface.get_rect(center=(x, y))
            screen.blit(rotated_surface, rect.topleft)
        else:
            rect = rocket_surface.get_rect(center=(x, y))
            screen.blit(rocket_surface, rect.topleft)


class StarField:
    """
    Star field background with motion blur effect.
    
    Creates a space background with twinkling stars that
    appear to move during rocket travel.
    """
    
    def __init__(self, width: int = 800, height: int = 600, num_stars: int = 100):
        """
        Initialize the star field.
        
        Args:
            width: Screen width
            height: Screen height
            num_stars: Number of stars to generate
        """
        self.width = width
        self.height = height
        self.stars = []
        self.motion_offset = 0
        self.twinkle_timer = 0
        
        # Generate random stars
        import random
        for _ in range(num_stars):
            self.stars.append({
                'x': random.randint(0, width),
                'y': random.randint(0, height),
                'size': random.randint(1, 3),
                'brightness': random.random(),
                'twinkle_speed': random.uniform(0.01, 0.05)
            })
    
    def update(self, progress: float, delta_time: float):
        """
        Update star field for motion effect.
        
        Args:
            progress: Animation progress (0.0 to 1.0)
            delta_time: Time since last update in seconds
        """
        # Create motion blur effect based on progress
        self.motion_offset += progress * 2 * delta_time
        
        # Update twinkle
        self.twinkle_timer += delta_time
        for star in self.stars:
            star['brightness'] += star['twinkle_speed']
            if star['brightness'] >= 1.0 or star['brightness'] <= 0.3:
                star['twinkle_speed'] *= -1
    
    def draw(self, screen):
        """
        Draw the star field.
        
        Args:
            screen: Pygame screen surface
        """
        # Draw space background
        screen.fill((26, 26, 62))  # Deep space blue
        
        # Draw stars with motion blur and twinkle
        for star in self.stars:
            # Apply motion offset
            x = (star['x'] - self.motion_offset) % self.width
            y = star['y']
            
            # Calculate brightness
            brightness = int(255 * star['brightness'])
            color = (brightness, brightness, brightness + 50)
            
            # Draw star
            pygame.draw.circle(screen, color, (int(x), int(y)), star['size'])


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
        self.start_time = 0
        
        # Planets
        self.from_planet: Optional[PlanetInfo] = None
        self.to_planet: Optional[PlanetInfo] = None
        
        # Progress tracking
        self.galaxy_progress = 0.0  # 0.0 to 1.0
        
        # Components
        self.star_field: Optional[StarField] = None
        self.rocket_animator: Optional[RocketAnimator] = None
        
        # Configuration
        self.animation_duration = 2.0  # 2 seconds
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
        self.from_planet = from_planet
        self.to_planet = to_planet
        self.galaxy_progress = galaxy_progress
        self.skip_requested = skip
        self.is_running = True
        self.animation_progress = 0.0
        self.start_time = time.time()
        
        # Initialize components
        self.star_field = StarField(self.width, self.height)
        self.rocket_animator = RocketAnimator()
        
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
    
    def handle_events(self, events):
        """
        Handle pygame events.
        
        Args:
            events: List of pygame events
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.skip_requested = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Click to skip
                self.skip_requested = True
    
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
    
    def _complete_transition(self):
        """Complete the transition and notify callback."""
        self.is_running = False
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
            
            # Angle based on progress
            angle = 0  # Could add rotation for realism
            
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
        
        # Background
        pygame.draw.rect(screen, (60, 60, 80), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, self.white, (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Fill
        fill_width = int(bar_width * self.galaxy_progress)
        pygame.draw.rect(screen, self.green, (bar_x, bar_y, fill_width, bar_height))
        
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
    
    def reset(self):
        """Reset the transition screen to initial state."""
        self.is_running = False
        self.animation_progress = 0.0
        self.skip_requested = False
        self.from_planet = None
        self.to_planet = None
        self.galaxy_progress = 0.0
        self.star_field = None
        self.rocket_animator = None


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

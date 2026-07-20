"""
Celebration screen for planet completion.

Displays full bloom celebration with sparkles, crystals, and rocket animation
when a planet is completed.
"""

from typing import Optional, Callable, Tuple
import pygame

from src.ui.theme import get_theme
from src.ui.planet_sprite import PlanetSprite
from src.ui.planet_bloom import PlanetBloom, create_planet_bloom
from src.ui.sparkle_effect import SparkleEffect, create_sparkle_effect
from src.ui.celebration_renderer import CelebrationRenderer, create_celebration_renderer
from src.components.audio_system import AudioSystem


class CelebrationScreen:
    """
    Full-screen celebration for planet completion.
    Shows bloom animation, sparkles, and rocket circling.
    """
    
    def __init__(self, typography: object, audio_system: AudioSystem):
        """
        Initialize celebration screen.
        
        Args:
            typography: Typography instance for text rendering
            audio_system: AudioSystem instance for audio feedback
        """
        self.typography = typography
        self.audio_system = audio_system
        
        # Celebration components
        self.planet: Optional[PlanetSprite] = None
        self.bloom: Optional[PlanetBloom] = None
        self.sparkles: Optional[SparkleEffect] = None
        self.celebration: Optional[CelebrationRenderer] = None
        
        # Configuration
        self.planet_number = 1
        self.planet_size = 150
        self.planet_position = (400, 300)  # Center of screen
        
        # State
        self.active = False
        self.showing = False
        
        # Callbacks
        self.on_continue: Optional[Callable[[], None]] = None
        
        # Timing
        self._show_duration = 3.0  # Show celebration for 3 seconds
        self._show_timer = 0.0
    
    def on_enter(self):
        """Called when screen becomes active."""
        self._show_timer = 0.0
        
        # Initialize celebration components
        self.planet = PlanetSprite(self.planet_number, self.planet_size)
        self.bloom = create_planet_bloom(self.planet, self.planet_number)
        self.sparkles = create_sparkle_effect(self.planet_position)
        self.celebration = create_celebration_renderer(
            planet_bloom=self.bloom,
            sparkles=self.sparkles,
            rocket=None  # Rocket celebration can be added later
        )
        
        # Start celebration
        self.celebration.start_celebration(self.planet_position)
        
        # Play victory fanfare
        if self.audio_system:
            self.audio_system.play_victory_fanfare()
    
    def on_exit(self):
        """Called when screen becomes inactive."""
        self.active = False
        self.showing = False
        
        # Stop celebration
        if self.celebration:
            self.celebration.stop_celebration()
    
    def start_celebration(self, planet_number: int = 1):
        """
        Start the celebration animation.
        
        Args:
            planet_number: Which planet is being celebrated (1-5)
        """
        self.planet_number = planet_number
        self.active = True
        self.showing = True
        self._show_timer = 0.0
    
    def update(self, delta_time: float) -> bool:
        """
        Update celebration state.
        
        Args:
            delta_time: Time since last update in seconds
            
        Returns:
            True if celebration is complete
        """
        if not self.active:
            return True
        
        self._show_timer += delta_time
        
        # Update celebration
        if self.celebration:
            self.celebration.update(delta_time)
            
            # Check if celebration is complete
            if self.celebration.is_complete():
                self.active = False
                return True
        
        # Also auto-complete after duration
        if self._show_timer >= self._show_duration:
            if self.celebration:
                self.celebration.stop_celebration()
            self.active = False
            return True
        
        return False
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render celebration to screen.
        
        Args:
            screen: Pygame surface to render on
        """
        if not self.active and not self.celebration:
            return
        
        # Clear screen with space theme background
        screen.fill((26, 26, 62))  # Deep space blue
        
        # Render celebration
        if self.celebration:
            self.celebration.render(screen)
        
        # Draw "Planet Complete!" message
        if self.typography:
            font = self.typography.get_font_large()
            text = font.render("Planet Complete!", True, (255, 255, 255))
            text_rect = text.get_rect(center=(400, 150))
            screen.blit(text, text_rect)
            
            # Draw "Press any key to continue" after completion
            if self.active == False and self.celebration and self.celebration.is_complete():
                font_small = self.typography.get_font_small()
                continue_text = font_small.render("Press any key to continue", True, (255, 255, 255))
                continue_rect = continue_text.get_rect(center=(400, 500))
                screen.blit(continue_text, continue_rect)
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Handle input events.
        
        Args:
            event: Pygame event
        """
        if event.type == pygame.KEYDOWN:
            if self.active == False and self.celebration and self.celebration.is_complete():
                # Celebration complete, allow continuation
                if self.on_continue:
                    self.on_continue()
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.active == False and self.celebration and self.celebration.is_complete():
                if self.on_continue:
                    self.on_continue()
    
    def is_complete(self) -> bool:
        """
        Check if celebration has completed.
        
        Returns:
            True if celebration finished
        """
        return not self.active
    
    def force_complete(self) -> None:
        """Force complete the celebration (for accessibility)."""
        if self.celebration:
            self.celebration.stop_celebration()
        self.active = False


def create_celebration_screen(typography: object, audio_system: AudioSystem) -> CelebrationScreen:
    """
    Factory function to create a celebration screen.
    
    Args:
        typography: Typography instance
        audio_system: AudioSystem instance
        
    Returns:
        Configured CelebrationScreen instance
    """
    return CelebrationScreen(typography, audio_system)
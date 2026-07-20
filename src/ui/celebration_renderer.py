"""
Celebration scene manager for planet completion.

Orchestrates bloom animations, sparkle effects, and rocket celebrations
for a complete planet completion experience.
"""

from typing import Optional, Tuple, Callable
import pygame

from .planet_bloom import PlanetBloom, BloomState, create_planet_bloom
from .sparkle_effect import SparkleEffect, create_sparkle_effect


class CelebrationState:
    """Celebration animation states."""
    IDLE = "idle"
    STARTING = "starting"
    CELEBRATING = "celebrating"
    COMPLETING = "completing"
    COMPLETE = "complete"


class CelebrationRenderer:
    """
    Orchestrates the full celebration scene for planet completion.
    Manages bloom, sparkles, rocket animation, and timing.
    """
    
    # Configuration
    DEFAULT_MAX_SPARKLES = 100
    STAR_EMIT_RATE = 0.1  # Emit sparkles every 100ms during celebration
    
    # Accessibility: reduced intensity mode
    REDUCED_MAX_SPARKLES = 50
    
    def __init__(self):
        """Initialize celebration renderer."""
        self.planet_bloom: Optional[PlanetBloom] = None
        self.sparkles: Optional[SparkleEffect] = None
        self.rocket = None  # Will be set if rocket celebration is enabled
        
        self.state = CelebrationState.IDLE
        self.active = False
        self.planet_position: Tuple[float, float] = (400, 300)  # Default center
        
        # Racing rocket on hover animation
        self._celebration_timer = 0.0
        self._bubble_timer = 0.0
        
        # Configuration
        self.rocket_celebration_enabled = True
        
        # Callbacks
        self.on_celebration_complete: Optional[Callable[[], None]] = None
        
        # Accessibility: intensity mode
        self.reduced_intensity = False
    
    def set_components(self, planet_bloom: Optional[PlanetBloom] = None,
                       sparkle_effect: Optional[SparkleEffect] = None,
                       rocket: Optional[object] = None) -> None:
        """
        Set celebration components.
        
        Args:
            planet_bloom: Planet bloom animation
            sparkle_effect: Sparkle particle system
            rocket: Rocket sprite for celebration (optional)
        """
        if planet_bloom:
            self.planet_bloom = planet_bloom
        if sparkle_effect:
            self.sparkles = sparkle_effect
        self.rocket = rocket
    
    def start_celebration(self, planet_position: Tuple[float, float]) -> None:
        """
        Begin planet completion celebration.
        
        Args:
            planet_position: (x, y) center position of planet
        """
        self.active = True
        self.state = CelebrationState.STARTING
        self.planet_position = planet_position
        self._celebration_timer = 0.0
        self._bubble_timer = 0.0
        
        # Initialize components
        if self.planet_bloom:
            self.planet_bloom.start_bloom()
        
        if self.sparkles:
            self.sparkles.set_center(planet_position)
            self.sparkles.start()
            # Initial burst
            self.sparkles.emit(count=10)
        
        # Animate rocket
        if self.rocket and self.rocket_celebration_enabled:
            if hasattr(self.rocket, 'start_celebration'):
                self.rocket.start_celebration()
    
    def update(self, delta_time: float) -> None:
        """
        Update celebration state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        if not self.active:
            return
        
        if self.state == CelebrationState.STARTING:
            self.state = CelebrationState.CELEBRATING
            self._celebration_timer = 0.0
        
        elif self.state == CelebrationState.CELEBRATING:
            self._celebration_timer += delta_time
            
            # Update components
            if self.planet_bloom:
                self.planet_bloom.update(delta_time)
            
            if self.sparkles:
                self.sparkles.update(delta_time)
            
            # Emit sparkles during bloom
            if self.planet_bloom and self.planet_bloom.state in [
                BloomState.BLOOMING, BloomState.HOLDING
            ]:
                # Emit more sparkles at peak intensity
                intensity = self.planet_bloom._get_intensity()
                emit_count = max(1, int(3 * intensity))
                self.sparkles.emit(count=emit_count)
            
            # Animate rocket circling planet
            if self.rocket and self.rocket_celebration_enabled:
                if hasattr(self.rocket, 'update_celebration'):
                    self.rocket.update_celebration(
                        self.planet_position, delta_time
                    )
            
            # Check for transition to completing state
            if (self.planet_bloom and 
                self.planet_bloom.state == BloomState.FADE_OUT):
                self.state = CelebrationState.COMPLETING
        
        elif self.state == CelebrationState.COMPLETING:
            # Continue updating for fade out
            if self.planet_bloom:
                self.planet_bloom.update(delta_time)
            
            if self.sparkles:
                self.sparkles.update(delta_time)
            
            # Update rocket as well during fade out
            if self.rocket and self.rocket_celebration_enabled:
                if hasattr(self.rocket, 'update_celebration'):
                    self.rocket.update_celebration(
                        self.planet_position, delta_time, slow=True
                    )
            
            # Check if celebration is complete
            if (self.planet_bloom and 
                self.planet_bloom.state == BloomState.IDLE and
                self.sparkles and not self.sparkles.is_active()):
                self.state = CelebrationState.COMPLETE
                self.active = False
                
                # Stop rocket celebration
                if self.rocket and self.rocket_celebration_enabled:
                    if hasattr(self.rocket, 'stop_celebration'):
                        self.rocket.stop_celebration()
                
                # Trigger completion callback
                if self.on_celebration_complete:
                    self.on_celebration_complete()
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render entire celebration scene.
        
        Args:
            screen: Pygame surface to render on
        """
        if not self.active and self.state != CelebrationState.CELEBRATING:
            return
        
        # Render bloom effect first (behind everything)
        if self.planet_bloom:
            self.planet_bloom.render(screen, self.planet_position)
        
        # Render sparkles
        if self.sparkles:
            self.sparkles.render(screen)
        
        # Render rocket on top
        if self.rocket and self.rocket_celebration_enabled:
            self.rocket.render_celebration(screen, self.planet_position)
    
    def is_active(self) -> bool:
        """
        Check if celebration is ongoing.
        
        Returns:
            True if celebration is in progress
        """
        return self.active
    
    def is_complete(self) -> bool:
        """
        Check if celebration has fully completed.
        
        Returns:
            True if animation finished
        """
        return self.state == CelebrationState.COMPLETE
    
    def get_state(self) -> str:
        """
        Get current celebration state.
        
        Returns:
            State string
        """
        return self.state
    
    def stop_celebration(self) -> None:
        """Immediately stop and reset celebration."""
        self.active = False
        self.state = CelebrationState.IDLE
        
        if self.planet_bloom:
            self.planet_bloom.state = BloomState.IDLE
        
        if self.sparkles:
            self.sparkles.stop()
        
        if self.rocket and self.rocket_celebration_enabled:
            if hasattr(self.rocket, 'stop_celebration'):
                self.rocket.stop_celebration()
    
    def set_rocket_celebration(self, enabled: bool) -> None:
        """
        Enable or disable rocket celebration animation.
        
        Args:
            enabled: Whether to show rocket circling
        """
        self.rocket_celebration_enabled = enabled
    
    def set_intensity_mode(self, reduced: bool = False) -> None:
        """
        Set intensity mode for accessibility.
        
        Args:
            reduced: If True, reduce particle effects for users with
                    visual sensitivities.
        """
        self.reduced_intensity = reduced
        
        # Apply to sparkles if already initialized
        if self.sparkles:
            self.sparkles.set_intensity_mode(reduced)
        
        # Adjust max particles
        if reduced:
            self.DEFAULT_MAX_SPARKLES = self.REDUCED_MAX_SPARKLES
        else:
            self.DEFAULT_MAX_SPARKLES = 100
    
    def skip_celebration(self) -> None:
        """
        Immediately skip the celebration and complete it.
        
        This provides accessibility support for users who want to
        skip animations or reduce visual effects.
        """
        if not self.active:
            return
        
        # Stop all components immediately
        if self.planet_bloom:
            self.planet_bloom.state = BloomState.IDLE
            self.planet_bloom.progress = 0.0
        
        if self.sparkles:
            self.sparkles.stop()
        
        if self.rocket and self.rocket_celebration_enabled:
            if hasattr(self.rocket, 'stop_celebration'):
                self.rocket.stop_celebration()
        
        # Reset celebration state
        self.state = CelebrationState.COMPLETE
        self.active = False
        
        # Trigger completion callback
        if self.on_celebration_complete:
            self.on_celebration_complete()


def create_celebration_renderer(
    planet_bloom: Optional[PlanetBloom] = None,
    sparkles: Optional[SparkleEffect] = None,
    rocket: Optional[object] = None
) -> CelebrationRenderer:
    """
    Factory function to create a celebration renderer.
    
    Args:
        planet_bloom: Optional planet bloom animation
        sparkles: Optional sparkle effect system
        rocket: Optional rocket sprite
        
    Returns:
        Configured CelebrationRenderer instance
    """
    renderer = CelebrationRenderer()
    renderer.set_components(
        planet_bloom=planet_bloom,
        sparkle_effect=sparkles,
        rocket=rocket
    )
    return renderer
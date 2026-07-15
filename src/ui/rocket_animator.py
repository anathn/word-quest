"""
Rocket Animator Component (STORY-005-02)

Manages rocket movement animations including approach, hover, and boost effects.
Provides smooth tweening and easing for all rocket animations.
"""

import pygame
import math
from typing import Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

from src.ui.rocket_sprite import RocketSprite
from src.ui.engine_flames import EngineFlames, create_engine_flames


class AnimationState(Enum):
    """Rocket animation states."""
    IDLE = "idle"
    APPROACH = "approach"
    HOVER = "hover"
    BOOST = "boost"
    TRANSITION = "transition"
    VICTORY = "victory"


@dataclass
class AnimationParams:
    """Parameters for rocket animations."""
    duration: float  # Animation duration in seconds
    easing: Callable[[float], float]  # Easing function
    start_pos: Tuple[float, float]
    end_pos: Tuple[float, float]
    start_angle: float = 0.0
    end_angle: float = 0.0


class RocketAnimator:
    """
    Manages rocket movement and position animations.
    
    Features:
    - Multiple animation states (approach, hover, boost, transition)
    - Smooth tweening with configurable easing
    - Integration with engine flames for visual effects
    - Time-based animation updates
    
    Attributes:
        rocket: RocketSprite instance to animate
        flames: EngineFlames instance for thrust effects
        state: Current animation state
        position: Current rocket position
        
    Example:
        >>> rocket = RocketSprite()
        >>> flames = EngineFlames()
        >>> animator = RocketAnimator(rocket, flames)
        >>> animator.animate_approach((0, 0), (400, 300), duration=1.5)
        >>> while not animator.is_complete():
        ...     animator.update(dt)
        ...     animator.render(screen)
    """
    
    # Default animation timings
    DEFAULT_APPROACH_DURATION = 1.5  # seconds
    DEFAULT_HOVER_AMPLITUDE = 5  # pixels
    DEFAULT_HOVER_FREQUENCY = 2.0  # Hz
    DEFAULT_BOOST_DURATION = 0.3  # seconds
    DEFAULT_TRANSITION_DURATION = 2.0  # seconds
    
    def __init__(
        self,
        rocket: RocketSprite,
        flames: Optional[EngineFlames] = None,
        initial_position: Tuple[int, int] = (0, 0)
    ):
        """
        Initialize rocket animator.
        
        Args:
            rocket: RocketSprite instance to animate
            flames: EngineFlames instance (created if None)
            initial_position: Starting position (x, y)
        """
        self.rocket = rocket
        self.flames = flames or create_engine_flames()
        
        self.position = initial_position
        self.angle = 0.0
        self.state = AnimationState.IDLE
        
        # Animation state
        self._current_animation: Optional[AnimationParams] = None
        self._animation_start_time = 0.0
        self._animation_elapsed = 0.0
        
        # Hover animation state
        self._hover_start_time = 0.0
        self._hover_position: Tuple[float, float] = (0, 0)
        self._hover_amplitude = self.DEFAULT_HOVER_AMPLITUDE
        self._hover_frequency = self.DEFAULT_HOVER_FREQUENCY
        
        # Boost animation state
        self._boost_duration = self.DEFAULT_BOOST_DURATION
        self._boost_elapsed = 0.0
        
        # Victory animation state
        self._victory_elapsed = 0.0
        self._victory_duration = 1.5
        self._victory_position: Tuple[float, float] = (0, 0)
        self._victory_amplitude = 10.0
        
        # Callback for animation completion
        self._on_complete_callback: Optional[Callable] = None
    
    def _ease_in_out(self, t: float) -> float:
        """
        Smooth ease-in-out interpolation.
        
        Args:
            t: Time fraction (0.0 to 1.0)
            
        Returns:
            Interpolated value with smooth acceleration/deceleration
        """
        return t * t * (3 - 2 * t)
    
    def _ease_out_cubic(self, t: float) -> float:
        """
        Cubic ease-out interpolation.
        
        Args:
            t: Time fraction (0.0 to 1.0)
            
        Returns:
            Interpolated value with deceleration
        """
        t = 1 - t
        return 1 - t * t * t
    
    def _ease_out_elastic(self, t: float) -> float:
        """
        Elastic ease-out for bounce/victory effects.
        
        Args:
            t: Time fraction (0.0 to 1.0)
            
        Returns:
            Interpolated value with bounce effect
        """
        if t == 0:
            return 0
        if t == 1:
            return 1
        
        p = 0.3
        a = 1
        s = p / 4
        
        return a * math.pow(2, -10 * t) * math.sin((t - s) * (2 * math.pi) / p) + 1
    
    def animate_approach(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        duration: float = None,
        start_angle: float = -90.0,  # Pointing down
        end_angle: float = 0.0
    ) -> None:
        """
        Animate rocket flying from start to end position.
        
        Args:
            start: Starting position (x, y)
            end: Ending position (x, y)
            duration: Animation duration in seconds
            start_angle: Starting orientation in degrees
            end_angle: Ending orientation in degrees
        """
        self.state = AnimationState.APPROACH
        self._current_animation = AnimationParams(
            duration=duration or self.DEFAULT_APPROACH_DURATION,
            easing=self._ease_in_out,
            start_pos=start,
            end_pos=end,
            start_angle=start_angle,
            end_angle=end_angle
        )
        self._animation_elapsed = 0.0
        self.flames.boost()
    
    def animate_hover(
        self,
        position: Tuple[float, float],
        amplitude: float = None,
        frequency: float = None
    ) -> None:
        """
        Animate gentle hovering motion at position.
        
        Args:
            position: Center position for hover (x, y)
            amplitude: Vertical oscillation amplitude in pixels
            frequency: Oscillation frequency in Hz
        """
        self.state = AnimationState.HOVER
        self._hover_position = position
        self._hover_amplitude = amplitude or self.DEFAULT_HOVER_AMPLITUDE
        self._hover_frequency = frequency or self.DEFAULT_HOVER_FREQUENCY
        self._hover_start_time = 0.0
        self.flames.idle()
    
    def animate_boost(
        self,
        position: Tuple[float, float],
        duration: float = None
    ) -> None:
        """
        Animate rocket boost/thrust effect.
        
        Args:
            position: Rocket position (x, y)
            duration: Boost duration in seconds
        """
        self.state = AnimationState.BOOST
        self.position = position
        self._boost_duration = duration or self.DEFAULT_BOOST_DURATION
        self._boost_elapsed = 0.0
        self.flames.boost()
    
    def animate_transition(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        duration: float = None
    ) -> None:
        """
        Animate rocket traveling between planets.
        
        Args:
            start: Starting position (x, y)
            end: Ending position (x, y)
            duration: Animation duration in seconds
        """
        self.state = AnimationState.TRANSITION
        self._current_animation = AnimationParams(
            duration=duration or self.DEFAULT_TRANSITION_DURATION,
            easing=self._ease_out_cubic,
            start_pos=start,
            end_pos=end,
            start_angle=-45.0,
            end_angle=-45.0
        )
        self._animation_elapsed = 0.0
        self.flames.boost()
    
    def animate_victory(
        self,
        position: Tuple[float, float],
        amplitude: float = 10.0
    ) -> None:
        """
        Animate victory/celebration effect.
        
        Args:
            position: Rocket position (x, y)
            amplitude: Bounce amplitude in pixels
        """
        self.state = AnimationState.VICTORY
        self._victory_position = position
        self._victory_amplitude = amplitude
        self._victory_elapsed = 0.0
        self._victory_duration = 1.5  # 1.5 second victory loop
        self.flames.boost()
    
    def stop_animation(self) -> None:
        """Stop current animation and return to idle."""
        self.state = AnimationState.IDLE
        self._current_animation = None
        self.flames.off()
    
    def update(self, delta_time: float) -> None:
        """
        Update animation state based on time delta.
        
        Args:
            delta_time: Time elapsed since last update in seconds
        """
        if self.state == AnimationState.IDLE:
            self._update_idle(delta_time)
        elif self.state == AnimationState.APPROACH:
            self._update_approach(delta_time)
        elif self.state == AnimationState.HOVER:
            self._update_hover(delta_time)
        elif self.state == AnimationState.BOOST:
            self._update_boost(delta_time)
        elif self.state == AnimationState.TRANSITION:
            self._update_transition(delta_time)
        elif self.state == AnimationState.VICTORY:
            self._update_victory(delta_time)
        
        # Update engine flames
        self.flames.update(delta_time)
    
    def _update_idle(self, delta_time: float) -> None:
        """Update idle state."""
        self.flames.off()
    
    def _update_approach(self, delta_time: float) -> None:
        """Update approach animation."""
        self._animation_elapsed += delta_time
        
        if self._animation_elapsed >= self._current_animation.duration:
            # Animation complete
            self.position = self._current_animation.end_pos
            self.angle = self._current_animation.end_angle
            self.state = AnimationState.HOVER
            self.animate_hover(self.position)
            if self._on_complete_callback:
                self._on_complete_callback()
            return
        
        # Calculate progress with easing
        progress = self._animation_elapsed / self._current_animation.duration
        eased_progress = self._current_animation.easing(progress)
        
        # Interpolate position
        start_x, start_y = self._current_animation.start_pos
        end_x, end_y = self._current_animation.end_pos
        
        self.position = (
            start_x + (end_x - start_x) * eased_progress,
            start_y + (end_y - start_y) * eased_progress
        )
        
        # Interpolate angle
        self.angle = (
            self._current_animation.start_angle +
            (self._current_animation.end_angle - self._current_animation.start_angle) *
            eased_progress
        )
    
    def _update_hover(self, delta_time: float) -> None:
        """Update hover animation."""
        self._hover_start_time += delta_time
        
        # Calculate sine wave for vertical motion
        hover_offset = math.sin(self._hover_start_time * 2 * math.pi * self._hover_frequency) * self._hover_amplitude
        
        center_x, center_y = self._hover_position
        self.position = (center_x, center_y + hover_offset)
        self.angle = 0.0
    
    def _update_boost(self, delta_time: float) -> None:
        """Update boost animation."""
        self._boost_elapsed += delta_time
        
        if self._boost_elapsed >= self._boost_duration:
            # Boost complete
            self.state = AnimationState.IDLE
            if self._on_complete_callback:
                self._on_complete_callback()
    
    def _update_transition(self, delta_time: float) -> None:
        """Update transition animation."""
        self._animation_elapsed += delta_time
        
        if self._animation_elapsed >= self._current_animation.duration:
            # Animation complete
            self.position = self._current_animation.end_pos
            self.angle = self._current_animation.end_angle
            self.state = AnimationState.IDLE
            if self._on_complete_callback:
                self._on_complete_callback()
            return
        
        # Calculate progress with easing
        progress = self._animation_elapsed / self._current_animation.duration
        eased_progress = self._current_animation.easing(progress)
        
        # Interpolate position
        start_x, start_y = self._current_animation.start_pos
        end_x, end_y = self._current_animation.end_pos
        
        self.position = (
            start_x + (end_x - start_x) * eased_progress,
            start_y + (end_y - start_y) * eased_progress
        )
        
        # Keep constant angle for transition
        self.angle = self._current_animation.end_angle
    
    def _update_victory(self, delta_time: float) -> None:
        """Update victory animation."""
        self._victory_elapsed += delta_time
        
        if self._victory_elapsed >= self._victory_duration:
            # Victory complete
            self.state = AnimationState.HOVER
            self.animate_hover(self._victory_position)
            if self._on_complete_callback:
                self._on_complete_callback()
            return
        
        # Bounce with elastic effect
        elapsed_fraction = self._victory_elapsed / self._victory_duration
        bounce = self._ease_out_elastic(elapsed_fraction) - 1
        
        center_x, center_y = self._victory_position
        self.position = (
            center_x,
            center_y + bounce * self._victory_amplitude
        )
        self.angle = 0.0
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render the animated rocket and flames.
        
        Args:
            screen: Pygame surface to render on
        """
        # Render rocket
        int_x, int_y = int(self.position[0]), int(self.position[1])
        self.rocket.render(screen, (int_x, int_y), self.angle)
        
        # Render engine flames at engine position (bottom of rocket)
        # Engine is approximately at bottom center of rocket
        rocket_height = self.rocket.get_height()
        engine_offset_y = rocket_height / 2 + 5  # Slightly below center
        engine_pos = (int_x, int_y + engine_offset_y)
        self.flames.render(screen, engine_pos)
    
    def is_complete(self) -> bool:
        """
        Check if current animation is complete.
        
        Returns:
            True if animation has finished
        """
        return self.state == AnimationState.IDLE and not self.flames.is_active()
    
    def set_completion_callback(self, callback: Callable) -> None:
        """
        Set callback for when animation completes.
        
        Args:
            callback: Function to call when animation completes
        """
        self._on_complete_callback = callback
    
    def get_position(self) -> Tuple[float, float]:
        """Get current rocket position."""
        return self.position
    
    def get_state(self) -> AnimationState:
        """Get current animation state."""
        return self.state


def create_rocket_animator(
    rocket: RocketSprite,
    flames: Optional[EngineFlames] = None,
    initial_position: Tuple[int, int] = (0, 0)
) -> RocketAnimator:
    """
    Factory function to create a RocketAnimator instance.
    
    Args:
        rocket: RocketSprite to animate
        flames: EngineFlames instance (optional)
        initial_position: Starting position
        
    Returns:
        Configured RocketAnimator instance
    """
    return RocketAnimator(rocket, flames, initial_position)
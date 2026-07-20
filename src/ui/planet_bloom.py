"""
Planet bloom animation for completed planets.

Provides bloom animation system showing flowers/crystals growing on planet surface
when a planet is completed.
"""

from enum import Enum
from typing import Optional, Tuple, Dict
import pygame
from dataclasses import dataclass


class BloomState:
    """Bloom animation states."""
    IDLE = "idle"
    STARTING = "starting"
    BLOOMING = "bloom"
    HOLDING = "holding"
    FADE_OUT = "fade_out"


@dataclass
class BloomColors:
    """Color configuration for bloom effect."""
    base: Tuple[int, int, int]
    bloom: Tuple[int, int, int]
    crystals: Tuple[int, int, int]
    sparkles: Tuple[int, int, int] = (255, 255, 255)


class PlanetBloom:
    """
    Manages planet bloom animation.
    Handles color transition, crystal/flower growth, and bloom state lifecycle.
    """
    
    # Animation timing (seconds)
    BLOOM_DURATION = 2.0  # Bloom to full intensity
    HOLD_DURATION = 0.5   # Hold at full intensity
    FADE_DURATION = 1.0   # Fade out duration
    
    # Crystal/flower colors
    CRYSTAL_COLORS = [
        (255, 235, 59),   # Yellow
        (244, 143, 177),  # Pink
        (255, 255, 255),  # White
        (173, 216, 230),  # Light blue
    ]
    
    # Planet color transitions (before -> after bloom)
    PLANET_COLORS: Dict[int, BloomColors] = {
        1: BloomColors(
            base=(255, 152, 0),    # Orange
            bloom=(255, 183, 77),  # Bright Orange
            crystals=(255, 235, 59)
        ),
        2: BloomColors(
            base=(33, 150, 243),   # Blue
            bloom=(100, 181, 246), # Bright Blue
            crystals=(173, 216, 230)
        ),
        3: BloomColors(
            base=(156, 39, 176),   # Purple
            bloom=(186, 104, 200), # Bright Purple
            crystals=(244, 143, 177)
        ),
        4: BloomColors(
            base=(76, 175, 80),    # Green
            bloom=(129, 199, 132), # Bright Green
            crystals=(205, 220, 57)
        ),
        5: BloomColors(
            base=(244, 67, 54),    # Red
            bloom=(229, 115, 115), # Bright Red
            crystals=(255, 235, 59)
        ),
    }
    
    def __init__(self, planet_sprite, planet_number: int = 1):
        """
        Initialize planet bloom.
        
        Args:
            planet_sprite: Planet sprite to animate
            planet_number: Planet number (1-5) for color selection
        """
        self.planet = planet_sprite
        self.planet_number = planet_number
        self.state = BloomState.IDLE
        self.progress = 0.0
        self.bloom_duration = self.BLOOM_DURATION
        self.hold_duration = self.HOLD_DURATION
        self.fade_duration = self.FADE_DURATION
        
        # Get colors for this planet
        if planet_number in self.PLANET_COLORS:
            self.colors = self.PLANET_COLORS[planet_number]
        else:
            # Default colors
            self.colors = BloomColors(
                base=(100, 100, 100),
                bloom=(150, 150, 150),
                crystals=(255, 235, 59)
            )
        
        # Bloom surface for crystals
        self._crystal_surface: Optional[pygame.Surface] = None
        self._crystal_density = 0.0
        
        # Timers
        self._state_timer = 0.0
    
    def start_bloom(self) -> None:
        """Trigger bloom animation."""
        self.state = BloomState.STARTING
        self.progress = 0.0
        self._state_timer = 0.0
        self._crystal_density = 0.0
        self._crystal_surface = None
    
    def update(self, delta_time: float) -> None:
        """
        Update bloom state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        if self.state == BloomState.STARTING:
            self.state = BloomState.BLOOMING
            self.progress = 0.0
            self._state_timer = 0.0
        
        elif self.state == BloomState.BLOOMING:
            self._state_timer += delta_time
            self.progress = min(1.0, self._state_timer / self.bloom_duration)
            
            # Update crystal density
            self._crystal_density = self.progress
            
            if self.progress >= 1.0:
                self.state = BloomState.HOLDING
                self._state_timer = 0.0
        
        elif self.state == BloomState.HOLDING:
            self._state_timer += delta_time
            
            if self._state_timer >= self.hold_duration:
                self.state = BloomState.FADE_OUT
                self._state_timer = 0.0
        
        elif self.state == BloomState.FADE_OUT:
            self._state_timer += delta_time
            fade_progress = self._state_timer / self.fade_duration
            self.progress = max(0.0, 1.0 - fade_progress)
            
            # Decrease crystal density
            self._crystal_density = self.progress
            
            if self._state_timer >= self.fade_duration:
                self.state = BloomState.IDLE
                self._crystal_surface = None
    
    def render(self, screen: pygame.Surface, position: Tuple[int, int]) -> None:
        """
        Render planet with bloom effect.
        
        Args:
            screen: Pygame surface to render on
            position: (x, y) center position
        """
        intensity = self._get_intensity()
        
        # Render planet with bloom
        if hasattr(self.planet, 'render_with_bloom'):
            self.planet.render_with_bloom(
                screen, position,
                bloom_intensity=intensity,
                crystal_density=intensity
            )
        else:
            # Fallback to standard render
            self.planet.render(screen, position)
    
    def _get_intensity(self) -> float:
        """
        Get current bloom intensity (0.0-1.0).
        
        Returns:
            Intensity value
        """
        if self.state == BloomState.IDLE:
            return 0.0
        elif self.state == BloomState.BLOOMING:
            return self.progress
        elif self.state == BloomState.HOLDING:
            return 1.0
        elif self.state == BloomState.FADE_OUT:
            return self.progress
        return 0.0
    
    def get_current_color(self) -> Tuple[int, int, int]:
        """
        Get current interpolated planet color.
        
        Returns:
            RGB color tuple
        """
        intensity = self._get_intensity()
        
        base = self.colors.base
        bloom = self.colors.bloom
        
        # Linear interpolation
        r = int(base[0] + (bloom[0] - base[0]) * intensity)
        g = int(base[1] + (bloom[1] - base[1]) * intensity)
        b = int(base[2] + (bloom[2] - base[2]) * intensity)
        
        return (r, g, b)
    
    def get_crystal_color(self) -> Tuple[int, int, int, int]:
        """
        Get current crystal/flower color with alpha.
        
        Returns:
            RGBA color tuple (R, G, B, A). Returns (0, 0, 0, 0) when
            density is 0 (transparent).
        """
        if self._crystal_density > 0:
            # Return color based on density
            return self.colors.crystals
        return (0, 0, 0, 0)  # Transparent
    
    def is_active(self) -> bool:
        """
        Check if bloom animation is currently active.
        
        Returns:
            True if bloom is in progress
        """
        return self.state != BloomState.IDLE
    
    def is_complete(self) -> bool:
        """
        Check if bloom animation has fully completed.
        
        Returns:
            True if animation is done (returned to idle)
        """
        return self.state == BloomState.IDLE and self.progress <= 0
    
    def get_state(self) -> str:
        """
        Get current bloom state.
        
        Returns:
            State string
        """
        return self.state
    
    def get_progress(self) -> float:
        """
        Get current animation progress (0.0-1.0).
        
        Returns:
            Progress value
        """
        return self.progress


def create_planet_bloom(planet_sprite, planet_number: int = 1) -> PlanetBloom:
    """
    Factory function to create a planet bloom animation.
    
    Args:
        planet_sprite: Planet sprite to animate
        planet_number: Planet number (1-5)
        
    Returns:
        Configured PlanetBloom instance
    """
    return PlanetBloom(planet_sprite, planet_number)
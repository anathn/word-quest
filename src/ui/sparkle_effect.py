"""
Sparkle particle effect for planet bloom celebration.

Provides particle system for sparkle effects during planet completion animations.
"""

import pygame
import random
import math
from typing import List, Tuple, Optional


class Particle:
    """
    Individual sparkle particle with position, velocity, and lifespan.
    """
    
    def __init__(self, x: float, y: float, 
                 color: Tuple[int, int, int] = (255, 255, 255),
                 size: Optional[int] = None):
        """
        Initialize particle.
        
        Args:
            x: Initial x position
            y: Initial y position
            color: Particle color (RGB tuple)
            size: Particle size in pixels (random if None)
        """
        self.x = x
        self.y = y
        
        # Random outward velocity
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 3)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        # Color
        self.color = color
        
        # Size (2-5 pixels)
        self.size = size if size is not None else random.randint(2, 5)
        
        # Lifespan (500-1000ms)
        self.total_life = random.uniform(0.5, 1.0)
        self.life = self.total_life
    
    def update(self, delta_time: float) -> None:
        """
        Update particle position and life.
        
        Args:
            delta_time: Time since last update in seconds
        """
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Update life
        self.life -= delta_time
    
    def is_dead(self) -> bool:
        """
        Check if particle has expired.
        
        Returns:
            True if particle life <= 0
        """
        return self.life <= 0
    
    def get_alpha(self) -> int:
        """
        Get current alpha based on remaining life.
        
        Returns:
            Alpha value (0-255)
        """
        life_ratio = self.life / self.total_life
        return int(life_ratio * 255)
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render particle with current alpha.
        
        Args:
            screen: Pygame surface to render on
        """
        alpha = self.get_alpha()
        
        # Create surface with alpha for this particle
        particle_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        
        # Draw circle with fading alpha
        if alpha > 0:
            color_with_alpha = (*self.color, alpha)
            center = (self.size, self.size)
            pygame.draw.circle(particle_surface, color_with_alpha, center, self.size)
            
            # Draw to screen
            screen_x = int(self.x - self.size)
            screen_y = int(self.y - self.size)
            screen.blit(particle_surface, (screen_x, screen_y))


class SparkleEffect:
    """
    Particle system for sparkle effects.
    Creates, updates, and renders sparkle particles for celebrations.
    """
    
    # Configuration constants
    DEFAULT_MAX_PARTICLES = 100
    DEFAULT_EMIT_COUNT = 3
    MIN_EMIT_COUNT = 1
    MAX_EMIT_COUNT = 5
    
    # Accessibility: Reduced intensity mode
    REDUCED_MAX_PARTICLES = 50
    REDUCED_EMIT_COUNT = 1
    
    # Magic number constants for configuration
    DEFAULT_EMIT_RATE = 0.1  # 100ms
    DEFAULT_GOLD_CHANCE = 0.3
    
    def __init__(self, center: Tuple[float, float], 
                 max_particles: int = DEFAULT_MAX_PARTICLES):
        """
        Initialize sparkle effect system.
        
        Args:
            center: Center position (x, y) for emission
            max_particles: Maximum simultaneous particles
        """
        self.center = center
        self.max_particles = max_particles
        self.particles: List[Particle] = []
        self.active = False
        self.emit_rate = 0.1  # Emit every 100ms during active bloom
        
        # Gold accent color for occasional particles
        self.gold_color = (255, 215, 0)
        self.white_color = (255, 255, 255)
        
        # Diamond-like shimmer colors
        self.particle_colors = [
            (255, 255, 255),  # White
            (255, 215, 0),    # Gold
            (173, 216, 230),  # Light blue
            (255, 192, 203),  # Pink
        ]
        
        # Timers
        self._emit_timer = 0.0
        
        # Accessibility: intensity mode (True = reduced effects)
        self.reduced_intensity = False
    
    def set_intensity_mode(self, reduced: bool = False) -> None:
        """
        Set intensity mode for accessibility.
        
        Args:
            reduced: If True, reduce particle count and emission for users with
                    visual sensitivities.
        """
        self.reduced_intensity = reduced
        if reduced:
            self.max_particles = self.REDUCED_MAX_PARTICLES
            self.emit_rate = 0.2  # Emit less frequently
        else:
            self.max_particles = self.DEFAULT_MAX_PARTICLES
            self.emit_rate = 0.1  # Normal emission rate
    
    def set_center(self, center: Tuple[float, float]) -> None:
        """
        Set emission center position.
        
        Args:
            center: New center position (x, y)
        """
        self.center = center
    
    def emit(self, count: Optional[int] = None) -> None:
        """
        Emit new sparkle particles from center.
        
        Args:
            count: Number of particles to emit (default: 3, max: 5)
        """
        if not self.active:
            return
            
        if count is None:
            count = self.DEFAULT_EMIT_COUNT
        
        # Adjust count based on intensity mode
        if self.reduced_intensity:
            count = min(count, self.REDUCED_EMIT_COUNT)
        
        count = max(self.MIN_EMIT_COUNT, min(self.MAX_EMIT_COUNT, count))
        
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            
            # Create particle at center
            particle = Particle(
                x=self.center[0],
                y=self.center[1],
                color=self._choose_color(),
                size=self._choose_size()
            )
            
            # Random outward velocity
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 3)
            particle.vx = math.cos(angle) * speed
            particle.vy = math.sin(angle) * speed
            
            self.particles.append(particle)
    
    def _choose_color(self) -> Tuple[int, int, int]:
        """
        Choose a random particle color.
        
        Returns:
            RGB color tuple
        """
        # 30% chance of gold accent
        if random.random() < 0.3:
            return self.gold_color
        return random.choice(self.particle_colors)
    
    def _choose_size(self) -> int:
        """
        Choose a random particle size.
        
        Returns:
            Size in pixels (2-5)
        """
        return random.randint(2, 5)
    
    def start(self) -> None:
        """Start the sparkle effect."""
        self.active = True
        self._emit_timer = 0.0
    
    def stop(self) -> None:
        """Stop the sparkle effect and clear all particles."""
        self.active = False
        self.particles.clear()
    
    def update(self, delta_time: float) -> None:
        """
        Update all particles and remove dead ones.
        Also handles automatic emission during active state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        if not self.active:
            return
        
        # Auto-emit particles during active state
        if self.active:
            self._emit_timer += delta_time
            if self._emit_timer >= self.emit_rate:
                self._emit_timer = 0.0
                self.emit()
        
        # Update all particles and remove dead ones
        for particle in self.particles[:]:
            particle.update(delta_time)
            if particle.is_dead():
                self.particles.remove(particle)
        
        # Deactivate if no particles remain
        if not self.particles:
            self.active = False
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render all sparkles to screen.
        
        Args:
            screen: Pygame surface to render on
        """
        for particle in self.particles:
            particle.render(screen)
    
    def is_active(self) -> bool:
        """
        Check if sparkle effect is currently active.
        
        Returns:
            True if sparkles are still visible
        """
        return self.active and len(self.particles) > 0
    
    def get_particle_count(self) -> int:
        """
        Get current number of active particles.
        
        Returns:
            Number of particles in system
        """
        return len(self.particles)


def create_sparkle_effect(center: Tuple[float, float], 
                          max_particles: int = 100) -> SparkleEffect:
    """
    Factory function to create a sparkle effect.
    
    Args:
        center: Emission center position (x, y)
        max_particles: Maximum particles (50-100)
        
    Returns:
        Configured SparkleEffect instance
    """
    max_particles = max(50, min(100, max_particles))
    return SparkleEffect(center, max_particles)
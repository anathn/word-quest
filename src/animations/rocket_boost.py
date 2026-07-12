"""
Rocket Boost Animation (STORY-004-02)

Golden rocket boost animation that plays at 3-word streak milestone.
Creates a celebratory particle trail effect with golden flames.
"""

import pygame
import math
import random
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Particle:
    """Represents a single golden particle in the boost trail."""
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    life: float
    max_life: float
    size: float
    
    def update(self, dt: float):
        """
        Update particle position and life.
        
        Args:
            dt: Time delta in seconds
        """
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
    
    def render(self, screen: pygame.Surface):
        """
        Render the particle with alpha transparency.
        
        Args:
            screen: Pygame surface to render on
        """
        if self.life <= 0:
            return
            
        alpha = self.life / self.max_life
        # Create a soft circular particle
        size = max(1, int(self.size * alpha))
        surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        
        # Golden gradient
        center = (size, size)
        pygame.draw.circle(surface, (*self.color, int(255 * alpha)), center, size)
        pygame.draw.circle(surface, (255, 255, int(200 * alpha)), center, size // 2)
        
        screen.blit(surface, (int(self.x - size), int(self.y - size)))


class RocketBoostAnimation:
    """
    Golden rocket boost animation for 3-word streak milestone.
    
    Features:
    - Golden flame particles trailing from rocket
    - Glowing effect around rocket position
    - Screen shake effect for impact
    - 1.5 second duration
    
    Args:
        screen: Pygame surface for rendering
        rocket_position: (x, y) position of the rocket
    """
    
    # Colors
    GOLD = (255, 215, 0)           # #FFD700
    GOLD_LIGHT = (255, 235, 59)    # Lighter gold accent
    WHITE_GLOW = (255, 255, 200)   # White-yellow glow
    
    # Timing
    DURATION_MS = 1500             # 1.5 seconds
    SCREEN_SHAKE_MS = 200          # 0.2 seconds
    
    # Particle system
    PARTICLE_COUNT = 15            # Particles to spawn per update
    PARTICLE_LIFE_MS = 800         # Particle lifespan
    PARTICLE_SIZE_MIN = 3
    PARTICLE_SIZE_MAX = 8
    
    def __init__(self, screen: pygame.Surface, rocket_position: Tuple[int, int]):
        """
        Initialize the rocket boost animation.
        
        Args:
            screen: Pygame surface for rendering
            rocket_position: (x, y) position of the rocket
        """
        self.screen = screen
        self.rocket_position = rocket_position
        self.duration = self.DURATION_MS
        self.elapsed = 0
        self.particles: List[Particle] = []
        
        # Screen shake state
        self.shake_offset = (0, 0)
        self.shake_intensity = 2  # 2 pixels max
        
        # Initialize particle system with time-based seed
        random.seed(pygame.time.get_ticks())
    
    def _create_particle(self, x: float, y: float) -> Particle:
        """
        Create a new golden particle.
        
        Args:
            x: Starting X position
            y: Starting Y position
            
        Returns:
            New Particle instance
        """
        # Random velocity for natural trail
        vx = random.uniform(-50, 50)
        vy = random.uniform(-100, -30)  # Upward motion
        
        # Random size
        size = random.uniform(self.PARTICLE_SIZE_MIN, self.PARTICLE_SIZE_MAX)
        
        # Golden color with slight variation
        if random.random() < 0.3:
            color = self.GOLD_LIGHT
        else:
            color = self.GOLD
        
        return Particle(
            x=x,
            y=y,
            vx=vx,
            vy=vy,
            color=color,
            life=self.PARTICLE_LIFE_MS / 1000.0,
            max_life=self.PARTICLE_LIFE_MS / 1000.0,
            size=size
        )
    
    def update(self, dt: float):
        """
        Update animation state.
        
        Args:
            dt: Time delta in seconds
        """
        self.elapsed = min(self.elapsed + dt, self.duration / 1000.0)
        
        # Update screen shake
        if self.elapsed < self.SCREEN_SHAKE_MS / 1000.0:
            self.shake_offset = (
                random.uniform(-self.shake_intensity, self.shake_intensity),
                random.uniform(-self.shake_intensity, self.shake_intensity)
            )
        else:
            self.shake_offset = (0, 0)
        
        # Spawn new particles from rocket position
        rocket_x, rocket_y = self.rocket_position
        for _ in range(self.PARTICLE_COUNT):
            # Spawn near rocket with slight offset
            spawn_x = rocket_x + random.uniform(-10, 10)
            spawn_y = rocket_y + random.uniform(-10, 10) + 20  # Below rocket
            self.particles.append(self._create_particle(spawn_x, spawn_y))
        
        # Update existing particles
        for particle in self.particles:
            particle.update(dt)
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.life > 0]
    
    def render(self):
        """Render the rocket boost animation."""
        # Apply screen shake offset
        shake_x, shake_y = self.shake_offset
        
        # Get rocket position with shake
        rocket_x = self.rocket_position[0] + shake_x
        rocket_y = self.rocket_position[1] + shake_y
        
        # Calculate glow intensity (stronger at start)
        glow_intensity = 1.0 - (self.elapsed / (self.duration / 1000.0))
        glow_radius = int(30 * glow_intensity)
        
        # Draw glow effect around rocket
        glow_surface = pygame.Surface((glow_radius * 2 + 20, glow_radius * 2 + 20), pygame.SRCALPHA)
        center = (glow_radius + 10, glow_radius + 10)
        
        # Multi-layer glow for soft effect
        for i in range(3):
            layer_radius = glow_radius - i * 5
            if layer_radius > 0:
                alpha = int(100 * glow_intensity * (1 - i * 0.3))
                glow_color = (*self.WHITE_GLOW, alpha)
                pygame.draw.circle(glow_surface, glow_color, center, max(1, layer_radius))
        
        # Render glow at rocket position
        glow_x = rocket_x - glow_radius - 10
        glow_y = rocket_y - glow_radius - 10
        # Don't render outside screen
        if glow_x + glow_surface.get_width() > 0 and glow_y + glow_surface.get_height() > 0:
            self.screen.blit(glow_surface, (glow_x, glow_y))
        
        # Render all particles
        for particle in self.particles:
            particle.render(self.screen)
    
    def is_complete(self) -> bool:
        """
        Check if animation is complete.
        
        Returns:
            True if animation has finished
        """
        return self.elapsed >= self.duration / 1000.0
    
    def get_progress(self) -> float:
        """
        Get animation progress as a fraction.
        
        Returns:
            Progress value from 0.0 to 1.0
        """
        return self.elapsed / (self.duration / 1000.0)


# Factory function
def create_rocket_boost_animation(
    screen: pygame.Surface,
    rocket_position: Tuple[int, int]
) -> RocketBoostAnimation:
    """
    Create a RocketBoostAnimation instance.
    
    Args:
        screen: Pygame surface for rendering
        rocket_position: Position of the rocket
        
    Returns:
        Configured RocketBoostAnimation instance
    
    Example:
        >>> # Create and use a rocket boost animation
        >>> screen = pygame.display.set_mode((800, 600))
        >>> rocket_pos = (700, 300)
        >>> animation = create_rocket_boost_animation(screen, rocket_pos)
        >>> 
        >>> # In your game loop:
        >>> animation.update(dt)  # Update each frame
        >>> animation.render()     # Render each frame
        >>> if animation.is_complete():
        ...     # Animation finished
        ...     pass
    """
    return RocketBoostAnimation(screen, rocket_position)
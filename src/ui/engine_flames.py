"""
Engine Flames Animation System (STORY-005-02)

Animated engine flame effect for rocket sprites.
Uses particle-based animation for flickering engine flames.
"""

import pygame
import math
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class FlameParticle:
    """
    Represents a single flame particle in the engine exhaust.
    
    Attributes:
        x: X position
        y: Y position
        vx: X velocity
        vy: Y velocity
        color: RGB color tuple
        life: Remaining life (0.0-1.0)
        size: Particle size
        opacity: Alpha transparency (0-255)
    """
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    life: float
    size: float
    opacity: int = 255
    
    def update(self, delta_time: float):
        """
        Update particle position and life based on time delta.
        
        Args:
            delta_time: Time elapsed since last update in seconds
        """
        # Update position
        self.x += self.vx * delta_time
        self.y += self.vy * delta_time
        
        # Reduce life
        self.life -= delta_time
        
        # Fade out as life decreases
        if self.life < 0.2:
            self.opacity = int(255 * (self.life / 0.2))
            self.opacity = max(0, min(255, self.opacity))
        else:
            self.opacity = 255


class EngineFlames:
    """
    Engine flame animation system for rocket sprites.
    
    Features:
    - Particle-based flame effect
    - Configurable intensity
    - Smooth flickering animation
    - Performance-optimized (60+ FPS target)
    
    Args:
        max_particles: Maximum number of flame particles (default: 20)
        base_color: Base flame color (default: orange)
    
    Example:
        >>> flames = EngineFlames(max_particles=20)
        >>> flames.emit()
        >>> flames.update(0.016)  # 16ms delta time
        >>> flames.render(screen, (100, 200))
    """
    
    # Flame color palette (orange to yellow gradient)
    FLAME_COLORS = [
        (255, 144, 0),    # Orange
        (255, 166, 0),    # Dark orange
        (255, 200, 0),    # Orange-yellow
        (255, 235, 59),   # Yellow
        (255, 255, 200),  # Light yellow
    ]
    
    # Animation timing
    DEFAULT_PARTICLE_SPAWN_RATE = 0.05  # Particles per update at full intensity
    PARTICLE_LIFESPAN_MIN = 0.2  # 200ms
    PARTICLE_LIFESPAN_MAX = 0.5  # 500ms
    
    # Particle physics
    BASE_VELOCITY_Y = -150  # Upward motion
    VELOCITY_VARIATION_X = 30  # Side-to-side variation
    GRAVITY_EFFECT = 30  # Slight downward pull
    
    # Size parameters
    PARTICLE_SIZE_MIN = 4
    PARTICLE_SIZE_MAX = 12
    
    # Performance target
    TARGET_FPS = 60
    MIN_PLAYABLE_FPS = 30
    
    def __init__(self, max_particles: int = 20, base_color: Optional[Tuple[int, int, int]] = None):
        """
        Initialize the engine flame system.
        
        Args:
            max_particles: Maximum number of flame particles (default: 20)
            base_color: Base flame color (default: orange)
        """
        self.max_particles = max_particles
        self.particles: List[FlameParticle] = []
        self.intensity = 1.0  # 0.0 to 1.0
        self.particle_spawn_counter = 0
        
        # Seed random with time for variety
        random.seed(pygame.time.get_ticks())
    
    def emit(self) -> None:
        """
        Emit new flame particles based on current intensity.
        
        Should be called each frame before updating particles.
        """
        # Calculate how many particles to spawn this frame
        spawn_rate = self.DEFAULT_PARTICLE_SPAWN_RATE * self.intensity
        particles_to_spawn = int(spawn_rate * self.TARGET_FPS)
        
        # Ensure at least one particle at full intensity
        if self.intensity > 0 and particles_to_spawn == 0:
            particles_to_spawn = 1
        
        # Respect max particle limit
        remaining_capacity = self.max_particles - len(self.particles)
        particles_to_spawn = min(particles_to_spawn, remaining_capacity)
        
        for _ in range(particles_to_spawn):
            self.particles.append(self._spawn_particle())
    
    def _spawn_particle(self) -> FlameParticle:
        """
        Create a new flame particle at engine position.
        
        Returns:
            New FlameParticle instance
        """
        # Start position (bottom center of rocket)
        x = 0  # Relative to engine position
        y = 0
        
        # Random velocity
        vx = random.uniform(-self.VELOCITY_VARIATION_X, self.VELOCITY_VARIATION_X)
        vy = random.uniform(
            self.BASE_VELOCITY_Y - 50,
            self.BASE_VELOCITY_Y + 50
        )
        
        # Random color from flame palette
        color = random.choice(self.FLAME_COLORS)
        
        # Random size
        size = random.uniform(self.PARTICLE_SIZE_MIN, self.PARTICLE_SIZE_MAX)
        
        # Random lifespan
        lifespan = random.uniform(
            self.PARTICLE_LIFESPAN_MIN,
            self.PARTICLE_LIFESPAN_MAX
        )
        
        return FlameParticle(
            x=x,
            y=y,
            vx=vx,
            vy=vy,
            color=color,
            life=lifespan,
            size=size,
            opacity=255
        )
    
    def update(self, delta_time: float) -> None:
        """
        Update all flame particles.
        
        Args:
            delta_time: Time elapsed since last update in seconds
            
        Example:
            >>> flames = EngineFlames()
            >>> # In game loop:
            >>> dt = clock.tick(60) / 1000.0
            >>> flames.emit()
            >>> flames.update(dt)
        """
        # Emit new particles
        self.emit()
        
        # Update existing particles
        for particle in self.particles:
            # Apply gravity effect
            particle.vy += self.GRAVITY_EFFECT * delta_time
            particle.update(delta_time)
        
        # Remove dead particles
        self.particles = [p for p in self.particles if p.life > 0]
        
        # Respect max particle limit (remove oldest if over limit)
        if len(self.particles) > self.max_particles:
            self.particles = self.particles[-self.max_particles:]
    
    def render(self, screen: pygame.Surface, base_position: Tuple[int, int]) -> None:
        """
        Render flame effect at engine position.
        
        Args:
            screen: Pygame surface to render on
            base_position: (x, y) position of engine (bottom center of rocket)
            
        Example:
            >>> flames = EngineFlames()
            >>> engine_pos = (400, 500)
            >>> flames.render(screen, engine_pos)
        """
        engine_x, engine_y = base_position
        
        for particle in self.particles:
            # Convert relative position to screen position
            screen_x = engine_x + particle.x
            screen_y = engine_y + particle.y
            
            # Skip if outside screen
            if (screen_x < -particle.size or 
                screen_x > screen.get_width() + particle.size or
                screen_y < -particle.size or 
                screen_y > screen.get_height() + particle.size):
                continue
            
            # Create particle surface
            size = int(particle.size)
            particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            
            # Draw circular gradient particle
            center = (size, size)
            
            # Apply opacity to color
            r, g, b = particle.color
            color_with_alpha = (r, g, b, particle.opacity)
            
            # Multi-layer circle for soft edge effect
            for i in range(3):
                layer_size = max(1, size - i)
                layer_alpha = int(particle.opacity * (1 - i * 0.4))
                if layer_alpha > 0:
                    layer_color = (r, g, b, layer_alpha)
                    pygame.draw.circle(
                        particle_surface,
                        layer_color,
                        center,
                        layer_size
                    )
            
            # Render with additive blending for glow effect
            screen.blit(particle_surface, (int(screen_x - size), int(screen_y - size)))
    
    def set_intensity(self, intensity: float) -> None:
        """
        Adjust flame intensity.
        
        Args:
            intensity: Intensity value 0.0 (off) to 1.0 (full)
            
        Example:
            >>> flames = EngineFlames()
            >>> flames.set_intensity(0.5)  # Half intensity
            >>> flames.set_intensity(1.0)  # Full boost
        """
        self.intensity = max(0.0, min(1.0, intensity))
    
    def boost(self) -> None:
        """Set intensity to maximum for boost effect."""
        self.set_intensity(1.0)
    
    def idle(self) -> None:
        """Set intensity to low for idle animation."""
        self.set_intensity(0.3)
    
    def off(self) -> None:
        """Turn off flames completely."""
        self.set_intensity(0.0)
    
    def get_particle_count(self) -> int:
        """
        Get current number of active particles.
        
        Returns:
            Number of active flame particles
        """
        return len(self.particles)
    
    def is_active(self) -> bool:
        """
        Check if flames are currently visible.
        
        Returns:
            True if any particles are active
        """
        return len(self.particles) > 0 and self.intensity > 0


def create_engine_flames(
    max_particles: int = 20,
    intensity: float = 1.0
) -> EngineFlames:
    """
    Factory function to create an EngineFlames instance.
    
    Args:
        max_particles: Maximum particle count (default: 20)
        intensity: Initial intensity (default: 1.0)
        
    Returns:
        Configured EngineFlames instance
        
    Example:
        >>> flames = create_engine_flames(max_particles=15, intensity=0.5)
        >>> flames.set_intensity(1.0)  # Boost
    """
    flames = EngineFlames(max_particles=max_particles)
    flames.set_intensity(intensity)
    return flames
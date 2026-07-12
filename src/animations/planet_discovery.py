"""
Planet Discovery Animation (STORY-004-02)

Special planet discovery animation that plays at 5-word streak milestone.
Shows a new planet appearing with sparkle effects and rocket flying toward it.
"""

import pygame
import math
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass
class Sparkle:
    """Represents a sparkle particle around the new planet."""
    x: float
    y: float
    vx: float
    vy: float
    size: float
    life: float
    max_life: float
    alpha: int
    
    def update(self, dt: float):
        """
        Update sparkle position and life.
        
        Args:
            dt: Time delta in seconds
        """
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        self.alpha = int(255 * (self.life / self.max_life))
    
    def render(self, screen: pygame.Surface):
        """
        Render the sparkle particle.
        
        Args:
            screen: Pygame surface to render on
        """
        if self.life <= 0 or self.alpha <= 0:
            return
            
        # Create sparkle surface
        size = max(1, int(self.size))
        surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        center = (size, size)
        
        # Draw 4-point star shape
        points = [
            (center[0], 0),
            (size, center[1]),
            (center[0], size * 2),
            (0, center[1])
        ]
        pygame.draw.polygon(surface, (255, 255, 255, self.alpha), points)
        
        screen.blit(surface, (int(self.x - size), int(self.y - size)))


@dataclass
class PlanetSprite:
    """Represents the new discovered planet."""
    x: float
    y: float
    radius: float
    max_radius: float
    color: Tuple[int, int, int]
    accent_color: Tuple[int, int, int]
    has_rings: bool
    
    def bloom(self, dt: float):
        """
        Bloom (grow) the planet from small to full size.
        
        Args:
            dt: Time delta in seconds
        """
        growth_rate = 100  # pixels per second
        self.radius = min(self.radius + growth_rate * dt, self.max_radius)
    
    def render(self, screen: pygame.Surface):
        """
        Render the planet.
        
        Args:
            screen: Pygame surface to render on
        """
        # Main planet body
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.radius))
        
        # Planet accent/bANDING
        if self.radius > 10:
            # Draw some surface detail
            detail_radius = self.radius * 0.7
            pygame.draw.circle(
                screen, 
                self.accent_color, 
                (int(self.x - self.radius * 0.2), int(self.y - self.radius * 0.2)), 
                int(detail_radius)
            )
        
        # Rings if applicable
        if self.has_rings and self.radius > 15:
            self._render_rings(screen)
    
    def _render_rings(self, screen: pygame.Surface):
        """
        Render planetary rings.
        
        Args:
            screen: Pygame surface to render on
        """
        ring_inner = int(self.radius * 1.2)
        ring_outer = int(self.radius * 1.8)
        
        # Create ring surface
        ring_size = ring_outer * 2
        ring_surface = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)
        center = (ring_size // 2, ring_size // 2)
        
        # Draw elliptical ring
        pygame.draw.ellipse(
            ring_surface,
            (*self._get_ring_color(), 200),
            pygame.Rect(0, 0, ring_size, int(ring_size * 0.4)),
            3
        )
        
        screen.blit(ring_surface, (int(self.x - ring_size // 2), int(self.y - ring_size // 4)))
    
    def _get_ring_color(self) -> Tuple[int, int, int]:
        """Get ring color based on planet color."""
        # Different ring colors based on planet
        lighter = tuple(min(255, c + 80) for c in self.color)
        return lighter


@dataclass
class RocketPathPoint:
    """Represents a point in the rocket's flight path."""
    x: float
    y: float


class PlanetDiscoveryAnimation:
    """
    Planet discovery animation for 5-word streak milestone.
    
    Features:
    - Camera pans to show new planet appearing
    - Planet blooms from small to full size
    - Sparkle particle explosions
    - Rocket flies toward planet, loops, returns
    - 2.5 second duration
    
    Args:
        screen: Pygame surface for rendering
        rocket_start_position: Starting position of the rocket
        planet_position: Position where planet appears
    """
    
    # Colors
    PLANET_COLORS = [
        ((100, 149, 237), (65, 105, 225)),   # Cornflower blue
        ((144, 238, 144), (102, 205, 170)),  # Light green
        ((255, 182, 193), (219, 112, 147)),  # Light pink
        ((221, 160, 221), (186, 85, 211)),   # Plum
        ((255, 218, 185), (244, 164, 96)),   # Peach
    ]
    
    # Timing
    DURATION_MS = 2500           # 2.5 seconds
    PLANET_APPEAR_TIME = 0.3     # Planet appears at 0.3s
    ROCKET_LEAVE_TIME = 0.5      # Rocket leaves at 0.5s
    ROCKET_RETURN_TIME = 2.0     # Rocket returns at 2.0s
    
    # Animation phases
    PHASE相機_PAN = "camera_pan"
    PHASE_PLANET_APPEAR = "planet_appear"
    PHASE_ROCKET_FLIGHT = "rocket_flight"
    PHASE_RETURN = "return"
    
    def __init__(
        self, 
        screen: pygame.Surface, 
        rocket_start_position: Tuple[int, int],
        planet_position: Tuple[int, int]
    ):
        """
        Initialize the planet discovery animation.
        
        Args:
            screen: Pygame surface for rendering
            rocket_start_position: Starting position of rocket
            planet_position: Position where planet appears
        """
        self.screen = screen
        self.rocket_start = rocket_start_position
        self.planet_position = planet_position
        
        self.duration = self.DURATION_MS
        self.elapsed = 0
        
        # Camera offset for pan effect
        self.camera_offset = (0, 0)
        self.max_camera_offset = (150, 0)  # Pan right by 150px
        
        # Planet state
        self.planet: Optional[PlanetSprite] = None
        self.planet_appeared = False
        
        # Sparkles
        self.sparkles: List[Sparkle] = []
        
        # Rocket flight path
        self.rocket_position = rocket_start_position
        self.rocket_path: List[RocketPathPoint] = []
        self.path_progress = 0.0
        
        # Initialize random seed
        random.seed(pygame.time.get_ticks())
    
    def _create_planet(self) -> PlanetSprite:
        """
        Create a new planet sprite with random properties.
        
        Returns:
            New PlanetSprite instance
        """
        # Random color selection
        color, accent = random.choice(self.PLANET_COLORS)
        has_rings = random.random() < 0.4  # 40% chance of rings
        
        return PlanetSprite(
            x=self.planet_position[0],
            y=self.planet_position[1],
            radius=0,  # Starts at 0, will bloom
            max_radius=40,
            color=color,
            accent_color=accent,
            has_rings=has_rings
        )
    
    def _create_sparkles(self, x: float, y: float, count: int = 20):
        """
        Create sparkle particles at position.
        
        Args:
            x: X position
            y: Y position
            count: Number of sparkles to create
        """
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            
            sparkle = Sparkle(
                x=x,
                y=y,
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                size=random.uniform(3, 8),
                life=random.uniform(0.5, 1.0),
                max_life=1.0,
                alpha=255
            )
            self.sparkles.append(sparkle)
    
    def _calculate_rocket_path(self):
        """Calculate the rocket's flight path toward the planet."""
        start = self.rocket_start
        target = self.planet_position
        
        # Create a curved path using quadratic Bezier curve
        # Control point offset from straight line
        control_x = (start[0] + target[0]) / 2 + 50  # Offset to the right
        control_y = min(start[1], target[1]) - 100   # Arc upward
        
        # Generate path points
        self.rocket_path = []
        points_count = 50
        for i in range(points_count):
            t = i / (points_count - 1)
            t2 = t * t
            one_t = 1 - t
            one_t2 = one_t * one_t
            
            # Quadratic Bezier formula
            x = one_t2 * start[0] + 2 * one_t * t * control_x + t2 * target[0]
            y = one_t2 * start[1] + 2 * one_t * t * control_y + t2 * target[1]
            
            self.rocket_path.append(RocketPathPoint(x, y))
        
        # Return path (straight line back)
        return_points = 30
        for i in range(return_points):
            t = i / (return_points - 1)
            x = target[0] * (1 - t) + start[0] * t
            y = target[1] * (1 - t) + start[1] * t
            self.rocket_path.append(RocketPathPoint(x, y))
    
    def update(self, dt: float):
        """
        Update animation state.
        
        Args:
            dt: Time delta in seconds
        """
        self.elapsed = min(self.elapsed + dt, self.duration / 1000.0)
        progress = self.elapsed / (self.duration / 1000.0)
        
        # Camera pan phase (first 0.3 seconds)
        if self.elapsed < 0.3:
            pan_progress = self.elapsed / 0.3
            self.camera_offset = (
                self.max_camera_offset[0] * pan_progress,
                self.max_camera_offset[1] * pan_progress
            )
        
        # Planet appears
        if self.elapsed >= self.PLANET_APPEAR_TIME and not self.planet_appeared:
            self.planet_appeared = True
            self.planet = self._create_planet()
            self._create_sparkles(self.planet_position[0], self.planet_position[1], 30)
            # Initialize rocket path calculation
            self._calculate_rocket_path()
        
        # Bloom the planet
        if self.planet:
            self.planet.bloom(dt)
        
        # Rocket flight phase
        if self.PLANET_APPEAR_TIME <= self.elapsed < self.ROCKET_RETURN_TIME and self.planet:
            # Calculate path progress
            if self.rocket_path:
                # Map time to path progress
                flight_time = self.ROCKET_RETURN_TIME - self.PLANET_APPEAR_TIME
                flight_progress = (self.elapsed - self.PLANET_APPEAR_TIME) / flight_time
                
                if flight_progress < 1.0:
                    # Going to planet
                    path_index = int(flight_progress * (len(self.rocket_path) // 2))
                    path_index = min(path_index, len(self.rocket_path) // 2 - 1)
                    self.rocket_position = (
                        self.rocket_path[path_index].x,
                        self.rocket_path[path_index].y
                    )
                else:
                    # Returning
                    return_progress = (self.elapsed - self.ROCKET_RETURN_TIME) / (
                        self.duration / 1000.0 - self.ROCKET_RETURN_TIME
                    )
                    start_idx = len(self.rocket_path) // 2
                    if return_progress < 1.0:
                        path_index = start_idx + int(return_progress * (len(self.rocket_path) - start_idx))
                        path_index = min(path_index, len(self.rocket_path) - 1)
                        self.rocket_position = (
                            self.rocket_path[path_index].x,
                            self.rocket_path[path_index].y
                        )
                    else:
                        self.rocket_position = self.rocket_start
        elif self.elapsed >= self.ROCKET_RETURN_TIME:
            self.rocket_position = self.rocket_start
        
        # Update sparkles
        for sparkle in self.sparkles:
            sparkle.update(dt)
        
        # Remove dead sparkles
        self.sparkles = [s for s in self.sparkles if s.life > 0]
    
    def render(self):
        """Render the planet discovery animation."""
        # Draw sparkle particles (behind planet)
        for sparkle in self.sparkles:
            sparkle.render(self.screen)
        
        # Draw planet if it has appeared
        if self.planet:
            self.planet.render(self.screen)
    
    def get_rocket_position(self) -> Tuple[int, int]:
        """
        Get current rocket position.
        
        Returns:
            Current (x, y) position of rocket
        """
        return self.rocket_position
    
    def get_camera_offset(self) -> Tuple[int, int]:
        """
        Get current camera offset.
        
        Returns:
            Current camera offset (dx, dy)
        """
        return self.camera_offset
    
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
def create_planet_discovery_animation(
    screen: pygame.Surface,
    rocket_start_position: Tuple[int, int],
    planet_position: Tuple[int, int]
) -> PlanetDiscoveryAnimation:
    """
    Create a PlanetDiscoveryAnimation instance.
    
    Args:
        screen: Pygame surface for rendering
        rocket_start_position: Starting rocket position
        planet_position: Where planet appears
        
    Returns:
        Configured PlanetDiscoveryAnimation instance
    
    Example:
        >>> # Create and use a planet discovery animation
        >>> screen = pygame.display.set_mode((800, 600))
        >>> rocket_pos = (700, 300)
        >>> planet_pos = (700, 300)
        >>> animation = create_planet_discovery_animation(screen, rocket_pos, planet_pos)
        >>> 
        >>> # In your game loop:
        >>> animation.update(dt)  # Update each frame
        >>> animation.render()     # Render each frame
        >>> if animation.is_complete():
        ...     # Animation finished
        ...     pass
        >>> 
        >>> # Get rocket position during animation
        >>> rocket_pos = animation.get_rocket_position()
    """
    return PlanetDiscoveryAnimation(screen, rocket_start_position, planet_position)
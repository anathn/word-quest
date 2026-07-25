"""
Map Elements UI Components

Rendering components for the space map:
- PlanetSprite: Renders planets with state-appropriate appearances
- PathRenderer: Draws connection paths between planets
- RocketIndicator: Shows current position with animated rocket
"""

from typing import Optional, Tuple, List
import pygame
import math

from src.models.map_state import PlanetNode, PlanetState
from src.ui.theme import ThemeManager


class PlanetSprite:
    """Renders a planet with state-appropriate visual appearance."""
    
    # State colors (color-blind safe palette)
    COLORS = {
        PlanetState.LOCKED: (80, 80, 100),      # Dark gray-blue
        PlanetState.VISITED: (100, 149, 237),   # Cornflower blue (dimmed)
        PlanetState.COMPLETED: (255, 215, 0),   # Gold (bright, celebratory)
        PlanetState.CURRENT: (0, 191, 255)      # Deep sky blue (pulsing)
    }
    
    # Planet sizes by state
    SIZES = {
        PlanetState.LOCKED: 40,
        PlanetState.VISITED: 50,
        PlanetState.COMPLETED: 60,
        PlanetState.CURRENT: 55
    }
    
    def __init__(self, planet_node: PlanetNode, size_override: Optional[int] = None):
        """
        Initialize planet sprite.
        
        Args:
            planet_node: Planet data from SpaceMapState
            size_override: Optional custom size in pixels
        """
        self.planet = planet_node
        self.state = planet_node.state
        self.size = size_override or self.SIZES.get(planet_node.state, 50)
        self.color = self.COLORS.get(planet_node.state, (200, 200, 200))
        
        # Animation state
        self.pulse_phase = 0.0
        self.pulse_speed = 2.0  # Radians per second
        self.pulse_amplitude = 3  # Pixel amplitude
        
        # Surface cache
        self._surface: Optional[pygame.Surface] = None
        self._last_state = None
        self._last_size = None
        
        # Lock icon for locked planets
        self._lock_surface: Optional[pygame.Surface] = None
        self._render_lock_icon()
    
    def _render_lock_icon(self):
        """Create lock icon surface for locked planets."""
        icon_size = 24
        self._lock_surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        
        # Lock body
        pygame.draw.rect(
            self._lock_surface,
            (150, 150, 160),
            pygame.Rect(4, 10, 16, 10),
            border_radius=3
        )
        
        # Lock shackle
        pygame.draw.arc(
            self._lock_surface,
            (150, 150, 160),
            pygame.Rect(6, 6, 12, 8),
            3.14159, 0, 3
        )
    
    def update(self, delta_time: float):
        """
        Update animation state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        if self.state == PlanetState.CURRENT:
            self.pulse_phase += self.pulse_speed * delta_time
    
    def _regenerate_surface(self):
        """Regenerate the planet surface."""
        self._surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        center = (self.size, self.size)
        
        # Calculate current size with pulse animation
        current_size = self.size
        if self.state == PlanetState.CURRENT:
            pulse_offset = int(self.pulse_amplitude * abs(pygame.math.Vector2().angle_to(
                pygame.math.Vector2(self.pulse_phase, 0)
            )) / 90)  # Simplified pulse
            pulse_offset = int(self.pulse_amplitude * abs(__import__('math').sin(self.pulse_phase)))
            current_size = self.size + pulse_offset
        
        # Draw planet glow
        glow_radius = current_size + 8
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surface,
            (*self.color, 80),  # Semi-transparent
            (glow_radius, glow_radius),
            glow_radius
        )
        self._surface.blit(glow_surface, (self.size - glow_radius, self.size - glow_radius))
        
        # Draw planet
        pygame.draw.circle(
            self._surface,
            self.color,
            center,
            current_size
        )
        
        # Draw border
        border_color = tuple(min(255, c + 50) for c in self.color)
        pygame.draw.circle(
            self._surface,
            border_color,
            center,
            current_size,
            3
        )
        
        # Draw shadow for depth
        shadow_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(
            shadow_surface,
            (0, 0, 0, 60),
            (self.size + 3, self.size + 4),
            current_size
        )
        self._surface.blit(shadow_surface, (0, 0))
        
        # Add lock icon for locked planets
        if self.state == PlanetState.LOCKED and self._lock_surface:
            lock_rect = self._lock_surface.get_rect(center=center)
            self._surface.blit(self._lock_surface, lock_rect)
        
        # Add completion stars for completed planets
        if self.state == PlanetState.COMPLETED:
            self._add_completion_stars(self._surface, center, current_size)
    
    def _add_completion_stars(self, surface: pygame.Surface, center: Tuple[int, int], radius: int):
        """Add sparkle stars around completed planet."""
        import math
        num_stars = 5
        for i in range(num_stars):
            angle = (i / num_stars) * 2 * math.pi + self.pulse_phase
            star_dist = radius + 15
            star_x = int(center[0] + star_dist * math.cos(angle))
            star_y = int(center[1] + star_dist * math.sin(angle))
            
            # Draw star
            star_size = 4
            points = []
            for j in range(5):
                inner_angle = angle + j * 2 * math.pi / 5
                outer_angle = inner_angle + math.pi / 5
                inner_dist = star_size // 2
                outer_dist = star_size
                
                px1 = int(center[0] + inner_dist * math.cos(inner_angle))
                py1 = int(center[1] + inner_dist * math.sin(inner_angle))
                px2 = int(center[0] + outer_dist * math.cos(outer_angle))
                py2 = int(center[1] + outer_dist * math.sin(outer_angle))
                
                points.extend([(px1, py1), (px2, py2)])
            
            if points:
                # Simple star as a small circle for now
                pygame.draw.circle(surface, (255, 255, 200), (star_x, star_y), star_size // 2)
    
    def get_surface(self) -> pygame.Surface:
        """Get the planet surface, regenerating if state changed."""
        if (self._last_state != self.state or self._last_size != self.size or 
            self._surface is None):
            self._regenerate_surface()
            self._last_state = self.state
            self._last_size = self.size
        
        return self._surface
    
    def get_rect(self) -> pygame.Rect:
        """Get the bounding rectangle for click detection."""
        if self._surface:
            return self._surface.get_rect(center=self.planet.position)
        # Fallback if not rendered yet
        half_size = self.size
        return pygame.Rect(
            self.planet.position[0] - half_size,
            self.planet.position[1] - half_size,
            self.size * 2,
            self.size * 2
        )
    
    def is_point_inside(self, point: Tuple[int, int]) -> bool:
        """Check if a point is inside the planet's clickable area."""
        dx = point[0] - self.planet.position[0]
        dy = point[1] - self.planet.position[1]
        distance = (dx * dx + dy * dy) ** 0.5
        return distance <= self.size


class PathRenderer:
    """Renders the connection path between planets."""
    
    def __init__(self, planets: List[PlanetNode], path_color: Optional[Tuple[int, int, int]] = None):
        """
        Initialize path renderer.
        
        Args:
            planets: List of planet nodes in order
            path_color: RGB color for path (defaults to theme color)
        """
        self.planets = planets
        self.path_color = path_color or (255, 255, 255)
        self.path_width = 4
        self.glow_width = 12
        
        # Animation
        self.animation_offset = 0.0
        self.animation_speed = 30.0  # Pixels per second
        
        # Pre-render path
        self._path_surface: Optional[pygame.Surface] = None
        self._cached_planet_ids = None
    
    def update(self, delta_time: float):
        """Update animation state."""
        self.animation_offset = (self.animation_offset + 
                                  self.animation_speed * delta_time) % self.glow_width
    
    def _regenerate_path(self):
        """Regenerate the path surface."""
        if len(self.planets) < 2:
            self._path_surface = None
            return
        
        # Find bounds
        min_x = min(p.position[0] for p in self.planets)
        max_x = max(p.position[0] for p in self.planets)
        min_y = min(p.position[1] for p in self.planets)
        max_y = max(p.position[1] for p in self.planets)
        
        # Add padding
        padding = 50
        width = max_x - min_x + padding * 2
        height = max_y - min_y + padding * 2
        
        self._path_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        offset = (min_x - padding, min_y - padding)
        
        # Add glow effect
        glow_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        points = [(p.position[0] - offset[0], p.position[1] - offset[1]) 
                  for p in self.planets]
        
        if len(points) > 1:
            # Draw thick glowing path
            for i in range(len(points) - 1):
                start = points[i]
                end = points[i + 1]
                pygame.draw.line(glow_surface, (*self.path_color, 40), start, end, self.glow_width + 8)
        
        self._path_surface.blit(glow_surface, (0, 0))
        
        # Draw main path
        pygame.draw.lines(self._path_surface, self.path_color, False, points, self.path_width)
        
        # Draw animated dash effect
        if len(points) > 1:
            dash_offset = int(self.animation_offset)
            dash_length = 20
            dash_gap = 10
            
            for i in range(len(points) - 1):
                start = points[i]
                end = points[i + 1]
                
                # Calculate line length
                dx = end[0] - start[0]
                dy = end[1] - start[1]
                length = (dx * dx + dy * dy) ** 0.5
                
                if length > 0:
                    ux, uy = dx / length, dy / length
                    
                    # Draw dashes along the line
                    pos = 0
                    while pos < length:
                        dash_start_pos = pos + dash_offset
                        if dash_start_pos % (dash_length + dash_gap) < dash_length:
                            dash_end_pos = min(dash_start_pos + dash_length, length)
                            dash_start = (int(start[0] + ux * dash_start_pos), 
                                         int(start[1] + uy * dash_start_pos))
                            dash_end = (int(start[0] + ux * dash_end_pos), 
                                       int(start[1] + uy * dash_end_pos))
                            pygame.draw.line(self._path_surface, 
                                           (*self.path_color, 100),
                                           dash_start, dash_end, 
                                           max(1, self.path_width - 1))
                        pos += 5  # Step size for dashes
        
        self._cached_planet_ids = [p.planet_id for p in self.planets]
    
    def get_surface(self) -> Optional[pygame.Surface]:
        """Get the path surface, regenerating if needed."""
        current_ids = [p.planet_id for p in self.planets]
        if (self._cached_planet_ids != current_ids or self._path_surface is None):
            self._regenerate_path()
        
        return self._path_surface
    
    def draw(self, screen: pygame.Surface):
        """Draw the path on screen."""
        if self._path_surface:
            # Find offset to center the path
            if self.planets:
                min_x = min(p.position[0] for p in self.planets)
                min_y = min(p.position[1] for p in self.planets)
                screen.blit(self._path_surface, (-min_x, -min_y))


class RocketIndicator:
    """Renders an animated rocket indicator at current position."""
    
    def __init__(self, position: Tuple[int, int], size: int = 48):
        """
        Initialize rocket indicator.
        
        Args:
            position: Center position for the rocket
            size: Rocket size in pixels
        """
        self.position = position
        self.size = size
        self.angle = 0.0
        self.bob_phase = 0.0
        self.bob_amplitude = 5
        self.bob_frequency = 3.0
        
        # Rocket surface
        self._surface: Optional[pygame.Surface] = None
        self._last_position = None
        
        # Flame effect
        self.flame_intensity = 0.8
        self.flame_phase = 0.0
    
    def update(self, delta_time: float):
        """Update animation state."""
        self.bob_phase += self.bob_frequency * delta_time * 2 * 3.14159
        self.flame_phase += 10.0 * delta_time
    
    def _render_rocket(self):
        """Render the rocket surface."""
        # Create surface
        surf_size = self.size + 16
        self._surface = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        center = (surf_size // 2, surf_size // 2)
        
        # Rocket body (triangle pointing up)
        body_points = [
            (center[0], center[1] - self.size // 2),  # Nose
            (center[0] - self.size // 3, center[1] + self.size // 3),  # Bottom left
            (center[0] + self.size // 3, center[1] + self.size // 3),  # Bottom right
        ]
        pygame.draw.polygon(self._surface, (200, 200, 220), body_points)
        pygame.draw.polygon(self._surface, (255, 255, 255), body_points, 2)
        
        # Cockpit window
        window_pos = (center[0], center[1] - self.size // 6)
        pygame.draw.circle(self._surface, (135, 206, 235), window_pos, self.size // 8)
        
        # Fins
        left_fin = [
            (center[0] - self.size // 3, center[1] + self.size // 3),
            (center[0] - self.size // 2, center[1] + self.size // 2),
            (center[0] - self.size // 4, center[1] + self.size // 3),
        ]
        right_fin = [
            (center[0] + self.size // 3, center[1] + self.size // 3),
            (center[0] + self.size // 2, center[1] + self.size // 2),
            (center[0] + self.size // 4, center[1] + self.size // 3),
        ]
        pygame.draw.polygon(self._surface, (180, 60, 60), left_fin)
        pygame.draw.polygon(self._surface, (180, 60, 60), right_fin)
        
        # Engine flame with flicker effect
        import math
        flame_length = int(self.size // 3 * self.flame_intensity)
        flame_variation = math.sin(self.flame_phase) * 3
        
        flame_points = [
            (center[0] - self.size // 6, center[1] + self.size // 3),
            (center[0], center[1] + self.size // 2 + flame_length + flame_variation),
            (center[0] + self.size // 6, center[1] + self.size // 3),
        ]
        pygame.draw.polygon(self._surface, (255, 165, 0), flame_points)
    
    def get_surface(self) -> Optional[pygame.Surface]:
        """Get the rocket surface."""
        if self._surface is None or self._last_position != self.position:
            self._render_rocket()
            self._last_position = self.position
        
        return self._surface
    
    def draw(self, screen: pygame.Surface):
        """Draw the rocket at current position."""
        import math
        if self._surface:
            # Calculate bob offset
            bob_y = int(self.bob_amplitude * math.sin(self.bob_phase))
            draw_pos = (self.position[0] - self._surface.get_width() // 2,
                       self.position[1] - self._surface.get_height() // 2 + bob_y)
            
            # Rotate slightly for added interest
            # Simple rotation for now - can be enhanced with proper rotation
            screen.blit(self._surface, draw_pos)


def create_planet_sprite(planet_node: PlanetNode, size_override: Optional[int] = None) -> PlanetSprite:
    """Create a PlanetSprite instance."""
    return PlanetSprite(planet_node, size_override)


def create_path_renderer(planets: List[PlanetNode], path_color: Optional[Tuple[int, int, int]] = None) -> PathRenderer:
    """Create a PathRenderer instance."""
    return PathRenderer(planets, path_color)


def create_rocket_indicator(position: Tuple[int, int], size: int = 48) -> RocketIndicator:
    """Create a RocketIndicator instance."""
    return RocketIndicator(position, size)
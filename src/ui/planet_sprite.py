"""
Planet sprite rendering module for Word Quest.

Provides planet visuals with bloom effects for completed planets.
"""

from typing import Tuple, Optional
import pygame

from .theme import get_theme, PLANET_1, PLANET_2, PLANET_3, PLANET_4, PLANET_5


class PlanetSprite:
    """
    Renders planet visuals with bloom effects.
    Supports different planet types/colors and completion states.
    """
    
    # Bloom effect constants
    BLOOM_STAGES = 5
    BLOOM_FADE_RATE = 30  # Alpha fade rate per second
    
    def __init__(self, planet_type: int = 1, size: int = 100):
        """
        Initialize planet sprite.
        
        Args:
            planet_type: Planet number (1-5) for color selection
            size: Planet diameter in pixels
        """
        self.planet_type = planet_type
        self.size = size
        self.radius = size // 2
        
        # Get planet color based on type
        self.theme = get_theme()
        self.base_color = self.theme.get_planet_color(planet_type)
        
        # Animation state
        self.completed = False
        self.bloom_alpha = 0
        self.bloom_direction = 1
        self.bloom_timer = 0
        self._bloom_surface: Optional[pygame.Surface] = None
    
    def set_completed(self, completed: bool = True) -> None:
        """
        Set planet completion state.
        
        Args:
            completed: Whether planet is completed
        """
        self.completed = completed
        if completed:
            self.bloom_direction = 1
    
    def update(self, delta_time: float) -> None:
        """
        Update planet animation state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        if self.completed:
            # Animate bloom effect
            self.bloom_timer += delta_time
            
            if self.bloom_timer >= 0.1:  # Update every 100ms
                self.bloom_timer = 0
                alpha_change = self.BLOOM_FADE_RATE * delta_time * self.bloom_direction
                self.bloom_alpha = max(0, min(128, self.bloom_alpha + alpha_change))
                
                if self.bloom_alpha >= 128:
                    self.bloom_direction = -1
                elif self.bloom_alpha <= 0:
                    self.bloom_direction = 1
    
    def _create_bloom_surface(self) -> pygame.Surface:
        """
        Create or recreate the bloom effect surface.
        
        Returns:
            Pre-rendered bloom surface
        """
        # Create surface large enough for bloom
        bloom_size = self.size + 40
        bloom_surface = pygame.Surface((bloom_size, bloom_size), pygame.SRCALPHA)
        
        center = bloom_size // 2
        
        # Create multiple concentric rings for soft glow
        for i in range(self.BLOOM_STAGES):
            ring_radius = self.radius + (i * 8)
            ring_alpha = int((self.BLOOM_STAGES - i) / self.BLOOM_STAGES * self.bloom_alpha)
            ring_color = (*self.base_color[:3], ring_alpha)
            
            # Draw ring
            pygame.draw.circle(bloom_surface, ring_color, (center, center), ring_radius, max(1, 3 - i // 2))
        
        return bloom_surface
    
    def render(self, screen: pygame.Surface, position: Tuple[int, int], 
               completed: Optional[bool] = None) -> None:
        """
        Render planet with optional bloom effect.
        
        Args:
            screen: Pygame surface to render on
            position: (x, y) center position
            completed: Override completion state (uses instance value if None)
        """
        x, y = position
        is_completed = completed if completed is not None else self.completed
        
        # Update bloom surface if needed
        if is_completed and (self._bloom_surface is None or 
                            self._bloom_surface.get_size() != (self.size + 40, self.size + 40)):
            self._bloom_surface = self._create_bloom_surface()
        
        # Render bloom effect first (behind planet)
        if is_completed and self._bloom_surface is not None:
            bloom_x = x - (self._bloom_surface.get_width() // 2)
            bloom_y = y - (self._bloom_surface.get_height() // 2)
            screen.blit(self._bloom_surface, (bloom_x, bloom_y))
        
        # Draw planet body
        planet_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Main planet circle
        pygame.draw.circle(planet_surface, self.base_color, 
                          (self.radius, self.radius), self.radius)
        
        # Add subtle highlight for 3D effect
        highlight_color = (*self.base_color[:3], 100)
        highlight_radius = self.radius // 3
        highlight_offset = self.radius // 4
        pygame.draw.circle(planet_surface, highlight_color,
                          (self.radius - highlight_offset, self.radius - highlight_offset),
                          highlight_radius)
        
        # Add border if completed
        if is_completed:
            border_color = (*self.base_color[:3], 200)
            pygame.draw.circle(planet_surface, border_color,
                              (self.radius, self.radius), self.radius, 3)
        
        # Draw planet to screen
        screen.blit(planet_surface, (x - self.radius, y - self.radius))
    
    def get_bounds(self, position: Tuple[int, int]) -> pygame.Rect:
        """
        Get bounding rectangle for the planet.
        
        Args:
            position: (x, y) center position
            
        Returns:
            pygame.Rect for collision detection
        """
        x, y = position
        return pygame.Rect(x - self.radius, y - self.radius, self.size, self.size)
    
    def set_planet_type(self, planet_type: int) -> None:
        """
        Change planet type (updates color).
        
        Args:
            planet_type: New planet number (1-5)
        """
        self.planet_type = max(1, min(5, planet_type))
        self.base_color = self.theme.get_planet_color(self.planet_type)
        self._bloom_surface = None  # Reset bloom surface


def create_planet(planet_number: int, size: int = 100) -> PlanetSprite:
    """
    Factory function to create a planet sprite.
    
    Args:
        planet_number: Planet number (1-5)
        size: Planet diameter
        
    Returns:
        Configured PlanetSprite instance
    """
    return PlanetSprite(planet_number, size)


class PlanetManager:
    """
    Manages multiple planets for the game.
    Handles planet states, positions, and collective rendering.
    """
    
    def __init__(self, planet_count: int = 5, planet_size: int = 80):
        """
        Initialize planet manager.
        
        Args:
            planet_count: Number of planets
            planet_size: Size of each planet in pixels
        """
        self.planet_count = planet_count
        self.planet_size = planet_size
        self.planets: list[PlanetSprite] = []
        
        # Create planets
        for i in range(planet_count):
            self.planets.append(PlanetSprite(i + 1, planet_size))
        
        # Default positions (will be set on first render)
        self._positions: list[Tuple[int, int]] = []
    
    def set_positions(self, positions: list[Tuple[int, int]]) -> None:
        """
        Set positions for all planets.
        
        Args:
            positions: List of (x, y) tuples for each planet
        """
        self._positions = positions
    
    def calculate_positions(self, screen_width: int, screen_height: int,
                           margin: int = 50) -> None:
        """
        Calculate horizontal positions for planets.
        
        Args:
            screen_width: Screen width
            screen_height: Screen height
            margin: Margin from edges
        """
        total_width = self.planet_count * self.planet_size
        spacing = (self.planet_count - 1) * 30  # 30px between planets
        available_width = screen_width - (2 * margin)
        
        if total_width + spacing > available_width:
            # Scale down planets if needed
            self.planet_size = max(40, (available_width - spacing) // self.planet_count)
            for planet in self.planets:
                planet.size = self.planet_size
                planet.radius = self.planet_size // 2
        
        # Calculate positions
        self._positions = []
        start_x = margin + self.planet_size // 2
        y_pos = screen_height // 3  # Place in upper third of screen
        
        for i in range(self.planet_count):
            x_pos = start_x + i * (self.planet_size + 30)
            self._positions.append((x_pos, y_pos))
    
    def update(self, delta_time: float) -> None:
        """
        Update all planets.
        
        Args:
            delta_time: Time since last update in seconds
        """
        for planet in self.planets:
            planet.update(delta_time)
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render all planets.
        
        Args:
            screen: Pygame surface to render on
        """
        for i, planet in enumerate(self.planets):
            if i < len(self._positions):
                planet.render(screen, self._positions[i])
    
    def set_planet_completed(self, planet_index: int, completed: bool = True) -> None:
        """
        Set completion state for a specific planet.
        
        Args:
            planet_index: Index of planet (0-based)
            completed: Completion state
        """
        if 0 <= planet_index < len(self.planets):
            self.planets[planet_index].set_completed(completed)
    
    def get_planet_at_position(self, x: int, y: int) -> Optional[int]:
        """
        Find which planet (if any) is at the given position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Planet index (0-based) or None if no planet at position
        """
        for i, planet in enumerate(self.planets):
            if i < len(self._positions):
                bounds = planet.get_bounds(self._positions[i])
                if bounds.collidepoint(x, y):
                    return i
        return None
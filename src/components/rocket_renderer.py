"""
Rocket Renderer Component (STORY-004-05)

Handles rendering of rocket sprites with customizable color tinting.
Applies color filters to a base rocket sprite for student personalization.
"""

import pygame
from typing import Optional
import math

from src.models.rocket_colors import DEFAULT_ROCKET_COLOR, hex_to_rgb


class RocketRenderer:
    """
    Renders rocket sprites with color tinting support.
    
    This component handles:
    - Loading and caching of base rocket sprite
    - Color tinting via pixel multiplication
    - Sprite caching to avoid recomputing each frame
    - Rendering at arbitrary positions
    
    Attributes:
        screen: Pygame surface for rendering
        base_sprite: Original uncolored rocket sprite
        tinted_sprite: Cached sprite with current color applied
        current_color: Current rocket color as hex string
    """
    
    # Default sprite path (can be overridden)
    DEFAULT_SPRITE_PATH = "assets/rocket/base.png"
    
    # Sprite dimensions
    DEFAULT_WIDTH = 64
    DEFAULT_HEIGHT = 96
    
    def __init__(self, screen: pygame.Surface, sprite_path: Optional[str] = None):
        """
        Initialize the rocket renderer.
        
        Args:
            screen: Pygame surface for rendering
            sprite_path: Path to base rocket sprite. Uses default if None.
        """
        self.screen = screen
        self.current_color = DEFAULT_ROCKET_COLOR
        self.base_sprite: Optional[pygame.Surface] = None
        self.tinted_sprite: Optional[pygame.Surface] = None
        
        # Attempt to load sprite, fall back to procedural if file doesn't exist
        if sprite_path is None:
            sprite_path = self.DEFAULT_SPRITE_PATH
        
        try:
            self.base_sprite = pygame.image.load(sprite_path).convert_alpha()
        except (FileNotFoundError, pygame.error):
            # Create a simple procedural rocket sprite
            self.base_sprite = self._create_procedural_rocket()
        
        self._recache_sprite()
    
    def _create_procedural_rocket(self) -> pygame.Surface:
        """
        Create a simple procedural rocket sprite for MVP.
        
        Returns:
            pygame.Surface with a basic rocket shape
        """
        # Create rocket body
        surface = pygame.Surface((self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT), pygame.SRCALPHA)
        
        # Rocket body (main cone)
        body_points = [
            (self.DEFAULT_WIDTH // 2, 10),  # Top tip
            (self.DEFAULT_WIDTH // 2 + 20, 50),  # Right shoulder
            (self.DEFAULT_WIDTH // 2 + 15, 80),  # Right bottom
            (self.DEFAULT_WIDTH // 2 - 15, 80),  # Left bottom
            (self.DEFAULT_WIDTH // 2 - 20, 50),  # Left shoulder
        ]
        pygame.draw.polygon(surface, (240, 240, 240), body_points)
        
        # Window
        pygame.draw.circle(surface, (135, 206, 235), (self.DEFAULT_WIDTH // 2, 35), 12)
        pygame.draw.circle(surface, (100, 150, 180), (self.DEFAULT_WIDTH // 2, 35), 12, 2)
        
        # Fins
        fin_points_left = [(20, 60), (5, 85), (20, 80)]
        fin_points_right = [(self.DEFAULT_WIDTH - 20, 60), (self.DEFAULT_WIDTH - 5, 85), (self.DEFAULT_WIDTH - 20, 80)]
        pygame.draw.polygon(surface, (200, 200, 200), fin_points_left)
        pygame.draw.polygon(surface, (200, 200, 200), fin_points_right)
        
        # Engine flame area (will be colored separately)
        flame_points = [
            (self.DEFAULT_WIDTH // 2 - 10, 85),
            (self.DEFAULT_WIDTH // 2 + 10, 85),
            (self.DEFAULT_WIDTH // 2, 100),
        ]
        pygame.draw.polygon(surface, (230, 230, 230), flame_points)
        
        return surface
    
    def set_color(self, hex_color: str):
        """
        Change the rocket color.
        
        Applies a color tint to the base sprite and updates the cached sprite.
        Performance: ~1-5ms for 64x96 sprite.
        
        Args:
            hex_color: Hex color string (e.g., "#FF4444")
        """
        if self.current_color != hex_color:
            self.current_color = hex_color
            self._recache_sprite()
    
    def get_color(self) -> str:
        """
        Get the current rocket color.
        
        Returns:
            Hex color string
        """
        return self.current_color
    
    def _recache_sprite(self):
        """
        Recompute the tinted sprite cache.
        
        Should be called after changing the rocket color.
        """
        if self.base_sprite is None:
            return
        
        # Parse hex color to RGB
        rgb = hex_to_rgb(self.current_color)
        
        # Apply color tint to base sprite
        self.tinted_sprite = self._apply_tint(self.base_sprite, rgb)
    
    def _apply_tint(self, sprite: pygame.Surface, rgb: tuple) -> pygame.Surface:
        """
        Apply color tint to a sprite using pixel multiplication.
        
        The tint is applied by multiplying each pixel's RGB values by the
        tint color (normalized to 0-1 range). This preserves the original
        shading and transparency while changing the base color.
        
        Args:
            sprite: Source sprite to tint
            rgb: RGB tint color (0-255 range)
            
        Returns:
            New surface with applied tint
        """
        # Create a copy of the sprite
        tinted = sprite.copy()
        
        # Normalize tint color to 0-1 range
        tint_r = rgb[0] / 255.0
        tint_g = rgb[1] / 255.0
        tint_b = rgb[2] / 255.0
        
        # Apply color multiplication to each pixel
        # Note: This is a simple approach; for better performance with
        # large sprites, consider using surface color keys or shaders
        for x in range(tinted.get_width()):
            for y in range(tinted.get_height()):
                pixel = tinted.get_at((x, y))
                
                # Only tint non-transparent pixels (alpha > 0)
                if pixel.a > 0:
                    # Multiply RGB by tint, clamping to 0-255
                    r = min(255, int(pixel.r * tint_r))
                    g = min(255, int(pixel.g * tint_g))
                    b = min(255, int(pixel.b * tint_b))
                    tinted.set_at((x, y), pygame.Color(r, g, b, pixel.a))
        
        return tinted
    
    def render(self, position: tuple):
        """
        Render the tinted rocket at the specified position.
        
        Args:
            position: (x, y) coordinates for top-left corner
        """
        if self.tinted_sprite is not None:
            self.screen.blit(self.tinted_sprite, position)
    
    def render_with_position(self, x: int, y: int):
        """
        Render the rocket at specific coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.render((x, y))
    
    def get_sprite_bounds(self) -> tuple:
        """
        Get the dimensions of the rocket sprite.
        
        Returns:
            (width, height) tuple
        """
        if self.tinted_sprite is not None:
            return self.tinted_sprite.get_size()
        return (self.DEFAULT_WIDTH, self.DEFAULT_HEIGHT)
    
    def get_width(self) -> int:
        """Get the rocket sprite width."""
        return self.get_sprite_bounds()[0]
    
    def get_height(self) -> int:
        """Get the rocket sprite height."""
        return self.get_sprite_bounds()[1]


def create_rocket_renderer(
    screen: pygame.Surface,
    sprite_path: Optional[str] = None,
    color: Optional[str] = None
) -> RocketRenderer:
    """
    Factory function to create a RocketRenderer instance.
    
    Args:
        screen: Pygame surface for rendering
        sprite_path: Optional path to custom rocket sprite
        color: Optional initial color (hex string)
        
    Returns:
        Configured RocketRenderer instance
        
    Example:
        >>> screen = pygame.display.set_mode((800, 600))
        >>> renderer = create_rocket_renderer(screen, color="#FF4444")
        >>> renderer.render((100, 100))
        >>> renderer.set_color("#4488FF")  # Change to blue
        >>> renderer.render((100, 100))
    """
    renderer = RocketRenderer(screen, sprite_path)
    if color:
        renderer.set_color(color)
    return renderer
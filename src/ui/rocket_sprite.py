"""
Rocket Sprite Component (STORY-005-02)

Main rocket rendering component with support for color customization,
rotation, and composition from geometric shapes.
"""

import pygame
import math
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class RocketDimensions:
    """Rocket sprite dimensions."""
    width: int = 64
    height: int = 96
    nose_height: int = 20
    body_height: int = 50
    wing_height: int = 25
    wing_width: int = 20


class RocketSprite:
    """
    Rocket sprite rendering component.
    
    Features:
    - Procedural rocket generation from geometric shapes
    - Color customization with tinting
    - Support for rotation/tilt
    - Bounding rectangle for collision detection
    - Sprite caching for performance
    
    Attributes:
        color: Current rocket body color (RGB tuple)
        size: Rocket size in pixels
        dimensions: Rocket part dimensions
        cached_surface: Cached rendered surface for performance
    
    Example:
        >>> rocket = RocketSprite(color=(255, 255, 255))
        >>> rocket.set_color((244, 67, 54))  # Change to red
        >>> rect = rocket.get_rect()
        >>> rocket.render(screen, (100, 100), angle=0)
    """
    
    # Default dimensions matching STORY-005-02 spec
    DEFAULT_WIDTH = 64
    DEFAULT_HEIGHT = 96
    
    # Performance targets
    MAX_RENDER_TIME_MS = 3  # Maximum time for rendering
    CACHE_ENABLED = True
    
    def __init__(
        self,
        color: Tuple[int, int, int] = (255, 255, 255),
        size: int = 64
    ):
        """
        Initialize rocket sprite.
        
        Args:
            color: Initial rocket body color (RGB tuple)
            size: Rocket size in pixels (scaled proportionally)
        """
        self.color = color
        self.base_size = size  # Reference size for scaling
        
        # Calculate dimensions based on size
        scale_factor = size / self.DEFAULT_WIDTH
        self.dimensions = RocketDimensions(
            width=int(self.DEFAULT_WIDTH * scale_factor),
            height=int(self.DEFAULT_HEIGHT * scale_factor),
            nose_height=int(20 * scale_factor),
            body_height=int(50 * scale_factor),
            wing_height=int(25 * scale_factor),
            wing_width=int(20 * scale_factor)
        )
        
        # Cache for rendered surface
        self.cached_surface: Optional[pygame.Surface] = None
        self._last_color = color
        self._last_size = size
        
        # Generate the base rocket sprite
        self._generate_rocket_sprite()
    
    def _generate_rocket_sprite(self) -> None:
        """
        Generate the rocket sprite from geometric shapes.
        
        Creates a classic rocket with nose cone, body, wings, and window.
        """
        w, h = self.dimensions.width, self.dimensions.height
        
        # Create surface with transparency
        self.cached_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        
        # Draw rocket body (main cone)
        self._draw_body()
        
        # Draw window
        self._draw_window()
        
        # Draw wings
        self._draw_wings()
        
        # Draw engine/rival area
        self._draw_engine_area()
    
    def _draw_body(self) -> None:
        """Draw the main rocket body."""
        w, h = self.dimensions.width, self.dimensions.height
        
        # Body points (pointed nose)
        nose_y = 0
        shoulder_y = h * 0.4  # 40% down
        body_bottom_y = h * 0.75  # 75% down
        
        body_points = [
            (w // 2, nose_y),  # Top tip
            (w // 2 + w * 0.28, shoulder_y),  # Right shoulder
            (w // 2 + w * 0.18, body_bottom_y),  # Right bottom
            (w // 2 - w * 0.18, body_bottom_y),  # Left bottom
            (w // 2 - w * 0.28, shoulder_y),  # Left shoulder
        ]
        
        # Adjust Y positions based on proportions
        body_points = [
            (w // 2, nose_y),
            (w // 2 + w * 0.3, shoulder_y),
            (w // 2 + w * 0.2, h * 0.7),
            (w // 2 - w * 0.2, h * 0.7),
            (w // 2 - w * 0.3, shoulder_y),
        ]
        
        pygame.draw.polygon(self.cached_surface, self.color, body_points)
        
        # Add body shading (slightly darker)
        shading_points = [
            (w // 2, nose_y),
            (w // 2 + w * 0.3, shoulder_y),
            (w // 2 + w * 0.15, h * 0.5),
            (w // 2 - w * 0.15, h * 0.5),
            (w // 2 - w * 0.3, shoulder_y),
        ]
        shading_color = tuple(max(0, c - 30) for c in self.color)
        pygame.draw.polygon(self.cached_surface, shading_color, shading_points)
    
    def _draw_window(self) -> None:
        """Draw the rocket window/cockpit."""
        w, h = self.dimensions.width, self.dimensions.height
        
        # Window position (center upper body)
        window_radius = w * 0.12
        window_center = (w // 2, h * 0.35)
        
        # Window glass (light blue)
        window_color = (135, 206, 235)  # Sky blue
        pygame.draw.circle(self.cached_surface, window_color, 
                          (int(window_center[0]), int(window_center[1])), 
                          int(window_radius))
        
        # Window frame (slightly darker)
        frame_color = (100, 150, 180)
        pygame.draw.circle(self.cached_surface, frame_color,
                          (int(window_center[0]), int(window_center[1])),
                          int(window_radius), 2)
        
        # Window highlight (white, semi-transparent)
        highlight_surface = pygame.Surface((int(window_radius * 2), int(window_radius * 2)), pygame.SRCALPHA)
        highlight_radius = int(window_radius * 0.3)
        pygame.draw.circle(highlight_surface, (255, 255, 255, 150),
                          (highlight_radius, highlight_radius), highlight_radius)
        self.cached_surface.blit(highlight_surface, 
                                 (int(window_center[0] - highlight_radius * 1.2),
                                  int(window_center[1] - highlight_radius * 1.2)))
    
    def _draw_wings(self) -> None:
        """Draw the rocket wings/fins."""
        w, h = self.dimensions.width, self.dimensions.height
        
        # Wing color (darker than body)
        wing_color = tuple(max(0, c - 50) for c in self.color)
        
        # Left wing
        left_wing_points = [
            (w * 0.15, h * 0.6),
            (w * 0.05, h * 0.9),
            (w * 0.15, h * 0.85),
        ]
        pygame.draw.polygon(self.cached_surface, wing_color, left_wing_points)
        
        # Right wing
        right_wing_points = [
            (w * 0.85, h * 0.6),
            (w * 0.95, h * 0.9),
            (w * 0.85, h * 0.85),
        ]
        pygame.draw.polygon(self.cached_surface, wing_color, right_wing_points)
        
        # Add wing outlines for visibility
        outline_color = tuple(min(255, c + 50) for c in wing_color)
        pygame.draw.polygon(self.cached_surface, outline_color, left_wing_points, 1)
        pygame.draw.polygon(self.cached_surface, outline_color, right_wing_points, 1)
    
    def _draw_engine_area(self) -> None:
        """Draw the engine/thruster area."""
        w, h = self.dimensions.width, self.dimensions.height
        
        # Engine area ( darker area at bottom)
        engine_rect = pygame.Rect(
            w * 0.35,
            h * 0.85,
            w * 0.3,
            h * 0.1
        )
        engine_color = tuple(max(0, c - 80) for c in self.color)
        pygame.draw.rect(self.cached_surface, engine_color, engine_rect)
    
    def set_color(self, rgb: Tuple[int, int, int]) -> None:
        """
        Change the rocket body color.
        
        Args:
            rgb: New RGB color tuple (0-255 values)
            
        Example:
            >>> rocket = RocketSprite()
            >>> rocket.set_color((244, 67, 54))  # Red
        """
        if self.color != rgb:
            self.color = rgb
            self._last_color = rgb
            self._regenerate_sprite()
    
    def _regenerate_sprite(self) -> None:
        """Regenerate the rocket sprite with current color."""
        self._generate_rocket_sprite()
    
    def render(
        self, 
        screen: pygame.Surface, 
        position: Tuple[int, int], 
        angle: float = 0.0
    ) -> None:
        """
        Render the rocket at the specified position with optional rotation.
        
        Args:
            screen: Pygame surface to render on
            position: (x, y) coordinates for center of rocket
            angle: Rotation angle in degrees (0 = upright)
            
        Example:
            >>> rocket = RocketSprite()
            >>> rocket.render(screen, (400, 300), angle=0)
            >>> rocket.render(screen, (400, 300), angle=45)  # Tilted
        """
        if self.cached_surface is None:
            return
        
        x, y = position
        
        if angle == 0:
            # No rotation - use cached surface directly
            rect = self.cached_surface.get_rect(center=(x, y))
            screen.blit(self.cached_surface, rect.topleft)
        else:
            # Rotate the sprite
            rotated_surface = pygame.transform.rotate(self.cached_surface, -angle)
            rect = rotated_surface.get_rect(center=(x, y))
            screen.blit(rotated_surface, rect.topleft)
    
    def render_at_corner(
        self,
        screen: pygame.Surface,
        position: Tuple[int, int],
        angle: float = 0.0
    ) -> None:
        """
        Render rocket with position as top-left corner.
        
        Args:
            screen: Pygame surface to render on
            position: (x, y) top-left corner coordinates
            angle: Rotation angle in degrees
        """
        if self.cached_surface is None:
            return
        
        x, y = position
        
        if angle == 0:
            screen.blit(self.cached_surface, position)
        else:
            rotated_surface = pygame.transform.rotate(self.cached_surface, -angle)
            rect = rotated_surface.get_rect(topleft=(x, y))
            screen.blit(rotated_surface, rect.topleft)
    
    def get_rect(self) -> pygame.Rect:
        """
        Get bounding rectangle for collision detection.
        
        Returns:
            pygame.Rect representing rocket bounds
        """
        if self.cached_surface:
            return self.cached_surface.get_rect()
        return pygame.Rect(0, 0, self.dimensions.width, self.dimensions.height)
    
    def get_bounds(self) -> Tuple[int, int, int, int]:
        """
        Get bounding box as (x, y, width, height).
        
        Returns:
            Tuple of (x, y, width, height)
        """
        rect = self.get_rect()
        return (rect.x, rect.y, rect.width, rect.height)
    
    def get_width(self) -> int:
        """Get rocket width in pixels."""
        return self.dimensions.width
    
    def get_height(self) -> int:
        """Get rocket height in pixels."""
        return self.dimensions.height
    
    def get_size(self) -> Tuple[int, int]:
        """Get rocket dimensions as (width, height)."""
        return (self.dimensions.width, self.dimensions.height)
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get current rocket color."""
        return self.color
    
    def contains_point(self, x: int, y: int) -> bool:
        """
        Check if a point is within the rocket bounds.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if point is within rocket bounds
        """
        rect = self.get_rect()
        # Adjust for current position (center-based)
        # This is a simplified check - use proper position in actual usage
        return rect.collidepoint(x, y)


def create_rocket_sprite(
    color: Tuple[int, int, int] = (255, 255, 255),
    size: int = 64
) -> RocketSprite:
    """
    Factory function to create a RocketSprite instance.
    
    Args:
        color: Initial rocket color (RGB tuple)
        size: Rocket size in pixels
        
    Returns:
        Configured RocketSprite instance
        
    Example:
        >>> rocket = create_rocket_sprite(color=(255, 255, 255), size=64)
        >>> rocket.render(screen, (100, 100))
    """
    return RocketSprite(color=color, size=size)
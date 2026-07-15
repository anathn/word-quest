"""
Star field rendering module for Word Quest.

Provides procedural star field generation with twinkling animation
for the space-themedbackground.
"""

import random
from typing import List, Tuple
import pygame

from .theme import get_theme, STAR_WHITE, STAR_PALE_YELLOW


class Star:
    """
    Represents a single star in the star field.
    Handles position, size, color, and twinkling animation.
    """
    
    def __init__(self, x: int, y: int, size: int, speed: float):
        """
        Initialize a star withrandom properties.
        
        Args:
            x: X position
            y: Y position
            size: Star size (1-4 pixels)
            speed: Twinkling speed (lower = slower)
        """
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        
        # Random color (white or pale yellow)
        self.color = random.choice([STAR_WHITE, STAR_PALE_YELLOW])
        
        # Twinkling state
        self.alpha = 255  # Start fully visible
        self.alpha_direction = -1  # Fade out first
        self.twinkle_timer = 0
        self.twinkle_interval = random.uniform(2.0, 4.0)  # 2-4 second cycle
        
        # Parallax depth (affects movement speed)
        self.depth = size / 4.0  # Larger stars = closer = faster
    
    def update(self, delta_time: float, scroll_speed: float = 0.0) -> None:
        """
        Update star twinkling state.
        
        Args:
            delta_time: Time since last update in seconds
            scroll_speed: Horizontal scroll speed for parallax effect
        """
        # Update twinkle timer
        self.twinkle_timer += delta_time
        
        # Update alpha for twinkling effect
        if self.twinkle_timer >= self.twinkle_interval:
            self.twinkle_timer = 0
            self.alpha_direction *= -1  # Reverse direction
        
        # Smooth alpha transition
        alpha_change = self.speed * 50 * delta_time * self.alpha_direction
        self.alpha = max(50, min(255, self.alpha + alpha_change))
        
        # Parallax horizontal movement (for rocket movement effect)
        if scroll_speed > 0:
            parallax_speed = scroll_speed * self.depth
            self.x -= parallax_speed
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render the star with current opacity.
        
        Args:
            screen: Pygame surface to render on
        """
        # Create a surface for the star with alpha
        star_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        
        # Draw circle with current alpha
        alpha_color = (*self.color[:3], int(self.alpha))
        pygame.draw.circle(star_surface, alpha_color, 
                          (self.size, self.size), self.size)
        
        # Blit to screen
        screen.blit(star_surface, (self.x - self.size, self.y - self.size))
    
    def reset_position(self, width: int, height: int) -> None:
        """
        Reset star to random position within bounds.
        
        Args:
            width: Screen width
            height: Screen height
        """
        self.x = random.randint(0, width)
        self.y = random.randint(0, height)


class StarField:
    """
    Renders and animates the star field background.
    Handles star creation, twinkling logic, and rendering optimization.
    """
    
    def __init__(self, width: int, height: int, star_count: int = 200):
        """
        Initialize star field.
        
        Args:
            width: Screen width
            height: Screen height
            star_count: Number of stars to generate (default: 200)
        """
        self.width = width
        self.height = height
        self.star_count = star_count
        self.stars: List[Star] = []
        
        # Performance tracking
        self._last_update_time = 0
        
        # Generate stars
        self._generate_stars()
    
    def _generate_stars(self) -> None:
        """Generate random stars within screen bounds."""
        self.stars = []
        for _ in range(self.star_count):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            
            # Random size (1-4 pixels for depth variation)
            size = random.randint(1, 4)
            
            # Random speed for twinkling variation
            speed = random.uniform(0.5, 2.0)
            
            self.stars.append(Star(x, y, size, speed))
    
    def update(self, delta_time: float, scroll_speed: float = 0.0) -> None:
        """
        Update all stars.
        
        Args:
            delta_time: Time since last update in seconds
            scroll_speed: Horizontal scroll speed for parallax (0 = static)
        """
        for star in self.stars:
            star.update(delta_time, scroll_speed)
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render all stars on screen.
        
        Args:
            screen: Pygame surface to render on
        """
        for star in self.stars:
            star.render(screen)
    
    def resize(self, new_width: int, new_height: int) -> None:
        """
        Resize star field to new dimensions.
        
        Args:
            new_width: New screen width
            new_height: New screen height
        """
        self.width = new_width
        self.height = new_height
        
        # Adjust star positions for new dimensions
        for star in self.stars:
            star.x = int(star.x * new_width / self.width) if self.width > 0 else random.randint(0, new_width)
            star.y = int(star.y * new_height / self.height) if self.height > 0 else random.randint(0, new_height)
            
            # Ensure stars stay in bounds
            star.x = max(0, min(new_width, star.x))
            star.y = max(0, min(new_height, star.y))
    
    def set_scroll_speed(self, speed: float) -> None:
        """
        Set the horizontal scroll speed for parallax effect.
        
        Args:
            speed: Scroll speed (pixels per second)
        """
        self.scroll_speed = speed
    
    def get_performance_stats(self) -> dict:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            "star_count": len(self.stars),
            "width": self.width,
            "height": self.height
        }


def create_star_field(width: int, height: int, star_count: int = 200) -> StarField:
    """
    Factory function to create a star field.
    
    Args:
        width: Screen width
        height: Screen height
        star_count: Number of stars
        
    Returns:
        Configured StarField instance
    """
    return StarField(width, height, star_count)
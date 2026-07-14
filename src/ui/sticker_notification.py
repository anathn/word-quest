"""
Sticker Notification Component (STORY-004-06)

Displays "New Sticker!" unlock animations with particle effects.
Shows when a student earns a new sticker reward.
"""

import pygame
from typing import Tuple, Optional, List
from math import sin, cos, pi
import random
import time

from src.components.sticker_manager import StickerDefinition, StickerRarity, RARITY_COLORS


class Particle:
    """A single particle for confetti effects."""
    
    def __init__(self, x: int, y: int, color: Tuple[int, int, int]):
        self.x = x
        self.y = y
        self.color = color
        self.size = random.randint(3, 8)
        self.velocity_x = random.uniform(-3, 3)
        self.velocity_y = random.uniform(-5, -1)
        self.gravity = 0.2
        self.alpha = 255
        self.rotation = random.uniform(0, 2 * pi)
        self.rotation_speed = random.uniform(-0.1, 0.1)
    
    def update(self) -> bool:
        """
        Update particle position.
        
        Returns:
            False if particle should be removed
        """
        self.velocity_y += self.gravity
        self.x += self.velocity_x
        self.y += self.velocity_y
        self.alpha = max(0, self.alpha - 2)
        self.rotation += self.rotation_speed
        
        return self.alpha > 0 and self.y < 1080  # Screen height
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the particle."""
        # Create a rotated rectangle for the particle
        surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        color_with_alpha = (*self.color, int(self.alpha))
        pygame.draw.rect(surface, color_with_alpha, (0, 0, self.size * 2, self.size * 2))
        
        rotated = pygame.transform.rotate(surface, self.rotation * 180 / pi)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(rotated, rect)


class StickerNotification:
    """
    Renders the sticker unlock notification.
    
    Features:
    - Spinning entrance animation
    - "NEW STICKER!" banner
    - Scaled sticker display
    - Name and description text
    - Particle/confetti effects
    - Automated fade-out after 4 seconds
    """
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    YELLOW = (255, 255, 0)
    ORANGE = (255, 165, 0)
    
    # Banner dimensions
    BANNER_WIDTH = 400
    BANNER_HEIGHT = 60
    BANNER_PADDING = 20
    
    # Sticker
    STICKER_SIZE = 120
    STICKER_SPIN_DURATION_MS = 600  # Spin completes in 600ms
    
    # Animation timing
    TOTAL_DURATION_MS = 4000  # 4 seconds total
    FADE_OUT_START_MS = 3000  # Start fading at 3 seconds
    
    # Text
    FONT_SIZE_TITLE = 48
    FONT_SIZE_NAME = 36
    FONT_SIZE_DESC = 24
    
    def __init__(self, screen: pygame.Surface, sticker: StickerDefinition, 
                 position: Tuple[int, int] = None):
        """
        Initialize the notification.
        
        Args:
            screen: Pygame surface for rendering
            sticker: The sticker that was unlocked
            position: Center position for the notification (default: screen center)
        """
        self.screen = screen
        self.sticker = sticker
        self.start_time = pygame.time.get_ticks()
        
        # Position
        if position:
            self.center_x, self.center_y = position
        else:
            self.center_x = screen.get_width() // 2
            self.center_y = screen.get_height() // 2
        
        # Animation state
        self.spin_angle = 0.0
        self.scale = 0.0
        self.current_alpha = 255
        self.is_complete = False
        
        # Particles
        self.particles: List[Particle] = []
        self._spawn_particles()
        
        # Load sticker assets
        self.sticker_surface = self._create_sticker_surface()
        
        # Fonts
        self.banner_font = pygame.font.Font(None, self.FONT_SIZE_TITLE)
        self.name_font = pygame.font.Font(None, self.FONT_SIZE_NAME)
        self.desc_font = pygame.font.Font(None, self.FONT_SIZE_DESC)
    
    def _spawn_particles(self) -> None:
        """Spawn confetti particles."""
        colors = list(RARITY_COLORS.values())
        sticker_color = RARITY_COLORS.get(self.sticker.rarity, RARITY_COLORS[StickerRarity.COMMON])
        colors.append(sticker_color)
        
        for _ in range(50):
            particle = Particle(self.center_x, self.center_y - 100, random.choice(colors))
            self.particles.append(particle)
    
    def _create_sticker_surface(self) -> pygame.Surface:
        """
        Create a procedural sticker surface.
        
        For MVP, uses procedural drawing. Later replaced with actual artwork.
        """
        size = self.STICKER_SIZE
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Get color based on rarity
        color = RARITY_COLORS.get(self.sticker.rarity, (192, 192, 192))
        
        # Draw sticker shape (rounded rectangle/shield)
        # Outer glow
        glow_surface = pygame.Surface((size + 20, size + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surface, (*color, 100), (0, 0, size + 20, size + 20))
        
        # Main sticker shape
        padding = 10
        pygame.draw.ellipse(surface, color, (padding, padding, size - 2*padding, size - 2*padding))
        
        # Inner highlight
        inner_padding = 15
        inner_color = (min(color[0] + 50, 255), min(color[1] + 50, 255), min(color[2] + 50, 255))
        pygame.draw.ellipse(surface, inner_color, 
                           (inner_padding, inner_padding, size - 2*inner_padding, size - 2*inner_padding // 3))
        
        # Add icon based on sticker type
        self._add_sticker_icon(surface, size)
        
        return surface
    
    def _add_sticker_icon(self, surface: pygame.Surface, size: int) -> None:
        """Add a simple icon representing the sticker type."""
        icon_center = (size // 2, size // 2)
        
        # Simple icons based on sticker id
        if self.sticker.id == 'planet_winner':
            # Planet with checkmark
            pygame.draw.circle(surface, self.WHITE, icon_center, 20, 3)
            pygame.draw.circle(surface, self.WHITE, (icon_center[0], icon_center[1] + 5), 12)
        elif self.sticker.id == 'flawless_victory':
            # Star
            self._draw_star(surface, icon_center, 25, 12, self.WHITE)
        elif self.sticker.id == 'speed_demon':
            # Lightning bolt
            points = [(icon_center[0], icon_center[1] - 20),
                     (icon_center[0] + 15, icon_center[1]),
                     (icon_center[0] - 10, icon_center[1]),
                     (icon_center[0] + 5, icon_center[1] + 20)]
            pygame.draw.polygon(surface, self.WHITE, points)
        elif self.sticker.id == 'hint_helper':
            # Lightbulb
            pygame.draw.ellipse(surface, self.WHITE, (icon_center[0] - 15, icon_center[1] - 20, 30, 25))
            pygame.draw.rect(surface, self.WHITE, (icon_center[0] - 8, icon_center[1] + 5, 16, 12))
        elif self.sticker.id == 'comeback_champion':
            # Phoenix/bird shape
            pygame.draw.circle(surface, self.WHITE, icon_center, 18)
        elif self.sticker.id == 'galaxy_explorer':
            # Solar system
            pygame.draw.circle(surface, self.WHITE, (icon_center[0], icon_center[1]), 18, 2)
            pygame.draw.circle(surface, self.WHITE, icon_center, 8)
        elif 'streak' in self.sticker.id:
            # Crown
            crown_points = [
                (icon_center[0] - 20, icon_center[1] + 15),
                (icon_center[0] - 15, icon_center[1] - 10),
                (icon_center[0] - 5, icon_center[1] + 5),
                (icon_center[0] + 5, icon_center[1] - 15),
                (icon_center[0] + 15, icon_center[1] + 5),
                (icon_center[0] + 20, icon_center[1] - 8),
                (icon_center[0] + 25, icon_center[1] + 15)
            ]
            pygame.draw.polygon(surface, self.WHITE, crown_points)
        elif self.sticker.id == 'word_master':
            # Book with stars
            pygame.draw.rect(surface, self.WHITE, (icon_center[0] - 20, icon_center[1] - 15, 40, 30))
            pygame.draw.line(surface, self.WHITE, (icon_center[0], icon_center[1] - 15), 
                           (icon_center[0], icon_center[1] + 15), 2)
        elif 'bird' in self.sticker.id:
            # Sun/bird
            pygame.draw.circle(surface, self.ORANGE, icon_center, 18)
            for i in range(8):
                angle = i * pi / 4
                x = icon_center[0] + 22 * cos(angle)
                y = icon_center[1] + 22 * sin(angle)
                pygame.draw.circle(surface, self.ORANGE, (int(x), int(y)), 4)
        elif 'owl' in self.sticker.id:
            # Moon/owl
            pygame.draw.circle(surface, (192, 192, 255), icon_center, 18)
            pygame.draw.circle(surface, self.BLACK, (icon_center[0] - 6, icon_center[1] - 3), 5)
            pygame.draw.circle(surface, self.BLACK, (icon_center[0] + 6, icon_center[1] - 3), 5)
            pygame.draw.circle(surface, self.WHITE, (icon_center[0] - 6, icon_center[1] - 3), 2)
            pygame.draw.circle(surface, self.WHITE, (icon_center[0] + 6, icon_center[1] - 3), 2)
        else:
            # Generic star
            self._draw_star(surface, icon_center, 20, 8, self.WHITE)
    
    def _draw_star(self, surface: pygame.Surface, center: Tuple[int, int], 
                   outer_radius: int, inner_radius: int, color: Tuple[int, int, int]) -> None:
        """Draw a star shape."""
        points = []
        for i in range(10):
            angle = i * pi / 5 - pi / 2
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = center[0] + radius * cos(angle)
            y = center[1] + radius * sin(angle)
            points.append((x, y))
        pygame.draw.polygon(surface, color, points)
    
    def update(self) -> bool:
        """
        Update the notification state.
        
        Returns:
            False if notification should be removed
        """
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.start_time
        
        # Check if done
        if elapsed >= self.TOTAL_DURATION_MS:
            self.is_complete = True
            return False
        
        # Handle entrance animation (first 600ms)
        if elapsed < self.STICKER_SPIN_DURATION_MS:
            progress = elapsed / self.STICKER_SPIN_DURATION_MS
            # Spin from 0 to 720 degrees (2 full rotations)
            self.spin_angle = progress * 4 * pi
            # Scale from 0 to 1
            self.scale = min(1.0, progress * 1.5)  # Overshoot slightly
        else:
            # Settle to normal size
            self.scale = 1.0
            self.spin_angle = 0
        
        # Handle fade out (last 1000ms)
        if elapsed >= self.FADE_OUT_START_MS:
            fade_progress = (elapsed - self.FADE_OUT_START_MS) / (self.TOTAL_DURATION_MS - self.FADE_OUT_START_MS)
            self.current_alpha = int(255 * (1 - fade_progress))
        
        # Update particles
        self.particles = [p for p in self.particles if p.update()]
        
        return True
    
    def render(self) -> None:
        """Render the notification."""
        # Draw particles (behind)
        for particle in self.particles:
            particle.render(self.screen)
        
        # Calculate centered position
        x = self.center_x
        y = self.center_y
        
        # Build banner surface
        banner_font = pygame.font.Font(None, self.FONT_SIZE_TITLE)
        banner_text = banner_font.render("NEW STICKER!", True, self.YELLOW)
        
        banner_width = max(self.BANNER_WIDTH, banner_text.get_width() + self.BANNER_PADDING * 2)
        banner_height = self.BANNER_HEIGHT
        
        banner_surface = pygame.Surface((banner_width, banner_height), pygame.SRCALPHA)
        
        # Draw banner background (gradient-like)
        pygame.draw.rect(banner_surface, (*self.ORANGE, 200), 
                        (0, 0, banner_width, banner_height), border_radius=10)
        pygame.draw.rect(banner_surface, (*self.YELLOW, 150), 
                        (5, 5, banner_width - 10, banner_height - 10), border_radius=6)
        
        # Draw banner text
        text_x = (banner_width - banner_text.get_width()) // 2
        text_y = (banner_height - banner_text.get_height()) // 2
        banner_surface.blit(banner_text, (text_x, text_y))
        
        # Apply alpha to entire notification
        alpha = self.current_alpha
        
        # Create a combined surface for the notification
        # Calculate total height
        total_height = banner_height + 40 + self.STICKER_SIZE + 30 + int(self.FONT_SIZE_NAME * 1.2) + int(self.FONT_SIZE_DESC * 1.2)
        
        notification_surface = pygame.Surface((max(500, banner_width), total_height), pygame.SRCALPHA)
        
        # Banner at top
        banner_dest_y = 10
        notification_surface.blit(banner_surface, ((500 - banner_width) // 2, banner_dest_y))
        
        # Spacer
        spacer_y = banner_dest_y + banner_height + 30
        
        # Sticker (with spin and scale)
        sticker_y = spacer_y
        
        if self.scale > 0:
            # Create transformed sticker
            rotated_sticker = pygame.transform.rotate(self.sticker_surface, -self.spin_angle * 180 / pi)
            scaled_sticker = pygame.transform.scale(
                rotated_sticker,
                (int(self.STICKER_SIZE * self.scale), int(self.STICKER_SIZE * self.scale))
            )
            
            sticker_center_x = 500 // 2
            sticker_center_y = sticker_y + self.STICKER_SIZE // 2
            notification_surface.blit(scaled_sticker, 
                                     (sticker_center_x - scaled_sticker.get_width() // 2,
                                      sticker_center_y - scaled_sticker.get_height() // 2))
        
        # Name
        name_y = sticker_y + self.STICKER_SIZE + 20
        name_surface = self.name_font.render(self.sticker.name, True, self.WHITE)
        name_x = (500 - name_surface.get_width()) // 2
        notification_surface.blit(name_surface, (name_x, name_y))
        
        # Description
        desc_y = name_y + int(self.FONT_SIZE_NAME * 1.1)
        desc_surface = self.desc_font.render(self.sticker.description, True, (200, 200, 200))
        desc_x = (500 - desc_surface.get_width()) // 2
        notification_surface.blit(desc_surface, (desc_x, desc_y))
        
        # Apply global alpha and blit to screen
        notification_surface.set_alpha(alpha)
        notification_rect = notification_surface.get_rect(center=(self.center_x, self.center_y))
        self.screen.blit(notification_surface, notification_rect)
    
    def is_fully_faded(self) -> bool:
        """Check if notification has fully faded out."""
        return self.current_alpha <= 0


# Factory function
def create_sticker_notification(
    screen: pygame.Surface,
    sticker: StickerDefinition,
    position: Tuple[int, int] = None
) -> StickerNotification:
    """
    Create a StickerNotification instance.
    
    Args:
        screen: Pygame surface for rendering
        sticker: The sticker that was unlocked
        position: Optional center position
        
    Returns:
        Configured StickerNotification instance
    
    Example:
        >>> # When a sticker is unlocked
        >>> notification = create_sticker_notification(screen, unlocked_sticker)
        >>> 
        >>> # In game loop
        >>> while running:
        ...     notification.update()
        ...     notification.render()
        ...     if notification.is_complete:
        ...         notification = None  # Remove from game
    """
    return StickerNotification(screen=screen, sticker=sticker, position=position)
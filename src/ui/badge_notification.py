"""
Badge Notification Display (STORY-004-03)

Renders badge unlock notifications with animation.
Shows celebration messages when students earn badges.
"""

import pygame
import math
from typing import Optional, Tuple
from dataclasses import dataclass

from src.components.badge_system import Badge, Rarity, RARITY_COLORS


@dataclass
class Particle:
    """Represents a confetti particle."""
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    size: int
    alpha: int
    decay: float


class BadgeNotification:
    """
    Displays badge unlock notifications.
    
    Features:
    - Badge icon zoom animation (0 → 1.0 scale in 300ms)
    - Confetti particle burst
    - "BADGE UNLOCKED!" text with rarity color
    - Badge name and description
    - Auto-dismiss after 3 seconds
    - Rarity-based border colors
    
    Visual Design:
    - Common: Silver border
    - Uncommon: Bronze border
    - Rare: Gold border
    - Legendary: Rainbow animated border
    """
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    DARK_BG = (0, 0, 0, 200)  # Semi-transparent
    
    # Rarity colors
    RARITY_COLORS_MAP = {
        Rarity.COMMON: (192, 192, 192),      # Silver
        Rarity.UNCOMMON: (205, 127, 50),     # Bronze
        Rarity.RARE: (255, 215, 0),          # Gold
        Rarity.LEGENDARY: (255, 0, 255)      # Rainbow
    }
    
    # Font sizes
    TITLE_FONT_SIZE = 64
    BADGE_NAME_FONT_SIZE = 48
    DESCRIPTION_FONT_SIZE = 32
    
    # Timing
    FADE_IN_MS = 300
    DISPLAY_DURATION_MS = 3000
    FADE_OUT_MS = 300
    
    # Visual effects
    ZOOM_EASING = 2.0  # Bounce easing factor
    
    # Badge icon size
    BADGE_ICON_SIZE = 128
    
    # Particle effects
    PARTICLE_COUNT = 50
    PARTICLE_LIFETIME_MS = 2000
    
    def __init__(self, screen: pygame.Surface, badge: Badge):
        """
        Initialize the badge notification.
        
        Args:
            screen: Pygame surface for rendering
            badge: Badge that was unlocked
        """
        self.screen = screen
        self.badge = badge
        
        # Timing state
        self.elapsed = 0.0
        self.total_duration = self.DISPLAY_DURATION_MS / 1000.0
        
        # Animation state
        self.zoom_progress = 0.0
        self.scale = 0.0
        
        # Position (center screen)
        self.position = (
            screen.get_width() // 2,
            screen.get_height() // 2
        )
        
        # Alpha for fade
        self.alpha = 0
        
        # Prepare badge display
        self._prepare_badge_display()
        
        # Create particles
        self._create_particles()
        
        # Rainbow animation state
        self.rainbow_offset = 0.0
        self.rainbow_speed = 3.0
    
    def _prepare_badge_display(self):
        """Prepare badge icon and text surfaces."""
        # Create badge icon surface
        self.badge_surface = self._create_badge_icon()
        
        # Render title
        title_font = pygame.font.Font(None, self.TITLE_FONT_SIZE)
        self.title_surface = title_font.render("BADGE UNLOCKED!", True, self.WHITE)
        
        # Render badge name (rarity-colored)
        name_font = pygame.font.Font(None, self.BADGE_NAME_FONT_SIZE)
        name_color = self._get_rarity_color()
        self.name_surface = name_font.render(self.badge.name, True, name_color)
        
        # Render description
        desc_font = pygame.font.Font(None, self.DESCRIPTION_FONT_SIZE)
        self.description_surface = desc_font.render(self.badge.description, True, self.WHITE)
    
    def _create_badge_icon(self) -> pygame.Surface:
        """Create a placeholder badge icon."""
        size = self.BADGE_ICON_SIZE
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw badge shape (rough shield/medal shape)
        center = size // 2
        radius = size // 2 - 5
        
        # Base circle
        color = self._get_rarity_color()
        pygame.draw.circle(surface, color, (center, center), radius)
        
        # Inner circle
        pygame.draw.circle(surface, self.WHITE, (center, center), radius - 15, 3)
        
        # Border based on rarity
        border_color = self.RARITY_COLORS_MAP.get(self.badge.rarity, (192, 192, 192))
        pygame.draw.circle(surface, border_color, (center, center), radius, 4)
        
        # Add some decoration based on badge ID
        self._add_badge_symbol(surface, center, radius)
        
        return surface
    
    def _add_badge_symbol(self, surface: pygame.Surface, center: Tuple[int, int], radius: int):
        """Add a symbol based on badge type."""
        symbol_color = (255, 255, 255)
        
        if self.badge.id == 'speed_speller':
            # Lightning bolt
            points = [
                (center[0] - 10, center[1] - 15),
                (center[0] + 5, center[1] - 15),
                (center[0] - 5, center[1] + 5),
                (center[0] + 10, center[1] + 5),
                (center[0] - 5, center[1] + 20),
                (center[0] - 5, center[1] - 5),
                (center[0] - 15, center[1] - 5)
            ]
            pygame.draw.polygon(surface, symbol_color, points)
        
        elif self.badge.id == 'perseverance':
            # Mountain/anchor
            pygame.draw.polygon(surface, symbol_color, [
                (center[0], center[1] - 15),
                (center[0] - 12, center[1] + 15),
                (center[0] + 12, center[1] + 15)
            ])
        
        elif self.badge.id == 'perfect_planet':
            # Five-pointed star
            self._draw_star(surface, center, radius - 10, 5, symbol_color)
        
        elif self.badge.id == 'streak_master':
            # Number 10
            font = pygame.font.Font(None, 64)
            text = font.render("10", True, symbol_color)
            surface.blit(text, (center - text.get_width() // 2, center - text.get_height() // 2))
        
        elif self.badge.id == 'word_warrior':
            # Shield shape
            points = [
                (center[0], center[1] - 15),
                (center[0] + 12, center[1] - 5),
                (center[0] + 8, center[1] + 15),
                (center[0] - 8, center[1] + 15),
                (center[0] - 12, center[1] - 5)
            ]
            pygame.draw.polygon(surface, symbol_color, points)
        
        elif self.badge.id == 'comeback_kid':
            # Upward arrow
            pygame.draw.line(surface, symbol_color, 
                           (center[0] - 8, center[1] + 10), 
                           (center[0] + 8, center[1] - 10), 3)
            pygame.draw.line(surface, symbol_color,
                           (center[0] + 8, center[1] - 10),
                           (center[0] - 5, center[1] - 10), 3)
    
    def _draw_star(self, surface: pygame.Surface, center: Tuple[int, int], radius: int, points: int, color: Tuple[int, int, int]):
        """Draw a star shape."""
        star_points = []
        for i in range(points * 2):
            angle = math.pi / 2 + i * math.pi / points
            r = radius if i % 2 == 0 else radius // 2
            x = center[0] + r * math.cos(angle)
            y = center[1] + r * math.sin(angle)
            star_points.append((x, y))
        pygame.draw.polygon(surface, color, star_points)
    
    def _get_rarity_color(self) -> Tuple[int, int, int]:
        """Get color for badge rarity."""
        if self.badge.rarity == Rarity.LEGENDARY and self.elapsed > 0:
            # Animate rainbow for legendary
            return self._get_rainbow_color()
        return self.RARITY_COLORS_MAP.get(self.badge.rarity, (192, 192, 255))
    
    def _get_rainbow_color(self) -> Tuple[int, int, int]:
        """Generate rainbow color based on time."""
        self.rainbow_offset += self.rainbow_speed * 0.016  # ~60fps
        hue = (self.rainbow_offset % 360) / 360.0
        return self._hsv_to_rgb(hue, 1.0, 1.0)
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB."""
        if s == 0:
            gray = int(v * 255)
            return (gray, gray, gray)
        
        i = int(h * 6)
        f = h * 6 - i
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        
        i %= 6
        
        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q
        
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def _create_particles(self):
        """Create confetti particles for burst effect."""
        self.particles = []
        
        base_color = self._get_rarity_color()
        colors = [
            base_color,
            self.WHITE,
            self.RARITY_COLORS_MAP.get(self.badge.rarity, base_color)
        ]
        
        for _ in range(self.PARTICLE_COUNT):
            angle = math.random() * 2 * math.pi
            speed = 200 + math.random() * 300
            
            self.particles.append(Particle(
                x=self.position[0],
                y=self.position[1],
                vx=math.cos(angle) * speed,
                vy=math.sin(angle) * speed,
                color=colors[int(math.random() * len(colors))],
                size=8 + int(math.random() * 8),
                alpha=255,
                decay=100 + math.random() * 100
            ))
    
    def update(self, dt: float):
        """
        Update notification state.
        
        Args:
            dt: Time delta in seconds
        """
        self.elapsed += dt
        
        # Fade in
        if self.elapsed < self.FADE_IN_MS / 1000.0:
            progress = self.elapsed / (self.FADE_IN_MS / 1000.0)
            # Easing for zoom
            self.zoom_progress = min(1.0, progress * self.ZOOM_EASING)
            self.scale = self.zoom_progress * self.zoom_progress  # Quadratic easing
            self.alpha = min(255, int(progress * 255))
        
        # Fade out
        fade_out_start = self.total_duration - (self.FADE_OUT_MS / 1000.0)
        if self.elapsed >= fade_out_start:
            fade_progress = (self.elapsed - fade_out_start) / (self.FADE_OUT_MS / 1000.0)
            self.alpha = max(0, int((1 - fade_progress) * 255))
        
        # Update particles
        for particle in self.particles:
            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.vy += 200 * dt  # Gravity
            particle.alpha = max(0, int(particle.alpha - particle.decay * dt))
    
    def render(self):
        """
        Render the notification.
        
        Only renders if alpha > 0.
        """
        if self.alpha <= 0:
            return
        
        # Draw dark background
        screen_rect = self.screen.get_rect()
        bg_surface = pygame.Surface((screen_rect.width, screen_rect.height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, self.alpha // 2))
        self.screen.blit(bg_surface, (0, 0))
        
        # Calculate scaled badge size
        scaled_size = int(self.BADGE_ICON_SIZE * self.scale)
        
        # Scale badge surface
        if self.scale > 0 and self.badge_surface:
            scaled_badge = pygame.transform.scale(self.badge_surface, (scaled_size, scaled_size))
            scaled_badge.set_alpha(self.alpha)
            
            # Draw badge (centered)
            badge_x = self.position[0] - scaled_size // 2
            badge_y = self.position[1] - scaled_size // 2 - 60
            self.screen.blit(scaled_badge, (badge_x, badge_y))
        
        # Draw particles
        for particle in self.particles:
            if particle.alpha > 0:
                particle_surf = pygame.Surface((particle.size, particle.size), pygame.SRCALPHA)
                pygame.draw.circle(
                    particle_surf,
                    (*particle.color, particle.alpha),
                    (particle.size // 2, particle.size // 2),
                    particle.size // 2
                )
                self.screen.blit(particle_surf, (int(particle.x) - particle.size // 2, int(particle.y) - particle.size // 2))
        
        # Draw title "BADGE UNLOCKED!" above badge
        title_y = badge_y - self.title_surface.get_height() - 10
        self.screen.blit(self.title_surface, (
            self.position[0] - self.title_surface.get_width() // 2,
            title_y
        ))
        
        # Draw badge name below badge
        name_y = badge_y + scaled_size + 10
        self.screen.blit(self.name_surface, (
            self.position[0] - self.name_surface.get_width() // 2,
            name_y
        ))
        
        # Draw description below name
        desc_y = name_y + self.name_surface.get_height() + 5
        self.screen.blit(self.description_surface, (
            self.position[0] - self.description_surface.get_width() // 2,
            desc_y
        ))
    
    def is_complete(self) -> bool:
        """
        Check if notification is complete.
        
        Returns:
            True if fade out has finished
        """
        return self.elapsed >= self.total_duration


def create_badge_notification(screen: pygame.Surface, badge: Badge) -> BadgeNotification:
    """
    Create a badge unlock notification.
    
    Args:
        screen: Pygame surface for rendering
        badge: Badge that was unlocked
        
    Returns:
        Configured BadgeNotification instance
    
    Example:
        >>> # Create and use a badge notification
        >>> screen = pygame.display.set_mode((800, 600))
        >>> badge = Badge(
        ...     id="speed_speller",
        ...     name="Speed Speller",
        ...     description="Complete 10 words in under 5 minutes",
        ...     icon_path="assets/badges/speed_speller.png",
        ...     rarity=Rarity.COMMON,
        ...     unlock_condition="10_words_in_5_minutes",
        ...     color_scheme="yellow_blue"
        ... )
        >>> notification = create_badge_notification(screen, badge)
        >>> 
        >>> # In your game loop:
        >>> notification.update(dt)  # Update each frame
        >>> notification.render()    # Render each frame
        >>> if notification.is_complete():
        ...     # Notification finished, handle cleanup if needed
        ...     pass
    """
    return BadgeNotification(screen, badge)


# Factory function for creating notifications
def create_notification_chain(screen: pygame.Surface, badges: list) -> list:
    """
    Create a chain of badge notifications.
    
    Args:
        screen: Pygame surface for rendering
        badges: List of badges to display
        
    Returns:
        List of BadgeNotification instances
    """
    return [create_badge_notification(screen, badge) for badge in badges]
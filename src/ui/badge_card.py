"""
Badge Card Component (STORY-007-02)

Individual badge display card with states for earned/locked badges.
Supports hover animations, click animations, and progress display.
"""

import pygame
import math
from typing import Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum

from src.components.badge_system import Badge, Rarity, BadgeProgress


class BadgeState(Enum):
    """Badge display state."""
    LOCKED = "locked"
    EARNED = "earned"
    NEWLY_EARNED = "newly_earned"  # For animation


@dataclass
class BadgeCardConfig:
    """Configuration for badge card rendering."""
    # Size and spacing
    CARD_SIZE: int = 80
    MARGIN: int = 10
    BORDER_WIDTH: int = 3
    
    # Colors
    BACKGROUND_UNLOCKED: Tuple[int, int, int] = (30, 30, 50)
    BACKGROUND_LOCKED: Tuple[int, int, int] = (20, 20, 35)
    BACKGROUND_HOVER: Tuple[int, int, int] = (40, 40, 70)
    
    # Rarity colors
    RARITY_COLORS: dict = None
    
    def __post_init__(self):
        if self.RARITY_COLORS is None:
            self.RARITY_COLORS = {
                Rarity.COMMON: (192, 192, 192),       # Silver
                Rarity.UNCOMMON: (205, 127, 50),      # Bronze
                Rarity.RARE: (255, 215, 0),          # Gold
                Rarity.LEGENDARY: (128, 0, 128)       # Purple
            }
    
    def get_rarity_color(self, rarity: Rarity) -> Tuple[int, int, int]:
        """Get color for rarity level."""
        return self.RARITY_COLORS.get(rarity, (192, 192, 192))


class BadgeCard:
    """
    Individual badge card with animations.
    
    Features:
    - Earned/locked states
    - Hover highlight
    - Click/pulse animations
    - Progress bar for incomplete badges
    - Lock icon for locked badges
    - Rarity-based coloring
    - Tooltip on hover
    
    States:
    - Locked: Grayed out, lock icon shown
    - Earned: Full color with rarity border
    - Newly earned: Pulsing animation
    """
    
    def __init__(
        self,
        badge: Badge,
        state: BadgeState,
        position: Tuple[int, int],
        progress: Optional[BadgeProgress] = None,
        on_click: Optional[Callable[[], None]] = None,
        config: Optional[BadgeCardConfig] = None
    ):
        """
        Initialize a badge card.
        
        Args:
            badge: Badge definition
            state: Current display state
            position: Top-left position (x, y)
            progress: Optional progress toward badge
            on_click: Optional callback for click
            config: Optional custom configuration
        """
        self.badge = badge
        self.state = state
        self.position = position
        self.progress = progress
        self.on_click = on_click
        self.config = config or BadgeCardConfig()
        
        # Size
        self.size = self.config.CARD_SIZE
        self.margin = self.config.MARGIN
        
        # Create rect for collision detection
        self.rect = pygame.Rect(position[0], position[1], self.size, self.size)
        
        # Animation state
        self.is_hovered = False
        self.hover_alpha = 0
        self.pulse_alpha = 255
        self.pulse_direction = 1
        self.pulse_speed = 3  # Alpha change per frame
        
        # New badge animation
        self.new_badge_timer = 0.0
        self.new_badge_pulse = 0.0
        
        # Lock icon
        self.lock_icon: Optional[pygame.Surface] = None
        self._create_lock_icon()
    
    def _create_lock_icon(self):
        """Create lock icon surface."""
        size = 24
        self.lock_icon = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        
        # Lock body
        body_rect = pygame.Rect(
            center - 8, center + 2,
            16, 14
        )
        pygame.draw.rect(self.lock_icon, (128, 128, 128), body_rect, border_radius=3)
        
        # Lock shackle
        shackle_rect = pygame.Rect(
            center - 6, center - 6,
            12, 12
        )
        pygame.draw.arc(self.lock_icon, (128, 128, 128),
                       shackle_rect, math.pi, 0, 2)
    
    def _create_badge_icon(self, size: int = 40) -> pygame.Surface:
        """Create badge icon surface based on rarity."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        radius = size // 2 - 4
        
        # Get color based on rarity
        color = self.config.get_rarity_color(self.badge.rarity)
        
        # Base circle
        pygame.draw.circle(surface, color, (center, center), radius)
        
        # Border
        pygame.draw.circle(surface, color, (center, center), radius, 2)
        
        # Inner detail based on rarity
        if self.badge.rarity == Rarity.LEGENDARY:
            # Stars for legendary
            for i in range(4):
                angle = i * math.pi / 2
                px = center + int(10 * math.cos(angle))
                py = center + int(10 * math.sin(angle))
                pygame.draw.circle(surface, (255, 255, 255), (px, py), 2)
        elif self.badge.rarity == Rarity.RARE:
            # Diamond for rare
            points = [
                (center, center - 8),
                (center + 8, center),
                (center, center + 8),
                (center - 8, center)
            ]
            pygame.draw.polygon(surface, (255, 255, 255), points)
        else:
            # Circle for common/uncommon
            pygame.draw.circle(surface, (255, 255, 255), (center, center), 6, 2)
        
        return surface
    
    def update(self, dt: float):
        """
        Update badge card animations.
        
        Args:
            dt: Time delta in seconds
        """
        # Update hover alpha
        if self.is_hovered:
            self.hover_alpha = min(255, self.hover_alpha + 200 * dt)
        else:
            self.hover_alpha = max(0, self.hover_alpha - 200 * dt)
        
        # Update pulse animation for newly earned badges
        if self.state == BadgeState.NEWLY_EARNED:
            self.new_badge_timer += dt
            # Pulse for 2 seconds
            if self.new_badge_timer < 2.0:
                phase = self.new_badge_timer / 2.0 * math.pi * 2
                self.new_badge_pulse = (math.sin(phase) + 1) / 2  # 0 to 1
            else:
                self.new_badge_pulse = 0
                # Transition to earned state
                self.state = BadgeState.EARNED
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle events (mouse click).
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            return True
        
        return False
    
    def draw(self, screen: pygame.Surface):
        """
        Draw the badge card.
        
        Args:
            screen: Pygame surface to draw on
        """
        x, y = self.position
        
        # Determine background color
        if self.state == BadgeState.LOCKED:
            bg_color = self.config.BACKGROUND_LOCKED
        else:
            bg_color = self.config.BACKGROUND_HOVER if self.is_hovered else self.config.BACKGROUND_UNLOCKED
        
        # Draw background
        bg_rect = pygame.Rect(x, y, self.size, self.size)
        pygame.draw.rect(screen, bg_color, bg_rect, border_radius=8)
        
        # Draw rarity border
        if self.state != BadgeState.LOCKED:
            color = self.config.get_rarity_color(self.badge.rarity)
            
            # Apply pulse effect for newly earned badges
            if self.state == BadgeState.NEWLY_EARNED:
                pulse_factor = 1.0 + 0.3 * self.new_badge_pulse
                inflated = bg_rect.copy()
                inflated.inflate_ip(
                    int((pulse_factor - 1) * self.size),
                    int((pulse_factor - 1) * self.size)
                )
                pygame.draw.rect(screen, color, inflated, 
                               int(self.config.BORDER_WIDTH * pulse_factor), 
                               border_radius=8)
            else:
                pygame.draw.rect(screen, color, bg_rect, 
                               self.config.BORDER_WIDTH, 
                               border_radius=8)
        
        # Draw badge icon
        icon_size = 32
        icon_x = x + (self.size - icon_size) // 2
        icon_y = y + (self.size - icon_size) // 2 - 8
        badge_icon = self._create_badge_icon(icon_size)
        screen.blit(badge_icon, (icon_x, icon_y))
        
        # Draw badge name (first word for compact display)
        name_font = pygame.font.Font(None, 18)
        name_text = self.badge.name.split()[0]
        name_surface = name_font.render(name_text, True, (255, 255, 255))
        name_x = x + (self.size - name_surface.get_width()) // 2
        name_y = icon_y + icon_size + 5
        screen.blit(name_surface, (name_x, name_y))
        
        # Draw progress bar or lock icon
        progress_y = y + self.size - 18
        
        if self.state == BadgeState.LOCKED:
            # Draw lock icon
            lock_x = x + (self.size - 24) // 2
            lock_y = y + (self.size - 24) // 2
            screen.blit(self.lock_icon, (lock_x, lock_y))
        elif self.progress and not self.progress.is_complete:
            # Draw progress bar
            self._draw_progress_bar(screen, x, progress_y)
        
        # Draw "NEW" indicator for newly earned badges
        if self.state == BadgeState.NEWLY_EARNED:
            self._draw_new_indicator(screen, x, y)
    
    def _draw_progress_bar(self, screen: pygame.Surface, x: int, y: int):
        """Draw progress bar below badge."""
        bar_width = self.size - 20
        bar_height = 4
        
        bg_rect = pygame.Rect(x + 10, y, bar_width, bar_height)
        fill_width = int(bar_width * self.progress.progress_percent())
        fill_rect = pygame.Rect(x + 10, y, fill_width, bar_height)
        
        # Background
        pygame.draw.rect(screen, (20, 20, 30), bg_rect, border_radius=2)
        
        # Fill with rarity color
        color = self.config.get_rarity_color(self.badge.rarity)
        pygame.draw.rect(screen, color, fill_rect, border_radius=2)
    
    def _draw_new_indicator(self, screen: pygame.Surface, x: int, y: int):
        """Draw 'NEW' sparkles for newly earned badges."""
        # Draw sparkle stars
        import random
        random.seed(hash(self.badge.id))  # Deterministic for same badge
        
        for i in range(3):
            angle = (self.new_badge_timer * 3 + i * 2) % (2 * math.pi)
            dist = 35 + 5 * math.sin(self.new_badge_timer * 5)
            star_x = x + self.size // 2 + int(dist * math.cos(angle))
            star_y = y + self.size // 2 + int(dist * math.sin(angle))
            
            # Draw star
            star_color = (255, 255, int(128 + 127 * self.new_badge_pulse))
            pygame.draw.circle(screen, star_color, (star_x, star_y), 2)
    
    def draw_tooltip(self, screen: pygame.Surface):
        """
        Draw tooltip with badge details.
        
        Args:
            screen: Pygame surface to draw on
        """
        if self.state == BadgeState.LOCKED:
            return
        
        margin = 15
        tooltip_width = 220
        tooltip_height = 100
        
        # Position tooltip to the right of the badge
        tooltip_x = self.rect.right + 10
        tooltip_y = self.rect.centery - tooltip_height // 2
        
        # Clamp to screen
        tooltip_x = min(tooltip_x, screen.get_width() - tooltip_width - margin)
        tooltip_y = max(margin, min(tooltip_y, screen.get_height() - tooltip_height - margin))
        
        # Create tooltip surface
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        
        # Semi-transparent background
        bg_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 200))
        screen.blit(bg_surface, tooltip_rect.topleft)
        
        # Border with rarity color
        color = self.config.get_rarity_color(self.badge.rarity)
        pygame.draw.rect(screen, color, tooltip_rect, 2, border_radius=8)
        
        # Badge name
        name_font = pygame.font.Font(None, 22)
        name_surface = name_font.render(self.badge.name, True, color)
        screen.blit(name_surface, (tooltip_rect.x + 10, tooltip_rect.y + 10))
        
        # Description
        desc_font = pygame.font.Font(None, 16)
        desc_lines = self._wrap_text(desc_font, self.badge.description, tooltip_width - 20)
        for i, line in enumerate(desc_lines):
            line_surface = desc_font.render(line, True, (255, 255, 255))
            screen.blit(line_surface, (tooltip_rect.x + 10, tooltip_rect.y + 40 + i * 18))
        
        # Status
        if self.state == BadgeState.NEWLY_EARNED:
            status_text = name_font.render("JUST UNLOCKED!", True, (255, 215, 0))
        else:
            status_text = name_font.render("UNLOCKED", True, (100, 255, 100))
        screen.blit(status_text, (tooltip_rect.x + 10, tooltip_rect.y + 85))
    
    def _wrap_text(self, font: pygame.font.Font, text: str, max_width: int) -> list:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.render(test_line, True, (255, 255, 255)).get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def is_point_inside(self, point: Tuple[int, int]) -> bool:
        """
        Check if point is inside badge card.
        
        Args:
            point: (x, y) coordinates
            
        Returns:
            True if point is inside
        """
        return self.rect.collidepoint(point)


def create_badge_card(
    badge: Badge,
    unlocked: bool,
    position: Tuple[int, int],
    progress: Optional[BadgeProgress] = None,
    on_click: Optional[Callable[[], None]] = None
) -> BadgeCard:
    """
    Factory function to create a badge card.
    
    Args:
        badge: Badge definition
        unlocked: Whether badge is unlocked
        position: Top-left position (x, y)
        progress: Optional progress toward badge
        on_click: Optional click callback
        
    Returns:
        Configured BadgeCard instance
    """
    state = BadgeState.LOCKED if not unlocked else BadgeState.EARNED
    return BadgeCard(badge, state, position, progress, on_click)


def create_newly_earned_badge_card(
    badge: Badge,
    position: Tuple[int, int],
    progress: Optional[BadgeProgress] = None,
    on_click: Optional[Callable[[], None]] = None
) -> BadgeCard:
    """
    Factory function to create a newly earned badge card with animation.
    
    Args:
        badge: Badge definition
        position: Top-left position (x, y)
        progress: Optional progress (should be complete)
        on_click: Optional click callback
        
    Returns:
        Configured BadgeCard with NEWLY_EARNED state
    """
    card = BadgeCard(badge, BadgeState.NEWLY_EARNED, position, progress, on_click)
    return card
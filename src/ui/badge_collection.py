"""
Badge Collection Display (STORY-004-03)

Renders the badge collection view for students.
Shows unlocked badges with progress toward locked ones.
"""

import pygame
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from src.components.badge_system import Badge, Rarity, BadgeManager, BadgeProgress


@dataclass
class BadgeSlot:
    """Represents a slot in the badge collection display."""
    badge: Optional[Badge]
    progress: Optional[BadgeProgress]
    unlocked: bool
    rect: pygame.Rect
    position: int  # Grid position (0-5 for 3x2)


class BadgeCollection:
    """
    Displays the badge collection.
    
    Features:
    - Grid layout (3x2 badges per page)
    - Unlocked badges: Full color with animations
    - Locked badges: Grayed out with lock icon
    - Progress bars for incomplete badges
    - Hover/click shows badge details
    - Rarity-based border colors
    
    Grid Layout:
    ┌─────┬─────┬─────┐
    │  0  │  1  │  2  │
    ├─────┼─────┼─────┤
    │  3  │  4  │  5  │
    └─────┴─────┴─────┘
    """
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (128, 128, 128)
    DARK_GRAY = (64, 64, 64)
    BACKGROUND = (26, 26, 62)  # Deep space blue
    
    # Rarity colors
    RARITY_COLORS = {
        Rarity.COMMON: (192, 192, 192),      # Silver
        Rarity.UNCOMMON: (205, 127, 50),     # Bronze
        Rarity.RARE: (255, 215, 0),          # Gold
        Rarity.LEGENDARY: (128, 0, 128)      # Purple
    }
    
    # Grid configuration
    GRID_COLS = 3
    GRID_ROWS = 2
    SLOT_SIZE = 100
    SLOT_MARGIN = 20
    SLOT_PADDING = 10
    
    # Badge icon size
    BADGE_SIZE = 64
    
    # Fonts
    TITLE_FONT_SIZE = 36
    BADGE_NAME_FONT_SIZE = 20
    PROGRESS_FONT_SIZE = 16
    
    def __init__(self, screen: pygame.Surface, badge_manager: BadgeManager):
        """
        Initialize the badge collection display.
        
        Args:
            screen: Pygame surface for rendering
            badge_manager: BadgeManager instance for badge data
        """
        self.screen = screen
        self.badge_manager = badge_manager
        
        # Calculate grid dimensions
        self.slot_width = self.SLOT_SIZE + self.SLOT_MARGIN
        self.slot_height = self.SLOT_SIZE + self.SLOT_MARGIN
        
        # Grid start position (centered)
        grid_width = self.GRID_COLS * self.slot_width - self.SLOT_MARGIN
        grid_height = self.GRID_ROWS * self.slot_height - self.SLOT_MARGIN
        self.grid_start = (
            (screen.get_width() - grid_width) // 2,
            80  # Offset from top
        )
        
        # Badge slots
        self.slots: List[BadgeSlot] = []
        
        # Hover state
        self.hovered_slot: Optional[BadgeSlot] = None
        self.hover_timer: float = 0.0
        self.detail_show_delay = 0.3  # Seconds before showing details
        
        # Hover text surface
        self.detail_surface: Optional[pygame.Surface] = None
        
        # Initialize slots
        self._create_slots()
    
    def _create_slots(self):
        """Create badge slots from badge manager data."""
        self.slots.clear()
        all_badges = self.badge_manager.get_all_badges()
        
        for i, badge in enumerate(all_badges[:6]):  # Limit to 6 badges
            unlocked = self.badge_manager.is_badge_unlocked(badge.id)
            progress = self.badge_manager.get_progress(badge.id)
            
            # Calculate position
            col = i % self.GRID_COLS
            row = i // self.GRID_COLS
            x = self.grid_start[0] + col * self.slot_width + self.SLOT_PADDING
            y = self.grid_start[1] + row * self.slot_height + self.SLOT_PADDING
            
            slot_rect = pygame.Rect(
                x, y,
                self.SLOT_SIZE,
                self.SLOT_SIZE
            )
            
            slot = BadgeSlot(
                badge=badge,
                progress=progress,
                unlocked=unlocked,
                rect=slot_rect,
                position=i
            )
            self.slots.append(slot)
    
    def _create_badge_icon(self, badge: Badge, size: int = 64) -> pygame.Surface:
        """Create a badge icon surface."""
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        radius = size // 2 - 5
        
        # Base circle
        color = self.RARITY_COLORS.get(badge.rarity, (192, 192, 192))
        pygame.draw.circle(surface, color, (center, center), radius)
        
        # Border
        pygame.draw.circle(surface, color, (center, center), radius, 3)
        
        # Inner detail
        if badge.rarity == Rarity.LEGENDARY:
            # Stars for legendary
            for _ in range(4):
                angle = _ * math.pi / 2
                px = center + int(15 * math.cos(angle))
                py = center + int(15 * math.sin(angle))
                pygame.draw.circle(surface, self.WHITE, (px, py), 3)
        else:
            # Simple icon
            pygame.draw.circle(surface, self.WHITE, (center, center), 15, 2)
        
        return surface
    
    def _draw_slot(self, slot: BadgeSlot):
        """Draw a single badge slot."""
        x, y = slot.rect.x, slot.rect.y
        
        # Draw slot background
        if slot.unlocked:
            # Unlocked badge
            pygame.draw.rect(self.screen, (30, 30, 50), slot.rect, border_radius=8)
            pygame.draw.rect(self.screen, self.RARITY_COLORS.get(slot.badge.rarity, (192, 192, 192)), 
                           slot.rect, 3, border_radius=8)
            
            # Draw badge icon
            if slot.badge:
                badge_icon = self._create_badge_icon(slot.badge, size=50)
                icon_x = x + (self.SLOT_SIZE - badge_icon.get_width()) // 2
                icon_y = y + (self.SLOT_SIZE - badge_icon.get_height()) // 2 - 10
                self.screen.blit(badge_icon, (icon_x, icon_y))
                
                # Draw badge name
                name_font = pygame.font.Font(None, self.BADGE_NAME_FONT_SIZE)
                name_text = name_font.render(slot.badge.name.split()[0], True, self.WHITE)  # First word
                name_x = x + (self.SLOT_SIZE - name_text.get_width()) // 2
                name_y = icon_y + badge_icon.get_height() + 10
                self.screen.blit(name_text, (name_x, name_y))
                
                # Draw progress bar if not complete
                if slot.progress and not slot.progress.is_complete:
                    self._draw_progress_bar(x, y + self.SLOT_SIZE - 20, slot.progress)
        
        else:
            # Locked badge
            pygame.draw.rect(self.screen, (20, 20, 35), slot.rect, border_radius=8)
            pygame.draw.rect(self.screen, self.GRAY, slot.rect, 2, border_radius=8)
            
            # Draw lock icon
            lock_size = 32
            lock_x = x + (self.SLOT_SIZE - lock_size) // 2
            lock_y = y + (self.SLOT_SIZE - lock_size) // 2
            
            # Lock body
            pygame.draw.rect(self.screen, self.DARK_GRAY, 
                           (lock_x + 4, lock_y + 8, lock_size - 8, lock_size - 12), 
                           border_radius=4)
            # Lock shackle
            pygame.draw.arc(self.screen, self.DARK_GRAY,
                          (lock_x + 6, lock_y + 4, lock_size - 12, 12),
                          math.pi, 0, 3)
    
    def _draw_progress_bar(self, x: int, y: int, progress: BadgeProgress):
        """Draw progress bar for a badge."""
        bar_width = self.SLOT_SIZE - 20
        bar_height = 6
        
        bg_rect = pygame.Rect(x + 10, y, bar_width, bar_height)
        fill_width = int(bar_width * progress.progress_percent())
        fill_rect = pygame.Rect(x + 10, y, fill_width, bar_height)
        
        # Background
        pygame.draw.rect(self.screen, self.DARK_GRAY, bg_rect, border_radius=3)
        
        # Fill
        pygame.draw.rect(self.screen, self.RARITY_COLORS.get(Rarity.COMMON, (192, 192, 192)), 
                       fill_rect, border_radius=3)
        
        # Progress text
        text = pygame.font.Font(None, self.PROGRESS_FONT_SIZE)
        text_surface = text.render(progress.get_progress_text(), True, self.WHITE)
        text_x = x + (self.SLOT_SIZE - text_surface.get_width()) // 2
        text_y = y - 18
        self.screen.blit(text_surface, (text_x, text_y))
    
    def _draw_detail_panel(self, slot: BadgeSlot):
        """Draw detail panel for hovered badge."""
        if not slot.badge:
            return
        
        margin = 20
        panel_width = 250
        panel_height = 120
        
        # Position below badge
        panel_x = slot.rect.centerx - panel_width // 2
        panel_y = slot.rect.bottom + 10
        
        # Clamp to screen
        panel_x = max(margin, min(panel_x, self.screen.get_width() - panel_width - margin))
        panel_y = min(panel_y, self.screen.get_height() - margin - panel_height)
        
        # Draw panel background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # Semi-transparent background
        bg_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 200))
        self.screen.blit(bg_surface, panel_rect.topleft)
        
        # Border
        color = self.RARITY_COLORS.get(slot.badge.rarity, (192, 192, 192))
        pygame.draw.rect(self.screen, color, panel_rect, 2, border_radius=8)
        
        # Badge name
        name_font = pygame.font.Font(None, self.TITLE_FONT_SIZE)
        name_text = name_font.render(slot.badge.name, True, color)
        self.screen.blit(name_text, (panel_rect.x + 10, panel_rect.y + 10))
        
        # Description
        desc_font = pygame.font.Font(None, 24)
        desc_lines = self._wrap_text(desc_font, slot.badge.description, panel_width - 20)
        for i, line in enumerate(desc_lines):
            line_surf = desc_font.render(line, True, self.WHITE)
            self.screen.blit(line_surf, (panel_rect.x + 10, panel_rect.y + 50 + i * 20))
        
        # Status
        if slot.unlocked:
            status_text = name_font.render("UNLOCKED", True, (0, 255, 0))
        else:
            progress = slot.progress.get_progress_text() if slot.progress else "?"
            status_text = name_font.render(f"In Progress: {progress}", True, self.GRAY)
        
        self.screen.blit(status_text, (panel_rect.x + 10, panel_rect.y + 90))
    
    def _wrap_text(self, font: pygame.font.Font, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.render(test_line, True, self.WHITE).get_width() <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle mouse events.
        
        Args:
            event: Pygame event
            
        Returns:
            True if event handled, False otherwise
        """
        if event.type == pygame.MOUSEMOTION:
            # Update hover state
            mouse_pos = event.pos
            self.hovered_slot = None
            
            for slot in self.slots:
                if slot.rect.collidepoint(mouse_pos):
                    self.hovered_slot = slot
                    break
            
            return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hovered_slot:
                # Clicked on a badge - could show full details or animation
                return True
        
        return False
    
    def update(self, dt: float):
        """
        Update badge collection state.
        
        Args:
            dt: Time delta in seconds
        """
        # Update hover timer
        if self.hovered_slot:
            self.hover_timer += dt
        else:
            self.hover_timer = 0.0
        
        # Refresh slots if badge manager data changed
        self._create_slots()
    
    def render(self):
        """Render the badge collection."""
        # Draw title
        title_font = pygame.font.Font(None, self.TITLE_FONT_SIZE)
        title_text = title_font.render("BADGE COLLECTION", True, self.WHITE)
        title_rect = title_text.get_rect(centerx=self.screen.get_width() // 2, top=30)
        self.screen.blit(title_text, title_rect)
        
        # Draw unlocked count
        count_font = pygame.font.Font(None, 24)
        unlocked = self.badge_manager.get_unlocked_count()
        total = self.badge_manager.get_total_count()
        count_text = count_font.render(f"{unlocked}/{total} Badges Unlocked", True, self.GRAY)
        count_rect = count_text.get_rect(centerx=self.screen.get_width() // 2, top=60)
        self.screen.blit(count_text, count_rect)
        
        # Draw slots
        for slot in self.slots:
            self._draw_slot(slot)
        
        # Draw hover detail if hover duration reached
        if self.hovered_slot and self.hover_timer >= self.detail_show_delay:
            self._draw_detail_panel(self.hovered_slot)
        
        # Draw hover highlight
        if self.hovered_slot:
            highlight = self.hovered_slot.rect.copy()
            highlight.inflate_ip(4, 4)
            pygame.draw.rect(self.screen, (255, 255, 255), highlight, 2, border_radius=10)
    
    def get_badge_info(self, badge_id: str) -> Optional[Dict]:
        """
        Get information about a specific badge.
        
        Args:
            badge_id: Badge identifier
            
        Returns:
            Dictionary with badge information or None
        """
        badge = self.badge_manager.get_badge_by_id(badge_id)
        if not badge:
            return None
        
        return {
            'id': badge.id,
            'name': badge.name,
            'description': badge.description,
            'rarity': badge.rarity.value,
            'unlocked': self.badge_manager.is_badge_unlocked(badge_id),
            'progress': self.badge_manager.get_progress(badge_id)
        }


# Factory function
def create_badge_collection(screen: pygame.Surface, badge_manager: BadgeManager) -> BadgeCollection:
    """
    Create a badge collection display.
    
    Args:
        screen: Pygame surface for rendering
        badge_manager: BadgeManager instance
        
    Returns:
        Configured BadgeCollection instance
    
    Example:
        >>> # Create badge collection display
        >>> screen = pygame.display.set_mode((800, 600))
        >>> badge_manager = create_badge_manager()
        >>> collection = create_badge_collection(screen, badge_manager)
        >>> 
        >>> # In your game loop:
        >>> for event in pygame.event.get():
        ...     collection.handle_event(event)
        >>> 
        >>> collection.update(dt)
        >>> collection.render()
        >>> 
        >>> # Get badge info
        >>> info = collection.get_badge_info('speed_speller')
        >>> print(f"{info['name']}: {'unlocked' if info['unlocked'] else 'locked'}")
    """
    return BadgeCollection(screen, badge_manager)
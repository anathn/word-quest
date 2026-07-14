"""
Sticker Collection Component (STORY-004-06)

Displays the student's sticker collection in a grid layout.
Shows unlocked stickers with full color, locked stickers grayed out.
"""

import pygame
from typing import Tuple, Optional, List
from src.components.sticker_manager import StickerManager, StickerDefinition, StickerRarity, RARITY_COLORS


class StickerCollection:
    """
    Renders the sticker collection grid.
    
    Features:
    - 4x3 grid layout (12 stickers per page)
    - Unlocked stickers in full color
    - Locked stickers grayed out with lock icon
    - Hover/click shows details
    - "New!" badge on recently unlocked
    - Progress indicator
    - Category filtering
    - Pagination for large collections
    """
    
    # Colors
    DARK_BG = (30, 30, 60)
    PANEL_BG = (40, 40, 80, 200)
    LOCKED_GRAY = (100, 100, 100)
    HIGHLIGHT = (255, 255, 0)
    WHITE = (255, 255, 255)
    GREEN = (0, 255, 0)
    NEW_BADGE_RED = (255, 50, 50)
    
    # Layout
    STICKER_SIZE = 80
    STICKER_PADDING = 15
    GRID_COLUMNS = 4
    GRID_ROWS = 3
    
    # Position
    DEFAULT_POSITION = (100, 100)
    
    # Fonts
    TITLE_FONT_SIZE = 32
    NAME_FONT_SIZE = 16
    DESC_FONT_SIZE = 14
    
    # Animation
    HOVER_SCALE = 1.15
    HOVER_DURATION_MS = 100
    
    # "New!" badge
    NEW_BADGE_DURATION_HOURS = 24
    BADGE_SIZE = 20
    
    def __init__(self, screen: pygame.Surface, sticker_manager: StickerManager,
                 position: Tuple[int, int] = DEFAULT_POSITION):
        """
        Initialize the collection display.
        
        Args:
            screen: Pygame surface for rendering
            sticker_manager: StickerManager with sticker data
            position: Top-left position for the grid
        """
        self.screen = screen
        self.manager = sticker_manager
        self.position = position
        
        # Get all stickers
        self.all_stickers = sticker_manager.get_all_stickers()
        self.unlocked_ids = set(sticker_manager.get_unlocked_stickers())
        
        # Current page
        self.current_page = 0
        self.pages = 1
        
        # Hover state
        self.hovered_sticker_id: Optional[str] = None
        self.hover_start_time: Optional[int] = None
        self.hover_scale = 1.0
        
        # Tooltip
        self.tooltip_visible = False
        self.tooltip_sticker: Optional[StickerDefinition] = None
        
        # Category filter
        self.current_category: Optional[str] = None
        
        # Fonts
        self.title_font = pygame.font.Font(None, self.TITLE_FONT_SIZE)
        self.name_font = pygame.font.Font(None, self.NAME_FONT_SIZE)
        self.desc_font = pygame.font.Font(None, self.DESC_FONT_SIZE)
        
        # Create assets
        self._create_sticker_surfaces()
        self._create_lock_icon()
        self._create_new_badge()
        
        # Calculate pages
        self._calculate_pages()
    
    def _create_sticker_surfaces(self) -> None:
        """Create rendered surfaces for all stickers."""
        self.sticker_surfaces: dict = {}
        
        for sticker in self.all_stickers:
            self.sticker_surfaces[sticker.id] = self._create_sticker_surface(sticker)
    
    def _create_sticker_surface(self, sticker: StickerDefinition) -> pygame.Surface:
        """
        Create a procedural sticker surface.
        
        For MVP, uses procedural drawing. Later replaced with actual artwork.
        """
        size = self.STICKER_SIZE
        surface = pygame.Surface((size, size), pygame.SRCALpha)
        
        # Get color based on rarity
        base_color = RARITY_COLORS.get(sticker.rarity, (192, 192, 192))
        
        # Draw sticker shape
        padding = 8
        pygame.draw.ellipse(surface, base_color, 
                           (padding, padding, size - 2*padding, size - 2*padding))
        
        # Inner highlight
        inner_color = (min(base_color[0] + 50, 255), 
                      min(base_color[1] + 50, 255), 
                      min(base_color[2] + 50, 255))
        inner_padding = 12
        pygame.draw.ellipse(surface, inner_color,
                           (inner_padding, inner_padding, 
                            size - 2*inner_padding, size - 2*inner_padding // 3))
        
        # Add icon
        self._add_sticker_icon(surface, sticker)
        
        return surface
    
    def _add_sticker_icon(self, surface: pygame.Surface, sticker: StickerDefinition) -> None:
        """Add a simple icon representing the sticker type."""
        center = (self.STICKER_SIZE // 2, self.STICKER_SIZE // 2)
        
        if 'streak' in sticker.id:
            # Crown
            crown_points = [
                (center[0] - 15, center[1] + 12),
                (center[0] - 12, center[1] - 8),
                (center[0] - 4, center[1] + 4),
                (center[0] + 4, center[1] - 12),
                (center[0] + 12, center[1] + 4),
                (center[0] + 15, center[1] - 6),
                (center[0] + 20, center[1] + 12)
            ]
            pygame.draw.polygon(surface, self.WHITE, crown_points)
        elif 'planet' in sticker.id or 'galaxy' in sticker.id:
            # Planet
            pygame.draw.circle(surface, self.WHITE, (center[0], center[1] - 3), 12)
            pygame.draw.ellipse(surface, self.WHITE, (center[0] - 18, center[1] + 2, 36, 8), 2)
        elif 'word' in sticker.id:
            # Book
            pygame.draw.rect(surface, self.WHITE, (center[0] - 15, center[1] - 12, 30, 24))
            pygame.draw.line(surface, self.WHITE, (center[0], center[1] - 12), (center[0], center[1] + 12), 2)
        elif 'hint' in sticker.id:
            # Lightbulb
            pygame.draw.ellipse(surface, self.WHITE, (center[0] - 12, center[1] - 16, 24, 20))
            pygame.draw.rect(surface, self.WHITE, (center[0] - 6, center[1] + 4, 12, 10))
        elif 'speed' in sticker.id:
            # Lightning
            points = [(center[0], center[1] - 16),
                     (center[0] + 12, center[1] - 4),
                     (center[0] - 8, center[1] - 4),
                     (center[0] + 4, center[1] + 16)]
            pygame.draw.polygon(surface, self.WHITE, points)
        elif 'flawless' in sticker.id or 'perfect' in sticker.id:
            # Star
            self._draw_star(surface, center, 18, 8, self.WHITE)
        elif 'comeback' in sticker.id:
            # Phoenix/bird
            pygame.draw.circle(surface, self.ORANGE, center, 14)
        elif 'bird' in sticker.id:
            # Sun
            pygame.draw.circle(surface, self.ORANGE, center, 14)
        elif 'owl' in sticker.id:
            # Owl eyes
            pygame.draw.circle(surface, (192, 192, 255), center, 14)
            pygame.draw.circle(surface, self.BLACK, (center[0] - 5, center[1] - 3), 4)
            pygame.draw.circle(surface, self.BLACK, (center[0] + 5, center[1] - 3), 4)
        else:
            # Generic star
            self._draw_star(surface, center, 16, 6, self.WHITE)
    
    def _draw_star(self, surface: pygame.Surface, center: Tuple[int, int],
                   outer_radius: int, inner_radius: int, color: Tuple[int, int, int]) -> None:
        """Draw a star shape."""
        from math import pi, sin, cos
        points = []
        for i in range(10):
            angle = i * pi / 5 - pi / 2
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = center[0] + radius * cos(angle)
            y = center[1] + radius * sin(angle)
            points.append((x, y))
        pygame.draw.polygon(surface, color, points)
    
    def _create_lock_icon(self) -> None:
        """Create the lock icon for locked stickers."""
        self.lock_icon = pygame.Surface((24, 28), pygame.SRCALPHA)
        # Lock body
        pygame.draw.rect(self.lock_icon, (150, 150, 150), (4, 12, 16, 16), border_radius=3)
        # Lock shackle
        pygame.draw.arc(self.lock_icon, (150, 150, 150), (4, 4, 16, 12), 0, 3.14159, 3)
        # Keyhole
        pygame.draw.circle(self.lock_icon, (80, 80, 80), (12, 18), 3)
        pygame.draw.rect(self.lock_icon, (80, 80, 80), (10, 20, 4, 6))
    
    def _create_new_badge(self) -> None:
        """Create the 'New!' badge."""
        self.new_badge = pygame.Surface((self.BADGE_SIZE * 2, self.BADGE_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(self.new_badge, (*self.NEW_BADGE_RED, 200), 
                          (self.BADGE_SIZE, self.BADGE_SIZE // 2), self.BADGE_SIZE)
    
    def _calculate_pages(self) -> None:
        """Calculate number of pages needed."""
        total_stickers = len(self.all_stickers)
        stickers_per_page = self.GRID_COLUMNS * self.GRID_ROWS
        self.pages = max(1, (total_stickers + stickers_per_page - 1) // stickers_per_page)
    
    def _is_new_sticker(self, sticker: StickerDefinition) -> bool:
        """Check if sticker is newly unlocked (within 24 hours)."""
        if not sticker.unlocked_at:
            return False
        
        from datetime import datetime, timedelta
        return datetime.now() - sticker.unlocked_at < timedelta(hours=self.NEW_BADGE_DURATION_HOURS)
    
    def _get_visible_stickers(self) -> List[StickerDefinition]:
        """Get stickers for the current page, optionally filtered by category."""
        if self.current_category:
            filtered = [s for s in self.all_stickers if s.category == self.current_category]
        else:
            filtered = list(self.all_stickers)
        
        # Calculate page range
        start = self.current_page * self.GRID_COLUMNS * self.GRID_ROWS
        end = start + self.GRID_COLUMNS * self.GRID_ROWS
        
        return filtered[start:end]
    
    def _get_sticker_rect(self, grid_x: int, grid_y: int) -> pygame.Rect:
        """Get the screen rect for a grid position."""
        x = self.position[0] + grid_x * (self.STICKER_SIZE + self.STICKER_PADDING)
        y = self.position[1] + 80 + grid_y * (self.STICKER_SIZE + self.STICKER_PADDING)  # 80 for title
        return pygame.Rect(x, y, self.STICKER_SIZE, self.STICKER_SIZE)
    
    def _check_hover(self, mouse_pos: Tuple[int, int]) -> None:
        """Check if mouse is hovering over a sticker."""
        visible_stickers = self._get_visible_stickers()
        self.hovered_sticker_id = None
        
        mouse_x, mouse_y = mouse_pos
        
        for grid_y in range(self.GRID_ROWS):
            for grid_x in range(self.GRID_COLUMNS):
                index = grid_y * self.GRID_COLUMNS + grid_x
                if index >= len(visible_stickers):
                    continue
                
                rect = self._get_sticker_rect(grid_x, grid_y)
                if rect.collidepoint(mouse_x, mouse_y):
                    self.hovered_sticker_id = visible_stickers[index].id
                    self.hover_start_time = pygame.time.get_ticks()
                    return
        
        # If no hover, reset hover animation
        if self.hovered_sticker_id is None:
            self.hover_scale = 1.0
    
    def _render_sticker(self, sticker: StickerDefinition, grid_x: int, grid_y: int) -> None:
        """Render a single sticker at the given grid position."""
        rect = self._get_sticker_rect(grid_x, grid_y)
        
        # Check if unlocked
        unlocked = sticker.id in self.unlocked_ids
        
        # Calculate scale for hover effect
        scale = 1.0
        if self.hovered_sticker_id == sticker.id and self.hover_start_time:
            elapsed = pygame.time.get_ticks() - self.hover_start_time
            if elapsed < self.HOVER_DURATION_MS:
                progress = elapsed / self.HOVER_DURATION_MS
                scale = 1.0 + (self.HOVER_SCALE - 1.0) * progress
        
        # Get sticker surface
        surface = self.sticker_surfaces.get(sticker.id)
        if surface:
            # Scale if hovering
            if scale != 1.0:
                scaled_surface = pygame.transform.scale(surface, 
                                                       (int(self.STICKER_SIZE * scale), 
                                                        int(self.STICKER_SIZE * scale)))
                # Center scaled surface
                offset_x = (self.STICKER_SIZE - scaled_surface.get_width()) // 2
                offset_y = (self.STICKER_SIZE - scaled_surface.get_height()) // 2
                rect = pygame.Rect(rect.x + offset_x, rect.y + offset_y, 
                                  scaled_surface.get_width(), scaled_surface.get_height())
                surface = scaled_surface
            
            # If locked, apply gray overlay
            if not unlocked:
                locked_surface = surface.copy()
                locked_surface.fill((128, 128, 128))  # Gray filter
                locked_surface.set_alpha(128)
                self.screen.blit(locked_surface, rect)
                
                # Draw lock icon
                lock_rect = self.lock_icon.get_rect(center=rect.center)
                self.screen.blit(self.lock_icon, lock_rect)
            else:
                # Normal render with glow for unlocked
                glow_surface = pygame.Surface((self.STICKER_SIZE + 10, self.STICKER_SIZE + 10), pygame.SRCALPHA)
                glow_rect = glow_surface.get_rect(center=rect.center)
                pygame.draw.ellipse(glow_surface, (*RARITY_COLORS.get(sticker.rarity, (192, 192, 192)), 30), 
                                   (0, 0, self.STICKER_SIZE + 10, self.STICKER_SIZE + 10))
                self.screen.blit(glow_surface, glow_rect)
                
                self.screen.blit(surface, rect)
        
        # Draw "New!" badge for recently unlocked
        if unlocked and self._is_new_sticker(sticker):
            badge_rect = self.new_badge.get_rect(
                topright=(rect.right + 5, rect.top - 5)
            )
            glow_badge = pygame.Surface((badge_rect.width + 4, badge_rect.height + 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_badge, (*self.NEW_BADGE_RED, 100), 
                              (badge_rect.width // 2 + 2, badge_rect.height // 2 + 2), 
                              badge_rect.width // 2 + 2)
            self.screen.blit(glow_badge, badge_rect.move(-2, -2))
            self.screen.blit(self.new_badge, badge_rect)
    
    def _render_title(self) -> None:
        """Render the collection title and progress."""
        title = "Sticker Collection"
        title_surface = self.title_font.render(title, True, self.WHITE)
        title_x = self.position[0] + (self.GRID_COLUMNS * (self.STICKER_SIZE + self.STICKER_PADDING) - title_surface.get_width()) // 2
        self.screen.blit(title_surface, (title_x, self.position[1]))
        
        # Progress
        unlocked_count = self.manager.get_unlocked_count()
        total_count = self.manager.get_total_count()
        progress_text = f"{unlocked_count}/{total_count} stickers collected"
        progress_surface = self.desc_font.render(progress_text, True, (150, 150, 150))
        progress_x = self.position[0] + (self.GRID_COLUMNS * (self.STICKER_SIZE + self.STICKER_PADDING) - progress_surface.get_width()) // 2
        self.screen.blit(progress_surface, (progress_x, self.position[1] + 35))
    
    def _render_category_filter(self) -> None:
        """Render category filter buttons."""
        categories = ["All", "Progression", "Skill", "Special"]
        button_width = 90
        button_height = 30
        button_padding = 5
        start_x = self.position[0]
        y = self.position[1] + 55
        
        for i, category in enumerate(categories):
            x = start_x + i * (button_width + button_padding)
            
            is_selected = (category == "All" and self.current_category is None) or category.lower() == self.current_category
            
            # Button background
            color = self.HIGHLIGHT if is_selected else (100, 100, 120)
            surface = pygame.Surface((button_width, button_height))
            surface.fill(color)
            pygame.draw.rect(surface, (200, 200, 200), (0, 0, button_width, button_height), 2)
            
            self.screen.blit(surface, (x, y))
            
            # Button text
            text = self.desc_font.render(category, True, self.WHITE)
            text_rect = text.get_rect(center=(x + button_width // 2, y + button_height // 2))
            self.screen.blit(text, text_rect)
    
    def _render_page_navigation(self) -> None:
        """Render page navigation."""
        if self.pages <= 1:
            return
        
        page_text = f"Page {self.current_page + 1} of {self.pages}"
        page_surface = self.desc_font.render(page_text, True, (150, 150, 150))
        
        grid_width = self.GRID_COLUMNS * (self.STICKER_SIZE + self.STICKER_PADDING) - self.STICKER_PADDING
        text_x = self.position[0] + grid_width // 2 - page_surface.get_width() // 2
        text_y = self.position[1] + 80 + self.GRID_ROWS * (self.STICKER_SIZE + self.STICKER_PADDING)
        
        self.screen.blit(page_surface, (text_x, text_y))
    
    def _render_tooltip(self) -> None:
        """Render the tooltip with sticker details."""
        if not self.tooltip_visible or not self.tooltip_sticker:
            return
        
        sticker = self.tooltip_sticker
        padding = 10
        
        # Calculate dimensions
        name_width = self.name_font.size(sticker.name)[0]
        desc_width = self.desc_font.size(sticker.description)[0]
        rarity_text = f"Rarity: {sticker.rarity.value.title()}"
        width = max(name_width, desc_width, self.name_font.size(rarity_text)[0]) + padding * 2
        height = 30 + self.name_font.get_height() + 10 + self.desc_font.get_height() + 10 + self.name_font.get_height()
        
        # Position (under mouse or offset)
        x = self.position[0] + self.GRID_COLUMNS * (self.STICKER_SIZE + self.STICKER_PADDING) + 20
        y = self.position[1] + 80
        
        # Draw tooltip background
        tooltip = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(tooltip, (*self.PANEL_BG[:3], 220), (0, 0, width, height), border_radius=8)
        pygame.draw.rect(tooltip, (100, 100, 150), (0, 0, width, height), 2)
        
        # Draw content
        # Name
        name_surface = self.name_font.render(sticker.name, True, RARITY_COLORS.get(sticker.rarity, (255, 255, 255)))
        tooltip.blit(name_surface, (padding, 5))
        
        # Rarity
        rarity_surface = self.name_font.render(rarity_text, True, (180, 180, 200))
        tooltip.blit(rarity_surface, (padding, 20))
        
        # Description
        desc_surface = self.desc_font.render(sticker.description, True, (220, 220, 220))
        tooltip.blit(desc_surface, (padding, 20 + self.name_font.get_height() + 5))
        
        self.screen.blit(tooltip, (x, y))
    
    def update(self, mouse_pos: Tuple[int, int], mouse_clicked: bool = False) -> None:
        """
        Update the collection display state.
        
        Args:
            mouse_pos: Current mouse position
            mouse_clicked: Whether mouse was clicked this frame
        """
        # Check hover
        self._check_hover(mouse_pos)
        
        # Update scale animation
        if self.hover_start_time:
            elapsed = pygame.time.get_ticks() - self.hover_start_time
            if elapsed >= self.HOVER_DURATION_MS:
                self.hover_scale = self.HOVER_SCALE
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Handle pygame events.
        
        Args:
            event: Pygame event
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check category buttons
                categories = ["All", "Progression", "Skill", "Special"]
                button_width = 90
                button_height = 30
                button_padding = 5
                y = self.position[1] + 55
                
                for i, category in enumerate(categories):
                    x = self.position[0] + i * (button_width + button_padding)
                    rect = pygame.Rect(x, y, button_width, button_height)
                    
                    if rect.collidepoint(event.pos):
                        # Toggle category
                        if self.current_category == category.lower() if category != "All" else self.current_category is None:
                            self.current_category = None
                        else:
                            self.current_category = category.lower() if category != "All" else None
                        self.current_page = 0
                        return
                
                # Check page navigation
                if self.pages > 1:
                    grid_height = self.GRID_ROWS * (self.STICKER_SIZE + self.STICKER_PADDING) - self.STICKER_PADDING
                    nav_y = self.position[1] + 80 + grid_height
                    page_text = f"Page {self.current_page + 1} of {self.pages}"
                    page_surface = self.desc_font.render(page_text, True, (150, 150, 150))
                    
                    # Previous page
                    prev_rect = pygame.Rect(self.position[0], nav_y, 30, 24)
                    if prev_rect.collidepoint(event.pos):
                        self.current_page = max(0, self.current_page - 1)
                        return
                    
                    # Next page
                    nav_width = self.GRID_COLUMNS * (self.STICKER_SIZE + self.STICKER_PADDING) - self.STICKER_PADDING
                    next_rect = pygame.Rect(self.position[0] + nav_width - 30, nav_y, 30, 24)
                    if next_rect.collidepoint(event.pos):
                        self.current_page = min(self.pages - 1, self.current_page + 1)
                        return
        
        elif event.type == pygame.MOUSEMOTION:
            # Update tooltip based on hover
            if self.hovered_sticker_id:
                sticker = self.manager.get_sticker_by_id(self.hovered_sticker_id)
                if sticker:
                    self.tooltip_visible = True
                    self.tooltip_sticker = sticker
            else:
                self.tooltip_visible = False
    
    def render(self) -> None:
        """Render the sticker collection."""
        # Draw title and progress
        self._render_title()
        
        # Draw category filters
        self._render_category_filter()
        
        # Draw stickers
        visible_stickers = self._get_visible_stickers()
        
        for grid_y in range(self.GRID_ROWS):
            for grid_x in range(self.GRID_COLUMNS):
                index = grid_y * self.GRID_COLUMNS + grid_x
                if index >= len(visible_stickers):
                    continue
                
                sticker = visible_stickers[index]
                self._render_sticker(sticker, grid_x, grid_y)
        
        # Draw page navigation
        self._render_page_navigation()
        
        # Draw tooltip
        self._render_tooltip()


# Factory function
def create_sticker_collection(
    screen: pygame.Surface,
    sticker_manager: StickerManager,
    position: Tuple[int, int] = StickerCollection.DEFAULT_POSITION
) -> StickerCollection:
    """
    Create a StickerCollection instance.
    
    Args:
        screen: Pygame surface for rendering
        sticker_manager: StickerManager with sticker data
        position: Top-left position for the grid
        
    Returns:
        Configured StickerCollection instance
    
    Example:
        >>> # In parent dashboard or student progress screen
        >>> collection = create_sticker_collection(screen, sticker_manager)
        >>> 
        >>> # In game loop
        >>> for event in pygame.event.get():
        ...     collection.handle_event(event)
        >>> 
        >>> mouse_pos = pygame.mouse.get_pos()
        >>> collection.update(mouse_pos, mouse_clicked)
        >>> collection.render()
    """
    return StickerCollection(screen=screen, sticker_manager=sticker_manager, position=position)
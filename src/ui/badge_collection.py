"""
Badge Collection Display (STORY-007-02)

Renders the badge collection view for students.
Shows unlocked badges with progress toward locked ones.
Includes category filtering and improved animations.
"""

import pygame
import math
import logging
from typing import List, Dict, Optional, Tuple, Callable, Any
from dataclasses import dataclass

from src.components.badge_system import Badge, Rarity, BadgeManager, BadgeProgress
from src.ui.badge_card import BadgeCard, BadgeCardConfig, BadgeState


@dataclass
class CategoryTab:
    """Represents a category filter tab."""
    name: str
    rect: pygame.Rect
    active: bool


class BadgeCollection:
    """
    Displays the badge collection with category filtering.
    
    Features:
    - Grid layout (3x2 badges per page)
    - Category filtering (All, Speed, Accuracy, Perseverance)
    - Unlocked badges: Full color with animations
    - Locked badges: Grayed out with lock icon
    - Progress bars for incomplete badges
    - Hover/click shows badge details
    - Rarity-based border colors
    - Newly earned badges pulse with animation
    - Keyboard navigation (arrow keys, Tab, Enter, Space)
    - Screen reader accessibility via caption integration
    
    Keyboard Controls:
    - Arrow Right/Left: Navigate between badges
    - Arrow Up/Down: Navigate between rows
    - Enter/Space: Select/activate badge
    - Tab: Cycle through category tabs
    - Escape: Deselect badge
    
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
    LIGHT_GRAY = (200, 200, 200)
    DARK_GRAY = (64, 64, 64)
    BACKGROUND = (26, 26, 62)  # Deep space blue
    
    # Tab colors
    TAB_INACTIVE = (50, 50, 80)
    TAB_ACTIVE = (30, 30, 60)
    TAB_HOVER = (70, 70, 100)
    TAB_TEXT_INACTIVE = (150, 150, 180)
    TAB_TEXT_ACTIVE = (255, 255, 215)
    
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
    
    # Badge icon size
    BADGE_SIZE = 64
    
    # Fonts
    TITLE_FONT_SIZE = 32
    TAB_FONT_SIZE = 18
    BADGE_NAME_FONT_SIZE = 18
    PROGRESS_FONT_SIZE = 14
    
    def __init__(
        self, 
        screen: pygame.Surface, 
        badge_manager: BadgeManager,
        on_badge_select: Optional[Callable[[Badge], None]] = None,
        caption_manager: Optional[Any] = None
    ):
        """
        Initialize the badge collection display.
        
        Args:
            screen: Pygame surface for rendering
            badge_manager: BadgeManager instance for badge data
            on_badge_select: Callback when a badge is clicked
            caption_manager: Optional CaptionManager for screen reader announcements
        """
        self.screen = screen
        self.badge_manager = badge_manager
        self.on_badge_select = on_badge_select
        self.caption_manager = caption_manager
        
        # Category filter
        self.current_category = "all"
        self.filtered_badges: List[Badge] = []
        
        # Badge cards
        self.badge_cards: List[BadgeCard] = []
        
        # Category tabs
        self.tabs: List[CategoryTab] = []
        
        # Hover state
        self.hovered_card: Optional[BadgeCard] = None
        self.hover_timer: float = 0.0
        self.detail_show_delay = 0.3  # Seconds before showing tooltip
        
        # Keyboard navigation state
        self.selected_card_index: int = 0  # Current keyboard-selected badge
        self.selected_tab_index: int = 0   # Current keyboard-selected tab
        self.navigation_mode: str = "badges"  # "tabs" or "badges"
        
        # UI layout
        self._init_layout()
    
    def _init_layout(self):
        """Initialize UI layout elements."""
        # Calculate grid position
        slot_width = self.SLOT_SIZE + self.SLOT_MARGIN
        slot_height = self.SLOT_SIZE + self.SLOT_MARGIN
        
        grid_width = self.GRID_COLS * slot_width - self.SLOT_MARGIN
        grid_height = self.GRID_ROWS * slot_height - self.SLOT_MARGIN
        
        self.grid_start = (
            (self.screen.get_width() - grid_width) // 2,
            120  # Offset from top (below tabs)
        )
        
        # Create category tabs
        self._create_category_tabs()
        
        # Initialize badge cards
        self._update_badge_cards()
    
    def _create_category_tabs(self):
        """Create category filter tabs."""
        categories = self.badge_manager.get_all_categories()
        
        # Tab configuration
        tab_width = 100
        tab_height = 30
        tab_margin = 10
        start_x = (self.screen.get_width() - (len(categories) + 1) * (tab_width + tab_margin)) // 2
        
        # "All" tab
        all_rect = pygame.Rect(start_x, 80, tab_width, tab_height)
        self.tabs.append(CategoryTab("All", all_rect, True))
        
        # Category tabs
        x = start_x + tab_width + tab_margin
        for category in categories:
            rect = pygame.Rect(x, 80, tab_width, tab_height)
            self.tabs.append(CategoryTab(category.capitalize(), rect, False))
            x += tab_width + tab_margin
        
        self.filtered_badges = self.badge_manager.get_all_badges()
    
    def _create_badge_card(self, badge: Badge) -> BadgeCard:
        """Create a badge card for a badge."""
        unlocked = self.badge_manager.is_badge_unlocked(badge.id)
        progress = self.badge_manager.get_progress(badge.id)
        
        # Calculate position
        all_badges = self.badge_manager.get_all_badges()
        idx = all_badges.index(badge) if badge in all_badges else 0
        
        col = idx % self.GRID_COLS
        row = idx // self.GRID_COLS
        
        x = self.grid_start[0] + col * (self.SLOT_SIZE + self.SLOT_MARGIN)
        y = self.grid_start[1] + row * (self.SLOT_SIZE + self.SLOT_MARGIN)
        
        # Determine state
        if unlocked:
            # Check if newly unlocked (just this session)
            state = BadgeState.EARNED
        else:
            state = BadgeState.LOCKED
        
        def on_click():
            if self.on_badge_select:
                self.on_badge_select(badge)
        
        return BadgeCard(badge, state, (x, y), progress, on_click)
    
    def _update_badge_cards(self):
        """Update the badge cards based on current filter."""
        self.badge_cards.clear()
        
        # Get badges based on category filter
        if self.current_category == "all":
            self.filtered_badges = self.badge_manager.get_all_badges()
        else:
            self.filtered_badges = self.badge_manager.get_badges_by_category(self.current_category)
        
        # Recreate cards at correct positions
        for idx, badge in enumerate(self.filtered_badges):
            col = idx % self.GRID_COLS
            row = idx // self.GRID_COLS
            
            x = self.grid_start[0] + col * (self.SLOT_SIZE + self.SLOT_MARGIN)
            y = self.grid_start[1] + row * (self.SLOT_SIZE + self.SLOT_MARGIN)
            
            unlocked = self.badge_manager.is_badge_unlocked(badge.id)
            progress = self.badge_manager.get_progress(badge.id)
            
            state = BadgeState.EARNED if unlocked else BadgeState.LOCKED
            
            def on_click(b=badge):
                if self.on_badge_select:
                    self.on_badge_select(b)
            
            card = BadgeCard(badge, state, (x, y), progress, on_click)
            self.badge_cards.append(card)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle events (mouse click, hover, keyboard).
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check tab clicks
                for tab in self.tabs:
                    if tab.rect.collidepoint(event.pos):
                        self.current_category = tab.name.lower()
                        # Update tab states
                        for t in self.tabs:
                            t.active = (t.name.lower() == self.current_category)
                        self._update_badge_cards()
                        return True
                
                # Check badge card clicks
                for card in self.badge_cards:
                    if card.handle_event(event):
                        return True
        
        elif event.type == pygame.MOUSEMOTION:
            # Update hover state for cards
            self.hovered_card = None
            for card in self.badge_cards:
                if card.rect.collidepoint(event.pos):
                    self.hovered_card = card
                    card.is_hovered = True
                else:
                    card.is_hovered = False
            
            return True
        
        elif event.type == pygame.KEYDOWN:
            return self._handle_keyboard(event)
        
        return False
    
    def update(self, dt: float):
        """
        Update badge collection state.
        
        Args:
            dt: Time delta in seconds
        """
        # Update hover timer
        if self.hovered_card:
            self.hover_timer += dt
        else:
            self.hover_timer = 0.0
        
        # Update all badge cards
        for card in self.badge_cards:
            card.update(dt)
        
        # Refresh cards if filter changed or manager data changed
        # (in a full implementation, we'd track for changes)
    
    def render(self):
        """Render the badge collection."""
        # Draw title
        self._draw_title()
        
        # Draw tabs
        self._draw_tabs()
        
        # Draw badge cards
        for card in self.badge_cards:
            card.draw(self.screen)
        
        # Draw tooltip if hovering long enough
        if self.hovered_card and self.hover_timer >= self.detail_show_delay:
            self.hovered_card.draw_tooltip(self.screen)
        
        # Draw empty state if no badges in category
        if not self.badge_cards:
            self._draw_empty_state()
    
    def _draw_title(self):
        """Draw the collection title and count."""
        # Title
        title_font = pygame.font.Font(None, self.TITLE_FONT_SIZE)
        title_text = title_font.render("BADGE COLLECTION", True, self.WHITE)
        title_rect = title_text.get_rect(centerx=self.screen.get_width() // 2, top=20)
        self.screen.blit(title_text, title_rect)
        
        # Unlocked count
        count_font = pygame.font.Font(None, 22)
        unlocked = self.badge_manager.get_unlocked_count()
        total = self.badge_manager.get_total_count()
        count_text = count_font.render(f"{unlocked}/{total} Badges Unlocked", True, self.LIGHT_GRAY)
        count_rect = count_text.get_rect(centerx=self.screen.get_width() // 2, top=50)
        self.screen.blit(count_text, count_rect)
    
    def _draw_tabs(self):
        """Draw category filter tabs."""
        for tab in self.tabs:
            # Background
            if tab.active:
                color = self.TAB_ACTIVE
                text_color = self.TAB_TEXT_ACTIVE
            elif tab.rect.collidepoint(pygame.mouse.get_pos()):
                color = self.TAB_HOVER
                text_color = self.TAB_TEXT_ACTIVE
            else:
                color = self.TAB_INACTIVE
                text_color = self.TAB_TEXT_INACTIVE
            
            pygame.draw.rect(self.screen, color, tab.rect, border_radius=5)
            
            # Text
            font = pygame.font.Font(None, self.TAB_FONT_SIZE)
            text_surf = font.render(tab.name, True, text_color)
            text_rect = text_surf.get_rect(center=tab.rect.center)
            self.screen.blit(text_surf, text_rect)
    
    def _draw_empty_state(self):
        """Draw empty state when no badges in category."""
        font = pygame.font.Font(None, 24)
        text = font.render("No badges in this category yet!", True, self.GRAY)
        rect = text.get_rect(centerx=self.screen.get_width() // 2, top=self.grid_start[1] + self.SLOT_SIZE)
        self.screen.blit(text, rect)
    
    def _handle_keyboard(self, event: pygame.event.Event) -> bool:
        """
        Handle keyboard events for accessibility.
        
        Args:
            event: Pygame KEYDOWN event
            
        Returns:
            True if event was handled
        """
        # Tab navigation between tabs and badges
        if event.key == pygame.K_TAB:
            # Shift+Tab goes backwards, Tab goes forwards
            if event.mod & pygame.KMOD_SHIFT:
                if self.navigation_mode == "badges" and self.selected_card_index > 0:
                    self.selected_card_index -= 1
                    self._announce_selected()
                else:
                    self.navigation_mode = "tabs"
                    if self.selected_tab_index > 0:
                        self.selected_tab_index -= 1
                        self._announce_selected()
            else:
                if self.navigation_mode == "tabs" and self.selected_tab_index < len(self.tabs) - 1:
                    self.selected_tab_index += 1
                    self._announce_selected()
                else:
                    self.navigation_mode = "badges"
                    if self.badge_cards:
                        self.selected_card_index = 0
                        self._announce_selected()
            return True
        
        # Tab navigation mode
        if self.navigation_mode == "tabs":
            if event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
                if self.selected_tab_index < len(self.tabs) - 1:
                    self.selected_tab_index += 1
                    self._announce_selected()
                return True
            elif event.key == pygame.K_LEFT or event.key == pygame.K_UP:
                if self.selected_tab_index > 0:
                    self.selected_tab_index -= 1
                    self._announce_selected()
                return True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # Activate selected tab
                tab = self.tabs[self.selected_tab_index]
                self.current_category = tab.name.lower()
                for t in self.tabs:
                    t.active = (t.name.lower() == self.current_category)
                self._update_badge_cards()
                self.navigation_mode = "badges"
                self.selected_card_index = 0
                self._update_tab_visuals()
                return True
        
        # Badge navigation mode
        elif self.navigation_mode == "badges":
            if event.key == pygame.K_RIGHT:
                if self.selected_card_index < len(self.badge_cards) - 1:
                    self.selected_card_index += 1
                    self._announce_selected()
                return True
            elif event.key == pygame.K_LEFT:
                if self.selected_card_index > 0:
                    self.selected_card_index -= 1
                    self._announce_selected()
                return True
            elif event.key == pygame.K_DOWN:
                # Move down one row (GRID_COLS badges per row)
                new_index = self.selected_card_index + self.GRID_COLS
                if new_index < len(self.badge_cards):
                    self.selected_card_index = new_index
                    self._announce_selected()
                return True
            elif event.key == pygame.K_UP:
                # Move up one row
                new_index = self.selected_card_index - self.GRID_COLS
                if new_index >= 0:
                    self.selected_card_index = new_index
                    self._announce_selected()
                return True
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                # Activate selected badge
                if self.badge_cards:
                    self._activate_selected_badge()
                return True
            elif event.key == pygame.K_ESCAPE:
                # Deselect
                self.selected_card_index = -1
                return True
        
        # Arrow keys to switch from tabs to badges
        if event.key in (pygame.K_RIGHT, pygame.K_DOWN) and self.navigation_mode == "tabs":
            if self.selected_tab_index < len(self.tabs) - 1:
                self.selected_tab_index += 1
            else:
                self.navigation_mode = "badges"
                self.selected_card_index = 0
            self._announce_selected()
            return True
        
        if event.key in (pygame.K_LEFT, pygame.K_UP) and self.navigation_mode == "badges":
            if self.selected_card_index > 0:
                self.selected_card_index -= 1
            else:
                self.navigation_mode = "tabs"
                self.selected_tab_index = len(self.tabs) - 1
            self._announce_selected()
            return True
        
        return False
    
    def _announce_selected(self):
        """Announce currently selected item via caption manager (screen reader)."""
        if not self.caption_manager:
            return
        
        try:
            if self.navigation_mode == "tabs":
                tab = self.tabs[self.selected_tab_index]
                caption_text = f"Category tab: {tab.name}"
            elif self.navigation_mode == "badges" and self.badge_cards:
                card = self.badge_cards[self.selected_card_index]
                badge = card.badge
                if card.state == BadgeState.EARNED:
                    caption_text = f"Badge: {badge.name}. {badge.description}"
                else:
                    caption_text = f"Locked badge: {badge.name}"
            else:
                return
            
            # Announce to screen reader
            self.caption_manager.show_caption(caption_text, duration=2.0)
        except Exception as e:
            # Don't let accessibility errors break core functionality
            logger = logging.getLogger(__name__)
            logger.debug(f"Caption announcement failed: {e}")
    
    def _activate_selected_badge(self):
        """Activate the currently selected badge."""
        if not self.badge_cards or self.selected_card_index < 0:
            return
        
        card = self.badge_cards[self.selected_card_index]
        badge = card.badge
        
        # Call the select callback if provided
        if self.on_badge_select:
            self.on_badge_select(badge)
        
        # Also show full details immediately
        card.is_hovered = True
        self.hovered_card = card
        self.hover_timer = self.detail_show_delay  # Show immediately
        
        # Announce badge details
        if self.caption_manager:
            caption_text = f"{badge.name}: {badge.description}"
            self.caption_manager.show_caption(caption_text, duration=3.0)
    
    def _update_tab_visuals(self):
        """Update tab visual states for keyboard selection."""
        for i, tab in enumerate(self.tabs):
            tab.active = (i == self.selected_tab_index) if self.navigation_mode == "tabs" else False
    
    def _update_selection_visuals(self):
        """Update visual selection indicators for keyboard navigation."""
        # Reset all card hover states
        for i, card in enumerate(self.badge_cards):
            card.is_hovered = (i == self.selected_card_index) if self.navigation_mode == "badges" else False
    
    def update(self, dt: float):
        """
        Update badge collection state.
        
        Args:
            dt: Time delta in seconds
        """
        # Update hover timer
        if self.hovered_card:
            self.hover_timer += dt
        else:
            self.hover_timer = 0.0
        
        # Update all badge cards
        for card in self.badge_cards:
            card.update(dt)
        
        # Update selection visuals for keyboard navigation
        if self.navigation_mode == "badges" and self.badge_cards:
            self._update_selection_visuals()
        
        # Refresh cards if filter changed or manager data changed
        # (in a full implementation, we'd track for changes)
    
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
            'category': badge.category,
            'rarity': badge.rarity.value,
            'unlocked': self.badge_manager.is_badge_unlocked(badge_id),
            'progress': self.badge_manager.get_progress(badge_id)
        }
    
    def set_category(self, category: str):
        """
        Set the category filter.
        
        Args:
            category: Category name or "all"
        """
        category_lower = category.lower()
        if category_lower == "all":
            self.current_category = "all"
            for tab in self.tabs:
                tab.active = (tab.name.lower() == "all")
        else:
            # Check if category exists
            categories = self.badge_manager.get_all_categories()
            if category_lower in [c.lower() for c in categories]:
                self.current_category = category_lower
                for tab in self.tabs:
                    tab.active = (tab.name.lower() == category_lower)
        self._update_badge_cards()


def create_badge_collection(
    screen: pygame.Surface, 
    badge_manager: BadgeManager,
    on_badge_select: Optional[Callable[[Badge], None]] = None,
    caption_manager: Optional[Any] = None
) -> BadgeCollection:
    """
    Create a badge collection display.
    
    Args:
        screen: Pygame surface for rendering
        badge_manager: BadgeManager instance
        on_badge_select: Callback when badge is clicked
        caption_manager: Optional CaptionManager for screen reader support
        
    Returns:
        Configured BadgeCollection instance
    """
    return BadgeCollection(screen, badge_manager, on_badge_select, caption_manager)
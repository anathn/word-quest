"""
Simple Progress Stats Display Component (STORY-007-04)

Display simple, encouraging progress statistics that are easy for
3rd graders to understand. Focuses on positive metrics that celebrate
achievements rather than highlighting failures.

Features:
- Words mastered counter (e.g., "23/50 words")
- Accuracy rate with encouraging format ("You get it right 8 out of 10 times!")
- Best streak achievement ("Your best streak: 7!")
- Total practice time in kid-friendly format ("You've practiced for 2 hours!")
- Today's practice summary ("Today: 8 words, 6 correct!")
- Upward trend indicators for improving metrics
"""

import pygame
import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

from src.ui.theme import ThemeManager
from src.utils.stats_calculator import StatsCalculator

logger = logging.getLogger(__name__)


@dataclass
class StatCardData:
    """Data for a single stat card."""
    title: str
    text: str
    icon: str
    value: Optional[int] = None
    trend: Optional[str] = None


class TrendIndicator:
    """
    Renders trend indicators (arrows) for stats.
    
    Shows whether a metric is improving, stable, or declining.
    Uses upward arrow for positive trends, neutral for stable, etc.
    """
    
    # Trend symbols and colors
    TRENDS = {
        "up": ("↑", (76, 175, 80)),      # Green upward arrow
        "down": ("↓", (255, 152, 0)),    # Orange downward arrow
        "stable": ("→", (189, 189, 189)), # Grey neutral arrow
        "new": ("⭐", (255, 215, 0))      # Gold star for new stats
    }
    
    def __init__(self, theme: ThemeManager):
        """
        Initialize trend indicator.
        
        Args:
            theme: ThemeManager instance for colors and fonts
        """
        self.theme = theme
    
    def get_symbol(self, trend: str) -> str:
        """
        Get the symbol for a trend.
        
        Args:
            trend: Trend value ("up", "down", "stable", "new")
            
        Returns:
            Symbol string
        """
        return self.TRENDS.get(trend, ("?", (189, 189, 189)))[0]
    
    def get_color(self, trend: str) -> Tuple[int, int, int]:
        """
        Get the color for a trend.
        
        Args:
            trend: Trend value
            
        Returns:
            RGB color tuple
        """
        return self.TRENDS.get(trend, ("?", (189, 189, 189)))[1]
    
    def render(self, screen: pygame.Surface, trend: str, x: int, y: int, size: int = 24):
        """
        Render a trend indicator.
        
        Args:
            screen: Pygame surface to render on
            trend: Trend value
            x: X position
            y: Y position
            size: Font size
        """
        symbol, color = self.TRENDS.get(trend, ("?", (189, 189, 189)))
        font = self.theme.get_font(size)
        text_surf = font.render(symbol, True, color)
        screen.blit(text_surf, (x, y))


class StatCard:
    """
    Individual stat card component.
    
    Displays a single metric with icon, title, value, and optional trend.
    """
    
    CARD_WIDTH = 280
    CARD_HEIGHT = 120
    BORDER_RADIUS = 15
    
    def __init__(self, theme: ThemeManager):
        """
        Initialize stat card.
        
        Args:
            theme: ThemeManager instance for colors and fonts
        """
        self.theme = theme
        self.trend_indicator = TrendIndicator(theme)
        self.card_rect: Optional[pygame.Rect] = None
    
    def draw(self, screen: pygame.Surface, x: int, y: int, data: StatCardData):
        """
        Draw the stat card.
        
        Args:
            screen: Pygame surface to draw on
            x: X position
            y: Y position
            data: Stat card data
        """
        # Create card rect
        card_rect = pygame.Rect(x, y, self.CARD_WIDTH, self.CARD_HEIGHT)
        self.card_rect = card_rect
        
        # Card background
        background_color = self.theme.get_color("UI_BG_DARK")
        border_color = self.theme.get_color("UI_ACCENT")
        
        pygame.draw.rect(screen, background_color, card_rect, border_radius=self.BORDER_RADIUS)
        pygame.draw.rect(screen, border_color, card_rect, width=2, border_radius=self.BORDER_RADIUS)
        
        # Icon (large, left side)
        icon_font = self.theme.get_font(40)
        icon_surf = icon_font.render(data.icon, True, self.theme.get_color("UI_ACCENT"))
        screen.blit(icon_surf, (x + 15, y + 15))
        
        # Title (top, next to icon)
        title_font = self.theme.get_font(18)
        title_surf = title_font.render(data.title, True, self.theme.get_color("UI_TEXT_NORMAL"))
        screen.blit(title_surf, (x + 70, y + 15))
        
        # Value/Text (center, large)
        value_font = self.theme.get_font(24)
        value_surf = value_font.render(data.text, True, self.theme.get_color("UI_TEXT_NORMAL"))
        
        # Wrap text if too long
        if value_surf.get_width() > self.CARD_WIDTH - 40:
            # Wrap text into multiple lines
            wrapped_lines = self._wrap_text(data.text, value_font, self.CARD_WIDTH - 50)
            for i, line in enumerate(wrapped_lines[:2]):  # Max 2 lines
                line_surf = value_font.render(line, True, self.theme.get_color("UI_TEXT_NORMAL"))
                screen.blit(line_surf, (x + 20, y + 55 + i * 24))
        else:
            screen.blit(value_surf, (x + 20, y + 55))
        
        # Trend indicator (bottom right, if present)
        if data.trend:
            trend_x = x + self.CARD_WIDTH - 40
            trend_y = y + self.CARD_HEIGHT - 28
            self.trend_indicator.render(screen, data.trend, trend_x, trend_y, size=24)
    
    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """
        Wrap text to fit within maximum width.
        
        Args:
            text: Text to wrap
            font: Font to use
            max_width: Maximum width in pixels
            
        Returns:
            List of wrapped lines
        """
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def get_rect(self) -> Optional[pygame.Rect]:
        """Get the card's bounding rectangle."""
        return self.card_rect


class ProgressStatsDisplay:
    """
    Main progress stats display component.
    
    Displays multiple stat cards in a grid layout with
    age-appropriate, encouraging metrics.
    
    Features:
    - 2x3 grid layout (up to 6 stat cards)
    - Auto-refresh after progress updates
    - Large, clear numbers for readability
    - High contrast display
    - Real-time updates after each word completion
    """
    
    STAT_CARDS = [
        {"id": "words_mastered", "title": "Words Mastered"},
        {"id": "accuracy", "title": "You're Doing Great!"},
        {"id": "best_streak", "title": "Best Streak"},
        {"id": "practice_time", "title": "Practice Time"},
        {"id": "today", "title": "Today's Progress"},
    ]
    
    def __init__(self, screen: pygame.Surface, progress_tracker, theme: Optional[ThemeManager] = None):
        """
        Initialize the progress stats display.
        
        Args:
            screen: Pygame surface to draw on
            progress_tracker: ProgressTracker instance for data
            theme: Optional ThemeManager (uses default if not provided)
        """
        self.screen = screen
        self.progress = progress_tracker
        self.theme = theme or ThemeManager()
        self.calculator = StatsCalculator(progress_tracker)
        
        # Layout configuration
        self.card_width = 280
        self.card_height = 120
        self.spacing = 20
        self.start_x = 50
        self.start_y = 100
        self.cols = 3
        
        # Components
        self.stat_cards: List[Tuple[int, int, StatCard, str]] = []
        self.title_rect: Optional[pygame.Rect] = None
        self.background_rect: Optional[pygame.Rect] = None
        
        # Build stat cards layout
        self._build_stat_cards()
        
        # Cache for cached display data
        self._cached_stats: Optional[Dict] = None
        self._cache_time = 0
    
    def _build_stat_cards(self):
        """Create stat card components and calculate layout."""
        self.stat_cards.clear()
        
        stats = self.calculator.get_all_stats()
        
        for i, card_config in enumerate(self.STAT_CARDS):
            card_id = card_config["id"]
            title = card_config["title"]
            
            # Get data for this stat
            stat_data = stats.get(card_id)
            
            if stat_data is None:
                # Skip this card if no data (e.g., today's summary when no practice today)
                continue
            
            # Determine value and trend
            value = stat_data.get("value", 0)
            
            # For accuracy, we need to extract trend specially
            trend = stat_data.get("trend", None)
            
            # Create StatCardData
            card_data = StatCardData(
                title=title,
                text=stat_data["text"],
                icon=stat_data["icon"],
                value=value,
                trend=trend
            )
            
            # Calculate position
            col = i % self.cols
            row = i // self.cols
            x = self.start_x + (col * (self.card_width + self.spacing))
            y = self.start_y + (row * (self.card_height + self.spacing))
            
            # Create stat card component
            card = StatCard(self.theme)
            self.stat_cards.append((x, y, card, card_data))
    
    def _draw_background(self):
        """Draw the background panel."""
        screen_rect = self.screen.get_rect()
        
        # Full screen background
        bg_color = self.theme.get_color("SPACE_BLUE")
        self.background_rect = pygame.Rect(0, 0, screen_rect.width, screen_rect.height)
        self.screen.fill(bg_color, self.background_rect)
        
        # Draw title
        title_font = self.theme.get_font(36)
        title_surf = title_font.render("Your Progress", True, self.theme.get_color("UI_ACCENT"))
        title_x = (screen_rect.width - title_surf.get_width()) // 2
        title_y = 30
        self.screen.blit(title_surf, (title_x, title_y))
        self.title_rect = pygame.Rect(title_x, title_y, title_surf.get_width(), title_surf.get_height())
    
    def update_stats(self):
        """
        Refresh all stats (call after progress changes).
        
        Should be called after completing a planet or word to
        update the displayed statistics.
        """
        self._build_stat_cards()
    
    def draw(self):
        """
        Render all stat cards.
        
        Call this each frame to display the progress stats.
        """
        self._draw_background()
        
        # Draw all stat cards
        for x, y, card, data in self.stat_cards:
            card.draw(self.screen, x, y, data)
    
    def draw_subtitle(self, text: str, y_offset: int = 160):
        """
        Draw a subtitle below the title.
        
        Args:
            text: Subtitle text
            y_offset: Y position for subtitle
        """
        subtitle_font = self.theme.get_font(20)
        subtitle_surf = subtitle_font.render(text, True, self.theme.get_color("UI_TEXT_MUTED"))
        subtitle_x = (self.screen.get_rect().width - subtitle_surf.get_width()) // 2
        self.screen.blit(subtitle_surf, (subtitle_x, y_offset))
    
    def get_card_at_position(self, x: int, y: int) -> Optional[Tuple[int, int, StatCard, str]]:
        """
        Get the stat card at a given position.
        
        Used for click/touch detection.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Tuple of (x, y, card, data) if card found, None otherwise
        """
        for card_x, card_y, card, data in self.stat_cards:
            rect = card.get_rect()
            if rect and rect.collidepoint(x, y):
                return (card_x, card_y, card, data)
        return None


def create_progress_stats_display(
    screen: pygame.Surface,
    progress_tracker,
    theme: Optional[ThemeManager] = None
) -> ProgressStatsDisplay:
    """
    Factory function to create a ProgressStatsDisplay.
    
    Args:
        screen: Pygame surface to draw on
        progress_tracker: ProgressTracker instance for data
        theme: Optional ThemeManager
        
    Returns:
        Configured ProgressStatsDisplay instance
    """
    return ProgressStatsDisplay(screen, progress_tracker, theme)
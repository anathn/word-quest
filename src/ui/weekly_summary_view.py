"""
Weekly Summary View Component

Displays parent-facing weekly progress summary.
Implements STORY-003-05: Weekly Summary View
"""

import pygame
from typing import List, Optional, Callable
from datetime import date, timedelta

from src.models.summary_data import WeeklySummary, Trend
from src.analytics.weekly_summary import WeeklySummaryGenerator
from src.ui.trend_graph import TrendGraph


class WeeklySummaryView:
    """
    UI component for displaying weekly progress summary.
    
    Shows words mastered, accuracy trends, practice time, and
    allows navigation between weeks.
    """
    
    # Colors
    COLOR_BG = (250, 250, 255)
    COLOR_CARD = (255, 255, 255)
    COLOR_TEXT = (50, 50, 70)
    COLOR_TEXT_LIGHT = (100, 100, 120)
    COLOR_BORDER = (200, 200, 220)
    COLOR_ACCENT = (76, 175, 80)
    COLOR_ACCENT_LIGHT = (100, 189, 100)
    COLOR_WARNING = (255, 152, 0)
    
    # Layout
    CARD_PADDING = 15
    METRIC_SPACING = 10
    SECTION_SPACING = 20
    
    def __init__(self, generator: WeeklySummaryGenerator, student_id: str,
                 width: int = 700, height: int = 500):
        """
        Initialize the weekly summary view.
        
        Args:
            generator: WeeklySummaryGenerator for fetching data
            student_id: ID of the student to show summary for
            width: View width in pixels
            height: View height in pixels
        """
        self.generator = generator
        self.student_id = student_id
        self.width = width
        self.height = height
        
        # Current display date (defaults to today)
        self._current_date = date.today()
        
        # Current summary data
        self._current_summary: Optional[WeeklySummary] = None
        self._history: List[WeeklySummary] = []
        
        # UI state
        self._hovered_navigate: Optional[str] = None  # "prev" or "next"
        self._expanded_lists: bool = False
        
        # Components
        self._trend_graph = TrendGraph(width=width - 60, height=180)
        
        # Fonts (initialized on first render)
        self._title_font: Optional[pygame.font.Font] = None
        self._header_font: Optional[pygame.font.Font] = None
        self._body_font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None
        
        # Navigation button rects (calculated on render)
        self._prev_button_rect: Optional[pygame.Rect] = None
        self._next_button_rect: Optional[pygame.Rect] = None
    
    def _init_fonts(self):
        """Initialize Pygame fonts."""
        if self._title_font is None:
            try:
                self._title_font = pygame.font.SysFont('arial', 20, bold=True)
                self._header_font = pygame.font.SysFont('arial', 16, bold=True)
                self._body_font = pygame.font.SysFont('arial', 14)
                self._small_font = pygame.font.SysFont('arial', 12)
            except Exception:
                self._title_font = pygame.font.Font(None, 20)
                self._header_font = pygame.font.Font(None, 16)
                self._body_font = pygame.font.Font(None, 14)
                self._small_font = pygame.font.Font(None, 12)
    
    def _load_data(self):
        """Load summary data for current week and history."""
        try:
            self._current_summary = self.generator.generate_summary(
                self.student_id, self._current_date
            )
            self._history = self.generator.get_weekly_history(
                self.student_id, weeks=4, reference_date=self._current_date
            )
        except Exception as e:
            # Create empty summary on error
            week_start, week_end = self.generator.get_week_for_date(self._current_date)
            self._current_summary = WeeklySummary(
                week_start=week_start,
                week_end=week_end,
                student_id=self.student_id
            )
    
    def render(self, surface: pygame.Surface):
        """
        Render the weekly summary view.
        
        Args:
            surface: Pygame surface to render to
        """
        self._init_fonts()
        self._load_data()
        
        # Clear background
        surface.fill(self.COLOR_BG)
        
        # Draw header with navigation
        self._draw_header(surface)
        
        # Draw content
        if self._current_summary and self._current_summary.has_data():
            self._draw_content(surface)
        else:
            self._draw_empty_state(surface)
    
    def _draw_header(self, surface: pygame.Surface):
        """Draw header with title and week navigation."""
        if not self._current_summary:
            return
        
        # Title
        if self._title_font:
            title = "Weekly Progress Summary"
            title_surf = self._title_font.render(title, True, self.COLOR_TEXT)
            surface.blit(title_surf, (20, 15))
        
        # Week display with navigation
        week_start = self._current_summary.week_start
        week_end = self._current_summary.week_end
        week_label = f"Week of {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"
        
        if self._body_font:
            week_surf = self._body_font.render(week_label, True, self.COLOR_TEXT)
            surface.blit(week_surf, (20, 50))
        
        # Navigation buttons
        nav_y = 45
        nav_size = 30
        
        # Previous button
        self._prev_button_rect = pygame.Rect(160, nav_y, nav_size, nav_size)
        self._draw_navigation_button(surface, self._prev_button_rect, "◄", "Previous Week")
        
        # Next button
        self._next_button_rect = pygame.Rect(195, nav_y, nav_size, nav_size)
        self._draw_navigation_button(surface, self._next_button_rect, "►", "Next Week")
    
    def _draw_navigation_button(self, surface: pygame.Surface, rect: pygame.Rect,
                                symbol: str, tooltip: str):
        """Draw a navigation button."""
        # Check hover
        is_hovered = rect.collidepoint(pygame.mouse.get_pos()) if self._prev_button_rect else False
        color = self.COLOR_ACCENT_LIGHT if is_hovered else self.COLOR_ACCENT
        
        # Button background
        pygame.draw.rect(surface, color, rect, border_radius=5)
        pygame.draw.rect(surface, self.COLOR_BORDER, rect, 2, border_radius=5)
        
        # Button symbol
        if self._header_font:
            symbol_surf = self._header_font.render(symbol, True, (255, 255, 255))
            symbol_rect = symbol_surf.get_rect(center=rect.center)
            surface.blit(symbol_surf, symbol_rect)
    
    def _draw_content(self, surface: pygame.Surface):
        """Draw the main content area."""
        if not self._current_summary:
            return
        
        summary = self._current_summary
        
        # Metrics cards row
        self._draw_metrics_row(surface, summary)
        
        # Trend graph
        self._draw_trend_section(surface, summary)
        
        # Word lists
        self._draw_word_lists(surface, summary)
    
    def _draw_metrics_row(self, surface: pygame.Surface, summary: WeeklySummary):
        """Draw the row of key metrics."""
        card_y = 90
        card_height = 80
        card_width = (self.width - 40) // 3
        gap = 10
        
        metrics = [
            ("Words Mastered", str(summary.words_mastered), self._format_trend(summary.trend_mastered)),
            ("Accuracy", f"{summary.accuracy_rate:.0%}", self._format_trend(summary.trend_accuracy)),
            ("Time Practiced", f"{summary.total_time_minutes} min", None)
        ]
        
        for i, (label, value, trend) in enumerate(metrics):
            x = 20 + i * (card_width + gap)
            self._draw_metric_card(surface, x, card_y, card_width, card_height,
                                   label, value, trend)
    
    def _draw_metric_card(self, surface: pygame.Surface, x: int, y: int,
                          width: int, height: int, label: str, value: str,
                          trend: Optional[str]):
        """Draw a single metric card."""
        # Card background
        card_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, self.COLOR_CARD, card_rect, border_radius=8)
        pygame.draw.rect(surface, self.COLOR_BORDER, card_rect, 2, border_radius=8)
        
        # Label
        if self._small_font:
            label_surf = self._small_font.render(label, True, self.COLOR_TEXT_LIGHT)
            surface.blit(label_surf, (x + 10, y + 10))
        
        # Value
        if self._header_font:
            value_surf = self._header_font.render(value, True, self.COLOR_TEXT)
            surface.blit(value_surf, (x + 10, y + 30))
        
        # Trend indicator
        if trend and self._small_font:
            trend_color = self._get_trend_color(trend)
            trend_surf = self._small_font.render(trend, True, trend_color)
            surface.blit(trend_surf, (x + width - 40, y + 15))
    
    def _draw_trend_section(self, surface: pygame.Surface, summary: WeeklySummary):
        """Draw the trend graph section."""
        graph_y = 190
        
        # Section header
        if self._header_font:
            header = "Accuracy Trend (4 Weeks)"
            header_surf = self._header_font.render(header, True, self.COLOR_TEXT)
            surface.blit(header_surf, (20, graph_y))
        
        # Graph area
        graph_rect = pygame.Rect(20, graph_y + 25, self.width - 40, 180)
        pygame.draw.rect(surface, self.COLOR_CARD, graph_rect, border_radius=8)
        pygame.draw.rect(surface, self.COLOR_BORDER, graph_rect, 2, border_radius=8)
        
        # Render the trend graph
        graph_surface = pygame.Surface((graph_rect.width - 16, graph_rect.height - 16))
        self._trend_graph.draw(graph_surface, self._history, "accuracy_rate", "Accuracy %")
        surface.blit(graph_surface, (graph_rect.x + 8, graph_rect.y + 8))
    
    def _draw_word_lists(self, surface: pygame.Surface, summary: WeeklySummary):
        """Draw the word lists section."""
        list_y = 400
        
        # Section header
        if self._header_font:
            header = "Words Mastered This Week"
            header_surf = self._header_font.render(header, True, self.COLOR_TEXT)
            surface.blit(header_surf, (20, list_y))
        
        # Words mastered list
        words_y = list_y + 25
        if summary.words_mastered_list:
            for i, word in enumerate(summary.words_mastered_list[:5]):
                if self._body_font:
                    word_surf = self._body_font.render(f"• {word}", True, self.COLOR_ACCENT)
                    surface.blit(word_surf, (30, words_y + i * 22))
        else:
            if self._small_font:
                no_words = "No words mastered yet. Keep practicing!"
                no_words_surf = self._small_font.render(no_words, True, self.COLOR_TEXT_LIGHT)
                surface.blit(no_words_surf, (30, words_y))
        
        # Words needing practice section
        practice_y = list_y + 150
        if self._header_font:
            header = "Words Needing More Practice"
            header_surf = self._header_font.render(header, True, self.COLOR_TEXT)
            surface.blit(header_surf, (20, practice_y))
        
        # Words needing practice list
        practice_words_y = practice_y + 25
        if summary.words_needing_practice:
            for i, word in enumerate(summary.words_needing_practice[:5]):
                if self._body_font:
                    word_surf = self._body_font.render(f"• {word}", True, self.COLOR_WARNING)
                    surface.blit(word_surf, (30, practice_words_y + i * 22))
        else:
            if self._small_font:
                no_words = "Great job! No words need extra practice."
                no_words_surf = self._small_font.render(no_words, True, self.COLOR_ACCENT)
                surface.blit(no_words_surf, (30, practice_words_y))
    
    def _draw_empty_state(self, surface: pygame.Surface):
        """Draw empty state when no data is available."""
        if not self._header_font:
            return
        
        # Centered message
        message = "No practice data for this week"
        message_surf = self._header_font.render(message, True, self.COLOR_TEXT_LIGHT)
        message_rect = message_surf.get_rect(center=(self.width // 2, self.height // 2 - 20))
        surface.blit(message_surf, message_rect)
        
        if self._body_font:
            hint = "Have your child complete some practice sessions to see progress!"
            hint_surf = self._body_font.render(hint, True, self.COLOR_TEXT_LIGHT)
            hint_rect = hint_surf.get_rect(center=(self.width // 2, self.height // 2 + 10))
            surface.blit(hint_surf, hint_rect)
    
    def _format_trend(self, trend: Optional[Trend]) -> str:
        """Format trend as display string."""
        if trend is None:
            return "-"
        symbols = {
            "improving": "↑",
            "stable": "→",
            "declining": "↓"
        }
        return symbols.get(trend.value, "-")
    
    def _get_trend_color(self, trend: str) -> tuple:
        """Get color for trend string."""
        colors = {
            "improving": (76, 175, 80),      # Green
            "stable": (158, 158, 158),       # Gray
            "declining": (244, 67, 54)       # Red
        }
        return colors.get(trend, (158, 158, 158))
    
    def navigate_previous_week(self):
        """Navigate to the previous week."""
        self._current_date -= timedelta(weeks=1)
        self._load_data()
    
    def navigate_next_week(self):
        """Navigate to the next week."""
        self._current_date += timedelta(weeks=1)
        self._load_data()
    
    def handle_mouse_click(self, pos: tuple) -> bool:
        """
        Handle mouse click for navigation.
        
        Args:
            pos: Mouse position (x, y)
            
        Returns:
            True if a navigation button was clicked
        """
        if self._prev_button_rect and self._prev_button_rect.collidepoint(pos):
            self.navigate_previous_week()
            return True
        
        if self._next_button_rect and self._next_button_rect.collidepoint(pos):
            self.navigate_next_week()
            return True
        
        return False
    
    def get_current_summary(self) -> Optional[WeeklySummary]:
        """Get the current week's summary."""
        return self._current_summary
    
    def has_sufficient_data(self) -> bool:
        """Check if there's sufficient data for meaningful display."""
        if not self._current_summary:
            return False
        return self.generator.has_sufficient_data(self.student_id)


def create_weekly_summary_view(
    generator: WeeklySummaryGenerator,
    student_id: str,
    width: int = 700,
    height: int = 500
) -> WeeklySummaryView:
    """
    Factory function to create a WeeklySummaryView.
    
    Args:
        generator: WeeklySummaryGenerator for fetching data
        student_id: ID of the student
        width: View width in pixels
        height: View height in pixels
        
    Returns:
        Configured WeeklySummaryView instance
    """
    return WeeklySummaryView(generator, student_id, width, height)
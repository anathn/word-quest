"""
Progress Journal Screen

Displays encouraging, age-appropriate text summaries of student progress.
Part of STORY-007-03: Progress Journal
"""

import pygame
from typing import List, Optional
from datetime import datetime, timedelta
import sys

from src.utils.progress_summarizer import ProgressSummarizer, JournalEntry
from src.components.progress_tracker import ProgressTracker
from src.ui.theme import ThemeManager


class ProgressJournalScreen:
    """
    Screen displaying weekly progress journal entries.
    
    Features:
    - Page through weekly summaries
    - Encouraging, age-appropriate language
    - Shows mastered words and practice recommendations
    - Large, readable text (24pt+)
    - Space-themed background
    """
    
    def __init__(
        self,
        progress_tracker: ProgressTracker,
        theme: Optional[ThemeManager] = None
    ):
        """
        Initialize the progress journal screen.
        
        Args:
            progress_tracker: ProgressTracker with session data
            theme: Optional ThemeManager instance
        """
        self.progress_tracker = progress_tracker
        self.theme = theme or ThemeManager()
        
        # Summarizer for generating journal entries
        self.summarizer = ProgressSummarizer(progress_tracker)
        
        # Journal entries (last 4 weeks)
        self.entries: List[JournalEntry] = []
        self.current_entry_index = 0
        
        # Screen dimensions
        self.screen_width = 1024
        self.screen_height = 768
        
        # Typography settings
        self.title_font_size = 28
        self.body_font_size = 24
        self.title_color = (255, 255, 255)  # White
        self.body_color = (240, 240, 240)  # Off-white
        
        # Navigation
        self._generate_entries()
        
        # Navigation button positions
        self.left_arrow_rect = pygame.Rect(50, self.screen_height // 2 - 50, 80, 100)
        self.right_arrow_rect = pygame.Rect(self.screen_width - 130, self.screen_height // 2 - 50, 80, 100)
    
    def _generate_entries(self):
        """Generate journal entries for the last 4 weeks."""
        self.entries = []
        current = datetime.now()
        
        for i in range(4):  # Last 4 weeks
            week_end = current - timedelta(weeks=i)
            week_start = week_end - timedelta(days=6)
            
            entry = self.summarizer.generate_weekly_summary(week_start, week_end)
            self.entries.append(entry)
        
        # Set appropriate starting index (most recent week)
        self.current_entry_index = 0
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle input events for navigation.
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT or event.key == pygame.K_LEFT:
                self._navigate_weeks(event.key == pygame.K_RIGHT)
                return True
            elif event.key == pygame.K_ESCAPE:
                # Return to previous screen
                return True
            elif event.key == pygame.K_e:
                # Current week
                if len(self.entries) > 0:
                    self.current_entry_index = 0
                    return True
            elif event.key == pygame.K_1:
                if len(self.entries) > 1:
                    self.current_entry_index = 1
                    return True
            elif event.key == pygame.K_2:
                if len(self.entries) > 2:
                    self.current_entry_index = 2
                    return True
            elif event.key == pygame.K_3:
                if len(self.entries) > 3:
                    self.current_entry_index = 3
                    return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.left_arrow_rect.collidepoint(event.pos):
                    self._navigate_weeks(direction=False)
                    return True
                elif self.right_arrow_rect.collidepoint(event.pos):
                    self._navigate_weeks(direction=True)
                    return True
        
        return False
    
    def _navigate_weeks(self, direction: bool):
        """Navigate to next or previous week."""
        if direction:
            # Next week (lower index in list)
            if self.current_entry_index < len(self.entries) - 1:
                self.current_entry_index += 1
        else:
            # Previous week (higher index in list)
            if self.current_entry_index > 0:
                self.current_entry_index -= 1
    
    def render(self, screen: pygame.Surface):
        """
        Render the journal entry to the screen.
        
        Args:
            screen: Pygame surface to render to
        """
        # Draw space background
        self._render_background(screen)
        
        # Get current entry
        if not self.entries or self.current_entry_index >= len(self.entries):
            self._render_empty_state(screen)
            return
        
        entry = self.entries[self.current_entry_index]
        
        # Draw title/period
        self._render_period_header(screen, entry.period)
        
        # Draw summary lines
        self._render_summary_lines(screen, entry.lines)
        
        # Draw practice recommendation if exists
        if entry.needs_practice:
            self._render_practice_section(screen, entry.needs_practice)
        
        # Draw navigation controls
        self._render_navigation(screen)
        
        # Draw week indicator
        self._render_week_indicator(screen, self.current_entry_index + 1)
    
    def _render_background(self, screen:pygame.Surface):
        """Draw space-themed background."""
        # Deep space blue background
        background_color = (26, 26, 62)  # #1a1a3e
        screen.fill(background_color)
        
        # Optional: Add subtle stars (could be enhanced with star field)
        # For now, simple background is sufficient
    
    def _render_period_header(self, screen: pygame.Surface, period: str):
        """Render the period header."""
        font = pygame.font.Font(None, self.title_font_size)
        
        # Center the title
        text_surface = font.render(period, True, self.title_color)
        text_rect = text_surface.get_rect(center=(self.screen_width // 2, 50))
        screen.blit(text_surface, text_rect)
    
    def _render_summary_lines(self, screen: pygame.Surface, lines: List[str]):
        """Render the summary text lines."""
        font = pygame.font.Font(None, self.body_font_size)
        
        y = 120
        line_height = 35
        
        for line in lines:
            text_surface = font.render(line, True, self.body_color)
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, y))
            screen.blit(text_surface, text_rect)
            y += line_height
    
    def _render_practice_section(self, screen: pygame.Surface, practice_data: dict):
        """Render the practice recommendation section."""
        font_bold = pygame.font.Font(None, self.body_font_size)
        font_regular = pygame.font.Font(None, self.body_font_size - 2)
        
        y = 120
        
        # Count summary lines to find position
        y += len(self.entries[self.current_entry_index].lines) * 35
        y += 30  # Additional spacing
        
        # Draw "Words to Practice" header
        title_surface = font_bold.render(practice_data["title"], True, (255, 200, 100))  # Orange
        title_rect = title_surface.get_rect(center=(self.screen_width // 2, y))
        screen.blit(title_surface, title_rect)
        
        y += 40
        
        # Draw practice words
        text_surface = font_regular.render(practice_data["text"], True, self.body_color)
        text_rect = text_surface.get_rect(center=(self.screen_width // 2, y))
        screen.blit(text_surface, text_rect)
    
    def _render_navigation(self, screen: pygame.Surface):
        """Draw navigation arrows."""
        # Draw left arrow button
        pygame.draw.rect(screen, (100, 100, 150), self.left_arrow_rect, border_radius=10)
        arrow_font = pygame.font.Font(None, 48)
        left_text = arrow_font.render("◀", True, (255, 255, 255))
        left_rect = left_text.get_rect(center=self.left_arrow_rect.center)
        screen.blit(left_text, left_rect)
        
        # Draw right arrow button
        pygame.draw.rect(screen, (100, 100, 150), self.right_arrow_rect, border_radius=10)
        right_text = arrow_font.render("▶", True, (255, 255, 255))
        right_rect = right_text.get_rect(center=self.right_arrow_rect.center)
        screen.blit(right_text, right_rect)
    
    def _render_week_indicator(self, screen: pygame.Surface, week_number: int):
        """Draw week indicator badge."""
        font = pygame.font.Font(None, 20)
        
        text = f"Week {week_number} of Your Journey"
        text_surface = font.render(text, True, (255, 255, 255), (0, 0, 100))  # White on dark blue
        
        # Draw rounded rectangle badge
        badge_rect = text_surface.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
        pygame.draw.rect(screen, (0, 0, 100), badge_rect, border_radius=15)
        screen.blit(text_surface, badge_rect)
    
    def _render_empty_state(self, screen: pygame.Surface):
        """Render empty state for new students."""
        font = pygame.font.Font(None, self.body_font_size)
        
        welcome_messages = self.summarizer.generate_welcome_message()
        y = 200
        
        for message in welcome_messages:
            text_surface = font.render(message, True, self.body_color)
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, y))
            screen.blit(text_surface, text_rect)
            y += 40
    
    def get_current_entry(self) -> Optional[JournalEntry]:
        """Get the currently displayed journal entry."""
        if self.entries and self.current_entry_index < len(self.entries):
            return self.entries[self.current_entry_index]
        return None
    
    def refresh_entries(self):
        """Regenerate entries (e.g., after new progress data)."""
        self._generate_entries()
        self.current_entry_index = 0


def create_progress_journal_screen(progress_tracker: ProgressTracker):
    """
    Factory function to create a ProgressJournalScreen.
    
    Args:
        progress_tracker: ProgressTracker instance
        
    Returns:
        ProgressJournalScreen instance
    """
    return ProgressJournalScreen(progress_tracker)
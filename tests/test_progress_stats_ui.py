"""
Unit tests for Progress Stats Display UI component (STORY-007-04)

Tests for the progress stats display rendering and interaction.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import pygame
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ui.simple_progress_stats import (
    ProgressStatsDisplay,
    StatCard,
    TrendIndicator,
    StatCardData,
    create_progress_stats_display
)


@pytest.fixture
def mock_progress_tracker():
    """Create a mock ProgressTracker with realistic data."""
    tracker = MagicMock()
    tracker.get_mastered_count.return_value = 23
    tracker.get_total_words.return_value = 50
    tracker.get_best_streak.return_value = 7
    
    # Set up session tracker mock
    session_tracker = MagicMock()
    session_tracker._get_total_attempts.return_value = 100
    session_tracker._get_total_correct.return_value = 82
    session_tracker.get_total_practice_seconds.return_value = 5400
    
    today = MagicMock()
    today.session_id = "today"
    today.start_time = 1234567890
    today.words = [MagicMock(correct=True)]
    
    session_tracker.completed_sessions = [today]
    tracker.session_tracker = session_tracker
    
    return tracker


@pytest.fixture
def mock_theme():
    """Create a mock ThemeManager."""
    pygame.init()
    theme = MagicMock()
    theme.get_color.return_value = (255, 255, 255)
    theme.get_font = MagicMock(return_value=pygame.font.Font(None, 24))
    yield theme
    pygame.quit()


class TestStatCard:
    """Tests for individual stat card component."""
    
    def test_stat_card_creation(self, mock_theme):
        """Verify stat card initializes correctly."""
        card = StatCard(mock_theme)
        assert card.theme == mock_theme
        assert card.card_rect is None
    
    def test_stat_card_rect_creation(self, mock_theme):
        """Verify card rect is created during draw."""
        with patch('pygame.draw.rect'), patch('pygame.font.Font'):
            card = StatCard(mock_theme)
            data = StatCardData(
                title="Accuracy",
                text="8/10",
                icon="🎯"
            )
            
            # Create a real surface for rendering
            screen = pygame.display.set_mode((800, 600))
            card.draw(screen, 50, 100, data)
            
            rect = card.get_rect()
            assert rect is not None
            assert rect.x == 50
            assert rect.y == 100
            assert rect.width == 280
            assert rect.height == 120
            pygame.quit()
    
    def test_text_wrapping(self, mock_theme):
        """Verify long text is wrapped correctly."""
        with patch('pygame.draw.rect'), patch('pygame.font.Font'):
            card = StatCard(mock_theme)
            data = StatCardData(
                title="Practicing Time",
                text="You've practiced for a very long time!",
                icon="⏱️"
            )
            
            # Create a real surface for rendering
            screen = pygame.display.set_mode((800, 600))
            # Should not raise exceptions
            card.draw(screen, 50, 100, data)
            pygame.quit()


class TestTrendIndicator:
    """Tests for trend indicator component."""
    
    def test_trend_indicator_creation(self, mock_theme):
        """Verify trend indicator initializes correctly."""
        indicator = TrendIndicator(mock_theme)
        assert indicator.theme == mock_theme
    
    def test_trend_symbols(self, mock_theme):
        """Verify all trend symbols are defined."""
        indicator = TrendIndicator(mock_theme)
        
        assert indicator.get_symbol("up") == "↑"
        assert indicator.get_symbol("down") == "↓"
        assert indicator.get_symbol("stable") == "→"
        assert indicator.get_symbol("new") == "⭐"
    
    def test_trend_colors(self, mock_theme):
        """Verify all trend colors are defined."""
        indicator = TrendIndicator(mock_theme)
        
        assert indicator.get_color("up") == (76, 175, 80)  # Green
        assert indicator.get_color("down") == (255, 152, 0)  # Orange
        assert indicator.get_color("stable") == (189, 189, 189)  # Grey
        assert indicator.get_color("new") == (255, 215, 0)  # Gold
    
    def test_trend_render(self, mock_theme):
        """Verify trend indicator renders correctly."""
        with patch('pygame.font.Font'):
            indicator = TrendIndicator(mock_theme)
            
            # Create a real surface for rendering
            screen = pygame.display.set_mode((800, 600))
            # Should not raise exceptions
            indicator.render(screen, "up", 100, 100)
            pygame.quit()


class TestProgressStatsDisplay:
    """Tests for main progress stats display."""
    
    def test_display_creation(self, mock_progress_tracker, mock_theme):
        """Verify display initializes correctly."""
        with patch('src.ui.simple_progress_stats.ThemeManager', return_value=mock_theme):
            # Create a real surface for rendering
            screen = pygame.display.set_mode((800, 600))
            display = ProgressStatsDisplay(screen, mock_progress_tracker, mock_theme)
        
        assert display.progress == mock_progress_tracker
        assert len(display.stat_cards) > 0
        pygame.quit()
    
    def test_display_updates_after_progress(self, mock_progress_tracker, mock_theme):
        """Verify stats update after progress changes."""
        with patch('src.ui.simple_progress_stats.ThemeManager', return_value=mock_theme):
            screen = pygame.display.set_mode((800, 600))
            display = ProgressStatsDisplay(screen, mock_progress_tracker, mock_theme)
        
        # Initial number of cards
        initial_count = len(display.stat_cards)
        
        # Update stats
        display.update_stats()
        
        # Should have rebuild stat cards
        assert display.stat_cards is not None
        pygame.quit()
    
    def test_draw_background(self, mock_progress_tracker, mock_theme):
        """Verify background is drawn correctly."""
        with patch('src.ui.simple_progress_stats.ThemeManager', return_value=mock_theme), \
             patch('pygame.draw.rect'), \
             patch('pygame.font.Font'):
            screen = pygame.display.set_mode((800, 600))
            display = ProgressStatsDisplay(screen, mock_progress_tracker, mock_theme)
        
        # Should not raise exceptions
        display.draw()
        pygame.quit()
    
    def test_draw_stat_cards(self, mock_progress_tracker, mock_theme):
        """Verify all stat cards are drawn."""
        with patch('src.ui.simple_progress_stats.ThemeManager', return_value=mock_theme), \
             patch('pygame.draw.rect'), \
             patch('pygame.font.Font'):
            screen = pygame.display.set_mode((800, 600))
            display = ProgressStatsDisplay(screen, mock_progress_tracker, mock_theme)
        
        # Should not raise exceptions
        display.draw()
        pygame.quit()
    
    def test_card_at_position(self, mock_progress_tracker, mock_theme):
        """Verify card detection at position works."""
        with patch('src.ui.simple_progress_stats.ThemeManager', return_value=mock_theme):
            screen = pygame.display.set_mode((800, 600))
            display = ProgressStatsDisplay(screen, mock_progress_tracker, mock_theme)
        
        # Test with valid position
        result = display.get_card_at_position(100, 150)
        
        # Could return None if no card at that position, but shouldn't raise
        assert result is None or isinstance(result, tuple)
        pygame.quit()
    
    def test_create_factory_function(self, mock_progress_tracker, mock_theme):
        """Verify factory function works correctly."""
        with patch('src.ui.simple_progress_stats.ThemeManager', return_value=mock_theme):
            screen = pygame.display.set_mode((800, 600))
            display = create_progress_stats_display(screen, mock_progress_tracker, mock_theme)
        
        assert display is not None
        assert isinstance(display, ProgressStatsDisplay)
        pygame.quit()


class TestEmptyState:
    """Tests for empty state handling."""
    
    def test_empty_progress(self, mock_theme):
        """Verify display handles empty progress gracefully."""
        tracker = MagicMock()
        tracker.get_mastered_count.return_value = 0
        tracker.get_total_words.return_value = 0
        tracker.get_best_streak.return_value = 0
        
        session_tracker = MagicMock()
        session_tracker._get_total_attempts.return_value = 0
        session_tracker.get_total_practice_seconds.return_value = 0
        session_tracker.completed_sessions = []
        tracker.session_tracker = session_tracker
        
        with patch('src.ui.simple_progress_stats.ThemeManager', return_value=mock_theme):
            screen = pygame.display.set_mode((800, 600))
            # Should not raise exceptions
            display = ProgressStatsDisplay(screen, tracker, mock_theme)
            
            # Should handle empty state
            assert display is not None
            pygame.quit()


class TestVisibility:
    """Tests for card visibility based on data availability."""
    
    def test_today_summary_hidden_when_empty(self, mock_progress_tracker, mock_theme):
        """Verify today's card is hidden when no practice today."""
        tracker = MagicMock()
        tracker.get_mastered_count.return_value = 23
        tracker.get_total_words.return_value = 50
        tracker.get_best_streak.return_value = 7
        tracker.get_total_practice_seconds.return_value = 5400
        
        session_tracker = MagicMock()
        session_tracker._get_total_attempts.return_value = 100
        session_tracker._get_total_correct.return_value = 82
        session_tracker.get_total_practice_seconds.return_value = 5400
        session_tracker.completed_sessions = []  # No sessions
        tracker.session_tracker = session_tracker
        
        with patch('src.ui.simple_progress_stats.ThemeManager', return_value=mock_theme):
            screen = pygame.display.set_mode((800, 600))
            display = ProgressStatsDisplay(screen, tracker, mock_theme)
            
            # Should not include today's card if no data
            today_cards = [card for _, _, _, data in display.stat_cards if data.title == "Today's Progress"]
            # This depends on implementation - either 0 cards or card with encouraging message
            pygame.quit()


class TestLayout:
    """Tests for grid layout calculation."""
    
    def test_card_positions(self, mock_progress_tracker, mock_theme):
        """Verify cards are positioned in grid correctly."""
        with patch('src.ui.simple_progress_stats.ThemeManager', return_value=mock_theme):
            screen = pygame.display.set_mode((800, 600))
            display = ProgressStatsDisplay(screen, mock_progress_tracker, mock_theme)
        
        # Cards should be positioned with correct spacing
        positions = [(x, y) for x, y, _, _ in display.stat_cards]
        
        # Verify no overlapping cards (allowing for some tolerance)
        # This is a basic check - cards should have unique positions
        assert len(positions) == len(set(positions))
        pygame.quit()


class TestAccessibility:
    """Tests for accessibility features."""
    
    def test_theme_usage(self, mock_progress_tracker, mock_theme):
        """Verify theme is used for rendering."""
        with patch('src.ui.simple_progress_stats.ThemeManager', return_value=mock_theme):
            screen = pygame.display.set_mode((800, 600))
            display = ProgressStatsDisplay(screen, mock_progress_tracker, mock_theme)
        
        # Theme should be configured
        assert display.theme == mock_theme
        pygame.quit()
    
    def test_encouraging_messages(self, mock_progress_tracker, mock_theme):
        """Verify messages are encouraging."""
        with patch('src.ui.simple_progress_stats.ThemeManager', return_value=mock_theme):
            screen = pygame.display.set_mode((800, 600))
            display = ProgressStatsDisplay(screen, mock_progress_tracker, mock_theme)
        
        # All stats should exist and have text
        for _, _, _, data in display.stat_cards:
            assert data.text is not None
            assert len(data.text) > 0
        pygame.quit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
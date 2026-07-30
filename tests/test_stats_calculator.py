"""
Unit tests for StatsCalculator (STORY-007-04)

Tests for the statistics calculation and formatting logic
used in the Simple Progress Stats display.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.stats_calculator import StatsCalculator


@pytest.fixture
def mock_progress_tracker():
    """Create a mock ProgressTracker with realistic data."""
    tracker = MagicMock()
    
    # Set up basic stats
    tracker.get_mastered_count.return_value = 23
    tracker.get_total_words.return_value = 50
    tracker.get_best_streak.return_value = 7
    
    # Set up session tracker mock
    session_tracker = MagicMock()
    
    # Mock total attempts and correct
    session_tracker._get_total_attempts.return_value = 100
    session_tracker._get_total_correct.return_value = 82
    session_tracker.get_total_practice_seconds.return_value = 5400  # 1.5 hours
    
    # Create mock completed sessions
    now = datetime.now()
    session1 = MagicMock()
    session1.session_id = "session_1"
    session1.start_time = (now - timedelta(days=1)).timestamp()
    session1.overall_accuracy = 0.85
    session1.words = [MagicMock(correct=True), MagicMock(correct=True), MagicMock(correct=False)]
    
    session2 = MagicMock()
    session2.session_id = "session_2"
    session2.start_time = (now - timedelta(days=2)).timestamp()
    session2.overall_accuracy = 0.75
    session2.words = [MagicMock(correct=True), MagicMock(correct=False), MagicMock(correct=False)]
    
    session_tracker.completed_sessions = [session1, session2]
    
    tracker.session_tracker = session_tracker
    
    return tracker


@pytest.fixture
def stats_calculator(mock_progress_tracker):
    """Create a StatsCalculator instance with mock data."""
    return StatsCalculator(mock_progress_tracker)


class TestWordsMastered:
    """Tests for words mastered calculation."""
    
    def test_get_words_mastered(self, stats_calculator, mock_progress_tracker):
        """Verify words mastered count matches progress data."""
        result = stats_calculator.get_words_mastered()
        assert result == 23
        mock_progress_tracker.get_mastered_count.assert_called_once()
    
    def test_get_total_words(self, stats_calculator, mock_progress_tracker):
        """Verify total words matches curriculum size."""
        result = stats_calculator.get_total_words()
        assert result == 50
        mock_progress_tracker.get_total_words.assert_called_once()
    
    def test_get_words_mastered_display(self, stats_calculator):
        """Verify words mastered display format."""
        result = stats_calculator.get_words_mastered_display()
        
        assert result["text"] == "23/50 words"
        assert result["mastered"] == 23
        assert result["total"] == 50
        assert result["icon"] == "⭐"


class TestAccuracy:
    """Tests for accuracy calculation and formatting."""
    
    def test_accuracy_format(self, stats_calculator):
        """Verify friendly format (X out of Y)."""
        result = stats_calculator.get_accuracy_display()
        
        assert "text" in result
        assert "8 out of 10" in result["text"]
        assert result["icon"] == "🎯"
        assert result["ratio"]["numerator"] == 8
        assert result["ratio"]["denominator"] == 10
    
    def test_accuracy_empty_state(self, stats_calculator, mock_progress_tracker):
        """Verify encouraging message when no attempts."""
        mock_progress_tracker.session_tracker._get_total_attempts.return_value = 0
        
        result = stats_calculator.get_accuracy_display()
        
        assert result["text"] == "Keep practicing!"
        assert result["ratio"]["numerator"] == 0
        assert result["trend"] == "new"
    
    def test_accuracy_high_encouragement(self, stats_calculator, mock_progress_tracker):
        """Verify extra encouragement for high accuracy."""
        mock_progress_tracker.session_tracker._get_total_attempts.return_value = 100
        mock_progress_tracker.session_tracker._get_total_correct.return_value = 95
        
        result = stats_calculator.get_accuracy_display()
        
        assert "Great job!" in result["text"]
    
    def test_accuracy_low_encouragement(self, stats_calculator, mock_progress_tracker):
        """Verify encouraging message for low accuracy."""
        mock_progress_tracker.session_tracker._get_total_attempts.return_value = 100
        mock_progress_tracker.session_tracker._get_total_correct.return_value = 30
        
        result = stats_calculator.get_accuracy_display()
        
        assert "keep practicing!" in result["text"]


class TestBestStreak:
    """Tests for best streak display."""
    
    def test_streak_calculation(self, stats_calculator):
        """Verify best streak is correctly retrieved."""
        result = stats_calculator.get_best_streak_display()
        
        assert result["value"] == 7
        assert result["icon"] == "🔥"
        assert "7 correct" in result["text"]
    
    def test_best_streak_emoji(self, stats_calculator):
        """Verify fire emoji is used."""
        result = stats_calculator.get_best_streak_display()
        assert result["icon"] == "🔥"
    
    def test_zero_streak(self, stats_calculator, mock_progress_tracker):
        """Verify message when no streak yet."""
        mock_progress_tracker.get_best_streak.return_value = 0
        
        result = stats_calculator.get_best_streak_display()
        
        assert result["value"] == 0
        assert result["text"] == "Start a streak!"
    
    def test_high_streak_achievement(self, stats_calculator, mock_progress_tracker):
        """Verify extra praise for high streaks."""
        mock_progress_tracker.get_best_streak.return_value = 15
        
        result = stats_calculator.get_best_streak_display()
        
        assert "Amazing!" in result["text"]


class TestPracticeTime:
    """Tests for practice time formatting."""
    
    def test_time_format_minutes(self, stats_calculator, mock_progress_tracker):
        """Verify time displays correctly for minutes."""
        mock_progress_tracker.session_tracker.get_total_practice_seconds.return_value = 2700  # 45 min
        
        result = stats_calculator.get_total_practice_time()
        
        assert "45 minutes" in result["text"]
        assert result["seconds"] == 2700
    
    def test_time_format_hours(self, stats_calculator, mock_progress_tracker):
        """Verify time displays correctly for hours."""
        mock_progress_tracker.session_tracker.get_total_practice_seconds.return_value = 7200  # 2 hours
        
        result = stats_calculator.get_total_practice_time()
        
        assert "2 hours" in result["text"]
    
    def test_time_format_hours_and_minutes(self, stats_calculator):
        """Verify time displays correctly for hours and minutes."""
        # Mock with 1 hour 30 minutes
        self.stats_calculator = stats_calculator
        with patch.object(stats_calculator.progress.session_tracker, 'get_total_practice_seconds', return_value=5400):
            result = stats_calculator.get_total_practice_time()
            
            assert "1 hour and 30 minutes" in result["text"]
    
    def test_time_just_getting_started(self, stats_calculator, mock_progress_tracker):
        """Verify message for very little practice."""
        mock_progress_tracker.session_tracker.get_total_practice_seconds.return_value = 120  # 2 minutes
        
        result = stats_calculator.get_total_practice_time()
        
        assert result["text"] == "Just getting started!"


class TestTodaySummary:
    """Tests for today's practice summary."""
    
    def test_today_summary_with_practice(self, stats_calculator, mock_progress_tracker):
        """Verify today's summary displays correctly."""
        today = datetime.now().date()
        
        # Create a mock session for today
        session = MagicMock()
        session.start_time = datetime.now().timestamp()
        session.words = [
            MagicMock(correct=True),
            MagicMock(correct=True),
            MagicMock(correct=False)
        ]
        
        mock_progress_tracker.session_tracker.completed_sessions = [session]
        
        result = stats_calculator.get_today_summary()
        
        assert result is not None
        assert result["words"] == 3
        assert result["correct"] == 2
        assert result["icon"] == "📅"
        assert "3 words, 2 correct" in result["text"]
    
    def test_today_summary_no_practice(self, stats_calculator, mock_progress_tracker):
        """Verify none returned when no practice today."""
        mock_progress_tracker.session_tracker.completed_sessions = []
        
        result = stats_calculator.get_today_summary()
        
        assert result is None
    
    def test_today_summary_encouraging_format(self, stats_calculator, mock_progress_tracker):
        """Verify encouraging format (no highlighting failures)."""
        today = datetime.now().date()
        
        # Create a mock session for today with no correct answers
        session = MagicMock()
        session.start_time = datetime.now().timestamp()
        session.words = [
            MagicMock(correct=False),
            MagicMock(correct=False)
        ]
        
        mock_progress_tracker.session_tracker.completed_sessions = [session]
        
        result = stats_calculator.get_today_summary()
        
        # Should still mention words attempted, but not highlight failures
        assert result is not None
        assert "words" in result["text"]


class TestAccuracyTrend:
    """Tests for accuracy trend calculation."""
    
    def test_trend_calculation_improving(self, stats_calculator, mock_progress_tracker):
        """Verify improving trend is detected."""
        # Recent week: 85%, Previous week: 70% (15% improvement)
        mock_progress_tracker.session_tracker.completed_sessions = [
            MagicMock(start_time=(datetime.now() - timedelta(days=3)).timestamp(), overall_accuracy=0.85),
            MagicMock(start_time=(datetime.now() - timedelta(days=8)).timestamp(), overall_accuracy=0.70),
        ]
        
        result = stats_calculator.calculate_accuracy_trend()
        
        assert result == "up"
    
    def test_trend_calculation_stable(self, stats_calculator, mock_progress_tracker):
        """Verify stable trend is detected."""
        # Both weeks have similar accuracy (within 5%)
        mock_progress_tracker.session_tracker.completed_sessions = [
            MagicMock(start_time=(datetime.now() - timedelta(days=3)).timestamp(), overall_accuracy=0.80),
            MagicMock(start_time=(datetime.now() - timedelta(days=8)).timestamp(), overall_accuracy=0.78),
        ]
        
        result = stats_calculator.calculate_accuracy_trend()
        
        assert result == "stable"
    
    def test_trend_calculation_declining(self, stats_calculator, mock_progress_tracker):
        """Verify declining trend is detected."""
        # Recent week: 65%, Previous week: 85% (20% decline)
        mock_progress_tracker.session_tracker.completed_sessions = [
            MagicMock(start_time=(datetime.now() - timedelta(days=3)).timestamp(), overall_accuracy=0.65),
            MagicMock(start_time=(datetime.now() - timedelta(days=8)).timestamp(), overall_accuracy=0.85),
        ]
        
        result = stats_calculator.calculate_accuracy_trend()
        
        assert result == "down"
    
    def test_trend_new_student(self, stats_calculator, mock_progress_tracker):
        """Verify 'new' for students with only one week of data."""
        mock_progress_tracker.session_tracker.completed_sessions = [
            MagicMock(start_time=(datetime.now() - timedelta(days=3)).timestamp(), overall_accuracy=0.80),
        ]
        
        result = stats_calculator.calculate_accuracy_trend()
        
        assert result == "new"


class TestAllStats:
    """Tests for combined stats retrieval."""
    
    def test_all_stats_consistency(self, stats_calculator):
        """Verify all stats return data from same source."""
        all_stats = stats_calculator.get_all_stats()
        
        assert "words_mastered" in all_stats
        assert "accuracy" in all_stats
        assert "best_streak" in all_stats
        assert "practice_time" in all_stats
        assert "today" in all_stats
        
        # Verify structure of each stat
        assert "text" in all_stats["words_mastered"]
        assert "icon" in all_stats["words_mastered"]
        
        assert "text" in all_stats["accuracy"]
        assert "trend" in all_stats["accuracy"]
        
        assert "text" in all_stats["best_streak"]
        assert "value" in all_stats["best_streak"]


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_data_handling(self, stats_calculator, mock_progress_tracker):
        """Verify graceful handling of empty data."""
        mock_progress_tracker.get_mastered_count.return_value = 0
        mock_progress_tracker.get_total_words.return_value = 0
        mock_progress_tracker.session_tracker._get_total_attempts.return_value = 0
        mock_progress_tracker.get_best_streak.return_value = 0
        
        all_stats = stats_calculator.get_all_stats()
        
        # Should not raise exceptions
        assert all_stats["words_mastered"]["text"] == "0/0 words"
        assert all_stats["accuracy"]["text"] == "Keep practicing!"
        assert all_stats["best_streak"]["text"] == "Start a streak!"
    
    def test_exception_handling_in_trend(self, stats_calculator, mock_progress_tracker):
        """Verify trend returns 'new' on errors."""
        # Make the accuracy calculation raise an exception
        mock_progress_tracker.session_tracker.completed_sessions = None
        
        result = stats_calculator.calculate_accuracy_trend()
        
        assert result == "new"  # Should gracefully return 'new'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
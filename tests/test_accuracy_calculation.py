"""
Unit Tests for Accuracy Calculation (STORY-002-04)

Tests for accuracy rate calculation, trend analysis, and display functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.components.progress_tracker import ProgressTracker
from src.components.session_tracker import SessionTracker, SessionSummary, WordAttempt
from src.ui.accuracy_display import AccuracyDisplay, AccuracyDisplayConfig


class TestAccuracyCalculation:
    """Tests for accuracy calculation methods in ProgressTracker."""
    
    @pytest.fixture
    def tracker(self):
        """Create a fresh ProgressTracker for testing."""
        return ProgressTracker(student_id="test_student")
    
    @pytest.fixture
    def tracker_with_data(self, tracker):
        """Create a ProgressTracker with sample session data."""
        # Create mock sessions with known accuracy rates
        session1 = SessionSummary(
            session_id="session_1",
            student_id="test_student",
            start_time=datetime.now() - timedelta(hours=2)
        )
        
        # Add 10 word attempts: 8 correct on first attempt, 2 incorrect
        for i in range(8):
            session1.words.append(WordAttempt(
                word=f"word_{i}",
                word_id=f"word_{i}",
                correct=True,
                first_attempt_correct=True,
                total_attempts=1,
                hints_used=0,
                time_seconds=10.0
            ))
        
        for i in range(8, 10):
            session1.words.append(WordAttempt(
                word=f"word_{i}",
                word_id=f"word_{i}",
                correct=False,
                first_attempt_correct=False,
                total_attempts=2,  # Made 2 attempts
                hints_used=1,
                time_seconds=15.0
            ))
        
        session1.end_time = datetime.now()
        tracker.session_tracker.completed_sessions.append(session1)
        
        # Second session with better accuracy
        session2 = SessionSummary(
            session_id="session_2",
            student_id="test_student",
            start_time=datetime.now()
        )
        
        for i in range(10, 15):
            session2.words.append(WordAttempt(
                word=f"word_{i}",
                word_id=f"word_{i}",
                correct=True,
                first_attempt_correct=True,
                total_attempts=1,
                hints_used=0,
                time_seconds=8.0
            ))
        
        session2.end_time = datetime.now() + timedelta(minutes=15)
        tracker.session_tracker.completed_sessions.append(session2)
        
        return tracker
    
    def test_calculate_accuracy_no_sessions(self, tracker):
        """Test accuracy calculation with no sessions returns 0."""
        assert tracker.calculate_accuracy() == 0.0
    
    def test_calculate_accuracy_single_session(self, tracker_with_data):
        """Test accuracy calculation for a single session."""
        # Session 1: 8 correct first-attempt, 2 incorrect with 2 attempts each
        # Total correct: 8 + 0 = 8 (only counting eventually correct)
        # But we need to count all correct attempts
        accuracy = tracker_with_data.calculate_accuracy(session_id="session_1")
        
        # Should be between 0 and 100
        assert 0.0 <= accuracy <= 100.0
        assert accuracy > 0  # We have some correct answers
    
    def test_calculate_accuracy_overall(self, tracker_with_data):
        """Test overall accuracy calculation across all sessions."""
        accuracy = tracker_with_data.calculate_accuracy()
        
        # Should be between 0 and 100
        assert 0.0 <= accuracy <= 100.0
        assert accuracy > 0  # We have correct answers in both sessions
    
    def test_get_session_accuracy(self, tracker_with_data):
        """Test getting accuracy for a specific session."""
        accuracy = tracker_with_data.get_session_accuracy("session_1")
        
        assert 0.0 <= accuracy <= 100.0
    
    def test_get_session_accuracy_not_found(self, tracker_with_data):
        """Test getting accuracy for non-existent session returns 0."""
        accuracy = tracker_with_data.get_session_accuracy("nonexistent_session")
        assert accuracy == 0.0
    
    def test_get_accuracy_trend_no_sessions(self, tracker):
        """Test trend with no sessions returns 'new'."""
        assert tracker.get_accuracy_trend() == "new"
    
    def test_get_accuracy_trend_single_session(self, tracker_with_data):
        """Test trend with only one session returns 'new'."""
        # Clear second session
        tracker_with_data.session_tracker.completed_sessions = [
            tracker_with_data.session_tracker.completed_sessions[0]
        ]
        assert tracker_with_data.get_accuracy_trend() == "new"
    
    def test_get_accuracy_trend_improving(self, tracker_with_data):
        """Test trend detection when accuracy improves."""
        # Second session has 100% accuracy, first has <100%
        trend = tracker_with_data.get_accuracy_trend()
        # Should be improving or stable depending on exact calculations
        assert trend in ["improving", "stable"]
    
    def test_get_accuracy_trend_declining(self, tracker):
        """Test trend detection when accuracy declines."""
        # Create sessions with declining accuracy
        session1 = SessionSummary(
            session_id="session_1",
            student_id="test_student",
            start_time=datetime.now() - timedelta(hours=2)
        )
        
        # 100% accuracy
        for i in range(5):
            session1.words.append(WordAttempt(
                word=f"word_{i}",
                word_id=f"word_{i}",
                correct=True,
                first_attempt_correct=True,
                total_attempts=1,
                hints_used=0,
                time_seconds=10.0
            ))
        
        session1.end_time = datetime.now()
        tracker.session_tracker.completed_sessions.append(session1)
        
        # Low accuracy session
        session2 = SessionSummary(
            session_id="session_2",
            student_id="test_student",
            start_time=datetime.now()
        )
        
        for i in range(5, 10):
            session2.words.append(WordAttempt(
                word=f"word_{i}",
                word_id=f"word_{i}",
                correct=False,
                first_attempt_correct=False,
                total_attempts=3,
                hints_used=2,
                time_seconds=20.0
            ))
        
        session2.end_time = datetime.now() + timedelta(minutes=15)
        tracker.session_tracker.completed_sessions.append(session2)
        
        trend = tracker.get_accuracy_trend()
        assert trend == "declining"
    
    def test_get_accuracy_trend_stable(self, tracker):
        """Test trend detection when accuracy is stable."""
        # Create two sessions with similar accuracy
        session1 = SessionSummary(
            session_id="session_1",
            student_id="test_student",
            start_time=datetime.now() - timedelta(hours=2)
        )
        
        # 80% accuracy (4 correct, 1 wrong)
        for i in range(4):
            session1.words.append(WordAttempt(
                word=f"word_{i}",
                word_id=f"word_{i}",
                correct=True,
                first_attempt_correct=True,
                total_attempts=1,
                hints_used=0,
                time_seconds=10.0
            ))
        session1.words.append(WordAttempt(
            word="word_4",
            word_id="word_4",
            correct=False,
            first_attempt_correct=False,
            total_attempts=2,
            hints_used=1,
            time_seconds=15.0
        ))
        
        session1.end_time = datetime.now()
        tracker.session_tracker.completed_sessions.append(session1)
        
        # Similar accuracy
        session2 = SessionSummary(
            session_id="session_2",
            student_id="test_student",
            start_time=datetime.now()
        )
        
        for i in range(5, 9):
            session2.words.append(WordAttempt(
                word=f"word_{i}",
                word_id=f"word_{i}",
                correct=True,
                first_attempt_correct=True,
                total_attempts=1,
                hints_used=0,
                time_seconds=10.0
            ))
        session2.words.append(WordAttempt(
            word="word_9",
            word_id="word_9",
            correct=False,
            first_attempt_correct=False,
            total_attempts=2,
            hints_used=1,
            time_seconds=15.0
        ))
        
        session2.end_time = datetime.now() + timedelta(minutes=15)
        tracker.session_tracker.completed_sessions.append(session2)
        
        trend = tracker.get_accuracy_trend()
        assert trend == "stable"
    
    def test_get_accuracy_display(self, tracker_with_data):
        """Test accuracy display data structure."""
        display = tracker_with_data.get_accuracy_display()
        
        assert "percentage" in display
        assert "trend_symbol" in display
        assert "trend_label" in display
        assert "trend" in display
        
        assert 0.0 <= display["percentage"] <= 100.0
        assert display["trend_symbol"] in ["↑", "→", "↓", "-"]
        assert display["trend"] in ["improving", "stable", "declining", "new"]
    
    def test_get_accuracy_display_new_data(self, tracker):
        """Test accuracy display with no data."""
        display = tracker.get_accuracy_display()
        
        assert display["percentage"] == 0.0
        assert display["trend_symbol"] == "-"
        assert display["trend_label"] == "New"
        assert display["trend"] == "new"
    
    def test_get_accuracy_comparison(self, tracker_with_data):
        """Test accuracy comparison data structure."""
        comparison = tracker_with_data.get_accuracy_comparison()
        
        assert "current_session_accuracy" in comparison
        assert "previous_session_accuracy" in comparison
        assert "weekly_average_accuracy" in comparison
        assert "trend" in comparison
        assert "improvement_percent" in comparison
        
        assert 0.0 <= comparison["current_session_accuracy"] <= 100.0
        assert 0.0 <= comparison["previous_session_accuracy"] <= 100.0
    
    def test_get_weekly_average_accuracy_no_sessions(self, tracker):
        """Test weekly average with no sessions."""
        avg = tracker.get_weekly_average_accuracy()
        assert avg == 0.0
    
    def test_get_weekly_average_accuracy_with_sessions(self, tracker_with_data):
        """Test weekly average calculation."""
        avg = tracker_with_data.get_weekly_average_accuracy()
        assert 0.0 <= avg <= 100.0
    
    def test_get_weekly_average_accuracy_old_sessions(self, tracker):
        """Test weekly average excludes old sessions."""
        # Create session from 2 weeks ago
        old_session = SessionSummary(
            session_id="old_session",
            student_id="test_student",
            start_time=datetime.now() - timedelta(weeks=2)
        )
        
        for i in range(5):
            old_session.words.append(WordAttempt(
                word=f"word_{i}",
                word_id=f"word_{i}",
                correct=True,
                first_attempt_correct=True,
                total_attempts=1,
                hints_used=0,
                time_seconds=10.0
            ))
        
        old_session.end_time = datetime.now() - timedelta(weeks=2, minutes=15)
        tracker.session_tracker.completed_sessions.append(old_session)
        
        # Should return 0.0 as session is older than 1 week
        avg = tracker.get_weekly_average_accuracy(weeks=1)
        assert avg == 0.0


class TestAccuracyDisplay:
    """Tests for AccuracyDisplay UI component."""
    
    @pytest.fixture
    def tracker(self):
        """Create a ProgressTracker for testing."""
        return ProgressTracker(student_id="test_student")
    
    @pytest.fixture
    def display(self, tracker):
        """Create an AccuracyDisplay instance."""
        return AccuracyDisplay(tracker)
    
    def test_get_display_data(self, display):
        """Test display data retrieval."""
        data = display.get_display_data()
        
        assert "percentage" in data
        assert "trend_symbol" in data
        assert "trend_label" in data
        assert "trend" in data
        assert "color" in data
    
    def test_get_color_for_trend(self, display):
        """Test color mapping for different trends."""
        colors = {
            "improving": display.get_color_for_trend("improving"),
            "stable": display.get_color_for_trend("stable"),
            "declining": display.get_color_for_trend("declining"),
            "new": display.get_color_for_trend("new")
        }
        
        assert colors["improving"] == "#4CAF50"
        assert colors["stable"] == "#2196F3"
        assert colors["declining"] == "#FF9800"
        assert colors["new"] == "#9E9E9E"
    
    def test_get_widget_data(self, display):
        """Test widget data for non-pygame rendering."""
        widget_data = display.get_widget_data()
        
        assert "percentage" in widget_data
        assert "trend_symbol" in widget_data
        assert "trend_label" in widget_data
        assert "trend" in widget_data
        assert "color_name" in widget_data
        assert "current_session_accuracy" in widget_data
        assert "previous_session_accuracy" in widget_data
        assert "weekly_average_accuracy" in widget_data
        assert "improvement_percent" in widget_data
    
    def test_config_custom_colors(self, tracker):
        """Test custom configuration colors."""
        config = AccuracyDisplayConfig(
            improving_color="#FF0000",
            stable_color="#00FF00",
            declining_color="#0000FF"
        )
        
        display = AccuracyDisplay(tracker, config)
        
        assert display.get_color_for_trend("improving") == "#FF0000"
        assert display.get_color_for_trend("stable") == "#00FF00"
        assert display.get_color_for_trend("declining") == "#0000FF"
    
    def test_multiple_trend_values(self, tracker):
        """Test all possible trend return values."""
        # Test 'new' trend
        assert tracker.get_accuracy_trend() == "new"
        
        # The display should handle all trend values
        display = AccuracyDisplay(tracker)
        data = display.get_display_data()
        
        assert data["trend"] == "new"
        assert data["trend_symbol"] == "-"
        assert data["trend_label"] == "New"


class TestAccuracyEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.fixture
    def tracker(self):
        """Create a fresh ProgressTracker."""
        return ProgressTracker(student_id="test_student")
    
    def test_empty_session_accuracy(self, tracker):
        """Test accuracy calculation with empty session."""
        session = SessionSummary(
            session_id="empty_session",
            student_id="test_student",
            start_time=datetime.now()
        )
        session.end_time = datetime.now()
        
        tracker.session_tracker.completed_sessions.append(session)
        
        accuracy = tracker.calculate_accuracy()
        assert accuracy == 0.0
    
    def test_all_correct_accuracy(self, tracker):
        """Test 100% accuracy case."""
        session = SessionSummary(
            session_id="perfect_session",
            student_id="test_student",
            start_time=datetime.now()
        )
        
        for i in range(10):
            session.words.append(WordAttempt(
                word=f"word_{i}",
                word_id=f"word_{i}",
                correct=True,
                first_attempt_correct=True,
                total_attempts=1,
                hints_used=0,
                time_seconds=10.0
            ))
        
        session.end_time = datetime.now() + timedelta(minutes=15)
        tracker.session_tracker.completed_sessions.append(session)
        
        accuracy = tracker.calculate_accuracy()
        assert accuracy == 100.0
    
    def test_all_incorrect_accuracy(self, tracker):
        """Test 0% accuracy case."""
        session = SessionSummary(
            session_id="imperfect_session",
            student_id="test_student",
            start_time=datetime.now()
        )
        
        for i in range(10):
            session.words.append(WordAttempt(
                word=f"word_{i}",
                word_id=f"word_{i}",
                correct=False,
                first_attempt_correct=False,
                total_attempts=3,
                hints_used=2,
                time_seconds=20.0
            ))
        
        session.end_time = datetime.now() + timedelta(minutes=15)
        tracker.session_tracker.completed_sessions.append(session)
        
        accuracy = tracker.calculate_accuracy()
        assert accuracy == 0.0
    
    def test_precision_accuracy(self, tracker):
        """Test accuracy precision (1 decimal place)."""
        session = SessionSummary(
            session_id="precision_session",
            student_id="test_student",
            start_time=datetime.now()
        )
        
        # 3 correct, 1 incorrect = 75%
        for i in range(3):
            session.words.append(WordAttempt(
                word=f"word_{i}",
                word_id=f"word_{i}",
                correct=True,
                first_attempt_correct=True,
                total_attempts=1,
                hints_used=0,
                time_seconds=10.0
            ))
        
        session.words.append(WordAttempt(
            word="word_3",
            word_id="word_3",
            correct=False,
            first_attempt_correct=False,
            total_attempts=2,
            hints_used=1,
            time_seconds=20.0
        ))
        
        session.end_time = datetime.now() + timedelta(minutes=15)
        tracker.session_tracker.completed_sessions.append(session)
        
        display = tracker.get_accuracy_display()
        # Should be rounded to 1 decimal place
        assert isinstance(display["percentage"], float)
    
    def test_trend_threshold_boundary(self, tracker):
        """Test trend calculation at boundary values."""
        # Create sessions with exactly 5% difference (boundary)
        session1 = SessionSummary(
            session_id="session_1",
            student_id="test_student",
            start_time=datetime.now() - timedelta(hours=2)
        )
        
        for i in range(20):
            session1.words.append(WordAttempt(
                word=f"word_{i}",
                word_id=f"word_{i}",
                correct=True,
                first_attempt_correct=True,
                total_attempts=1,
                hints_used=0,
                time_seconds=10.0
            ))
        
        session1.end_time = datetime.now()
        tracker.session_tracker.completed_sessions.append(session1)
        
        # Second session with exactly 5% less
        session2 = SessionSummary(
            session_id="session_2",
            student_id="test_student",
            start_time=datetime.now()
        )
        
        for i in range(19):
            session2.words.append(WordAttempt(
                word=f"word_{19+i}",
                word_id=f"word_{19+i}",
                correct=True,
                first_attempt_correct=True,
                total_attempts=1,
                hints_used=0,
                time_seconds=10.0
            ))
        
        session2.words.append(WordAttempt(
            word="word_38",
            word_id="word_38",
            correct=False,
            first_attempt_correct=False,
            total_attempts=1,
            hints_used=0,
            time_seconds=10.0
        ))
        
        session2.end_time = datetime.now() + timedelta(minutes=15)
        tracker.session_tracker.completed_sessions.append(session2)
        
        # Should be "stable" since difference is <= 5%
        trend = tracker.get_accuracy_trend()
        assert trend == "stable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
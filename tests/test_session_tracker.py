"""
Unit tests for SessionTracker component (STORY-002-01)

Tests for comprehensive session data collection that tracks all relevant 
metrics during gameplay for later analysis and progress visualization.
"""

import pytest
from datetime import datetime, timedelta
from src.components.session_tracker import (
    SessionTracker,
    SessionSummary,
    WordAttempt,
    create_session_tracker
)


class TestWordAttempt:
    """Tests for the WordAttempt dataclass."""
    
    def test_word_attempt_initialization(self):
        """Test WordAttempt initializes correctly."""
        attempt = WordAttempt(
            word="hello",
            word_id="word_1",
            correct=True,
            first_attempt_correct=True,
            total_attempts=1,
            hints_used=0,
            time_seconds=5.2
        )
        
        assert attempt.word == "hello"
        assert attempt.word_id == "word_1"
        assert attempt.correct is True
        assert attempt.first_attempt_correct is True
        assert attempt.total_attempts == 1
        assert attempt.hints_used == 0
        assert attempt.time_seconds == 5.2
        assert isinstance(attempt.timestamp, datetime)
    
    def test_word_attempt_with_multiple_attempts(self):
        """Test WordAttempt with multiple attempts and hints."""
        attempt = WordAttempt(
            word="computer",
            word_id="word_2",
            correct=True,
            first_attempt_correct=False,
            total_attempts=3,
            hints_used=2,
            time_seconds=15.8
        )
        
        assert attempt.total_attempts == 3
        assert attempt.hints_used == 2
        assert attempt.first_attempt_correct is False


class TestSessionSummary:
    """Tests for the SessionSummary dataclass."""
    
    def test_session_summary_initialization(self):
        """Test SessionSummary initializes correctly."""
        summary = SessionSummary(
            session_id="test_session_1",
            student_id="student_1",
            start_time=datetime(2026, 7, 7, 10, 0, 0)
        )
        
        assert summary.session_id == "test_session_1"
        assert summary.student_id == "student_1"
        assert summary.words_attempted == 0
        assert summary.words_correct == 0
        assert summary.accuracy == 0.0
        assert summary.best_streak == 0
        assert summary.total_hints_used == 0
    
    def test_duration_seconds_with_end_time(self):
        """Test duration calculation with end_time set."""
        start = datetime(2026, 7, 7, 10, 0, 0)
        end = datetime(2026, 7, 7, 10, 5, 30)  # 5 minutes 30 seconds
        
        summary = SessionSummary(
            session_id="test_session",
            student_id="student_1",
            start_time=start,
            end_time=end
        )
        
        assert summary.duration_seconds == 330.0  # 5*60 + 30
    
    def test_accuracy_calculation(self):
        """Test accuracy calculation with mixed results."""
        summary = SessionSummary(
            session_id="test_session",
            student_id="student_1",
            start_time=datetime.now()
        )
        
        # Add words: 2 first-attempt correct, 1 not
        summary.words.append(
            WordAttempt("word1", "id1", True, True, 1, 0, 5.0)
        )
        summary.words.append(
            WordAttempt("word2", "id2", True, True, 1, 0, 6.0)
        )
        summary.words.append(
            WordAttempt("word3", "id3", True, False, 2, 1, 10.0)
        )
        
        assert summary.words_attempted == 3
        assert summary.words_correct == 2  # 2 with first_attempt_correct
        assert summary.accuracy == 2/3  # 66.67%
    
    def test_best_streak_calculation(self):
        """Test best streak calculation with breaks."""
        summary = SessionSummary(
            session_id="test_session",
            student_id="student_1",
            start_time=datetime.now()
        )
        
        # Pattern: correct, correct, wrong, correct, correct, correct, wrong, correct
        patterns = [
            (True, True),   # streak 1
            (True, True),   # streak 2
            (False, False), # streak 0
            (True, True),   # streak 1
            (True, True),   # streak 2
            (True, True),   # streak 3 (max)
            (False, False), # streak 0
            (True, True),   # streak 1
        ]
        
        for i, (correct, first_correct) in enumerate(patterns):
            summary.words.append(
                WordAttempt(f"word{i}", f"id{i}", correct, first_correct, 1, 0, 5.0)
            )
        
        assert summary.best_streak == 3
    
    def test_avg_time_per_word(self):
        """Test average time calculation."""
        summary = SessionSummary(
            session_id="test_session",
            student_id="student_1",
            start_time=datetime.now()
        )
        
        summary.words.append(WordAttempt("word1", "id1", True, True, 1, 0, 5.0))
        summary.words.append(WordAttempt("word2", "id2", True, True, 1, 0, 10.0))
        summary.words.append(WordAttempt("word3", "id3", True, True, 1, 0, 15.0))
        
        assert summary.avg_time_per_word == 10.0  # (5+10+15)/3
    
    def test_to_dict_serialization(self):
        """Test conversion to dictionary."""
        summary = SessionSummary(
            session_id="test_session",
            student_id="student_1",
            start_time=datetime(2026, 7, 7, 10, 0, 0),
            end_time=datetime(2026, 7, 7, 10, 5, 0)
        )
        
        summary.words.append(
            WordAttempt("hello", "word_1", True, True, 1, 0, 5.0)
        )
        
        data = summary.to_dict()
        
        assert data['session_id'] == "test_session"
        assert data['student_id'] == "student_1"
        assert data['words_attempted'] == 1
        assert data['accuracy'] == 1.0
        assert data['best_streak'] == 1
        assert len(data['words']) == 1


class TestSessionTracker:
    """Tests for the SessionTracker class."""
    
    @pytest.fixture
    def tracker(self):
        """Create a fresh SessionTracker for testing."""
        return create_session_tracker(student_id="test_student")
    
    def test_tracker_initialization(self):
        """Test SessionTracker initializes correctly."""
        tracker = create_session_tracker(student_id="student_123")
        
        assert tracker.student_id == "student_123"
        assert tracker.current_session is None
        assert len(tracker.completed_sessions) == 0
    
    def test_start_session(self, tracker):
        """Test starting a new session."""
        session = tracker.start_session()
        
        assert session is not None
        assert session.student_id == "test_student"
        assert session.session_id.startswith("test_student_")
        assert tracker.current_session == session
    
    def test_start_session_with_custom_id(self, tracker):
        """Test starting session with custom ID."""
        session = tracker.start_session(session_id="custom_session_123")
        
        assert session.session_id == "custom_session_123"
    
    def test_start_session_ends_previous(self, tracker):
        """Test that starting new session ends previous one."""
        tracker.start_session(session_id="session_1")
        tracker.current_session.words.append(WordAttempt(
            "word1", "id1", True, True, 1, 0, 5.0
        ))
        
        tracker.start_session(session_id="session_2")
        
        # Previous session should be in completed
        assert len(tracker.completed_sessions) == 1
        assert tracker.completed_sessions[0].session_id == "session_1"
        assert len(tracker.completed_sessions[0].words) == 1
    
    def test_start_word(self, tracker):
        """Test starting word tracking."""
        tracker.start_session()
        tracker.start_word("word_1", "hello")
        
        # Word tracking should be active
        assert tracker._current_word == "hello"
        assert tracker._current_word_id == "word_1"
        assert tracker._word_attempts == 0
    
    def test_record_attempt(self, tracker):
        """Test recording attempts."""
        tracker.start_session()
        tracker.start_word("word_1", "hello")
        
        tracker.record_attempt(False)  # First attempt wrong
        assert tracker._word_attempts == 1
        
        tracker.record_attempt(False)  # Second attempt wrong
        assert tracker._word_attempts == 2
        
        tracker.record_attempt(True)  # Third attempt correct
        assert tracker._word_attempts == 3
    
    def test_record_hint(self, tracker):
        """Test recording hint usage."""
        tracker.start_session()
        tracker.start_word("word_1", "hello")
        
        tracker.record_hint()
        assert tracker._word_hints_used == 1
        
        tracker.record_hint()
        assert tracker._word_hints_used == 2
    
    def test_complete_word(self, tracker):
        """Test completing word tracking."""
        tracker.start_session()
        tracker.start_word("word_1", "hello")
        
        # Simulate 2 wrong attempts and 3 hints
        tracker.record_attempt(False)
        tracker.record_hint()
        tracker.record_hint()
        tracker.record_attempt(False)
        tracker.record_hint()
        
        # Finally correct (which also records the 3rd attempt)
        tracker.complete_word(True)
        
        # Word should be in session
        assert len(tracker.current_session.words) == 1
        
        word = tracker.current_session.words[0]
        assert word.word == "hello"
        assert word.word_id == "word_1"
        assert word.total_attempts == 3  # 2 wrong + 1 correct
        assert word.hints_used == 3
        assert word.first_attempt_correct is False
        assert word.correct is True
    
    def test_complete_word_first_attempt(self, tracker):
        """Test completing word on first attempt."""
        tracker.start_session()
        tracker.start_word("word_1", "hello")
        tracker.complete_word(True)
        
        word = tracker.current_session.words[0]
        assert word.first_attempt_correct is True
        assert word.total_attempts == 1
        assert word.hints_used == 0
    
    def test_complete_session(self, tracker):
        """Test completing a session."""
        tracker.start_session(session_id="test_session")
        tracker.start_word("word1", "hello")
        tracker.complete_word(True)
        
        session = tracker.complete_session(planet="mercury")
        
        assert session is not None
        assert session.session_id == "test_session"
        assert session.planet_completed == "mercury"
        assert session.end_time is not None
        assert len(tracker.completed_sessions) == 1
        assert tracker.current_session is None
    
    def test_complete_session_with_in_progress_word(self, tracker):
        """Test that completing session finalizes in-progress word."""
        tracker.start_session()
        tracker.start_word("word1", "hello")
        # Start word but don't complete it
        
        tracker.complete_session(planet="mercury")
        
        # Word should still be recorded
        assert len(tracker.completed_sessions[0].words) == 1
    
    def test_get_current_session_stats(self, tracker):
        """Test getting current session statistics."""
        tracker.start_session()
        tracker.start_word("word1", "hello")
        tracker.complete_word(True)
        tracker.start_word("word2", "world")
        tracker.complete_word(False)
        
        stats = tracker.get_current_session_stats()
        
        assert stats['words_attempted'] == 2
        assert stats['words_correct'] == 1
        assert stats['accuracy'] == 0.5  # 1 first-attempt correct out of 2
    
    def test_get_session_stats(self, tracker):
        """Test getting specific session statistics."""
        tracker.start_session(session_id="test_1")
        tracker.complete_session()
        
        tracker.start_session(session_id="test_2")
        tracker.start_word("word1", "hello")
        tracker.complete_word(True)
        tracker.complete_session()
        
        stats = tracker.get_session_stats("test_2")
        
        assert stats['session_id'] == "test_2"
        assert stats['words_attempted'] == 1
        assert stats['accuracy'] == 1.0
    
    def test_get_all_sessions(self, tracker):
        """Test getting all completed sessions."""
        tracker.start_session(session_id="s1")
        tracker.complete_session()
        
        tracker.start_session(session_id="s2")
        tracker.complete_session()
        
        all_sessions = tracker.get_all_sessions()
        
        assert len(all_sessions) == 2
        assert all_sessions[0]['session_id'] == "s1"
        assert all_sessions[1]['session_id'] == "s2"
    
    def test_get_recent_sessions(self, tracker):
        """Test getting recent sessions."""
        for i in range(5):
            tracker.start_session(session_id=f"s{i}")
            tracker.complete_session()
        
        recent = tracker.get_recent_sessions(count=3)
        
        assert len(recent) == 3
        assert recent[0]['session_id'] == "s2"
        assert recent[-1]['session_id'] == "s4"
    
    def test_reset(self, tracker):
        """Test resetting the tracker."""
        tracker.start_session()
        tracker.start_word("word1", "hello")
        tracker.complete_word(True)
        tracker.complete_session()
        
        tracker.reset()
        
        assert tracker.current_session is None
        assert len(tracker.completed_sessions) == 0
        assert tracker._current_word is None


class TestIntegration:
    """Integration tests for SessionTracker."""
    
    def test_full_session_workflow(self):
        """Test complete session workflow."""
        tracker = create_session_tracker(student_id="student_1")
        
        # Start session
        session = tracker.start_session()
        assert session.session_id.startswith("student_1")
        
        # Complete several words - all must be correct to call complete_word
        words = [
            ("word1", "hello", 1, 0),      # 1 attempt (first correct), 0 hints
            ("word2", "world", 2, 2),       # 2 attempts (1 wrong + 1 right), 2 hints
            ("word3", "test", 1, 0),        # 1 attempt (first correct), 0 hints
            ("word4", "challenge", 2, 0),   # 2 attempts (1 wrong + 1 right), 0 hints  
            ("word5", "planet", 1, 0),      # 1 attempt (first correct), 0 hints
        ]
        
        for word_id, text, attempts, hints in words:
            tracker.start_word(word_id, text)
            
            # Simulate wrong attempts (total_attempts - 1 wrong attempts)
            for _ in range(attempts - 1):
                tracker.record_attempt(False)
                # Distribute hints among wrong attempts
                for _ in range(hints // (attempts - 1) if attempts > 1 else 0):
                    tracker.record_hint()
            
            # Final attempt (correct)
            tracker.record_attempt(True)
            tracker.complete_word(True)  # Word was completed correctly
        
        # Complete session
        tracker.complete_session(planet="mercury")
        
        # Verify stats
        stats = tracker.get_current_session_stats()
        assert stats is None  # Session completed
        
        final_stats = tracker.get_session_stats(session.session_id)
        assert final_stats['words_attempted'] == 5
        # Streak pattern: 1 (word1) - 0 (word2 broken) - 1 (word3) - 0 (word4 broken) - 1 (word5)
        # Best consecutive first-attempt correct streak is 1
        assert final_stats['best_streak'] == 1  # Single first-attempt correct words
        assert final_stats['total_hints_used'] == 2  # 0 + 2 + 0 + 0 + 0 = 2
        # 3/5 words correct on first attempt = 60%
        assert final_stats['accuracy'] == 0.6  # 3/5 first-attempt correct (words 1, 3, 5)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

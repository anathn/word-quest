"""
Unit tests for SessionTracker component (STORY-002-01)

Tests for comprehensive session data collection that tracks all relevant 
metrics during gameplay for later analysis and progress visualization.
"""

import pytest
import time
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
        assert data['first_attempt_accuracy'] == 1.0
        assert data['best_streak'] == 1
        assert len(data['words']) == 1


@pytest.fixture
def tracker():
    """Create a fresh SessionTracker for testing."""
    return create_session_tracker(student_id="test_student")


class TestSessionTracker:
    """Tests for the SessionTracker class."""
    
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
        
        # Finally correct (record the 3rd attempt before completing)
        tracker.record_attempt(True)
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
    
    def test_streak_tracking_first_attempt_correct(self, tracker):
        """Test that streak tracking works correctly for first-attempt correct words."""
        tracker.start_session()
        
        # Word 1: Correct on first attempt - streak should be 1
        tracker.start_word("word1", "hello")
        tracker.record_attempt(True)
        tracker.complete_word(True)
        assert tracker._current_streak == 1
        
        # Word 2: Correct on first attempt - streak should be 2
        tracker.start_word("word2", "world")
        tracker.record_attempt(True)
        tracker.complete_word(True)
        assert tracker._current_streak == 2
        
        # Word 3: Wrong first, then correct - streak should be 0
        tracker.start_word("word3", "test")
        tracker.record_attempt(False)
        tracker.record_attempt(True)
        tracker.complete_word(True)
        assert tracker._current_streak == 0
        
        # Word 4: Correct on first attempt - streak should be 1
        tracker.start_word("word4", "again")
        tracker.record_attempt(True)
        tracker.complete_word(True)
        assert tracker._current_streak == 1
        
        # Verify best_streak in session summary
        session = tracker.complete_session()
        assert session.best_streak == 2  # Max consecutive first-attempt correct was 2
    
    def test_streak_tracking_best_streak_calculation(self, tracker):
        """Test best_streak calculation in SessionSummary."""
        tracker.start_session()
        
        # Create a pattern: 3 correct, 1 wrong, 2 correct
        patterns = [
            ("word1", True),   # streak 1
            ("word2", True),   # streak 2
            ("word3", True),   # streak 3 (max)
            ("word4", False),  # streak 0
            ("word5", True),   # streak 1
            ("word6", True),   # streak 2
        ]
        
        for word_id, first_correct in patterns:
            tracker.start_word(word_id, word_id)
            if first_correct:
                tracker.record_attempt(True)
            else:
                tracker.record_attempt(False)
                tracker.record_attempt(True)  # Eventually correct
            tracker.complete_word(True)
        
        session = tracker.complete_session()
        assert session.best_streak == 3  # First 3 words were first-attempt correct
    
    def test_total_attempts_zero_handling(self, tracker):
        """Test that total_attempts can be 0 when no attempts recorded."""
        tracker.start_session()
        tracker.start_word("word1", "hello")
        # Don't record any attempts, just complete
        tracker._word_final_correct = True  # Set directly to simulate edge case
        tracker._complete_word_tracking()
        
        word = tracker.current_session.words[0]
        # total_attempts should now be 0, not faked to 1
        assert word.total_attempts == 0
    
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
        assert stats['first_attempt_accuracy'] == 0.5  # 1 first-attempt correct out of 2
    
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
        assert stats['first_attempt_accuracy'] == 1.0
    
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



    
    def test_full_session_workflow(self):
        """Test complete session workflow."""
        tracker = create_session_tracker(student_id="student_1")
        
        # Start session
        session = tracker.start_session()
        assert session.session_id.startswith("student_1")
        
        # Complete several words - pattern matters for streak tracking
        # Word 1: Correct first attempt - streak 1
        # Word 2: Correct first attempt - streak 2 (max)
        # Word 3: Wrong then correct - streak 0
        # Word 4: Correct first attempt - streak 1
        # Word 5: Correct first attempt - streak 2
        workflow = [
            # word_id, text, attempts (list of correctness), hints
            ("word1", "hello", [True], 0),         # First correct, streak=1
            ("word2", "world", [True], 0),         # First correct, streak=2 (max)
            ("word3", "test", [False, True], 1),   # Wrong then correct, streak=0
            ("word4", "again", [True], 0),         # First correct, streak=1
            ("word5", "planet", [True], 0),        # First correct, streak=2
        ]
        
        for word_id, text, attempts_list, hints in workflow:
            tracker.start_word(word_id, text)
            
            # Record all but last attempt
            for is_correct in attempts_list[:-1]:
                tracker.record_attempt(is_correct)
                for _ in range(hints // len(attempts_list[:-1]) if attempts_list[:-1] else 0):
                    tracker.record_hint()
            
            # Final attempt
            tracker.record_attempt(attempts_list[-1])
            tracker.complete_word(True)  # Word was completed correctly
        
        # Complete session
        tracker.complete_session(planet="mercury")
        
        # Verify stats
        stats = tracker.get_current_session_stats()
        assert stats is None  # Session completed
        
        final_stats = tracker.get_session_stats(session.session_id)
        assert final_stats['words_attempted'] == 5
        # Streak pattern: 1, 2, 0, 1, 2 - best streak is 2
        assert final_stats['best_streak'] == 2
        assert final_stats['total_hints_used'] == 1  # Only word3 had 1 hint
        # 4/5 words correct on first attempt = 80%
        assert final_stats['first_attempt_accuracy'] == 0.8  # 4/5 first-attempt correct
    
    def test_pending_sessions_queue(self, tracker):
        """Test that failed saves queue sessions for later."""
        # Monkey-patch save_session to simulate failure
        original_save = tracker.save_session
        tracker.save_session = lambda s: False  # Always fail
        
        tracker.start_session(session_id="fail_session")
        tracker.start_word("word1", "hello")
        tracker.complete_word(True)
        session = tracker.complete_session()
        
        # Should be in pending, not completed
        assert len(tracker.pending_sessions) == 1
        assert len(tracker.completed_sessions) == 0
        
        # Restore and flush
        tracker.save_session = original_save
        saved_count = tracker.flush_pending_sessions()
        
        assert saved_count == 1
        assert len(tracker.pending_sessions) == 0
        assert len(tracker.completed_sessions) == 1


class TestPerformance:
    """Performance tests for SessionTracker."""
    
    def test_performance_overhead(self):
        """Verify data collection stays under 10ms per word."""
        import time
        
        tracker = create_session_tracker("perf_test")
        tracker.start_session()
        
        times = []
        for i in range(100):
            start = time.perf_counter()
            tracker.start_word(f"word{i}", f"word{i}")
            tracker.record_attempt(True)
            tracker.complete_word(True)
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Verify average is well under 10ms (should be < 1ms actually)
        assert avg_time < 10, f"Performance overhead too high: avg={avg_time:.2f}ms, max={max_time:.2f}ms"
        # Bonus assertion: average should actually be < 1ms for efficient code
        assert avg_time < 1, f"Average performance overhead too high: {avg_time:.2f}ms"



    
    def test_empty_student_id_validation(self):
        """Test that empty student_id raises error."""
        tracker = create_session_tracker("")
        with pytest.raises(ValueError, match="student_id cannot be empty"):
            tracker.start_session()
    
    def test_idle_timeout_triggers_session_complete(self, tracker):
        """Test that idle timeout auto-completes session."""
        import time
        
        tracker.IDLE_TIMEOUT_SECONDS = 0.1  # 100ms for testing
        tracker.start_session()
        tracker.start_word("word1", "hello")
        tracker.complete_word(True)
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Start next word - should trigger idle timeout check
        tracker.start_word("word2", "world")
        
        # First session should have been auto-completed due to idle timeout
        assert len(tracker.completed_sessions) == 1
    
    def test_record_attempt_without_active_word(self, tracker):
        """Test recording attempt when no word is active."""
        tracker.start_session()
        # No start_word called
        tracker.record_attempt(True)
        # Should not crash, just return early
        assert len(tracker.current_session.words) == 0
    
    def test_total_attempts_zero_in_word(self, tracker):
        """Test that WordAttempt can have total_attempts=0."""
        tracker.start_session()
        tracker.start_word("word1", "hello")
        # Don't record any attempts, just complete with force
        tracker._word_final_correct = True
        tracker._word_attempts = 0  # Explicitly set to 0
        tracker._complete_word_tracking()
        
        word = tracker.current_session.words[0]
        assert word.total_attempts == 0
        assert word.first_attempt_correct is False  # None defaulted to False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Unit tests for StreakTracker component (STORY-004-01)

Tests the streak tracking functionality for consecutive correct answers.
"""

import pytest
from src.components.streak_tracker import StreakTracker, create_streak_tracker


class TestStreakTracker:
    """Test suite for StreakTracker class."""
    
    def test_create_streak_tracker(self):
        """Test factory function creates valid instance."""
        tracker = create_streak_tracker()
        assert tracker is not None
        assert isinstance(tracker, StreakTracker)
    
    def test_initial_streak_is_zero(self):
        """Test that streak starts at 0."""
        tracker = StreakTracker()
        assert tracker.get_current_streak() == 0
        assert tracker.get_best_streak() == 0
    
    def test_correct_answer_increments_streak(self):
        """Test that correct answer increments streak."""
        tracker = StreakTracker()
        
        streak1 = tracker.record_correct_answer()
        assert streak1 == 1
        assert tracker.get_current_streak() == 1
    
    def test_multiple_correct_answers(self):
        """Test streak increments with multiple correct answers."""
        tracker = StreakTracker()
        
        assert tracker.record_correct_answer() == 1
        assert tracker.record_correct_answer() == 2
        assert tracker.record_correct_answer() == 3
        assert tracker.get_current_streak() == 3
    
    def test_incorrect_answer_resets_streak(self):
        """Test that incorrect answer resets streak to 0."""
        tracker = StreakTracker()
        
        # Build up a streak
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        assert tracker.get_current_streak() == 2
        
        # Reset on incorrect
        tracker.record_incorrect_answer()
        assert tracker.get_current_streak() == 0
    
    def test_best_streak_remembers_highest(self):
        """Test that best streak tracks highest achieved."""
        tracker = StreakTracker()
        
        # First streak
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        assert tracker.get_best_streak() == 3
        
        # Reset
        tracker.record_incorrect_answer()
        assert tracker.get_current_streak() == 0
        assert tracker.get_best_streak() == 3  # Best should remain 3
        
        # Build smaller streak
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        assert tracker.get_current_streak() == 2
        assert tracker.get_best_streak() == 3  # Best should still be 3
    
    def test_best_streak_updates_on_new_record(self):
        """Test that best streak updates when current exceeds it."""
        tracker = StreakTracker()
        
        # First streak
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        assert tracker.get_best_streak() == 2
        
        # Reset and build bigger streak
        tracker.record_incorrect_answer()
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        assert tracker.get_best_streak() == 3
    
    def test_reset_session_preserves_best(self):
        """Test that reset_session preserves best streak."""
        tracker = StreakTracker()
        
        # Build streak
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        assert tracker.get_best_streak() == 3
        
        # Reset session
        tracker.reset_session()
        assert tracker.get_current_streak() == 0
        assert tracker.get_best_streak() == 3  # Best persists
    
    def test_reset_clears_all(self):
        """Test that reset() clears both current and best streak."""
        tracker = StreakTracker()
        
        # Build streak
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        assert tracker.get_best_streak() == 2
        
        # Full reset
        tracker.reset()
        assert tracker.get_current_streak() == 0
        assert tracker.get_best_streak() == 0
    
    def test_set_best_streak(self):
        """Test setting best streak from persisted data."""
        tracker = StreakTracker()
        
        # Set best from persistence
        tracker.set_best_streak(5)
        assert tracker.get_best_streak() == 5
        
        # Current should still be 0
        assert tracker.get_current_streak() == 0
    
    def test_set_best_streak_doesnt_decrease(self):
        """Test that set_best_streak doesn't decrease existing best."""
        tracker = StreakTracker()
        
        # Build streak
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        assert tracker.get_best_streak() == 3
        
        # Try to set lower value
        tracker.set_best_streak(2)
        assert tracker.get_best_streak() == 3  # Should stay at 3
    
    def test_to_dict_serialization(self):
        """Test serialization to dictionary."""
        tracker = StreakTracker()
        
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        tracker.record_incorrect_answer()
        
        data = tracker.to_dict()
        assert data['current_streak'] == 0
        assert data['best_streak'] == 2
        assert data['streak_start_time'] is None
    
    def test_from_dict_deserialization(self):
        """Test deserialization from dictionary."""
        tracker = StreakTracker()
        
        # Set some values
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        
        # Create new tracker and restore
        tracker2 = StreakTracker()
        tracker2.from_dict({'current_streak': 3, 'best_streak': 5, 'streak_start_time': 123.0})
        
        assert tracker2.get_current_streak() == 3
        assert tracker2.get_best_streak() == 5
    
    def test_non_punitive_reset(self):
        """Test that streak reset doesn't trigger negative state."""
        tracker = StreakTracker()
        
        tracker.record_correct_answer()
        tracker.record_incorrect_answer()
        
        # Should be able to immediately start new streak
        streak = tracker.record_correct_answer()
        assert streak == 1
        # No "penalty" state - can immediately start building streak again
    
    def test_streak_after_multiple_resets(self):
        """Test streak behavior after multiple correct/incorrect cycles."""
        tracker = StreakTracker()
        
        # Cycle 1
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        tracker.record_incorrect_answer()
        assert tracker.get_current_streak() == 0
        assert tracker.get_best_streak() == 2
        
        # Cycle 2
        tracker.record_correct_answer()
        tracker.record_incorrect_answer()
        assert tracker.get_current_streak() == 0
        assert tracker.get_best_streak() == 2
        
        # Cycle 3 - new record
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        tracker.record_correct_answer()
        assert tracker.get_current_streak() == 4
        assert tracker.get_best_streak() == 4


class TestStreakDisplayIntegration:
    """Integration-style tests for streak display scenarios."""
    
    def test_streak_hidden_until_first_correct(self):
        """Test that streak shows nothing until first correct answer."""
        tracker = StreakTracker()
        
        # Should be 0 (hidden state)
        assert tracker.get_current_streak() == 0
        
        # After first correct
        tracker.record_correct_answer()
        assert tracker.get_current_streak() == 1  # Now visible
    
    def test_streak_sequence_typical_gameplay(self):
        """Test typical game session streak progression."""
        tracker = StreakTracker()
        
        # Word 1: correct
        assert tracker.record_correct_answer() == 1
        
        # Word 2: correct
        assert tracker.record_correct_answer() == 2
        
        # Word 3: incorrect (reset)
        tracker.record_incorrect_answer()
        assert tracker.get_current_streak() == 0
        
        # Word 4: correct (new streak)
        assert tracker.record_correct_answer() == 1
        
        # Word 5: correct
        assert tracker.record_correct_answer() == 2
        
        # Best streak should be 2
        assert tracker.get_best_streak() == 2
    
    def test_high_streak_threshold(self):
        """Test streak at high thresholds (e.g., 5+ for special effects)."""
        tracker = StreakTracker()
        
        # Build to 5
        for i in range(5):
            assert tracker.record_correct_answer() == i + 1
        
        assert tracker.get_current_streak() == 5
        assert tracker.get_best_streak() == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
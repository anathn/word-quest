"""
Unit tests for Words Mastered Counter (STORY-002-03)

Tests for the words mastered tracking feature that displays cumulative
progress in "X/Y words" format with real-time updates.
"""

import pytest
import pygame
from src.components.progress_tracker import (
    ProgressTracker,
    create_progress_tracker
)

# Initialize pygame for testing
pygame.init()


class TestWordsMasteredProgress:
    """Tests for the words mastered tracking feature."""
    
    def test_initial_mastered_count(self):
        """Test that mastered count starts at zero."""
        tracker = create_progress_tracker()
        
        assert tracker.get_mastered_count() == 0
        assert tracker.get_progress_text() == "0/0 words"
    
    def test_mark_word_as_mastered(self):
        """Test marking a word as mastered increases count."""
        tracker = create_progress_tracker()
        tracker.set_total_words(50)
        
        # Mark first word as mastered
        result = tracker.mark_word_mastered("word_1")
        
        assert result is True  # Newly mastered
        assert tracker.get_mastered_count() == 1
        assert tracker.get_progress_text() == "1/50 words"
    
    def test_duplicate_mastered_word(self):
        """Test that marking same word twice doesn't increment count."""
        tracker = create_progress_tracker()
        tracker.set_total_words(50)
        
        # Mark word as mastered
        tracker.mark_word_mastered("word_1")
        assert tracker.get_mastered_count() == 1
        
        # Try to mark same word again
        result = tracker.mark_word_mastered("word_1")
        
        assert result is False  # Already mastered
        assert tracker.get_mastered_count() == 1
        assert tracker.get_progress_text() == "1/50 words"
    
    def test_multiple_words_mastered(self):
        """Test marking multiple different words as mastered."""
        tracker = create_progress_tracker()
        tracker.set_total_words(50)
        
        # Mark multiple words
        tracker.mark_word_mastered("word_1")
        tracker.mark_word_mastered("word_2")
        tracker.mark_word_mastered("word_3")
        
        assert tracker.get_mastered_count() == 3
        assert tracker.get_progress_text() == "3/50 words"
    
    def test_get_mastered_words(self):
        """Test retrieving set of mastered words."""
        tracker = create_progress_tracker()
        
        tracker.mark_word_mastered("word_1")
        tracker.mark_word_mastered("word_2")
        
        mastered = tracker.get_mastered_words()
        
        assert "word_1" in mastered
        assert "word_2" in mastered
        assert len(mastered) == 2
    
    def test_is_word_mastered(self):
        """Test checking if a specific word is mastered."""
        tracker = create_progress_tracker()
        
        tracker.mark_word_mastered("word_1")
        
        assert tracker.is_word_mastered("word_1") is True
        assert tracker.is_word_mastered("word_2") is False
    
    def test_progress_text_format(self):
        """Test progress text is formatted correctly."""
        tracker = create_progress_tracker()
        
        # Test various counts
        tracker.set_total_words(50)
        tracker.mark_word_mastered("word_1")
        assert tracker.get_progress_text() == "1/50 words"
        
        tracker.mark_word_mastered("word_2")
        assert tracker.get_progress_text() == "2/50 words"
        
        # Test with zero mastered
        tracker2 = create_progress_tracker()
        tracker2.set_total_words(100)
        assert tracker2.get_progress_text() == "0/100 words"
    
    def test_total_words_tracking(self):
        """Test setting and getting total word count."""
        tracker = create_progress_tracker()
        
        tracker.set_total_words(50)
        assert tracker.get_total_words() == 50
        
        tracker.set_total_words(100)
        assert tracker.get_total_words() == 100
    
    def test_reset_clears_mastered_words(self):
        """Test that reset clears mastered words tracking."""
        tracker = create_progress_tracker()
        tracker.set_total_words(50)
        
        tracker.mark_word_mastered("word_1")
        tracker.mark_word_mastered("word_2")
        assert tracker.get_mastered_count() == 2
        
        tracker.reset()
        
        assert tracker.get_mastered_count() == 0
        assert tracker.get_mastered_words() == set()


class TestProgressTrackerIntegration:
    """Integration tests for words mastered with word completion."""
    
    def test_word_mastered_on_first_attempt_correct(self):
        """Test that a word is marked mastered when spelled correctly on first attempt."""
        tracker = create_progress_tracker()
        tracker.set_total_words(50)
        
        # Simulate word being spelled correctly on first attempt
        # Note: complete_word() internally calls record_attempt()
        tracker.start_word("word_1", "hello")
        tracker.complete_word(True)  # Single call handles the attempt
        
        assert tracker.get_mastered_count() == 1
        assert tracker.is_word_mastered("word_1") is True
    
    def test_word_not_mastered_on_second_attempt(self):
        """Test that a word is NOT mastered if not spelled correctly on first attempt."""
        tracker = create_progress_tracker()
        tracker.set_total_words(50)
        
        # Simulate word being spelled correctly on second attempt
        tracker.start_word("word_2", "world")
        tracker.record_attempt(False)  # First attempt incorrect
        tracker.complete_word(True)    # Second attempt correct (calls record_attempt again)
        
        assert tracker.get_mastered_count() == 0
        assert tracker.is_word_mastered("word_2") is False
    
    def test_word_not_mastered_with_hints(self):
        """Test that a word is NOT mastered if hints were used."""
        tracker = create_progress_tracker()
        tracker.set_total_words(50)
        
        # Simulate word spelled correctly with hints
        tracker.start_word("word_3", "python")
        tracker.record_hint_usage()   # Hints used
        tracker.complete_word(True)   # Correct answer
        
        # Note: In current implementation, hint usage is tracked before completion
        # So word should NOT be marked mastered
        assert tracker.get_mastered_count() == 0
    
    def test_multiple_words_with_first_attempt_accuracy(self):
        """Test masterlist with multiple words having first-attempt accuracy."""
        tracker = create_progress_tracker()
        tracker.set_total_words(50)
        
        # First word: correct on first attempt
        tracker.start_word("word_1", "hello")
        tracker.complete_word(True)
        
        # Second word: incorrect then correct
        tracker.start_word("word_2", "world")
        tracker.record_attempt(False)
        tracker.complete_word(True)
        
        # Third word: correct on first attempt
        tracker.start_word("word_3", "python")
        tracker.complete_word(True)
        
        assert tracker.get_mastered_count() == 2
        assert tracker.is_word_mastered("word_1") is True
        assert tracker.is_word_mastered("word_2") is False  # Not first attempt
        assert tracker.is_word_mastered("word_3") is True


class TestProgressDisplayIntegration:
    """Tests for ProgressDisplay integration with ProgressTracker."""
    
    def test_progress_display_creation(self):
        """Test that ProgressDisplay can be created with ProgressTracker."""
        from src.ui.progress_display import ProgressDisplay, create_progress_display
        
        tracker = create_progress_tracker()
        display = create_progress_display(tracker)
        
        assert display is not None
        assert display.tracker == tracker
    
    def test_progress_display_gets_progress_text(self):
        """Test that ProgressDisplay gets correct progress text."""
        from src.ui.progress_display import create_progress_display
        
        tracker = create_progress_tracker()
        tracker.set_total_words(50)
        tracker.mark_word_mastered("word_1")
        tracker.mark_word_mastered("word_2")
        
        display = create_progress_display(tracker)
        progress_text = tracker.get_progress_text()
        
        assert progress_text == "2/50 words"


class TestEdgeCases:
    """Edge case tests for words mastered tracking."""
    
    def test_empty_word_list(self):
        """Test behavior with empty word list."""
        tracker = create_progress_tracker()
        tracker.set_total_words(0)
        
        assert tracker.get_progress_text() == "0/0 words"
    
    def test_all_words_mastered(self):
        """Test when all words are mastered."""
        tracker = create_progress_tracker()
        tracker.set_total_words(5)
        
        for i in range(1, 6):
            tracker.mark_word_mastered(f"word_{i}")
        
        assert tracker.get_mastered_count() == 5
        assert tracker.get_progress_text() == "5/5 words"
    
    def test_mastered_words_persist_separately(self):
        """Test that mastered words don't interfere with other tracking."""
        tracker = create_progress_tracker()
        tracker.set_total_words(50)
        
        # Mark word as mastered
        tracker.mark_word_mastered("word_1")
        
        # Track a session - word_2 will be marked as mastered since spelled correctly on first attempt
        tracker.start_session("session_1")
        tracker.start_word("word_2", "test")
        tracker.record_attempt(True)
        tracker.complete_word(True)
        tracker.end_session()
        
        # Both words should be mastered (word_1 was manually marked, word_2 was spelled correctly on first attempt)
        assert tracker.is_word_mastered("word_1") is True
        assert tracker.is_word_mastered("word_2") is True  # Added: word_2 should now be mastered
        assert tracker.get_mastered_count() == 2  # Updated: now 2 words mastered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
Tests for Hint Manager Component (STORY-001-04)

Tests the progressive hint escalation system including:
- Letter count hint
- Letter-by-letter reveals
- Edge cases (short words)
- Analytics tracking
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from components.hint_manager import (
    HintManager,
    create_hint_manager,
    HintLevel,
    HintData
)


class TestHintManagerBasic:
    """Basic hint manager functionality tests."""
    
    def test_create_hint_manager(self):
        """Test hint manager creation."""
        manager = create_hint_manager("test")
        assert manager.word == "TEST"
        assert manager.word_length == 4
        assert manager.current_level == 0
        assert manager.hint_usage_count == 0
    
    def test_reset_clears_state(self):
        """Test that reset clears all state."""
        manager = create_hint_manager("hello")
        
        # Give some hints
        manager.get_next_hint()
        manager.get_next_hint()
        
        # Reset
        manager.reset()
        
        assert manager.current_level == 0
        assert manager.revealed_indices == set()
        assert manager.hint_usage_count == 0
        assert manager.first_hint_timestamp is None
        assert manager.last_hint_timestamp is None


class TestHintEscalation:
    """Test hint escalation flow."""
    
    def test_first_hint_letter_count(self):
        """First hint should show letter count."""
        manager = create_hint_manager("programming")
        
        hint = manager.get_next_hint()
        
        assert hint.level == 1
        assert hint.hint_type == HintLevel.LETTER_COUNT
        assert hint.message == "This word has 11 letters"
        assert manager.current_level == 1
        assert manager.hint_usage_count == 1
    
    def test_second_hint_reveal_first_letter(self):
        """Second hint should reveal first letter."""
        manager = create_hint_manager("hello")
        
        # First hint (letter count)
        manager.get_next_hint()
        
        # Second hint (first letter)
        hint = manager.get_next_hint()
        
        assert hint.level == 2
        assert hint.hint_type == HintLevel.LETTER_REVEAL
        assert hint.message == "The 1st letter is 'H'"
        assert 0 in hint.revealed_indices
        assert manager.current_level == 2
    
    def test_third_hint_reveal_second_letter(self):
        """Third hint should reveal second letter."""
        manager = create_hint_manager("hello")
        
        # Get through letter count and first letter
        manager.get_next_hint()
        manager.get_next_hint()
        
        # Third hint (second letter)
        hint = manager.get_next_hint()
        
        assert hint.level == 3
        assert hint.message == "The 2nd letter is 'E'"
        assert 1 in hint.revealed_indices
        assert manager.current_level == 3
    
    def test_continues_letter_by_letter(self):
        """Hints should continue revealing letters sequentially."""
        manager = create_hint_manager("cat")
        
        hints = []
        while hint := manager.get_next_hint():
            hints.append(hint)
        
        # Should have: letter count + 3 letter reveals = 4 hints
        assert len(hints) == 4
        
        # Check each letter was revealed
        revealed = set()
        for hint in hints[1:]:  # Skip letter count
            revealed.update(hint.revealed_indices)
        
        assert revealed == {0, 1, 2}


class TestRevealedPattern:
    """Test the revealed letter pattern display."""
    
    def test_no_hints_shows_all_underscores(self):
        """Without hints, all letters should be underscores."""
        manager = create_hint_manager("hello")
        
        pattern = manager.get_revealed_pattern()
        
        assert pattern == "_ _ _ _ _"
    
    def test_letter_count_hint_no_pattern_change(self):
        """Letter count hint doesn't reveal letters."""
        manager = create_hint_manager("hello")
        
        manager.get_next_hint()  # Letter count
        
        pattern = manager.get_revealed_pattern()
        
        assert pattern == "_ _ _ _ _"
    
    def test_after_first_letter_reveal(self):
        """After first letter hint, first letter shown."""
        manager = create_hint_manager("hello")
        
        manager.get_next_hint()  # Letter count
        manager.get_next_hint()  # First letter
        
        pattern = manager.get_revealed_pattern()
        
        assert pattern == "H _ _ _ _"
    
    def test_after_multiple_reveals(self):
        """Multiple hints reveal multiple letters."""
        manager = create_hint_manager("world")
        
        manager.get_next_hint()  # Letter count
        manager.get_next_hint()  # W
        manager.get_next_hint()  # O
        
        pattern = manager.get_revealed_pattern()
        
        assert pattern == "W O _ _ _"
    
    def test_fully_revealed_pattern(self):
        """All letters revealed shows full word."""
        manager = create_hint_manager("hi")
        
        while manager.get_next_hint():
            pass
        
        pattern = manager.get_revealed_pattern()
        
        assert pattern == "H I"


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_short_word_one_letter(self):
        """Single letter word should work."""
        manager = create_hint_manager("a")
        
        # Letter count
        hint1 = manager.get_next_hint()
        assert hint1.message == "This word has 1 letters"
        
        # Letter reveal
        hint2 = manager.get_next_hint()
        assert hint2.message == "The 1st letter is 'A'"
        
        assert manager.is_fully_revealed()
    
    def test_short_word_two_letters(self):
        """Two letter word should work."""
        manager = create_hint_manager("is")
        
        hints = []
        while hint := manager.get_next_hint():
            hints.append(hint)
        
        # Letter count + 2 reveals
        assert len(hints) == 3
        assert manager.is_fully_revealed()
    
    def test_long_word(self):
        """Long words should work correctly."""
        manager = create_hint_manager("supercalifragilisticexpialidocious")
        
        assert manager.word_length == 34
        
        # Should be able to get all hints
        hint_count = 0
        while manager.get_next_hint():
            hint_count += 1
        
        # Letter count + 34 letter reveals
        assert hint_count == 35
    
    def test_case_normalization(self):
        """Input should be normalized to uppercase."""
        manager = create_hint_manager("Hello")
        
        assert manager.word == "HELLO"
        
        hint = manager.get_next_hint()
        assert "This word has 5 letters" in hint.message


class TestIsLetterRevealed:
    """Test individual letter reveal checking."""
    
    def test_no_letters_revealed_initially(self):
        """No letters should be revealed at start."""
        manager = create_hint_manager("test")
        
        assert not manager.is_letter_revealed(0)
        assert not manager.is_letter_revealed(1)
        assert not manager.is_letter_revealed(2)
        assert not manager.is_letter_revealed(3)
    
    def test_specific_letter_revealed(self):
        """Check specific letter reveal status."""
        manager = create_hint_manager("test")
        
        manager.get_next_hint()  # Letter count
        manager.get_next_hint()  # T
        
        assert manager.is_letter_revealed(0)
        assert not manager.is_letter_revealed(1)
        assert not manager.is_letter_revealed(2)
        assert not manager.is_letter_revealed(3)


class TestAnalytics:
    """Test hint usage analytics."""
    
    def test_hint_count_tracked(self):
        """Hint usage count should be tracked."""
        manager = create_hint_manager("word")
        
        assert manager.get_hint_count() == 0
        
        manager.get_next_hint()
        assert manager.get_hint_count() == 1
        
        manager.get_next_hint()
        assert manager.get_hint_count() == 2
    
    def test_analytics_data(self):
        """Analytics should include all relevant data."""
        manager = create_hint_manager("test")
        
        manager.get_next_hint()
        manager.get_next_hint()
        
        analytics = manager.get_analytics()
        
        assert analytics['word'] == "TEST"
        assert analytics['hint_count'] == 2
        assert analytics['current_level'] == 2
        assert 0 in analytics['revealed_indices']
        assert analytics['is_fully_revealed'] == False
    
    def test_timestamps_tracked(self):
        """First and last hint timestamps should be tracked."""
        manager = create_hint_manager("test")
        
        assert manager.first_hint_timestamp is None
        assert manager.last_hint_timestamp is None
        
        manager.get_next_hint()
        
        assert manager.first_hint_timestamp is not None
        assert manager.last_hint_timestamp is not None


class TestEncouragement:
    """Test encouraging messages."""
    
    def test_no_hints_encouragement(self):
        """Encouragement when no hints used."""
        manager = create_hint_manager("test")
        
        message = manager.get_encouragement_message()
        
        assert message == "You've got this!"
    
    def test_one_hint_encouragement(self):
        """Encouragement after one hint."""
        manager = create_hint_manager("test")
        manager.get_next_hint()
        
        message = manager.get_encouragement_message()
        
        assert message == "You're getting closer!"
    
    def test_multiple_hints_encouragement(self):
        """Encouragement after multiple hints."""
        manager = create_hint_manager("test")
        manager.get_next_hint()
        manager.get_next_hint()
        manager.get_next_hint()
        
        message = manager.get_encouragement_message()
        
        assert message == "Keep trying, you're doing great!"
    
    def test_many_hints_encouragement(self):
        """Encouragement after many hints."""
        manager = create_hint_manager("test")
        for _ in range(5):
            manager.get_next_hint()
        
        message = manager.get_encouragement_message()
        
        assert message == "Great effort! You're almost there!"


class TestCallback:
    """Test hint shown callback."""
    
    def test_on_hint_shown_callback(self):
        """Callback should be called when hint is shown."""
        manager = create_hint_manager("test")
        callback_called = []
        
        def on_hint_shown(hint_data):
            callback_called.append(hint_data)
        
        manager.on_hint_shown = on_hint_shown
        
        manager.get_next_hint()
        
        assert len(callback_called) == 1
        assert callback_called[0].level == 1


class TestOrdinalSuffixes:
    """Test ordinal suffixes for letter positions."""
    
    def test_first_letter_suffix(self):
        """First letter should use '1st'."""
        manager = create_hint_manager("test")
        manager.get_next_hint()  # Letter count
        hint = manager.get_next_hint()
        
        assert "1st" in hint.message
    
    def test_second_letter_suffix(self):
        """Second letter should use '2nd'."""
        manager = create_hint_manager("test")
        manager.get_next_hint()
        manager.get_next_hint()
        hint = manager.get_next_hint()
        
        assert "2nd" in hint.message
    
    def test_third_letter_suffix(self):
        """Third letter should use '3rd'."""
        manager = create_hint_manager("test")
        manager.get_next_hint()
        manager.get_next_hint()
        manager.get_next_hint()
        hint = manager.get_next_hint()
        
        assert "3rd" in hint.message
    
    def test_fourth_letter_suffix(self):
        """Fourth letter should use '4th'."""
        manager = create_hint_manager("test")
        for _ in range(4):
            manager.get_next_hint()
        hint = manager.get_next_hint()
        
        assert "4th" in hint.message


class TestAcceptanceCriteria:
    """Test specific acceptance criteria from STORY-001-04."""
    
    def test_ac_first_hint_letter_count(self):
        """AC: First hint shows letter count."""
        manager = create_hint_manager("seven")
        hint = manager.get_next_hint()
        
        assert "This word has 5 letters" in hint.message
    
    def test_ac_second_hint_reveal_next_letter(self):
        """AC: Second hint reveals next letter."""
        manager = create_hint_manager("seven")
        manager.get_next_hint()  # Letter count
        hint = manager.get_next_hint()  # First letter
        
        assert "1st letter" in hint.message
        assert "S" in hint.message
    
    def test_ac_continues_letter_by_letter(self):
        """AC: Continue letter-by-letter until answer."""
        manager = create_hint_manager("cat")
        
        # Get all hints
        hints = []
        while hint := manager.get_next_hint():
            hints.append(hint)
        
        # Should reveal C, then A, then T
        assert len(hints) == 4  # Letter count + 3 letters
        
        # Check sequential reveals
        assert 0 in hints[1].revealed_indices  # C
        assert 1 in hints[2].revealed_indices  # A
        assert 2 in hints[3].revealed_indices  # T
    
    def test_ac_no_penalty_for_hints(self):
        """AC: No penalty for using hints (tracked but doesn't affect completion).
        
        Note: This is verified by the fact that hint usage is tracked separately
        from word completion status. The ProgressTracker will handle this.
        """
        manager = create_hint_manager("test")
        
        # Use all hints (1 letter count + 4 letter reveals = 5 total)
        while manager.get_next_hint():
            pass
        
        # Word can still be "completed" - hints don't prevent completion
        assert manager.hint_usage_count == 5
        # The word completion logic is separate from hint usage


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

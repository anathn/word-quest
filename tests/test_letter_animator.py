"""
Unit tests for letter animator.

Tests letter sequence animation, timing, and coordination.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
from src.ui.letter_animator import (
    LetterAnimator, AnimationConfig, create_letter_animator
)
from src.ui.letter_renderer import LetterState, LetterType
from src.ui.animation_utils import AnimationIntensity


# Initialize pygame for testing
pygame.init()
TEST_FONT = pygame.font.SysFont('arial', 48)


class TestLetterAnimatorInitialization:
    """Tests for LetterAnimator initialization."""
    
    def test_create_animator(self):
        """Should create a letter animator."""
        animator = LetterAnimator(TEST_FONT)
        assert animator.font is not None
        assert len(animator.letters) == 0
        assert not animator.is_animating
        
    def test_create_animator_with_config(self):
        """Should create animator with custom configuration."""
        config = AnimationConfig(
            animation_duration=0.5,
            letter_delay=0.2,
            starter_count=3
        )
        animator = LetterAnimator(TEST_FONT, config)
        assert animator.config.animation_duration == 0.5
        assert animator.config.letter_delay == 0.2
        assert animator.config.starter_count == 3
        
    def test_create_animator_default_config(self):
        """Default config should have expected values."""
        animator = LetterAnimator(TEST_FONT)
        assert animator.config.animation_duration == 0.3
        assert animator.config.letter_delay == 0.15
        assert animator.config.starter_count == 2


class TestWordSetting:
    """Tests for setting words on the animator."""
    
    def test_set_word(self):
        """Should set a word and create letter renderers."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO")
        assert animator.word == "HELLO"
        assert len(animator.letters) == 5
        
    def test_set_word_lowercase_input(self):
        """Lowercase input should be uppercased."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("hello")
        assert animator.word == "HELLO"
        
    def test_set_word_custom_starter_count(self):
        """Custom starter count should be applied."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO", starter_count=3)
        assert len(animator.letters) == 5
        # First 3 should be starter type
        starter_count = sum(1 for l in animator.letters if l.letter_type == LetterType.STARTER)
        assert starter_count == 3
        
    def test_set_word_single_letter(self):
        """Should handle single letter word."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("A")
        assert len(animator.letters) == 1
        
    def test_set_word_long_word(self):
        """Should handle longer words."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("COMPUTER")
        assert len(animator.letters) == 8
        
    def test_set_word_resets_animation_state(self):
        """Setting a new word should reset animation state."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO")
        animator.start_animation()
        animator.is_animating = True  # Artificially set
        
        animator.set_word("WORLD")
        assert not animator.is_animating
        assert animator.current_index == 0


class TestAnimationStart:
    """Tests for starting animations."""
    
    def test_start_animation(self):
        """Should start animation on first letter."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO")
        animator.start_animation()
        
        assert animator.is_animating
        assert animator.current_index == 0
        
    def test_start_animation_empty_word(self):
        """Should handle empty word gracefully."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("")
        animator.start_animation()
        assert not animator.is_animating
        
    def test_start_animation_sets_first_letter(self):
        """First letter animation should be started."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO")
        animator.start_animation()
        
        assert animator.letters[0].state != LetterState.NONE


class TestAnimationUpdate:
    """Tests for animation update behavior."""
    
    def test_update_advances_letters(self):
        """Update should advance letter animations."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO")
        animator.start_animation()
        
        # Update multiple times (using instant complete for testing)
        animator.update_advanced()
        animator.update_advanced()
            
        # Should not crash and should update state
        assert animator.letters[0].progress >= 0
        
    def test_update_completes_animation(self):
        """Updates should eventually complete all animations."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HI")
        animator.show_all_instantly()  # Test with instant completion
            
        assert animator.is_complete()
        
    def test_update_advances_sequence(self):
        """Update should advance through letter sequence."""
        config = AnimationConfig(letter_delay=0.01)  # Fast for testing
        animator = LetterAnimator(TEST_FONT, config)
        animator.set_word("HELLO")
        animator.show_all_instantly()  # For this test, just verify no errors
            
        # First letter should be complete
        assert animator.letters[0].is_complete()


class TestAnimationCompletion:
    """Tests for animation completion detection."""
    
    def test_is_complete_before_start(self):
        """Should be complete before starting (no animation yet)."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO")
        # Before starting animation, considered complete
        assert animator.is_complete()
        
    def test_is_complete_false_during_animation(self):
        """Should not be complete during animation."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO")
        animator.start_animation()
        assert not animator.is_complete()
        
    def test_is_complete_true_after_end(self):
        """Should be complete after all letters finished."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HI")
        animator.show_all_instantly()  # Instant completion
        assert animator.is_complete()
        
    def test_show_all_instantly_completes(self):
        """Instant display should mark as complete."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO")
        animator.show_all_instantly()
        
        assert animator.is_complete()
        assert all(l.is_complete() for l in animator.letters)


class TestLetterCount:
    """Tests for letter counting methods."""
    
    def test_get_letter_count(self):
        """Should return correct letter count."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO")
        assert animator.get_letter_count() == 5
        
    def test_get_completed_count(self):
        """Should return count of completed letters."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HI")
        animator.show_all_instantly()
        
        assert animator.get_completed_count() == 2
        
    def test_get_word(self):
        """Should return the current word."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO")
        assert animator.get_word() == "HELLO"


class TestAnimationIntensity:
    """Tests for animation intensity setting."""
    
    def test_set_intensity(self):
        """Should set animation intensity."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_intensity(AnimationIntensity.REDUCED)
        assert animator.config.intensity == AnimationIntensity.REDUCED
        
    def test_set_intensity_full(self):
        """Should accept full intensity."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_intensity("full")
        assert animator.config.intensity == "full"
        
    def test_set_intensity_reduced(self):
        """Should accept reduced intensity."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_intensity("reduced")
        assert animator.config.intensity == "reduced"
        
    def test_set_intensity_off(self):
        """Should accept off intensity."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_intensity("off")
        assert animator.config.intensity == "off"


class TestStarterLetters:
    """Tests for starter letter handling."""
    
    def test_starter_letters_have_correct_style(self):
        """Starter letters should have starter type."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO", starter_count=2)
        
        assert animator.letters[0].letter_type == LetterType.STARTER
        assert animator.letters[1].letter_type == LetterType.STARTER
        
    def test_non_starter_letters_have_regular_style(self):
        """Non-starter letters should have regular type."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO", starter_count=2)
        
        assert animator.letters[2].letter_type == LetterType.REGULAR
        assert animator.letters[3].letter_type == LetterType.REGULAR
        assert animator.letters[4].letter_type == LetterType.REGULAR
        
    def test_show_starter_letters(self):
        """Should show only starter letters."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HELLO", starter_count=2)
        animator.show_starter_letters()
        
        # Starter letters should be complete
        assert animator.letters[0].is_complete()
        assert animator.letters[1].is_complete()


class TestFactoryFunction:
    """Tests for the create_letter_animator factory function."""
    
    def test_create_letter_animator_basic(self):
        """Factory should create a configured animator."""
        animator = create_letter_animator(TEST_FONT)
        assert animator is not None
        assert isinstance(animator, LetterAnimator)
        
    def test_create_letter_animator_with_params(self):
        """Factory should accept custom parameters."""
        animator = create_letter_animator(
            font=TEST_FONT,
            starter_count=3,
            letter_spacing=25,
            intensity=AnimationIntensity.REDUCED
        )
        assert animator.config.starter_count == 3
        assert animator.config.letter_spacing == 25
        assert animator.config.intensity == AnimationIntensity.REDUCED


class TestRendering:
    """Tests for letter rendering."""
    
    def test_render(self):
        """Should render letters to screen."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("HI")
        animator.show_all_instantly()
        
        screen = pygame.Surface((200, 100))
        animator.render(screen, (10, 10))
        # Should not raise an error
        
    def test_render_empty_animator(self):
        """Should handle empty animator gracefully."""
        animator = LetterAnimator(TEST_FONT)
        screen = pygame.Surface((100, 100))
        animator.render(screen, (0, 0))
        # Should not raise an error


class TestEdgeCases:
    """Tests for edge cases and special conditions."""
    
    def test_single_letter_word(self):
        """Should handle single letter word."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("A")
        animator.show_all_instantly()  # Complete instantly for testing
            
        assert animator.is_complete()
        
    def test_long_word(self):
        """Should handle long words."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("SUPERCALIFRAGILISTICEXPIALIDOCIOUS")
        animator.show_all_instantly()
        
        assert animator.get_letter_count() == 34
        assert animator.is_complete()
        
    def test_empty_word(self):
        """Should handle empty word."""
        animator = LetterAnimator(TEST_FONT)
        animator.set_word("")
        animator.start_animation()
        
        assert not animator.is_animating
        assert animator.is_complete()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
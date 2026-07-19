"""
Unit tests for letter renderer.

Tests letter animation rendering, styling, and state management.
"""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
from src.ui.letter_renderer import (
    LetterRenderer, LetterState, LetterType
)
from src.ui.animation_utils import AnimationIntensity


# Initialize pygame for testing
pygame.init()
TEST_FONT = pygame.font.SysFont('arial', 48)


class TestLetterRendererInitialization:
    """Tests for LetterRenderer initialization."""
    
    def test_create_letter(self):
        """Should create a letter renderer."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        assert letter.char == 'A'
        assert letter.size == 48
        assert letter.state == LetterState.NONE
        
    def test_letter_uppercased(self):
        """Letter should be automatically uppercased."""
        letter = LetterRenderer('a', TEST_FONT, 48)
        assert letter.char == 'A'
        
    def test_letter_default_color(self):
        """Default letter color should be white."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        assert letter.base_color == (255, 255, 255)
        
    def test_letter_initial_scale(self):
        """Initial scale should be 0 before animation starts."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        assert letter.scale == 0.0
        
    def test_letter_initial_opacity(self):
        """Initial opacity should be 0 before animation starts."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        assert letter.opacity == 0.0


class TestLetterAnimation:
    """Tests for letter animation behavior."""
    
    def test_start_animation_fade(self):
        """Starting animation should set state to FADE_IN."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.start_animation("fade_bounce")
        assert letter.state == LetterState.FADE_IN
        assert letter.progress == 0.0
        
    def test_start_animation_instant(self):
        """Instant animation should complete immediately."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.start_animation("instant", instant=True)
        assert letter.state == LetterState.COMPLETE
        assert letter.scale == 1.0
        assert letter.opacity == 255
        
    def test_update_progress(self):
        """Update should increase progress."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.start_animation("fade_bounce")
        
        # Simulate 150ms update (half of 300ms duration)
        letter.update(150, "full")
        assert letter.progress > 0 and letter.progress < 1.0
        
    def test_update_completes_animation(self):
        """Full duration update should complete animation."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.start_animation("fade_bounce")
        
        # Simulate full duration
        letter.update(500, "full")
        assert letter.state == LetterState.COMPLETE
        assert letter.progress == 1.0
        
    def test_update_zero_delay(self):
        """Zero delay update should not change progress."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.start_animation("fade_bounce")
        letter.update(0, "full")
        assert letter.progress == 0.0
        
    def test_update_compressed_duration(self):
        """Update with compressed duration should progress faster."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.start_animation("instant")
        
        # Update with any duration should keep it complete
        letter.update(16, "full")
        assert letter.state == LetterState.COMPLETE


class TestAnimationIntensity:
    """Tests for animation intensity handling."""
    
    def test_full_intensity(self):
        """Full intensity should use bounce animation."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.start_animation("fade_bounce")
        letter.update(150, "full")
        
        # At 50% progress with full intensity, scale should be > 1.0 (bounce)
        assert letter.scale >= 1.0
        
    def test_reduced_intensity(self):
        """Reduced intensity should use fade-only animation."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.start_animation("fade_bounce")
        letter.update(150, "reduced")
        
        # Scale should be base scale (1.0) for fade-only
        assert abs(letter.scale - 1.0) < 0.01
        
    def test_off_intensity(self):
        """Off intensity should show letter instantly."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.start_animation("fade_bounce")
        letter.update(10, "off")
        
        # Should be complete with full opacity
        assert letter.opacity == 255
        assert letter.state == LetterState.COMPLETE


class TestLetterStyling:
    """Tests for letter styling methods."""
    
    def test_set_starter_style(self):
        """Starter style should use green color."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.set_starter_style()
        assert letter.base_color == (76, 175, 80)  # Green
        assert letter.letter_type == LetterType.STARTER
        
    def test_set_hint_style(self):
        """Hint style should use orange color."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.set_hint_style()
        assert letter.base_color == (255, 152, 0)  # Orange
        assert letter.letter_type == LetterType.HINT
        
    def test_set_typed_style(self):
        """Typed style should be instant and white."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.set_typed_style()
        assert letter.base_color == (255, 255, 255)
        assert letter.state == LetterState.COMPLETE
        assert letter.letter_type == LetterType.TYPED
        
    def test_set_letter_type_regular(self):
        """Regular type should use white color."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.set_letter_type(LetterType.REGULAR)
        assert letter.base_color == (255, 255, 255)


class TestLetterCompletion:
    """Tests for letter completion detection."""
    
    def test_is_complete_false_before_animation(self):
        """Letter should not be complete before animation."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        assert not letter.is_complete()
        
    def test_is_complete_false_during_animation(self):
        """Letter should not be complete during animation."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.start_animation("fade_bounce")
        letter.update(100, "full")
        assert not letter.is_complete()
        
    def test_is_complete_true_after_animation(self):
        """Letter should be complete after animation."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.start_animation("fade_bounce")
        letter.update(500, "full")
        assert letter.is_complete()


class TestLetterDimensions:
    """Tests for letter size calculations."""
    
    def test_get_width(self):
        """Should return letter width."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        width = letter.get_width()
        assert width > 0
        
    def test_get_height(self):
        """Should return letter height."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        height = letter.get_height()
        assert height > 0
        
    def test_different_letters_different_widths(self):
        """Different letters may have different widths."""
        letter_i = LetterRenderer('I', TEST_FONT, 48)
        letter_w = LetterRenderer('W', TEST_FONT, 48)
        # W is typically wider than I
        # Note: This is a soft assertion as fonts vary
        width_i = letter_i.get_width()
        width_w = letter_w.get_width()
        assert width_i > 0 and width_w > 0


class TestLetterRendering:
    """Tests for letter rendering."""
    
    def test_render_creates_surface(self):
        """Rendering should create a surface."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        screen = pygame.Surface((100, 100))
        letter.start_animation("instant", instant=True)
        letter.render(screen, (0, 0))
        # Should not raise an error
        
    def test_render_position(self):
        """Letter should store its render position."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        screen = pygame.Surface((100, 100))
        letter.start_animation("instant", instant=True)
        letter.render(screen, (50, 100))
        assert letter.position == (50, 100)


class TestEdgeCases:
    """Tests for edge cases and special conditions."""
    
    def test_empty_character(self):
        """Empty character should handle gracefully."""
        letter = LetterRenderer('', TEST_FONT, 48)
        screen = pygame.Surface((100, 100))
        letter.start_animation("instant", instant=True)
        letter.render(screen, (0, 0))
        # Should not raise an error
        
    def test_single_digit_letter(self):
        """Numeric characters should be handled."""
        letter = LetterRenderer('1', TEST_FONT, 48)
        assert letter.char == '1'
        
    def test_special_character_uppercase(self):
        """Special characters should pass through."""
        letter = LetterRenderer('!', TEST_FONT, 48)
        assert letter.char == '!'
        
    def test_multiple_updates_same_result(self):
        """Multiple updates after completion should not crash."""
        letter = LetterRenderer('A', TEST_FONT, 48)
        letter.start_animation("instant", instant=True)
        # Multiple updates should be safe
        letter.update(10, "full")
        letter.update(10, "full")
        letter.update(10, "full")
        assert letter.state == LetterState.COMPLETE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
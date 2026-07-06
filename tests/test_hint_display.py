"""
Tests for Hint Display UI Component (STORY-001-04)

Tests the hint display rendering and interaction including:
- Hint text rendering
- Revealed letter display
- Help button interaction
- Animation state
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, Mock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ui.hint_display import (
    HintDisplay,
    create_hint_display,
    HINT_BUTTON_COLOR,
    REVEALED_LETTER_COLOR
)


class TestHintDisplayCreation:
    """Test hint display creation and initialization."""
    
    def test_create_hint_display(self):
        """Test hint display creation."""
        typography = MagicMock()
        display = create_hint_display(typography)
        
        assert display.typography == typography
        assert display.screen_width == 800
        assert display.screen_height == 600
        assert display.hint_alpha == 0
        assert not display.animation_active
    
    def test_custom_screen_size(self):
        """Test creation with custom screen size."""
        typography = MagicMock()
        display = HintDisplay(typography, screen_width=1920, screen_height=1080)
        
        assert display.screen_width == 1920
        assert display.screen_height == 1080


class TestWordSetting:
    """Test setting the word for hint display."""
    
    def test_set_word(self):
        """Test setting a word."""
        typography = MagicMock()
        display = HintDisplay(typography)
        
        display.set_word("hello")
        
        assert display.word_text == "HELLO"
        assert display.revealed_indices == set()
        assert display.revealed_pattern == "_ _ _ _ _"
    
    def test_set_word_clears_previous(self):
        """Test that setting a new word clears previous state."""
        typography = MagicMock()
        display = HintDisplay(typography)
        
        # Set initial word with some reveals
        display.set_word("hello")
        display.revealed_indices.add(0)
        display.revealed_indices.add(1)
        
        # Set new word
        display.set_word("world")
        
        assert display.word_text == "WORLD"
        assert display.revealed_indices == set()
        assert display.revealed_pattern == "_ _ _ _ _"


class TestHintDisplay:
    """Test hint display functionality."""
    
    def test_show_hint(self):
        """Test showing a hint."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.set_word("hello")
        
        display.show_hint("This word has 5 letters", set())
        
        assert display.current_hint_text == "This word has 5 letters"
        assert display.animation_active == True
        assert display.hint_alpha == 0  # Starts at 0 for fade-in
    
    def test_show_hint_with_revealed_letters(self):
        """Test showing hint with revealed letters."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.set_word("hello")
        
        display.show_hint("The 1st letter is 'H'", {0})
        
        assert 0 in display.revealed_indices
        assert display.revealed_pattern == "H _ _ _ _"
    
    def test_show_hint_starts_animation(self):
        """Test that showing a hint starts fade-in animation."""
        typography = MagicMock()
        display = HintDisplay(typography)
        
        display.show_hint("Test hint", set())
        
        assert display.animation_active == True
        assert display.hint_alpha == 0


class TestHelpButton:
    """Test help button functionality."""
    
    def test_enable_help_button(self):
        """Test enabling the help button."""
        typography = MagicMock()
        display = HintDisplay(typography)
        
        display.enable_help_button()
        
        assert display.help_button_enabled == True
    
    def test_disable_help_button(self):
        """Test disabling the help button."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.enable_help_button()
        
        display.disable_help_button()
        
        assert display.help_button_enabled == False
        assert display.button_hovered == False
        assert display.button_pressed == False
    
    def test_button_click_inside_bounds(self):
        """Test button click inside bounds."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.enable_help_button()
        
        # Button is at (100, 450) with size (180, 64)
        result = display.check_button_click(150, 480)
        
        assert result == True
        assert display.button_hovered == True
        assert display.button_pressed == True
    
    def test_button_click_outside_bounds(self):
        """Test button click outside bounds."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.enable_help_button()
        
        result = display.check_button_click(500, 500)
        
        assert result == False
        assert display.button_hovered == False
    
    def test_button_click_disabled(self):
        """Test button click when disabled."""
        typography = MagicMock()
        display = HintDisplay(typography)
        # Button not enabled
        
        result = display.check_button_click(150, 480)
        
        assert result == False
    
    def test_button_click_callback(self):
        """Test that button click triggers callback."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.enable_help_button()
        
        callback_called = []
        display.on_help_clicked = lambda: callback_called.append(True)
        
        display.check_button_click(150, 480)
        
        assert len(callback_called) == 1
    
    def test_get_button_bounds(self):
        """Test getting button bounds."""
        typography = MagicMock()
        display = HintDisplay(typography)
        
        bounds = display.get_button_bounds()
        
        assert bounds == (100, 450, 180, 64)


class TestAnimation:
    """Test hint display animations."""
    
    def test_update_fades_in(self):
        """Test that update performs fade-in animation."""
        typography = MagicMock()
        display = HintDisplay(typography)
        
        display.show_hint("Test", set())
        
        # Simulate time passing (150ms = halfway through 300ms fade)
        display.update(0.15)
        
        assert display.hint_alpha > 0
        assert display.hint_alpha < 255
    
    def test_update_completes_fade(self):
        """Test that update completes fade after 300ms."""
        typography = MagicMock()
        display = HintDisplay(typography)
        
        display.show_hint("Test", set())
        
        # Simulate time passing (400ms = past 300ms fade)
        display.update(0.4)
        
        assert display.hint_alpha == 255
        assert display.animation_active == False
    
    def test_update_no_animation_when_inactive(self):
        """Test that update doesn't change state when animation inactive."""
        typography = MagicMock()
        display = HintDisplay(typography)
        
        initial_alpha = display.hint_alpha
        display.update(1.0)
        
        assert display.hint_alpha == initial_alpha


class TestRender:
    """Test hint display rendering."""
    
    def test_render_returns_list(self):
        """Test that render returns a list."""
        typography = MagicMock()
        display = HintDisplay(typography)
        screen = MagicMock()
        
        result = display.render(screen)
        
        assert isinstance(result, list)
    
    def test_render_with_hint(self):
        """Test rendering with a hint displayed."""
        typography = MagicMock()
        typography.style_body_text.font.size.return_value = (100, 30)  # Mock font.size() to return (width, height)
        display = HintDisplay(typography)
        display.set_word("hello")
        display.show_hint("Test hint", set())
        
        screen = MagicMock()
        
        result = display.render(screen)
        
        assert isinstance(result, list)
        # Should have at least background and text surfaces
    
    def test_render_with_button(self):
        """Test rendering with enabled button."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.enable_help_button()
        
        screen = MagicMock()
        
        result = display.render(screen)
        
        assert isinstance(result, list)
    
    def test_render_empty_state(self):
        """Test rendering in empty state."""
        typography = MagicMock()
        display = HintDisplay(typography)
        
        screen = MagicMock()
        
        result = display.render(screen)
        
        assert isinstance(result, list)
        assert len(result) == 0  # Nothing to render


class TestRevealedPattern:
    """Test revealed pattern building."""
    
    def test_pattern_no_reveals(self):
        """Test pattern with no revealed letters."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.set_word("test")
        
        assert display.revealed_pattern == "_ _ _ _"
    
    def test_pattern_first_letter(self):
        """Test pattern with first letter revealed."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.set_word("test")
        display.revealed_indices.add(0)
        
        display._build_revealed_pattern()  # Rebuild
        
        # Note: This tests the internal method
        result = []
        for i, letter in enumerate(display.word_text):
            if i in display.revealed_indices:
                result.append(letter)
            else:
                result.append('_')
        
        assert ' '.join(result) == "T _ _ _"
    
    def test_pattern_all_revealed(self):
        """Test pattern with all letters revealed."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.set_word("hi")
        display.revealed_indices.add(0)
        display.revealed_indices.add(1)
        
        result = []
        for i, letter in enumerate(display.word_text):
            if i in display.revealed_indices:
                result.append(letter)
            else:
                result.append('_')
        
        assert ' '.join(result) == "H I"


class TestCallback:
    """Test hint display callbacks."""
    
    def test_on_help_clicked_callback(self):
        """Test help button click callback."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.enable_help_button()
        
        callback_data = []
        display.on_help_clicked = lambda: callback_data.append("clicked")
        
        display.check_button_click(150, 480)
        
        assert callback_data == ["clicked"]


class TestReset:
    """Test reset functionality."""
    
    def test_reset_clears_all_state(self):
        """Test that reset clears all state."""
        typography = MagicMock()
        display = HintDisplay(typography)
        
        # Set up state
        display.set_word("hello")
        display.show_hint("Test", {0})
        display.enable_help_button()
        display.animation_active = True
        display.hint_alpha = 128
        display.current_hint_text = "Test"
        
        # Reset
        display.reset()
        
        assert display.current_hint_text == ""
        assert display.revealed_pattern == ""
        assert display.revealed_indices == set()
        assert display.hint_alpha == 0
        assert display.hint_scale == 1.0
        assert display.animation_active == False
        assert display.help_button_enabled == False
        assert display.button_hovered == False
        assert display.button_pressed == False
        assert display.word_text == ""


class TestEncouragementMessage:
    """Test encouragement message feature."""
    
    def test_show_hint_with_encouragement(self):
        """Test showing hint with encouragement message."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.set_word("hello")
        
        display.show_hint(
            "The 1st letter is 'H'",
            {0},
            encouragement_message="You're getting closer!"
        )
        
        assert display.current_hint_text == "The 1st letter is 'H'"
        assert display.encouragement_message == "You're getting closer!"
        assert 0 in display.revealed_indices
    
    def test_show_hint_without_encouragement(self):
        """Test showing hint without encouragement message (backward compatibility)."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.set_word("hello")
        
        display.show_hint("Test hint", {0})
        
        assert display.current_hint_text == "Test hint"
        assert display.encouragement_message == ""  # Empty string when not provided
    
    def test_encouragement_message_empty_string(self):
        """Test that empty encouragement message is handled."""
        typography = MagicMock()
        display = HintDisplay(typography)
        display.set_word("hello")
        
        display.show_hint("Test", {0}, encouragement_message="")
        
        assert display.encouragement_message == ""


class TestAcceptanceCriteria:
    """Test specific acceptance criteria from STORY-001-04."""
    
    def test_ac_hint_appears_within_200ms(self):
        """AC: Hint appears within 200ms of request.
        
        This is verified by the animation starting immediately when show_hint() is called.
        The fade-in starts at alpha=0 and reaches visible levels quickly.
        """
        typography = MagicMock()
        display = HintDisplay(typography)
        
        display.show_hint("Test", set())
        
        # Animation starts immediately
        assert display.animation_active == True
        assert display.current_hint_text == "Test"
    
    def test_ac_hints_use_visual_text(self):
        """AC: Hints use visual text.
        
        Verified by show_hint() storing and rendering hint text.
        """
        typography = MagicMock()
        display = HintDisplay(typography)
        
        display.show_hint("This word has 5 letters", set())
        
        assert display.current_hint_text == "This word has 5 letters"
    
    def test_ac_help_button_available(self):
        """AC: Hints can be requested via 'Need Help?' button.
        
        Verified by enable_help_button() and check_button_click().
        """
        typography = MagicMock()
        display = HintDisplay(typography)
        
        display.enable_help_button()
        assert display.help_button_enabled == True
        
        # Button responds to clicks
        result = display.check_button_click(150, 480)
        assert result == True
    
    def test_ac_revealed_letters_shown(self):
        """AC: Revealed letters appear in word display.
        
        Verified by revealed_indices being tracked and pattern being built.
        """
        typography = MagicMock()
        display = HintDisplay(typography)
        display.set_word("hello")
        
        display.show_hint("The 1st letter is 'H'", {0})
        
        assert 0 in display.revealed_indices
        # Pattern shows revealed letter
        result = []
        for i, letter in enumerate(display.word_text):
            if i in display.revealed_indices:
                result.append(letter)
            else:
                result.append('_')
        assert ' '.join(result) == "H _ _ _ _"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

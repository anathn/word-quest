"""
Unit tests for InputHandler component.

Tests cover:
- Character input handling
- Backspace functionality
- Submit handling
- Input validation
- State transitions
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.components.input_handler import InputHandler, InputDisplay, InputState, InputEvent


class TestInputHandler(unittest.TestCase):
    """Tests for the InputHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = InputHandler(max_length=5)
        
        # Track callbacks
        self.callback_calls = []
        self.handler.on_input_changed = lambda text: self.callback_calls.append(('input_changed', text))
        self.handler.on_invalid_input = lambda reason: self.callback_calls.append(('invalid', reason))
        self.handler.on_submit = lambda text: self.callback_calls.append(('submit', text))
        self.handler.on_complete = lambda text: self.callback_calls.append(('complete', text))
    
    def test_initial_state(self):
        """Test initial handler state."""
        self.assertEqual(self.handler.get_input(), "")
        self.assertEqual(self.handler.get_input_length(), 0)
        self.assertEqual(self.handler.get_remaining_length(), 5)
        self.assertTrue(self.handler.is_empty())
        self.assertFalse(self.handler.is_complete())
    
    def test_handle_character(self):
        """Test handling character input."""
        event = self.handler.handle_keydown('K_a', 'a')
        
        self.assertEqual(self.handler.get_input(), "a")
        self.assertEqual(self.handler.get_input_length(), 1)
        self.assertEqual(self.handler.get_remaining_length(), 4)
        self.assertEqual(event.event_type, 'char')
        self.assertEqual(event.character, 'a')
    
    def test_handle_character_uppercase(self):
        """Test uppercase characters are converted to lowercase."""
        self.handler.handle_keydown('K_A', 'A')
        self.assertEqual(self.handler.get_input(), "a")
    
    def test_handle_multiple_characters(self):
        """Test handling multiple character inputs."""
        self.handler.handle_keydown('K_a', 'a')
        self.handler.handle_keydown('K_b', 'b')
        self.handler.handle_keydown('K_c', 'c')
        
        self.assertEqual(self.handler.get_input(), "abc")
        self.assertEqual(self.handler.get_input_length(), 3)
    
    def test_handle_backspace(self):
        """Test backspace handling."""
        self.handler.handle_keydown('K_a', 'a')
        self.handler.handle_keydown('K_b', 'b')
        self.handler.handle_keydown('K_BACKSPACE')
        
        self.assertEqual(self.handler.get_input(), "a")
        self.assertEqual(self.handler.get_input_length(), 1)
    
    def test_handle_backspace_empty(self):
        """Test backspace has no effect when empty."""
        event = self.handler.handle_keydown('K_BACKSPACE')
        self.assertIsNone(event)
        self.assertEqual(self.handler.get_input(), "")
    
    def test_handle_delete(self):
        """Test delete key acts like backspace."""
        self.handler.handle_keydown('K_a', 'a')
        self.handler.handle_keydown('K_DELETE')
        self.assertEqual(self.handler.get_input(), "")
    
    def test_handle_submit(self):
        """Test submit handling."""
        self.handler.handle_keydown('K_a', 'a')
        event = self.handler.handle_keydown('K_RETURN')
        
        self.assertEqual(event.event_type, 'submit')
        self.assertEqual(self.handler.state, InputState.SUBMITTED)
    
    def test_handle_submit_enter(self):
        """Test submit with Enter key."""
        self.handler.handle_keydown('K_a', 'a')
        event = self.handler.handle_keydown('K_RETURN')
        self.assertEqual(event.event_type, 'submit')
    
    def test_handle_submit_kp_enter(self):
        """Test submit with numpad enter."""
        self.handler.handle_keydown('K_a', 'a')
        event = self.handler.handle_keydown('K_KP_ENTER')
        self.assertEqual(event.event_type, 'submit')
    
    def test_handle_invalid_character(self):
        """Test invalid characters are rejected."""
        event = self.handler.handle_keydown('K_1', '1')
        
        self.assertEqual(self.handler.get_input(), "")
        self.assertEqual(event.event_type, 'invalid')
        self.assertEqual(event.character, '1')
    
    def test_handle_special_characters(self):
        """Test special characters are rejected."""
        for char in ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')']:
            event = self.handler.handle_keydown('K_UNKNOWN', char)
            self.assertEqual(event.event_type, 'invalid', f"Failed for {char}")
    
    def test_handle_numbers(self):
        """Test numbers are rejected."""
        for char in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
            event = self.handler.handle_keydown('K_UNKNOWN', char)
            self.assertEqual(event.event_type, 'invalid', f"Failed for {char}")
    
    def test_handle_max_length(self):
        """Test input is limited to max length."""
        for char in ['a', 'b', 'c', 'd', 'e']:
            self.handler.handle_keydown('K_UNKNOWN', char)
        
        self.assertTrue(self.handler.is_complete())
        self.assertEqual(self.handler.get_input_length(), 5)
        
        # Try to add more
        event = self.handler.handle_keydown('K_f', 'f')
        self.assertEqual(event.event_type, 'invalid')
        self.assertEqual(self.handler.get_input_length(), 5)
    
    def test_handle_clear(self):
        """Test escape key clears input."""
        self.handler.handle_keydown('K_a', 'a')
        self.handler.handle_keydown('K_b', 'b')
        self.handler.handle_keydown('K_ESCAPE')
        
        self.assertEqual(self.handler.get_input(), "")
        self.assertEqual(self.handler.state, InputState.EMPTY)
    
    def test_handle_virtual_key(self):
        """Test virtual keyboard input."""
        event = self.handler.handle_virtual_key('a')
        
        self.assertEqual(self.handler.get_input(), "a")
        self.assertEqual(event.event_type, 'char')
    
    def test_handle_virtual_backspace(self):
        """Test virtual backspace."""
        self.handler.handle_virtual_key('a')
        self.handler.handle_virtual_key('BACKSPACE')
        self.assertEqual(self.handler.get_input(), "")
    
    def test_handle_virtual_enter(self):
        """Test virtual enter."""
        self.handler.handle_virtual_key('a')
        event = self.handler.handle_virtual_key('ENTER')
        self.assertEqual(event.event_type, 'submit')
    
    def test_handle_virtual_submit(self):
        """Test virtual submit."""
        self.handler.handle_virtual_key('a')
        event = self.handler.handle_virtual_key('SUBMIT')
        self.assertEqual(event.event_type, 'submit')
    
    def test_handle_virtual_clear(self):
        """Test virtual clear."""
        self.handler.handle_virtual_key('a')
        self.handler.handle_virtual_key('CLEAR')
        self.assertEqual(self.handler.get_input(), "")
    
    def test_callbacks_on_input(self):
        """Test callbacks are invoked on input."""
        self.handler.handle_keydown('K_a', 'a')
        
        self.assertIn(('input_changed', 'a'), self.callback_calls)
    
    def test_callbacks_on_complete(self):
        """Test complete callback when max length reached."""
        for char in ['a', 'b', 'c', 'd', 'e']:
            self.handler.handle_keydown('K_UNKNOWN', char)
        
        self.assertIn(('complete', 'abcde'), self.callback_calls)
    
    def test_callbacks_on_submit(self):
        """Test submit callback."""
        self.handler.handle_keydown('K_a', 'a')
        self.handler.handle_keydown('K_RETURN')
        
        self.assertIn(('submit', 'a'), self.callback_calls)
    
    def test_callbacks_on_invalid(self):
        """Test invalid input callback."""
        self.handler.handle_keydown('K_1', '1')
        
        self.assertIn(('invalid', '1'), self.callback_calls)
    
    def test_clear_method(self):
        """Test clear method."""
        self.handler.handle_keydown('K_a', 'a')
        self.handler.handle_keydown('K_b', 'b')
        self.handler.clear()
        
        self.assertEqual(self.handler.get_input(), "")
        self.assertEqual(self.handler.state, InputState.EMPTY)
    
    def test_reset_method(self):
        """Test reset method."""
        self.handler.handle_keydown('K_a', 'a')
        self.handler.handle_keydown('K_b', 'b')
        self.handler.reset()
        
        self.assertEqual(self.handler.get_input(), "")
        self.assertEqual(self.handler.input_history, [])
    
    def test_set_input(self):
        """Test setting input directly."""
        self.handler.set_input("hello")
        self.assertEqual(self.handler.get_input(), "hello")
    
    def test_set_input_sanitizes(self):
        """Test set_input sanitizes invalid characters."""
        self.handler.set_input("hel1o!")
        # Note: digits and symbols are removed
        result = self.handler.get_input()
        self.assertIn('h', result)
        self.assertIn('e', result)
        self.assertIn('l', result)
        self.assertIn('o', result)
        self.assertNotIn('1', result)
        self.assertNotIn('!', result)
    
    def test_set_input_truncates(self):
        """Test set_input truncates to max length."""
        self.handler.set_input("abcdef")
        self.assertEqual(self.handler.get_input(), "abcde")
    
    def test_set_input_case_lower(self):
        """Test set_input converts to lowercase."""
        self.handler.set_input("ABC")
        self.assertEqual(self.handler.get_input(), "abc")
    
    def test_state_transitions(self):
        """Test state transitions during input."""
        self.assertEqual(self.handler.state, InputState.EMPTY)
        
        self.handler.handle_keydown('K_a', 'a')
        self.assertEqual(self.handler.state, InputState.TYPING)
        
        # Fill to max
        for char in ['b', 'c', 'd', 'e']:
            self.handler.handle_keydown('K_UNKNOWN', char)
        self.assertEqual(self.handler.state, InputState.COMPLETE)
        
        # Submit
        self.handler.handle_keydown('K_RETURN')
        self.assertEqual(self.handler.state, InputState.SUBMITTED)


class TestInputDisplay(unittest.TestCase):
    """Tests for the InputDisplay class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.display = InputDisplay(max_length=5, letter_spacing=10)
    
    def test_initial_state(self):
        """Test initial display state."""
        self.assertEqual(self.display.get_display_letters(), [])
        self.assertEqual(self.display.get_placeholder_count(), 5)
    
    def test_set_letters(self):
        """Test setting letters."""
        self.display.set_letters(['a', 'b', 'c'])
        self.assertEqual(self.display.get_display_letters(), ['a', 'b', 'c'])
    
    def test_add_letter(self):
        """Test adding a letter."""
        self.display.add_letter('a')
        self.assertEqual(self.display.get_display_letters(), ['a'])
        
        self.display.add_letter('b')
        self.assertEqual(self.display.get_display_letters(), ['a', 'b'])
    
    def test_add_letter_max_length(self):
        """Test adding letter at max length."""
        for char in ['a', 'b', 'c', 'd', 'e']:
            self.display.add_letter(char)
        
        self.display.add_letter('f')  # Should be ignored
        self.assertEqual(len(self.display.get_display_letters()), 5)
    
    def test_remove_letter(self):
        """Test removing a letter."""
        self.display.set_letters(['a', 'b', 'c'])
        self.display.remove_letter()
        self.assertEqual(self.display.get_display_letters(), ['a', 'b'])
    
    def test_remove_letter_empty(self):
        """Test removing letter when empty."""
        self.display.remove_letter()  # Should not error
        self.assertEqual(self.display.get_display_letters(), [])
    
    def test_clear(self):
        """Test clearing display."""
        self.display.set_letters(['a', 'b', 'c'])
        self.display.clear()
        self.assertEqual(self.display.get_display_letters(), [])
    
    def test_placeholder_count(self):
        """Test placeholder count calculation."""
        self.assertEqual(self.display.get_placeholder_count(), 5)
        
        self.display.add_letter('a')
        self.assertEqual(self.display.get_placeholder_count(), 4)
        
        self.display.add_letter('b')
        self.assertEqual(self.display.get_placeholder_count(), 3)
    
    def test_update_cursor_blink(self):
        """Test cursor blink update."""
        initial_visible = self.display.is_cursor_visible()
        
        # Simulate time passing
        self.display.update(current_time=1.0)
        
        # Cursor state may have changed
        self.assertIsInstance(self.display.is_cursor_visible(), bool)
    
    def test_convert_to_lowercase(self):
        """Test letters are converted to lowercase."""
        self.display.add_letter('A')
        self.assertEqual(self.display.get_display_letters(), ['a'])


class TestInputEvent(unittest.TestCase):
    """Tests for the InputEvent dataclass."""
    
    def test_event_creation(self):
        """Test event creation."""
        event = InputEvent(event_type='char', character='a')
        self.assertEqual(event.event_type, 'char')
        self.assertEqual(event.character, 'a')
        self.assertIsNotNone(event.timestamp)
    
    def test_event_without_character(self):
        """Test event without character."""
        event = InputEvent(event_type='submit')
        self.assertIsNone(event.character)


class TestFactoryFunction(unittest.TestCase):
    """Tests for factory functions."""
    
    def test_create_input_handler(self):
        """Test create_input_handler function."""
        from src.components.input_handler import create_input_handler
        
        handler = create_input_handler(max_length=10)
        self.assertIsInstance(handler, InputHandler)
        self.assertEqual(handler.max_length, 10)


if __name__ == '__main__':
    unittest.main()

"""
Unit tests for SpellingChallengeScreen component.

Tests cover:
- Word presentation flow
- Starter letter handling
- Input validation
- Answer checking
- State transitions
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.screens.spelling_challenge import (
    SpellingChallengeScreen,
    ChallengeState,
    WordPresentation,
    HintRenderer,
    create_spelling_challenge_screen
)
from src.components.word_manager import SpellingWord


class MockAudioSystem:
    """Mock audio system for testing."""
    
    def __init__(self):
        self.speak_calls = []
        self.audio_available = True
    
    def speak(self, text, on_complete=None):
        self.speak_calls.append(text)
        # Simulate immediate completion
        if on_complete:
            on_complete()
        return True
    
    def is_audio_available(self):
        return self.audio_available
    
    def stop(self):
        pass


class MockTypography:
    """Mock typography for testing."""
    
    def __init__(self):
        self.render_calls = []
    
    def render_text(self, text, style):
        self.render_calls.append((text, style))
        return MagicMock()
    
    def measure_text(self, text, style):
        return (len(text) * 10, 30)  # Approximate
    
    @property
    def style_starter_letters(self):
        return MagicMock()
    
    @property
    def style_word_display(self):
        return MagicMock()
    
    @property
    def style_definition(self):
        return MagicMock()


class MockWordManager:
    """Mock word manager for testing."""
    
    def __init__(self):
        self.words = [
            SpellingWord("w001", "because", "reason", "because clause", 1, 3),
            SpellingWord("w002", "friend", "pal", "my friend", 1, 3),
            SpellingWord("w003", "beautiful", "pretty", "beautiful day", 2, 2),
            SpellingWord("w004", "accomplish", "achieve", "accomplish goal", 3, 1),
        ]
    
    def get_word_by_id(self, word_id):
        for word in self.words:
            if word.id == word_id:
                return word
        return None
    
    def get_random_word(self):
        import random
        return random.choice(self.words)


class TestSpellingChallengeScreen(unittest.TestCase):
    """Tests for the SpellingChallengeScreen class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.word_manager = MockWordManager()
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        
        self.screen = SpellingChallengeScreen(
            word_manager=self.word_manager,
            audio_system=self.audio_system,
            typography=self.typography
        )
        
        # Track callback invocations
        self.callback_called = False
        self.callback_data = None
    
    def on_word_presented(self, presentation):
        self.callback_called = True
        self.callback_data = presentation
    
    def on_input_changed(self, input_text):
        self.callback_called = True
        self.callback_data = input_text
    
    def on_submit(self, is_correct, answer):
        self.callback_called = True
        self.callback_data = (is_correct, answer)
    
    def test_initial_state(self):
        """Test screen starts in IDLE state."""
        self.assertEqual(self.screen.state, ChallengeState.IDLE)
        self.assertIsNone(self.screen.current_word)
        self.assertIsNone(self.screen.input_handler)
    
    def test_present_word_basic(self):
        """Test basic word presentation."""
        word = self.word_manager.get_word_by_id("w001")  # because
        self.screen.present_word(word)
        
        self.assertEqual(self.screen.state, ChallengeState.READY_FOR_INPUT)
        self.assertEqual(self.screen.current_word.text, "because")
        self.assertEqual(self.screen.starter_letters, ['b', 'e', 'c'])
    
    def test_present_word_audio_called(self):
        """Test that audio is spoken when presenting word."""
        word = self.word_manager.get_word_by_id("w001")
        self.screen.present_word(word)
        
        self.assertEqual(len(self.audio_system.speak_calls), 1)
        self.assertEqual(self.audio_system.speak_calls[0], "because")
    
    def test_present_word_callback(self):
        """Test that on_word_presented callback is invoked."""
        word = self.word_manager.get_word_by_id("w001")
        self.screen.on_word_presented = self.on_word_presented
        self.screen.present_word(word)
        
        self.assertTrue(self.callback_called)
        self.assertIsInstance(self.callback_data, WordPresentation)
        self.assertEqual(self.callback_data.word_text, "because")
    
    def test_present_word_starter_letters_by_difficulty(self):
        """Test starter letters vary by difficulty."""
        # Difficulty 1: 3 starter letters
        word1 = self.word_manager.get_word_by_id("w001")  # because
        self.screen.present_word(word1)
        self.assertEqual(''.join(self.screen.starter_letters), "bec")
        
        # Difficulty 2: 2 starter letters
        word2 = self.word_manager.get_word_by_id("w003")  # beautiful
        self.screen.present_word(word2)
        self.assertEqual(''.join(self.screen.starter_letters), "be")
        
        # Difficulty 3: 1 starter letter
        word3 = self.word_manager.get_word_by_id("w004")  # accomplish
        self.screen.present_word(word3)
        self.assertEqual(''.join(self.screen.starter_letters), "a")
    
    def test_replay_audio(self):
        """Test audio replay functionality."""
        word = self.word_manager.get_word_by_id("w001")
        self.screen.present_word(word)
        
        initial_calls = len(self.audio_system.speak_calls)
        self.screen.replay_audio()
        
        self.assertEqual(len(self.audio_system.speak_calls), initial_calls + 1)
    
    def test_handle_key_input(self):
        """Test handling key input."""
        word = self.word_manager.get_word_by_id("w001")
        self.screen.present_word(word)
        
        self.screen.handle_key_input('K_a', 'a')
        self.assertEqual(self.screen.get_current_input(), "a")
        
        self.screen.handle_key_input('K_u', 'u')
        self.assertEqual(self.screen.get_current_input(), "au")
    
    def test_handle_key_input_case_insensitive(self):
        """Test that input is converted to lowercase."""
        word = self.word_manager.get_word_by_id("w001")
        self.screen.present_word(word)
        
        self.screen.handle_key_input('K_A', 'A')
        self.assertEqual(self.screen.get_current_input(), "a")
    
    def test_handle_backspace(self):
        """Test backspace handling."""
        word = self.word_manager.get_word_by_id("w001")
        self.screen.present_word(word)
        
        self.screen.handle_key_input('K_a', 'a')
        self.screen.handle_key_input('K_u', 'u')
        self.assertEqual(self.screen.get_current_input(), "au")
        
        self.screen.handle_backspace()
        self.assertEqual(self.screen.get_current_input(), "a")
        
        self.screen.handle_backspace()
        self.assertEqual(self.screen.get_current_input(), "")
    
    def test_backspace_when_empty(self):
        """Test backspace has no effect when input is empty."""
        word = self.word_manager.get_word_by_id("w001")
        self.screen.present_word(word)
        
        self.screen.handle_backspace()
        self.assertEqual(self.screen.get_current_input(), "")
    
    def test_get_full_answer(self):
        """Test getting the complete answer."""
        word = self.word_manager.get_word_by_id("w001")  # because
        self.screen.present_word(word)
        
        self.screen.handle_key_input('K_a', 'a')
        self.screen.handle_key_input('K_u', 'u')
        self.screen.handle_key_input('K_s', 's')
        self.screen.handle_key_input('K_e', 'e')
        
        self.assertEqual(self.screen.get_full_answer(), "because")
    
    def test_submit_correct_answer(self):
        """Test submitting a correct answer."""
        word = self.word_manager.get_word_by_id("w001")  # because
        self.screen.present_word(word)
        
        # Type remaining letters
        for char in "ause":
            self.screen.handle_key_input(f'K_{char}', char)
        
        is_correct, answer = self.screen.submit_answer()
        
        self.assertTrue(is_correct)
        self.assertEqual(answer, "because")
    
    def test_submit_incorrect_answer(self):
        """Test submitting an incorrect answer."""
        word = self.word_manager.get_word_by_id("w001")  # because
        self.screen.present_word(word)
        
        # Type wrong letters
        for char in "xyz":
            self.screen.handle_key_input(f'K_{char}', char)
        
        is_correct, answer = self.screen.submit_answer()
        
        self.assertFalse(is_correct)
        self.assertEqual(answer, "becxyz")
    
    def test_submit_callback(self):
        """Test that on_submit callback is invoked."""
        word = self.word_manager.get_word_by_id("w001")
        self.screen.present_word(word)
        
        self.screen.on_submit = self.on_submit
        
        # Type and submit
        for char in "ause":
            self.screen.handle_key_input(f'K_{char}', char)
        
        self.screen.submit_answer()
        
        self.assertTrue(self.callback_called)
        self.assertEqual(self.callback_data, (True, "because"))
    
    def test_get_word_text(self):
        """Test getting the target word text."""
        word = self.word_manager.get_word_by_id("w001")
        self.screen.present_word(word)
        
        self.assertEqual(self.screen.get_word_text(), "because")
    
    def test_get_definition(self):
        """Test getting the word definition."""
        word = self.word_manager.get_word_by_id("w001")
        self.screen.present_word(word)
        
        self.assertEqual(self.screen.get_definition(), "reason")
    
    def test_get_context_sentence(self):
        """Test getting the context sentence."""
        word = self.word_manager.get_word_by_id("w001")
        self.screen.present_word(word)
        
        self.assertEqual(self.screen.get_context_sentence(), "because clause")
    
    def test_reset(self):
        """Test resetting the screen."""
        word = self.word_manager.get_word_by_id("w001")
        self.screen.present_word(word)
        
        # Add some input
        self.screen.handle_key_input('K_a', 'a')
        
        # Reset
        self.screen.reset()
        
        self.assertEqual(self.screen.state, ChallengeState.IDLE)
        self.assertIsNone(self.screen.current_word)
        self.assertIsNone(self.screen.input_handler)
    
    def test_state_transitions(self):
        """Test state transitions during gameplay."""
        word = self.word_manager.get_word_by_id("w001")
        
        # Start
        self.assertEqual(self.screen.state, ChallengeState.IDLE)
        
        # Present word (async -> READY_FOR_INPUT)
        self.screen.present_word(word)
        self.assertEqual(self.screen.state, ChallengeState.READY_FOR_INPUT)
        
        # Submit answer
        self.screen.submit_answer()
        self.assertEqual(self.screen.state, ChallengeState.AWAITING_RESPONSE)
    
    def test_input_blocked_in_wrong_state(self):
        """Test that input is ignored in non-READY states."""
        # Try to input before presenting word
        self.screen.handle_key_input("a")
        self.assertEqual(self.screen.get_current_input(), "")
    
    def test_audio_available_check(self):
        """Test audio availability check."""
        self.assertTrue(self.screen.is_audio_available())
        
        # Test with audio disabled
        self.audio_system.audio_available = False
        self.assertFalse(self.screen.is_audio_available())


class TestHintRenderer(unittest.TestCase):
    """Tests for the HintRenderer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.typography = MockTypography()
        self.renderer = HintRenderer(self.typography)
    
    def test_render_starter_hint(self):
        """Test rendering a single hint."""
        result = self.renderer.render_starter_hint("b", (100, 200))
        
        # Should call typography to render
        self.assertIsNotNone(result)
    
    def test_render_hidden_hint(self):
        """Test that hidden hints return None."""
        result = self.renderer.render_starter_hint("b", (100, 200), is_revealed=False)
        self.assertIsNone(result)
    
    def test_render_starter_hints(self):
        """Test rendering multiple hints in a row."""
        rendered = self.renderer.render_starter_hints("bec", (100, 200))
        
        self.assertEqual(len(rendered), 3)
        
        # Check positions increment
        self.assertEqual(rendered[0][1][0], 100)  # First at x=100


class TestCreateSpellingChallengeScreen(unittest.TestCase):
    """Tests for the factory function."""
    
    def test_create_with_mocks(self):
        """Test creating screen with mock dependencies."""
        word_manager = MockWordManager()
        audio_system = MockAudioSystem()
        typography = MockTypography()
        
        screen = create_spelling_challenge_screen(
            word_manager=word_manager,
            audio_system=audio_system,
            typography=typography
        )
        
        self.assertIsInstance(screen, SpellingChallengeScreen)
        self.assertEqual(screen.word_manager, word_manager)
        self.assertEqual(screen.audio_system, audio_system)
        self.assertEqual(screen.typography, typography)


class TestPerformanceTracking(unittest.TestCase):
    """Tests for performance tracking features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.word_manager = MockWordManager()
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        
        self.screen = SpellingChallengeScreen(
            word_manager=self.word_manager,
            audio_system=self.audio_system,
            typography=self.typography
        )
    
    def test_performance_stats_empty(self):
        """Test performance stats when no renders yet."""
        stats = self.screen.get_performance_stats()
        self.assertEqual(stats["avg_ms"], 0)
        self.assertEqual(stats["max_ms"], 0)
    
    def test_performance_stats_after_presentation(self):
        """Test performance stats after word presentations."""
        word = self.word_manager.get_word_by_id("w001")
        
        # Present multiple words
        for _ in range(5):
            self.screen.present_word(word)
        
        stats = self.screen.get_performance_stats()
        
        self.assertEqual(stats["sample_count"], 5)
        self.assertGreater(stats["avg_ms"], 0)
        self.assertGreater(stats["max_ms"], 0)
        self.assertGreater(stats["min_ms"], 0)
        self.assertLessEqual(stats["min_ms"], stats["avg_ms"])
        self.assertGreaterEqual(stats["max_ms"], stats["avg_ms"])


if __name__ == '__main__':
    unittest.main()

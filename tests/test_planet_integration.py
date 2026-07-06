"""
Integration tests for the Planet completion flow.

These tests verify the interaction between:
- PlanetManager: Manages the word set and mastery logic.
- ProgressTracker: Tracks analytics and session data.
- SpellingChallengeScreen: Handles word presentation and user input.
"""

import unittest
from unittest.mock import Mock, MagicMock
from src.components.planet_manager import PlanetManager, PlanetStatus, create_planet_manager
from src.components.progress_tracker import ProgressTracker, create_progress_tracker
from src.components.word_manager import SpellingWord
from src.screens.spelling_challenge import SpellingChallengeScreen

class MockAudioSystem:
    def speak(self, text, on_complete=None):
        if on_complete: on_complete()
        return True
    def is_audio_available(self): return True
    def stop(self): pass

class MockTypography:
    def render_text(self, text, style): return MagicMock()
    def measure_text(self, text, style): return (10, 10)
    @property
    def style_starter_letters(self): return MagicMock()
    @property
    def style_word_display(self): return MagicMock()
    @property
    def style_definition(self): return MagicMock()

class MockWordManager:
    def __init__(self, words):
        self.words = words
    def get_word_by_id(self, word_id):
        return next((w for w in self.words if w.id == word_id), None)

class TestPlanetIntegration(unittest.TestCase):
    def setUp(self):
        # Setup words for a planet
        self.mock_words = [
            SpellingWord(f"w{i}", f"word{i}", f"def{i}", f"ctx{i}", 1, 3)
            for i in range(5)
        ]
        
        self.planet_id = "planet-1"
        self.planet_name = "Mercury"
        
        self.planet_manager = create_planet_manager(
            self.planet_id, self.planet_name, self.mock_words
        )
        
        self.progress_tracker = create_progress_tracker()
        self.progress_tracker.start_session("session-1")
        self.progress_tracker.start_planet(self.planet_id, self.planet_name)
        
        self.word_manager = MockWordManager(self.mock_words)
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        
        self.challenge_screen = SpellingChallengeScreen(
            word_manager=self.word_manager,
            audio_system=self.audio_system,
            typography=self.typography
        )

    def simulate_word_attempt(self, word, correct=True, attempts=1):
        """Simulates the full flow for a single word."""
        # 1. Present word
        self.challenge_screen.present_word(word)
        
        # 2. Simulate typing (if correct, type the word, else type gibberish)
        if correct:
            for char in word.text:
                self.challenge_screen.handle_key_input(f'K_{char}', char)
        else:
            for char in "wrong":
                self.challenge_screen.handle_key_input(f'K_{char}', char)
        
        # 3. Submit
        is_correct, answer = self.challenge_screen.submit_answer()
        
        # 4. Record results in PlanetManager
        self.planet_manager.record_word_result(
            word.id, word.text, is_correct, attempts
        )
        
        # 5. Record results in ProgressTracker
        self.progress_tracker.record_planet_word_result(
            word.id, word.text, is_correct, attempts
        )
        
        return is_correct

    def test_full_planet_completion_flow_success(self):
        """Test 1: Full planet flow: 5 words -> results -> next action."""
        # Simulate 5 correct words on first attempt
        for i in range(5):
            word = self.planet_manager.get_current_word()
            self.simulate_word_attempt(word, correct=True, attempts=1)
            self.planet_manager.get_next_word()
            
        self.assertTrue(self.planet_manager.is_complete)
        status = self.planet_manager.get_completion_status()
        self.assertEqual(status.status, PlanetStatus.COMPLETED)
        self.assertTrue(status.unlock_next)

    def test_callback_chain_integration(self):
        """Test 2: Callback chain verification."""
        callback_mock = Mock()
        self.planet_manager.on_planet_complete = callback_mock
        
        # Complete the planet
        for i in range(5):
            word = self.planet_manager.get_current_word()
            self.simulate_word_attempt(word)
            self.planet_manager.get_next_word()
            
        self.assertTrue(callback_mock.called)
        result = callback_mock.call_args[0][0]
        self.assertEqual(result.planet_id, self.planet_id)
        self.assertEqual(result.status, PlanetStatus.COMPLETED)

    def test_retry_flow_with_same_words(self):
        """Test 3: Retry restarts with same words."""
        # First attempt: fail the planet
        for i in range(5):
            word = self.planet_manager.get_current_word()
            self.simulate_word_attempt(word, correct=False, attempts=2)
            self.planet_manager.get_next_word()
            
        status = self.planet_manager.get_completion_status()
        self.assertEqual(status.status, PlanetStatus.NEEDS_HELP)
        
        # Reset and retry
        self.planet_manager.reset()
        self.planet_manager.shuffle_words()
        
        self.assertFalse(self.planet_manager.is_complete)
        self.assertEqual(len(self.planet_manager.words), 5)
        # Verify words are still the same set
        self.assertEqual(set([w.text for w in self.planet_manager.words]), 
                         set([w.text for w in self.mock_words]))

    def test_progress_saved_after_each_word(self):
        """Test 4: Progress saved correctly after each word."""
        word = self.planet_manager.get_current_word()
        self.simulate_word_attempt(word, correct=True, attempts=1)
        
        self.assertEqual(len(self.planet_manager.word_results), 1)
        self.assertEqual(len(self.progress_tracker.planet_word_results), 1)
        self.assertEqual(self.planet_manager.get_words_remaining(), 4)

    def test_state_transitions_across_multiple_planets(self):
        """Test 5: State transitions across Multiple planets."""
        # Planet 1
        for i in range(5):
            word = self.planet_manager.get_current_word()
            self.simulate_word_attempt(word)
            self.planet_manager.get_next_word()
        
        self.assertTrue(self.planet_manager.is_complete)
        
        # Transition to Planet 2
        planet2_id = "planet-2"
        planet2_name = "Venus"
        planet2_words = [SpellingWord(f"p2w{i}", f"vword{i}", f"dv{i}", f"cv{i}", 1, 3) for i in range(5)]
        
        self.planet_manager = create_planet_manager(planet2_id, planet2_name, planet2_words)
        self.progress_tracker.start_planet(planet2_id, planet2_name)
        
        self.assertFalse(self.planet_manager.is_complete)
        self.assertEqual(self.planet_manager.planet_id, planet2_id)

    def test_integration_with_progress_tracker(self):
        """Test 6: Integration with ProgressTracker mastery logic."""
        # Simulate 3/5 correct on first attempt, 2 incorrect (needs HELP threshold)
        for i in range(5):
            word = self.planet_manager.get_current_word()
            is_correct = (i < 3)
            # Only first 3 are correct on first attempt; last 2 are incorrect with multiple attempts
            attempts = 1 if is_correct else 2
            self.simulate_word_attempt(word, correct=is_correct, attempts=attempts)
            self.planet_manager.get_next_word()
            
        # Progress tracker should have processed this
        # Note: ProgressTracker._complete_planet is called automatically when 5 words are recorded
        
        # Verify session data
        session = self.progress_tracker.current_session
        self.assertEqual(len(session.planets_completed), 1)
        planet_data = session.planets_completed[0]
        self.assertEqual(planet_data.first_attempt_correct, 3)
        self.assertEqual(planet_data.planet_id, self.planet_id)

if __name__ == '__main__':
    unittest.main()

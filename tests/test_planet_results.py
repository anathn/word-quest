"""
Unit tests for PlanetResultsScreen component.

Tests cover:
- Title text for each status (COMPLETED/RETRY/NEEDS_HELP)
- Summary text formatting
- Button text and color selection
- Callback invocation on button click
- Audio playback triggers
- Performance timing
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.screens.planet_results import (
    PlanetResultsScreen,
    ResultsState,
    WordResultDisplay,
    create_planet_results_screen
)
from src.components.planet_manager import PlanetManager, PlanetStatus, PlanetResult


class MockAudioSystem:
    """Mock audio system for testing."""
    
    def __init__(self):
        self.speak_calls = []
        self.audio_available = True
        self.victory_played = False
        self.encouraging_played = False
        self.gentle_played = False
    
    def speak(self, text, on_complete=None):
        self.speak_calls.append(text)
        if on_complete:
            on_complete()
        return True
    
    def is_audio_available(self):
        return self.audio_available
    
    def stop(self):
        pass
    
    def play_victory_fanfare(self):
        self.victory_played = True
    
    def play_encouraging_tone(self):
        self.encouraging_played = True
    
    def play_gentle_tone(self):
        self.gentle_played = True


class MockTypography:
    """Mock typography for testing."""
    
    def __init__(self):
        self.render_calls = []
    
    def render_text(self, text, style):
        self.render_calls.append((text, style))
        return MagicMock()
    
    def measure_text(self, text, style):
        return (len(text) * 10, 30)


class MockPlanetResult:
    """Mock PlanetResult for testing."""
    
    def __init__(self, status, first_attempt_correct=0):
        self.planet_id = "planet-1"
        self.planet_name = "Mercury"
        self.total_words = 5
        self.correct_words = first_attempt_correct
        self.first_attempt_correct = first_attempt_correct
        self.status = status
        self.notify_parent = status == PlanetStatus.NEEDS_HELP
        self.unlock_next = status == PlanetStatus.COMPLETED
        self.word_results = []


class TestPlanetResultsScreenInit(unittest.TestCase):
    """Tests for PlanetResultsScreen initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
    
    def test_initial_state(self):
        """Test screen starts in IDLE state."""
        self.assertEqual(self.screen.state, ResultsState.IDLE)
        self.assertIsNone(self.screen.planet_result)
        self.assertEqual(len(self.screen.word_displays), 0)
    
    def test_initial_callbacks(self):
        """Test callbacks are None initially."""
        self.assertIsNone(self.screen.on_continue)
        self.assertIsNone(self.screen.on_retry)
        self.assertIsNone(self.screen.on_practice)
    
    def test_initial_positions(self):
        """Test UI element positions are set."""
        self.assertEqual(self.screen.title_position, (400, 100))
        self.assertEqual(self.screen.results_position, (400, 250))
        self.assertEqual(self.screen.button_position, (400, 500))


class TestShowResults(unittest.TestCase):
    """Tests for show_results method."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
    
    def test_show_results_sets_state(self):
        """Test that show_results changes state to SHOWING_RESULTS then AWAITING_ACTION."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        
        self.screen.show_results(mock_result)
        
        self.assertEqual(self.screen.state, ResultsState.AWAITING_ACTION)
        self.assertIsNotNone(self.screen.planet_result)
    
    def test_show_results_builds_word_displays(self):
        """Test that word displays are created."""
        # Create a mock result with word results
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED, first_attempt_correct=5)
        mock_result.word_results = [
            Mock(word_text="because", correct=True, attempts=1, first_attempt=True),
            Mock(word_text="friend", correct=True, attempts=1, first_attempt=True),
        ]
        
        self.screen.show_results(mock_result)
        
        self.assertEqual(len(self.screen.word_displays), 2)
        self.assertEqual(self.screen.word_displays[0].word_text, "because")
        self.assertTrue(self.screen.word_displays[0].is_mastered)
    
    def test_show_results_plays_victory_audio(self):
        """Test that COMPLETED status plays victory fanfare."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        
        self.screen.show_results(mock_result)
        
        self.assertTrue(self.audio_system.victory_played)
        self.assertTrue(len(self.audio_system.speak_calls) > 0)
    
    def test_show_results_plays_encouraging_audio(self):
        """Test that RETRY status plays encouraging tone."""
        self.audio_system = MockAudioSystem()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
        
        mock_result = MockPlanetResult(PlanetStatus.RETRY, first_attempt_correct=3)
        
        self.screen.show_results(mock_result)
        
        self.assertTrue(self.audio_system.encouraging_played)
    
    def test_show_results_plays_gentle_audio(self):
        """Test that NEEDS_HELP status plays gentle tone."""
        self.audio_system = MockAudioSystem()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
        
        mock_result = MockPlanetResult(PlanetStatus.NEEDS_HELP, first_attempt_correct=1)
        
        self.screen.show_results(mock_result)
        
        self.assertTrue(self.audio_system.gentle_played)


class TestGetTitleText(unittest.TestCase):
    """Tests for get_title_text method."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
    
    def test_title_completed(self):
        """Test title for COMPLETED status."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        title = self.screen.get_title_text()
        
        self.assertEqual(title, "Planet Complete!")
    
    def test_title_retry(self):
        """Test title for RETRY status."""
        mock_result = MockPlanetResult(PlanetStatus.RETRY)
        self.screen.show_results(mock_result)
        
        title = self.screen.get_title_text()
        
        self.assertEqual(title, "Good Effort!")
    
    def test_title_needs_help(self):
        """Test title for NEEDS_HELP status."""
        mock_result = MockPlanetResult(PlanetStatus.NEEDS_HELP)
        self.screen.show_results(mock_result)
        
        title = self.screen.get_title_text()
        
        self.assertEqual(title, "Let's Practice More")
    
    def test_title_no_result(self):
        """Test title when no result is set."""
        title = self.screen.get_title_text()
        
        self.assertEqual(title, "")


class TestGetSummaryText(unittest.TestCase):
    """Tests for get_summary_text method."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
    
    def test_summary_completed(self):
        """Test summary for COMPLETED status."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED, first_attempt_correct=4)
        self.screen.show_results(mock_result)
        
        summary = self.screen.get_summary_text()
        
        self.assertIn("4", summary)
        self.assertIn("5", summary)
        self.assertIn("mastered", summary.lower())
    
    def test_summary_retry(self):
        """Test summary for RETRY status."""
        mock_result = MockPlanetResult(PlanetStatus.RETRY, first_attempt_correct=3)
        self.screen.show_results(mock_result)
        
        summary = self.screen.get_summary_text()
        
        self.assertIn("3", summary)
        self.assertIn("5", summary)
    
    def test_summary_needs_help(self):
        """Test summary for NEEDS_HELP status."""
        mock_result = MockPlanetResult(PlanetStatus.NEEDS_HELP, first_attempt_correct=1)
        self.screen.show_results(mock_result)
        
        summary = self.screen.get_summary_text()
        
        self.assertIn("1", summary)
        self.assertIn("5", summary)
        self.assertIn("practice", summary.lower())


class TestActionButton(unittest.TestCase):
    """Tests for action button methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
    
    def test_button_text_completed(self):
        """Test button text for COMPLETED status."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        button_text = self.screen.get_action_button_text()
        
        self.assertEqual(button_text, "Continue to Next Planet")
    
    def test_button_text_retry(self):
        """Test button text for RETRY status."""
        mock_result = MockPlanetResult(PlanetStatus.RETRY)
        self.screen.show_results(mock_result)
        
        button_text = self.screen.get_action_button_text()
        
        self.assertEqual(button_text, "Try Again")
    
    def test_button_text_needs_help(self):
        """Test button text for NEEDS_HELP status."""
        mock_result = MockPlanetResult(PlanetStatus.NEEDS_HELP)
        self.screen.show_results(mock_result)
        
        button_text = self.screen.get_action_button_text()
        
        self.assertEqual(button_text, "Practice More")
    
    def test_button_color_completed(self):
        """Test button color for COMPLETED status (green)."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        color = self.screen.get_action_button_color()
        
        self.assertEqual(color, (34, 139, 34))  # Forest green
    
    def test_button_color_retry(self):
        """Test button color for RETRY status (orange)."""
        mock_result = MockPlanetResult(PlanetStatus.RETRY)
        self.screen.show_results(mock_result)
        
        color = self.screen.get_action_button_color()
        
        self.assertEqual(color, (255, 140, 0))  # Dark orange
    
    def test_button_color_needs_help(self):
        """Test button color for NEEDS_HELP status (blue)."""
        mock_result = MockPlanetResult(PlanetStatus.NEEDS_HELP)
        self.screen.show_results(mock_result)
        
        color = self.screen.get_action_button_color()
        
        self.assertEqual(color, (30, 144, 255))  # Dodger blue


class TestCallbackInvocation(unittest.TestCase):
    """Tests for callback invocation on button click."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
    
    def test_callback_continue_invoked(self):
        """Test that on_continue callback is invoked for COMPLETED."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        callback_invoked = False
        self.screen.on_continue = lambda: setattr(self, 'callback_invoked', True)
        
        self.screen.handle_action_button_click()
        
        self.assertTrue(self.callback_invoked)
    
    def test_callback_retry_invoked(self):
        """Test that on_retry callback is invoked for RETRY."""
        self.audio_system = MockAudioSystem()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
        
        mock_result = MockPlanetResult(PlanetStatus.RETRY)
        self.screen.show_results(mock_result)
        
        self.screen.on_retry = lambda: setattr(self, 'callback_invoked', True)
        
        self.screen.handle_action_button_click()
        
        self.assertTrue(self.callback_invoked)
    
    def test_callback_practice_invoked(self):
        """Test that on_practice callback is invoked for NEEDS_HELP."""
        self.audio_system = MockAudioSystem()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
        
        mock_result = MockPlanetResult(PlanetStatus.NEEDS_HELP)
        self.screen.show_results(mock_result)
        
        self.screen.on_practice = lambda: setattr(self, 'callback_invoked', True)
        
        self.screen.handle_action_button_click()
        
        self.assertTrue(self.callback_invoked)
    
    def test_no_callback_when_none_set(self):
        """Test that no error occurs when callbacks are None."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        # Should not raise
        self.screen.handle_action_button_click()


class TestStatusCheckMethods(unittest.TestCase):
    """Tests for status check helper methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
    
    def test_is_mastered_true(self):
        """Test is_mastered returns True for COMPLETED."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        self.assertTrue(self.screen.is_mastered())
    
    def test_is_mastered_false(self):
        """Test is_mastered returns False for RETRY."""
        mock_result = MockPlanetResult(PlanetStatus.RETRY)
        self.screen.show_results(mock_result)
        
        self.assertFalse(self.screen.is_mastered())
    
    def test_needs_retry_true(self):
        """Test needs_retry returns True for RETRY."""
        mock_result = MockPlanetResult(PlanetStatus.RETRY)
        self.screen.show_results(mock_result)
        
        self.assertTrue(self.screen.needs_retry())
    
    def test_needs_retry_false(self):
        """Test needs_retry returns False for COMPLETED."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        self.assertFalse(self.screen.needs_retry())
    
    def test_needs_help_true(self):
        """Test needs_help returns True for NEEDS_HELP."""
        mock_result = MockPlanetResult(PlanetStatus.NEEDS_HELP)
        self.screen.show_results(mock_result)
        
        self.assertTrue(self.screen.needs_help())
    
    def test_needs_help_false(self):
        """Test needs_help returns False for RETRY."""
        mock_result = MockPlanetResult(PlanetStatus.RETRY)
        self.screen.show_results(mock_result)
        
        self.assertFalse(self.screen.needs_help())
    
    def test_should_unlock_next_true(self):
        """Test should_unlock_next returns True for COMPLETED."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        self.assertTrue(self.screen.should_unlock_next())
    
    def test_should_unlock_next_false(self):
        """Test should_unlock_next returns False for RETRY."""
        mock_result = MockPlanetResult(PlanetStatus.RETRY)
        self.screen.show_results(mock_result)
        
        self.assertFalse(self.screen.should_unlock_next())
    
    def test_should_notify_parent_true(self):
        """Test should_notify_parent returns True for NEEDS_HELP."""
        mock_result = MockPlanetResult(PlanetStatus.NEEDS_HELP)
        self.screen.show_results(mock_result)
        
        self.assertTrue(self.screen.should_notify_parent())
    
    def test_should_notify_parent_false(self):
        """Test should_notify_parent returns False for COMPLETED."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        self.assertFalse(self.screen.should_notify_parent())


class TestProgressAndDisplay(unittest.TestCase):
    """Tests for progress and display methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
    
    def test_get_progress_percent(self):
        """Test progress percentage calculation."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED, first_attempt_correct=4)
        self.screen.show_results(mock_result)
        
        percent = self.screen.get_progress_percent()
        
        self.assertEqual(percent, 0.8)  # 4/5 = 80%
    
    def test_get_progress_percent_zero(self):
        """Test progress percentage when no words mastered."""
        mock_result = MockPlanetResult(PlanetStatus.NEEDS_HELP, first_attempt_correct=0)
        self.screen.show_results(mock_result)
        
        percent = self.screen.get_progress_percent()
        
        self.assertEqual(percent, 0.0)
    
    def test_get_word_results_display(self):
        """Test getting word results for display."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        mock_result.word_results = [
            Mock(word_text="because", correct=True, attempts=1, first_attempt=True),
        ]
        self.screen.show_results(mock_result)
        
        displays = self.screen.get_word_results_display()
        
        self.assertEqual(len(displays), 1)
        self.assertEqual(displays[0].word_text, "because")


class TestReset(unittest.TestCase):
    """Tests for reset method."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
    
    def test_reset_clears_result(self):
        """Test that reset clears planet_result."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        self.screen.reset()
        
        self.assertIsNone(self.screen.planet_result)
    
    def test_reset_clears_word_displays(self):
        """Test that reset clears word_displays."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        self.screen.reset()
        
        self.assertEqual(len(self.screen.word_displays), 0)
    
    def test_reset_returns_to_idle(self):
        """Test that reset returns state to IDLE."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        self.screen.reset()
        
        self.assertEqual(self.screen.state, ResultsState.IDLE)
    
    def test_reset_clears_timestamp(self):
        """Test that reset clears results_start_time."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        start_time = self.screen.results_start_time
        
        self.screen.reset()
        
        self.assertEqual(self.screen.results_start_time, 0)


class TestUpdate(unittest.TestCase):
    """Tests for update method."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
    
    def test_update_no_error(self):
        """Test that update runs without error."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        # Should not raise
        self.screen.update(time.time())


class TestPerformanceTiming(unittest.TestCase):
    """Tests for performance timing methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
        self.screen = PlanetResultsScreen(self.typography, self.audio_system)
    
    def test_get_performance_ms_zero_when_not_shown(self):
        """Test performance returns 0 when results not shown."""
        ms = self.screen.get_performance_ms()
        
        self.assertEqual(ms, 0.0)
    
    def test_get_performance_ms_positive_after_show(self):
        """Test performance returns positive value after show_results."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        ms = self.screen.get_performance_ms()
        
        self.assertGreater(ms, 0)
    
    def test_performance_under_500ms_threshold(self):
        """Test that results display is under 500ms threshold."""
        mock_result = MockPlanetResult(PlanetStatus.COMPLETED)
        self.screen.show_results(mock_result)
        
        ms = self.screen.get_performance_ms()
        
        # Should be well under 500ms for typical execution
        self.assertLess(ms, 500, "Results display exceeded 500ms threshold")


class TestFactoryFunction(unittest.TestCase):
    """Tests for the factory function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.typography = MockTypography()
    
    def test_create_planet_results_screen(self):
        """Test factory function creates PlanetResultsScreen."""
        screen = create_planet_results_screen(self.typography, self.audio_system)
        
        self.assertIsInstance(screen, PlanetResultsScreen)
        self.assertEqual(screen.typography, self.typography)
        self.assertEqual(screen.audio_system, self.audio_system)


if __name__ == '__main__':
    unittest.main()

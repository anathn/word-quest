"""
Unit tests for FeedbackController component.

Tests cover:
- Success feedback display
- Retry feedback display
- Audio playback
- Auto-advance timing
- Animation updates
"""

import unittest
import sys
import os
import time
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.components.feedback_controller import (
    FeedbackController,
    FeedbackType,
    FeedbackState,
    FeedbackConfig,
    CelebrationAnimation,
    RetryIndicator,
    create_feedback_controller
)


class MockAudioSystem:
    """Mock audio system for testing."""
    
    def __init__(self):
        self.speak_calls = []
        self.audio_available = True
    
    def speak(self, text, on_complete=None):
        self.speak_calls.append(text)
        if on_complete:
            on_complete()
        return True
    
    def is_audio_available(self):
        return self.audio_available


class TestFeedbackController(unittest.TestCase):
    """Tests for the FeedbackController class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.audio_system = MockAudioSystem()
        self.controller = FeedbackController(audio_system=self.audio_system)
        
        # Track callbacks
        self.callback_calls = []
        self.controller.on_feedback_shown = lambda ft: self.callback_calls.append(('feedback_shown', ft))
        self.controller.on_feedback_complete = lambda ft: self.callback_calls.append(('feedback_complete', ft))
        self.controller.on_auto_advance = lambda: self.callback_calls.append(('auto_advance',))
        self.controller.on_hint_requested = lambda: self.callback_calls.append(('hint_requested',))
    
    def test_initial_state(self):
        """Test initial controller state."""
        self.assertEqual(self.controller.state, FeedbackState.IDLE)
        self.assertIsNone(self.controller.current_feedback)
        self.assertFalse(self.controller.is_feedback_active())
    
    def test_show_success_feedback(self):
        """Test showing success feedback."""
        result = self.controller.show_feedback(True)
        
        self.assertTrue(result)
        self.assertEqual(self.controller.state, FeedbackState.SHOWING_SUCCESS)
        self.assertEqual(self.controller.current_feedback, FeedbackType.SUCCESS)
        self.assertTrue(self.controller.is_feedback_active())
    
    def test_show_retry_feedback(self):
        """Test showing retry feedback."""
        result = self.controller.show_feedback(False)
        
        self.assertTrue(result)
        self.assertEqual(self.controller.state, FeedbackState.SHOWING_RETRY)
        self.assertEqual(self.controller.current_feedback, FeedbackType.RETRY)
        self.assertTrue(self.controller.is_feedback_active())
    
    def test_success_triggers_audio(self):
        """Test that success feedback plays audio."""
        self.audio_system.speak_calls = []
        self.controller.show_feedback(True)
        
        # Should speak the success message
        self.assertGreater(len(self.audio_system.speak_calls), 0)
        self.assertIn("Great job!", self.audio_system.speak_calls[0])
    
    def test_retry_triggers_audio(self):
        """Test that retry feedback plays audio."""
        self.audio_system.speak_calls = []
        self.controller.show_feedback(False)
        
        # Should speak the retry message
        self.assertGreater(len(self.audio_system.speak_calls), 0)
        self.assertIn("Try again!", self.audio_system.speak_calls[0])
    
    def test_retry_triggers_hint_request(self):
        """Test that retry feedback triggers hint request."""
        self.callback_calls = []
        self.controller.show_feedback(False)
        
        self.assertIn(('hint_requested',), self.callback_calls)
    
    def test_success_callback(self):
        """Test callback is invoked on success feedback."""
        self.callback_calls = []
        self.controller.show_feedback(True)
        
        self.assertIn(('feedback_shown', FeedbackType.SUCCESS), self.callback_calls)
    
    def test_retry_callback(self):
        """Test callback is invoked on retry feedback."""
        self.callback_calls = []
        self.controller.show_feedback(False)
        
        self.assertIn(('feedback_shown', FeedbackType.RETRY), self.callback_calls)
    
    def test_success_auto_advance_timer(self):
        """Test that success sets auto-advance timer."""
        self.controller.show_feedback(True)
        
        self.assertIsNotNone(self.controller.auto_advance_timer)
        self.assertGreater(self.controller.auto_advance_timer, time.time())
    
    def test_retry_no_auto_advance(self):
        """Test that retry does not set auto-advance timer."""
        self.controller.show_feedback(False)
        
        # Timer should not be set for retry
        self.assertIsNone(self.controller.auto_advance_timer)
    
    def test_update_success_animation(self):
        """Test animation progress update for success."""
        self.controller.show_feedback(True)
        
        start_time = time.time()
        self.controller.update(start_time + 0.5)  # Halfway through
        
        progress = self.controller.get_animation_progress()
        self.assertGreater(progress, 0)
        self.assertLessEqual(progress, 1.0)
    
    def test_update_retry_pulse(self):
        """Test pulse animation for retry feedback."""
        self.controller.show_feedback(False)
        
        start_time = time.time()
        self.controller.update(start_time + 0.5)
        
        # Retry should have pulse animation
        progress = self.controller.get_animation_progress()
        self.assertGreater(progress, 0)
    
    def test_get_feedback_message_success(self):
        """Test getting success feedback message."""
        self.controller.show_feedback(True)
        
        message = self.controller.get_feedback_message()
        self.assertEqual(message, "Great job!")
    
    def test_get_feedback_message_retry(self):
        """Test getting retry feedback message."""
        self.controller.show_feedback(False)
        
        message = self.controller.get_feedback_message()
        self.assertEqual(message, "Try again!")
    
    def test_get_feedback_message_idle(self):
        """Test getting feedback message when idle."""
        message = self.controller.get_feedback_message()
        self.assertEqual(message, "")
    
    def test_force_complete(self):
        """Test forcing feedback completion."""
        self.controller.show_feedback(False)
        self.assertTrue(self.controller.is_feedback_active())
        
        self.controller.force_complete()
        self.assertFalse(self.controller.is_feedback_active())
    
    def test_reset(self):
        """Test resetting the controller."""
        self.controller.show_feedback(True)
        self.controller.reset()
        
        self.assertEqual(self.controller.state, FeedbackState.IDLE)
        self.assertEqual(self.controller.current_feedback, FeedbackType.NONE)
        self.assertFalse(self.controller.is_feedback_active())
    
    def test_feedback_timing_within_1_second(self):
        """Test feedback starts within 1 second of call."""
        start_time = time.time()
        self.controller.show_feedback(True)
        end_time = time.time()
        
        elapsed = (end_time - start_time) * 1000  # Convert to ms
        self.assertLess(elapsed, 1000)  # Should be well under 1 second
    
    def test_no_audio_fallback(self):
        """Test graceful fallback when audio unavailable."""
        self.audio_system.audio_available = False
        controller = FeedbackController(audio_system=self.audio_system)
        
        # Should not raise exception
        result = controller.show_feedback(True)
        self.assertTrue(result)
    
    def test_custom_config(self):
        """Test custom feedback configuration."""
        config = FeedbackConfig(
            success_display_duration=3.0,
            success_message="Awesome!",
            auto_advance_on_success=False
        )
        controller = FeedbackController(audio_system=self.audio_system, config=config)
        
        controller.show_feedback(True)
        
        self.assertEqual(controller.get_feedback_message(), "Awesome!")
        self.assertIsNone(controller.auto_advance_timer)
    
    def test_set_audio_system(self):
        """Test setting audio system after creation."""
        controller = FeedbackController()
        new_audio = MockAudioSystem()
        
        controller.set_audio_system(new_audio)
        self.assertEqual(controller.audio_system, new_audio)


class TestCelebrationAnimation(unittest.TestCase):
    """Tests for CelebrationAnimation class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.animation = CelebrationAnimation()
    
    def test_initial_state(self):
        """Test initial animation state."""
        self.assertFalse(self.animation.active)
        self.assertEqual(len(self.animation.particles), 0)
    
    def test_start_creates_particles(self):
        """Test that start creates particles."""
        self.animation.start()
        
        self.assertTrue(self.animation.active)
        self.assertGreater(len(self.animation.particles), 0)
    
    def test_update_progresses_particles(self):
        """Test that update progresses particle positions."""
        self.animation.start()
        start_time = time.time()
        
        self.animation.update(start_time + 0.5)
        
        # Particles should have moved
        for particle in self.animation.particles:
            self.assertGreater(particle['life'], 0)
    
    def test_is_complete(self):
        """Test completion detection."""
        self.animation.start()
        self.assertFalse(self.animation.is_complete())
    
    def test_stop(self):
        """Test stopping animation."""
        self.animation.start()
        self.animation.stop()
        
        self.assertFalse(self.animation.active)
        self.assertEqual(len(self.animation.particles), 0)
    
    def test_particle_colors(self):
        """Test particle color assignment."""
        self.animation.start()
        
        for particle in self.animation.particles:
            color = particle['color']
            self.assertIsInstance(color, tuple)
            self.assertEqual(len(color), 3)  # RGB


class TestRetryIndicator(unittest.TestCase):
    """Tests for RetryIndicator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.indicator = RetryIndicator()
    
    def test_initial_state(self):
        """Test initial indicator state."""
        self.assertFalse(self.indicator.active)
    
    def test_start_activates(self):
        """Test that start activates indicator."""
        self.indicator.start()
        self.assertTrue(self.indicator.active)
    
    def test_get_pulse_intensity(self):
        """Test pulse intensity calculation."""
        self.indicator.start()
        start_time = time.time()
        
        intensity = self.indicator.get_pulse_intensity(start_time + 0.5)
        
        # Should be approximately between 0.7 and 1.0 (allowing for floating point)
        self.assertGreaterEqual(intensity, 0.69)
        self.assertLessEqual(intensity, 1.01)
    
    def test_get_pulse_intensity_inactive(self):
        """Test pulse intensity when inactive."""
        intensity = self.indicator.get_pulse_intensity(time.time())
        self.assertEqual(intensity, 0.0)
    
    def test_stop(self):
        """Test stopping indicator."""
        self.indicator.start()
        self.indicator.stop()
        self.assertFalse(self.indicator.active)


class TestFactoryFunction(unittest.TestCase):
    """Tests for factory functions."""
    
    def test_create_feedback_controller(self):
        """Test create_feedback_controller function."""
        audio = MockAudioSystem()
        controller = create_feedback_controller(audio)
        
        self.assertIsInstance(controller, FeedbackController)
        self.assertEqual(controller.audio_system, audio)
    
    def test_create_feedback_controller_no_audio(self):
        """Test creating controller without audio."""
        controller = create_feedback_controller()
        self.assertIsInstance(controller, FeedbackController)
        self.assertIsNone(controller.audio_system)


class TestFeedbackConfig(unittest.TestCase):
    """Tests for FeedbackConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = FeedbackConfig()
        
        self.assertEqual(config.success_display_duration, 2.0)
        self.assertEqual(config.success_volume, 0.7)
        self.assertEqual(config.retry_volume, 0.5)
        self.assertEqual(config.success_message, "Great job!")
        self.assertEqual(config.retry_message, "Try again!")
        self.assertTrue(config.auto_advance_on_success)
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = FeedbackConfig(
            success_display_duration=3.0,
            success_message="Excellent!",
            auto_advance_on_success=False
        )
        
        self.assertEqual(config.success_display_duration, 3.0)
        self.assertEqual(config.success_message, "Excellent!")
        self.assertFalse(config.auto_advance_on_success)


if __name__ == '__main__':
    unittest.main()

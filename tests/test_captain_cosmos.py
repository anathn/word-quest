"""
Unit Tests for Captain Cosmos Component (STORY-004-04)

Tests for the Captain Cosmos character system including:
- Voice line selection and categorization
- State management and transitions
- Event handlers
- Data loading and configuration
"""

import pytest
import os
import json
import tempfile
from pathlib import Path


# Test fixtures
@pytest.fixture
def temp_data_dir():
    """Create temporary data directory with voice lines."""
    with tempfile.TemporaryDirectory() as tmpdir:
        voice_lines = {
            "captain_cosmos": {
                "correct": ["Great job!", "Well done!", "Excellent!"],
                "incorrect": ["Try again!", "Keep trying!", "You've got this!"],
                "streak": ["3 in a row!", "On fire!", "Streak master!"],
                "planet_complete": ["Planet cleared!", "World conquered!", "Amazing!"],
                "hint_request": ["Let me help.", "Here's a clue...", "I can help with that."],
                "badge_unlock": ["Badge unlocked!", "Congratulations!", "Awesome!"],
                "greeting": ["Welcome!", "Hello explorer!", "Hi there!"],
                "tutorial": {
                    "welcome": "Welcome to Word Quest!",
                    "objective": "Let's spell words!",
                    "controls": "Type the letters.",
                    "feedback": "Press Enter to submit.",
                    "hints": "Click 'Need Help?' for hints.",
                    "progression": "Complete 5 words per planet."
                }
            }
        }
        
        voice_lines_path = os.path.join(tmpdir, "voice_lines.json")
        with open(voice_lines_path, 'w') as f:
            json.dump(voice_lines, f)
        
        yield tmpdir


@pytest.fixture
def captain(temp_data_dir):
    """Create CaptainCosmos instance with test data."""
    from src.components.captain_cosmos import CaptainCosmos, reset_captain_cosmos
    
    reset_captain_cosmos()
    captain = CaptainCosmos(data_dir=temp_data_dir)
    return captain


class TestCaptainInitialization:
    """Test Captain Cosmos initialization and data loading."""
    
    def test_captain_initializes_with_idle_state(self, captain):
        """Captain should start in IDLE state."""
        from src.components.captain_cosmos import CaptainState
        assert captain.get_state() == CaptainState.IDLE
    
    def test_captain_loads_voice_lines(self, captain, temp_data_dir):
        """Captain should load voice lines from JSON file."""
        assert "correct" in captain._voice_lines
        assert "incorrect" in captain._voice_lines
        assert "streak" in captain._voice_lines
        assert len(captain._voice_lines["correct"]) == 3
    
    def test_captain_handles_missing_voice_lines_file(self):
        """Captain should handle missing voice lines file gracefully."""
        from src.components.captain_cosmos import CaptainCosmos
        
        with tempfile.TemporaryDirectory() as tmpdir:
            captain = CaptainCosmos(data_dir=tmpdir)
            assert captain._voice_lines == {"captain_cosmos": {}}
    
    def test_captain_handles_invalid_json(self):
        """Captain should handle invalid JSON file gracefully."""
        from src.components.captain_cosmos import CaptainCosmos
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create invalid JSON file
            voice_lines_path = os.path.join(tmpdir, "voice_lines.json")
            with open(voice_lines_path, 'w') as f:
                f.write("invalid json {{{")
            
            captain = CaptainCosmos(data_dir=tmpdir)
            assert captain._voice_lines == {"captain_cosmos": {}}


class TestVoiceLineSelection:
    """Test voice line selection logic."""
    
    def test_speak_selects_from_category(self, captain):
        """speak() should select a voice line from the specified category."""
        result = captain.speak("correct")
        assert result in captain._voice_lines["correct"]
    
    def test_speak_returns_empty_string_for_missing_category(self, captain):
        """speak() should return empty string for missing category."""
        result = captain.speak("nonexistent_category")
        assert result == ""
    
    def test_speak_sets_talking_state(self, captain):
        """speak() should set state to TALKING."""
        from src.components.captain_cosmos import CaptainState
        
        captain.speak("correct")
        assert captain.get_state() == CaptainState.TALKING
    
    def test_speak_sets_current_line(self, captain):
        """speak() should set current_line with correct data."""
        result = captain.speak("incorrect")
        line = captain.get_current_line()
        
        assert line is not None
        assert line.text == result
        assert line.category == "incorrect"
        assert line.priority == 1  # NORMAL_PRIORITY
    
    def test_unique_line_selection_avoids_repetition(self, temp_data_dir):
        """Voice line selection should avoid repeating lines until all used."""
        from src.components.captain_cosmos import CaptainCosmos
        
        captain = CaptainCosmos(data_dir=temp_data_dir)
        correct_lines = captain._voice_lines["correct"]
        
        # Get multiple lines
        results = [captain.speak("correct") for _ in range(len(correct_lines))]
        
        # All results should be unique
        assert len(set(results)) == len(results)
    
    def test_unique_line_selection_resets_after_all_used(self, temp_data_dir):
        """Voice line selection should reset after all lines are used."""
        from src.components.captain_cosmos import CaptainCosmos
        
        captain = CaptainCosmos(data_dir=temp_data_dir)
        correct_lines = captain._voice_lines["correct"]
        
        # Use all lines
        for _ in range(len(correct_lines)):
            captain.speak("correct")
        
        # Next call should reset and pick a line again (won't be empty)
        result = captain.speak("correct")
        assert result != ""


class TestEventHandlers:
    """Test Captain Cosmos event handlers."""
    
    def test_on_correct_answer(self, captain):
        """on_correct_answer should speak from 'correct' category."""
        result = captain.on_correct_answer()
        assert result in captain._voice_lines["correct"]
    
    def test_on_incorrect_answer(self, captain):
        """on_incorrect_answer should speak from 'incorrect' category."""
        result = captain.on_incorrect_answer()
        assert result in captain._voice_lines["incorrect"]
    
    def test_on_streak_milestone_calls_on_three(self, captain):
        """on_streak_milestone should speak only on milestone streaks."""
        result = captain.on_streak_milestone(3)
        assert result in captain._voice_lines["streak"]
    
    def test_on_streak_milestone_calls_on_five(self, captain):
        """on_streak_milestone should speak on streak 5."""
        result = captain.on_streak_milestone(5)
        assert result in captain._voice_lines["streak"]
    
    def test_on_streak_milestone_calls_on_ten(self, captain):
        """on_streak_milestone should speak on streak 10."""
        result = captain.on_streak_milestone(10)
        assert result in captain._voice_lines["streak"]
    
    def test_on_streak_milestone_skips_non_milestones(self, captain):
        """on_streak_milestone should return empty string for non-milestones."""
        result = captain.on_streak_milestone(2)
        assert result == ""
    
    def test_on_planet_complete(self, captain):
        """on_planet_complete should speak from 'planet_complete' category."""
        result = captain.on_planet_complete()
        assert result in captain._voice_lines["planet_complete"]
    
    def test_on_hint_request(self, captain):
        """on_hint_request should speak from 'hint_request' category."""
        result = captain.on_hint_request()
        assert result in captain._voice_lines["hint_request"]
    
    def test_on_badge_unlock(self, captain):
        """on_badge_unlock should speak from 'badge_unlock' category."""
        result = captain.on_badge_unlock()
        assert result in captain._voice_lines["badge_unlock"]
    
    def test_on_greeting(self, captain):
        """on_greeting should speak from 'greeting' category."""
        result = captain.on_greeting()
        assert result in captain._voice_lines["greeting"]


class TestTutorialLines:
    """Test tutorial line retrieval."""
    
    def test_start_tutorial_returns_welcome(self, captain):
        """start_tutorial should return welcome message."""
        result = captain.start_tutorial()
        assert result == "Welcome to Word Quest!"
    
    def test_get_tutorial_line_returns_correct_step(self, captain):
        """get_tutorial_line should return specific tutorial step."""
        result = captain.get_tutorial_line("objective")
        assert result == "Let's spell words!"
    
    def test_get_tutorial_line_handles_missing_step(self, captain):
        """get_tutorial_line should return empty string for missing step."""
        result = captain.get_tutorial_line("nonexistent_step")
        assert result == ""
    
    def test_get_tutorial_steps_returns_all_keys(self, captain):
        """get_tutorial_steps should return all tutorial step keys."""
        steps = captain.get_tutorial_steps()
        expected = ["welcome", "objective", "controls", "feedback", "hints", "progression"]
        assert steps == expected


class TestStateManagement:
    """Test Captain state management."""
    
    def test_set_state(self, captain):
        """set_state should change Captain's state."""
        from src.components.captain_cosmos import CaptainState
        
        captain.set_state(CaptainState.CELEBRATING)
        assert captain.get_state() == CaptainState.CELEBRATING
    
    def test_trigger_celebration(self, captain):
        """trigger_celebration should set CELEBRATING state."""
        from src.components.captain_cosmos import CaptainState
        
        captain.trigger_celebration()
        assert captain.get_state() == CaptainState.CELEBRATING
    
    def test_trigger_encouragement(self, captain):
        """trigger_encouragement should set ENCOURAGING state."""
        from src.components.captain_cosmos import CaptainState
        
        captain.trigger_encouragement()
        assert captain.get_state() == CaptainState.ENCOURAGING
    
    def test_enter_hint_mode(self, captain):
        """enter_hint_mode should set HINT_MODE state."""
        from src.components.captain_cosmos import CaptainState
        
        captain.enter_hint_mode()
        assert captain.get_state() == CaptainState.HINT_MODE
    
    def test_reset(self, captain):
        """reset should return Captain to initial state."""
        from src.components.captain_cosmos import CaptainState
        
        # Set various states and values
        captain.speak("correct")
        captain.trigger_celebration()
        captain._used_lines.add(0)
        captain._tts_callback = lambda: None
        
        # Reset
        captain.reset()
        
        # Verify reset
        assert captain.get_state() == CaptainState.IDLE
        assert captain.get_current_line() is None
        assert len(captain._used_lines) == 0
        assert captain._tts_callback is None


class TestTTSCompletionCallback:
    """Test TTS completion callback handling."""
    
    def test_on_tts_complete_calls_callback(self, captain):
        """on_tts_complete should call the registered callback."""
        callback_called = False
        
        def my_callback():
            nonlocal callback_called
            callback_called = True
        
        # Set callback
        captain.speak_with_callback("correct", my_callback)
        captain._tts_callback = my_callback
        
        # Simulate TTS completion
        captain.on_tts_complete()
        
        assert callback_called is True
        assert captain._tts_callback is None
    
    def test_on_tts_complete_returns_to_idle(self, captain):
        """on_tts_complete should return to IDLE state."""
        from src.components.captain_cosmos import CaptainState
        
        captain.speak("correct")
        assert captain.get_state() == CaptainState.TALKING
        
        captain.on_tts_complete()
        assert captain.get_state() == CaptainState.IDLE
    
    def test_speak_with_callback(self, captain):
        """speak_with_callback should set callback and return line."""
        callback_called = False
        
        def my_callback():
            nonlocal callback_called
            callback_called = True
        
        result = captain.speak_with_callback("correct", my_callback)
        
        assert result in captain._voice_lines["correct"]
        assert captain._tts_callback == my_callback


class TestVoiceLineConfiguration:
    """Test runtime voice line configuration."""
    
    def test_add_voice_lines(self, captain):
        """add_voice_lines should add custom voice lines."""
        custom_lines = ["Custom line 1", "Custom line 2"]
        
        captain.add_voice_lines("custom_category", custom_lines)
        
        assert "custom_category" in captain._voice_lines
        assert custom_lines[0] in captain._voice_lines["custom_category"]
        assert custom_lines[1] in captain._voice_lines["custom_category"]
    
    def test_add_voice_lines_to_existing_category(self, captain):
        """add_voice_lines should extend existing category."""
        original_count = len(captain._voice_lines["correct"])
        new_lines = ["New line 1"]
        
        captain.add_voice_lines("correct", new_lines)
        
        assert len(captain._voice_lines["correct"]) == original_count + 1


class TestSingletonPattern:
    """Test Captain Cosmos singleton pattern."""
    
    def test_get_captain_cosmos_returns_singleton(self, temp_data_dir):
        """get_captain_cosmos should return the same instance."""
        from src.components.captain_cosmos import get_captain_cosmos, reset_captain_cosmos
        
        reset_captain_cosmos()
        
        captain1 = get_captain_cosmos(data_dir=temp_data_dir)
        captain2 = get_captain_cosmos(data_dir=temp_data_dir)
        
        assert captain1 is captain2
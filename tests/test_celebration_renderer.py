"""
Unit tests for celebration renderer system.

Tests cover initialization, state transitions, component integration,
and edge cases for the celebration ceremony flow.
"""

import pytest
from unittest.mock import MagicMock, call

import sys
sys.path.insert(0, '/home/nathan/repo/word-quest')

from src.ui.celebration_renderer import (
    CelebrationRenderer,
    CelebrationState,
    create_celebration_renderer
)
from src.ui.planet_bloom import BloomState
from src.ui.sparkle_effect import SparkleEffect


class TestCelebrationRendererInitialization:
    """Tests for celebration renderer initialization."""
    
    def test_initial_state(self):
        """Test renderer initializes in IDLE state."""
        renderer = CelebrationRenderer()
        
        assert renderer.state == CelebrationState.IDLE
        assert renderer.active == False
        assert renderer.planet_bloom is None
        assert renderer.sparkles is None
        assert renderer.rocket is None
    
    def test_default_position(self):
        """Test default planet position is set."""
        renderer = CelebrationRenderer()
        
        assert renderer.planet_position == (400, 300)
    
    def test_rocket_celebration_enabled_by_default(self):
        """Test rocket celebration is enabled by default."""
        renderer = CelebrationRenderer()
        
        assert renderer.rocket_celebration_enabled == True
    
    def test_callback_initially_none(self):
        """Test completion callback is None initially."""
        renderer = CelebrationRenderer()
        
        assert renderer.on_celebration_complete is None


class TestSetComponents:
    """Tests for component setup."""
    
    def test_set_all_components(self):
        """Test setting all three components."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        sparkles = MagicMock()
        rocket = MagicMock()
        
        renderer.set_components(
            planet_bloom=planet_bloom,
            sparkle_effect=sparkles,
            rocket=rocket
        )
        
        assert renderer.planet_bloom == planet_bloom
        assert renderer.sparkles == sparkles
        assert renderer.rocket == rocket
    
    def test_set_optional_components(self):
        """Test setting components individually."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        
        renderer.set_components(planet_bloom=planet_bloom)
        
        assert renderer.planet_bloom == planet_bloom
        assert renderer.sparkles is None
        assert renderer.rocket is None
    
    def test_set_only_rocket(self):
        """Test setting only rocket component."""
        renderer = CelebrationRenderer()
        rocket = MagicMock()
        
        renderer.set_components(rocket=rocket)
        
        assert renderer.rocket == rocket


class TestStartCelebration:
    """Tests for starting celebrations."""
    
    def test_start_sets_state_to_starting(self):
        """Test start_celebration sets state to STARTING."""
        renderer = CelebrationRenderer()
        
        renderer.start_celebration(planet_position=(400, 300))
        
        assert renderer.state == CelebrationState.STARTING
        assert renderer.active == True
        assert renderer.planet_position == (400, 300)
    
    def test_start_triggers_bloom(self):
        """Test start_celebration triggers bloom."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        renderer.set_components(planet_bloom=planet_bloom)
        
        renderer.start_celebration(planet_position=(400, 300))
        
        planet_bloom.start_bloom.assert_called_once()
    
    def test_start_triggers_sparkles(self):
        """Test start_celebration starts sparkles and emits burst."""
        renderer = CelebrationRenderer()
        sparkles = MagicMock()
        renderer.set_components(sparkle_effect=sparkles)
        
        renderer.start_celebration(planet_position=(400, 300))
        
        sparkles.set_center.assert_called_once_with((400, 300))
        sparkles.start.assert_called_once()
        sparkles.emit.assert_called_once_with(count=10)
    
    def test_start_triggers_rocket_when_enabled(self):
        """Test start_celebration triggers rocket animation."""
        renderer = CelebrationRenderer()
        rocket = MagicMock()
        renderer.set_components(rocket=rocket)
        renderer.rocket_celebration_enabled = True
        
        renderer.start_celebration(planet_position=(400, 300))
        
        rocket.start_celebration.assert_called_once()
    
    def test_start_does_not_trigger_rocket_when_disabled(self):
        """Test start_celebration skips rocket when disabled."""
        renderer = CelebrationRenderer()
        rocket = MagicMock()
        renderer.set_components(rocket=rocket)
        renderer.rocket_celebration_enabled = False
        
        renderer.start_celebration(planet_position=(400, 300))
        
        rocket.start_celebration.assert_not_called()
    
    def test_reset_timers_on_start(self):
        """Test timers are reset when starting celebration."""
        renderer = CelebrationRenderer()
        
        # Set timers to non-zero values
        renderer._celebration_timer = 10.0
        renderer._bubble_timer = 10.0
        
        renderer.start_celebration(planet_position=(400, 300))
        
        assert renderer._celebration_timer == 0.0
        assert renderer._bubble_timer == 0.0


class TestUpdate:
    """Tests for update state machine."""
    
    def test_update_does_nothing_when_inactive(self):
        """Test update has no effect when celebration not active."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        renderer.set_components(planet_bloom=planet_bloom)
        
        renderer.update(0.1)
        
        planet_bloom.update.assert_not_called()
    
    def test_starting_transitions_to_celebrating(self):
        """Test STARTING state transitions to CELEBRATING."""
        renderer = CelebrationRenderer()
        renderer.start_celebration(planet_position=(400, 300))
        
        renderer.update(0.1)
        
        assert renderer.state == CelebrationState.CELEBRATING
    
    def test_celebrating_updates_bloom(self):
        """Test CELEBRATING state updates bloom."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.BLOOMING
        sparkles = MagicMock()
        renderer.set_components(planet_bloom=planet_bloom, sparkle_effect=sparkles)
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # Transition to CELEBRATING
        
        renderer.update(0.1)
        
        planet_bloom.update.assert_called()
    
    def test_celebrating_updates_sparkles(self):
        """Test CELEBRATING state updates sparkles."""
        renderer = CelebrationRenderer()
        sparkles = MagicMock()
        sparkles.is_active.return_value = True
        renderer.set_components(sparkle_effect=sparkles)
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # Transition to CELEBRATING
        
        renderer.update(0.1)
        
        sparkles.update.assert_called()
    
    def test_celebrating_emits_sparkles_during_bloom(self):
        """Test sparkles are emitted during BLOOMING and HOLDING states."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.BLOOMING
        sparkles = MagicMock()
        renderer.set_components(planet_bloom=planet_bloom, sparkle_effect=sparkles)
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # Transition to CELEBRATING
        
        renderer.update(0.1)
        
        sparkles.emit.assert_called()
    
    def test_celebrating_updates_rocket(self):
        """Test CELEBRATING state updates rocket animation."""
        renderer = CelebrationRenderer()
        rocket = MagicMock()
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.BLOOMING
        sparkles = MagicMock()
        renderer.set_components(
            planet_bloom=planet_bloom,
            sparkle_effect=sparkles,
            rocket=rocket
        )
        renderer.rocket_celebration_enabled = True
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # Transition to CELEBRATING
        
        renderer.update(0.1)
        
        rocket.update_celebration.assert_called()
    
    def test_celebrating_transitions_to_completing_on_fade(self):
        """Test CELEBRATING transitions to COMPLETING when bloom fades."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.FADE_OUT
        renderer.set_components(planet_bloom=planet_bloom)
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # Transition to CELEBRATING
        
        renderer.update(0.1)
        
        assert renderer.state == CelebrationState.COMPLETING
    
    def test_completing_updates_all_components(self):
        """Test COMPLETING state continues updating all components."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.FADE_OUT
        sparkles = MagicMock()
        sparkles.is_active.return_value = True
        rocket = MagicMock()
        renderer.set_components(
            planet_bloom=planet_bloom,
            sparkle_effect=sparkles,
            rocket=rocket
        )
        renderer.rocket_celebration_enabled = True
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # Transition to CELEBRATING
        renderer.update(0.1)  # Transition to COMPLETING
        
        renderer.update(0.1)
        
        planet_bloom.update.assert_called()
        sparkles.update.assert_called()
        rocket.update_celebration.assert_called()
    
    def test_completing_sets_complete_when_idle(self):
        """Test COMPLETING transitions to COMPLETE when all done."""
        renderer = CelebrationRenderer()
        # Set bloom to FADE_OUT to transition to COMPLETING
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.FADE_OUT
        sparkles = MagicMock()
        sparkles.is_active.return_value = False
        renderer.set_components(
            planet_bloom=planet_bloom,
            sparkle_effect=sparkles
        )
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # Transition to CELEBRATING
        # Transition to COMPLETING because bloom is in FADE_OUT
        renderer.update(0.1)
        
        assert renderer.state == CelebrationState.COMPLETING
        
        # Now set bloom to IDLE to transition to COMPLETE
        planet_bloom.state = BloomState.IDLE
        renderer.update(0.1)
        
        assert renderer.state == CelebrationState.COMPLETE
        assert renderer.active == False
    
    def test_complete_stops_rocket(self):
        """Test completion stops rocket celebration."""
        renderer = CelebrationRenderer()
        # Bloom needs to be in FADE_OUT first to transition to COMPLETING
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.FADE_OUT
        sparkles = MagicMock()
        sparkles.is_active.return_value = False
        rocket = MagicMock()
        renderer.set_components(
            planet_bloom=planet_bloom,
            sparkle_effect=sparkles,
            rocket=rocket
        )
        renderer.rocket_celebration_enabled = True
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # CELEBRATING
        renderer.update(0.1)  # COMPLETING (bloom is FADE_OUT)
        
        # Now set bloom to IDLE and update to COMPLETE
        planet_bloom.state = BloomState.IDLE
        renderer.update(0.1)  # COMPLETE
        
        # Rocket should have stop_celebration called when transitioning to COMPLETE
        rocket.stop_celebration.assert_called()
    
    def test_complete_triggers_callback(self):
        """Test completion triggers completion callback."""
        renderer = CelebrationRenderer()
        # Bloom needs to be in FADE_OUT first to transition to COMPLETING
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.FADE_OUT
        sparkles = MagicMock()
        sparkles.is_active.return_value = False
        renderer.set_components(
            planet_bloom=planet_bloom,
            sparkle_effect=sparkles
        )
        
        callback = MagicMock()
        renderer.on_celebration_complete = callback
        
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # CELEBRATING
        renderer.update(0.1)  # COMPLETING
        
        # Now set bloom to IDLE to transition to COMPLETE
        planet_bloom.state = BloomState.IDLE
        renderer.update(0.1)  # COMPLETE
        
        # Callback should be called when transitioning to COMPLETE
        callback.assert_called_once()
    
    def test_callback_not_called_if_none(self):
        """Test no error when callback is None."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.IDLE
        sparkles = MagicMock()
        sparkles.is_active.return_value = False
        renderer.set_components(
            planet_bloom=planet_bloom,
            sparkle_effect=sparkles
        )
        
        # on_celebration_complete is None by default
        
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)
        renderer.update(0.1)
        
        # Should not raise exception
        renderer.update(0.1)


class TestRender:
    """Tests for rendering."""
    
    def test_render_does_nothing_when_inactive(self):
        """Test render has no effect when not active."""
        renderer = CelebrationRenderer()
        screen = MagicMock()
        
        renderer.render(screen)
        
        # Should not call any render methods
    
    def test_render_bloom(self):
        """Test render calls bloom render."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        renderer.set_components(planet_bloom=planet_bloom)
        renderer.active = True
        renderer.state = CelebrationState.CELEBRATING
        renderer.planet_position = (400, 300)
        screen = MagicMock()
        
        renderer.render(screen)
        
        planet_bloom.render.assert_called_once_with(screen, (400, 300))
    
    def test_render_sparkles(self):
        """Test render calls sparkle render."""
        renderer = CelebrationRenderer()
        sparkles = MagicMock()
        renderer.set_components(sparkle_effect=sparkles)
        renderer.active = True
        renderer.state = CelebrationState.CELEBRATING
        screen = MagicMock()
        
        renderer.render(screen)
        
        sparkles.render.assert_called_once()
    
    def test_render_rocket(self):
        """Test render calls rocket render when enabled."""
        renderer = CelebrationRenderer()
        rocket = MagicMock()
        renderer.set_components(rocket=rocket)
        renderer.rocket_celebration_enabled = True
        renderer.active = True
        renderer.state = CelebrationState.CELEBRATING
        renderer.planet_position = (400, 300)
        screen = MagicMock()
        
        renderer.render(screen)
        
        rocket.render_celebration.assert_called_once_with(screen, (400, 300))
    
    def test_render_does_not_render_rocket_when_disabled(self):
        """Test render skips rocket when disabled."""
        renderer = CelebrationRenderer()
        rocket = MagicMock()
        renderer.set_components(rocket=rocket)
        renderer.rocket_celebration_enabled = False
        renderer.active = True
        renderer.planet_position = (400, 300)
        screen = MagicMock()
        
        renderer.render(screen)
        
        rocket.render_celebration.assert_not_called()
    
    def test_render_order(self):
        """Test render order: bloom first, then sparkles, then rocket."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        sparkles = MagicMock()
        renderer.set_components(
            planet_bloom=planet_bloom,
            sparkle_effect=sparkles
        )
        renderer.active = True
        renderer.planet_position = (400, 300)
        screen = MagicMock()
        
        renderer.render(screen)
        
        # Verify render order
        calls = screen.method_calls
        assert planet_bloom.render.called
        assert sparkles.render.called


class TestStateQueryMethods:
    """Tests for state query methods."""
    
    def test_is_active_returns_true_during(self):
        """Test is_active returns True during celebration."""
        renderer = CelebrationRenderer()
        
        assert renderer.is_active() == False
        
        renderer.start_celebration(planet_position=(400, 300))
        assert renderer.is_active() == True
    
    def test_is_active_returns_false_when_complete(self):
        """Test is_active returns False when complete."""
        renderer = CelebrationRenderer()
        # Bloom needs to be in FADE_OUT first to transition to COMPLETING
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.FADE_OUT
        sparkles = MagicMock()
        sparkles.is_active.return_value = False
        renderer.set_components(
            planet_bloom=planet_bloom,
            sparkle_effect=sparkles
        )
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # CELEBRATING
        renderer.update(0.1)  # COMPLETING
        
        # Now set bloom to IDLE to transition to COMPLETE
        planet_bloom.state = BloomState.IDLE
        renderer.update(0.1)  # COMPLETE
        
        # After completion, active should be False
        assert renderer.is_active() == False
        assert renderer.state == CelebrationState.COMPLETE
    
    def test_is_complete_returns_true_when_done(self):
        """Test is_complete returns True only when done."""
        renderer = CelebrationRenderer()
        
        # IDLE state should return True for is_complete
        assert renderer.state == CelebrationState.IDLE
        
        renderer.start_celebration(planet_position=(400, 300))
        assert renderer.is_complete() == False
        
        # After full cycle
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.FADE_OUT
        sparkles = MagicMock()
        sparkles.is_active.return_value = False
        renderer.set_components(
            planet_bloom=planet_bloom,
            sparkle_effect=sparkles
        )
        renderer.update(0.1)  # CELEBRATING
        renderer.update(0.1)  # COMPLETING
        
        # Now set bloom to IDLE to transition to COMPLETE
        planet_bloom.state = BloomState.IDLE
        renderer.update(0.1)  # COMPLETE
        
        # Should now be COMPLETE state
        assert renderer.state == CelebrationState.COMPLETE
        assert renderer.is_complete() == True
    
    def test_get_state_returns_current_state(self):
        """Test get_state returns current state string."""
        renderer = CelebrationRenderer()
        
        assert renderer.get_state() == CelebrationState.IDLE


class TestStopCelebration:
    """Tests for stop_celebration method."""
    
    def test_stop_resets_state_to_idle(self):
        """Test stop_celebration resets state to IDLE."""
        renderer = CelebrationRenderer()
        renderer.start_celebration(planet_position=(400, 300))
        
        renderer.stop_celebration()
        
        assert renderer.state == CelebrationState.IDLE
        assert renderer.active == False
    
    def test_stop_resets_bloom(self):
        """Test stop_celebration resets bloom state."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        renderer.set_components(planet_bloom=planet_bloom)
        renderer.start_celebration(planet_position=(400, 300))
        
        renderer.stop_celebration()
        
        assert planet_bloom.state == BloomState.IDLE
    
    def test_stop_stops_sparkles(self):
        """Test stop_celebration stops sparkles."""
        renderer = CelebrationRenderer()
        sparkles = MagicMock()
        renderer.set_components(sparkle_effect=sparkles)
        renderer.start_celebration(planet_position=(400, 300))
        
        renderer.stop_celebration()
        
        sparkles.stop.assert_called_once()
    
    def test_stop_stops_rocket(self):
        """Test stop_celebration stops rocket."""
        renderer = CelebrationRenderer()
        rocket = MagicMock()
        renderer.set_components(rocket=rocket)
        renderer.rocket_celebration_enabled = True
        renderer.start_celebration(planet_position=(400, 300))
        
        renderer.stop_celebration()
        
        rocket.stop_celebration.assert_called_once()
    
    def test_stop_does_not_call_rocket_when_disabled(self):
        """Test stop_celebration skips rocket when disabled."""
        renderer = CelebrationRenderer()
        rocket = MagicMock()
        renderer.set_components(rocket=rocket)
        renderer.rocket_celebration_enabled = False
        renderer.start_celebration(planet_position=(400, 300))
        
        renderer.stop_celebration()
        
        rocket.stop_celebration.assert_not_called()


class TestSetRocketCelebration:
    """Tests for rocket celebration toggle."""
    
    def test_disable_rocket_celebration(self):
        """Test disabling rocket celebration."""
        renderer = CelebrationRenderer()
        
        renderer.set_rocket_celebration(False)
        
        assert renderer.rocket_celebration_enabled == False
    
    def test_enable_rocket_celebration(self):
        """Test enabling rocket celebration."""
        renderer = CelebrationRenderer()
        renderer.rocket_celebration_enabled = False
        
        renderer.set_rocket_celebration(True)
        
        assert renderer.rocket_celebration_enabled == True


class TestSetIntensityMode:
    """Tests for accessibility intensity mode."""
    
    def test_set_reduced_intensity_applied_to_sparkles(self):
        """Test reduced intensity mode applied to sparkles."""
        renderer = CelebrationRenderer()
        sparkles = MagicMock()
        renderer.set_components(sparkle_effect=sparkles)
        
        renderer.set_intensity_mode(reduced=True)
        
        sparkles.set_intensity_mode.assert_called_once_with(True)
        assert renderer.reduced_intensity == True
    
    def test_normal_intensity_mode(self):
        """Test normal intensity mode enabled."""
        renderer = CelebrationRenderer()
        sparkles = MagicMock()
        renderer.set_components(sparkle_effect=sparkles)
        
        renderer.set_intensity_mode(reduced=False)
        
        sparkles.set_intensity_mode.assert_called_once_with(False)
        assert renderer.reduced_intensity == False


class TestSkipCelebration:
    """Tests for skip_celebration method."""
    
    def test_skip_does_nothing_when_inactive(self):
        """Test skip_celebration has no effect when not active."""
        renderer = CelebrationRenderer()
        
        renderer.skip_celebration()
        
        # Should not change state
        assert renderer.state == CelebrationState.IDLE
        assert renderer.active == False
    
    def test_skip_stops_bloom(self):
        """Test skip_celebration stops bloom."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        renderer.set_components(planet_bloom=planet_bloom)
        renderer.start_celebration(planet_position=(400, 300))
        
        renderer.skip_celebration()
        
        assert planet_bloom.state == BloomState.IDLE
        assert planet_bloom.progress == 0.0
    
    def test_skip_stops_sparkles(self):
        """Test skip_celebration stops sparkles."""
        renderer = CelebrationRenderer()
        sparkles = MagicMock()
        renderer.set_components(sparkle_effect=sparkles)
        renderer.start_celebration(planet_position=(400, 300))
        
        renderer.skip_celebration()
        
        sparkles.stop.assert_called_once()
    
    def test_skip_stops_rocket(self):
        """Test skip_celebration stops rocket."""
        renderer = CelebrationRenderer()
        rocket = MagicMock()
        renderer.set_components(rocket=rocket)
        renderer.rocket_celebration_enabled = True
        renderer.start_celebration(planet_position=(400, 300))
        
        renderer.skip_celebration()
        
        rocket.stop_celebration.assert_called_once()
    
    def test_skip_sets_state_to_complete(self):
        """Test skip_celebration sets state to COMPLETE."""
        renderer = CelebrationRenderer()
        renderer.start_celebration(planet_position=(400, 300))
        
        renderer.skip_celebration()
        
        assert renderer.state == CelebrationState.COMPLETE
        assert renderer.active == False
    
    def test_skip_triggers_callback(self):
        """Test skip_celebration triggers completion callback."""
        renderer = CelebrationRenderer()
        callback = MagicMock()
        renderer.on_celebration_complete = callback
        renderer.start_celebration(planet_position=(400, 300))
        
        renderer.skip_celebration()
        
        callback.assert_called_once()


class TestCreateCelebrationRenderer:
    """Tests for factory function."""
    
    def test_create_with_no_components(self):
        """Test factory creates renderer with no components."""
        renderer = create_celebration_renderer()
        
        assert renderer.planet_bloom is None
        assert renderer.sparkles is None
        assert renderer.rocket is None
    
    def test_create_with_all_components(self):
        """Test factory creates renderer with all components."""
        planet_bloom = MagicMock()
        sparkles = MagicMock()
        rocket = MagicMock()
        
        renderer = create_celebration_renderer(
            planet_bloom=planet_bloom,
            sparkles=sparkles,
            rocket=rocket
        )
        
        assert renderer.planet_bloom == planet_bloom
        assert renderer.sparkles == sparkles
        assert renderer.rocket == rocket
    
    def test_create_with_partial_components(self):
        """Test factory creates renderer with partial components."""
        sparkles = MagicMock()
        
        renderer = create_celebration_renderer(sparkles=sparkles)
        
        assert renderer.planet_bloom is None
        assert renderer.sparkles == sparkles
        assert renderer.rocket is None


class TestDefensiveRocketChecks:
    """Tests for defensive checks on rocket methods."""
    
    def test_handles_rocket_without_start_celebration(self):
        """Test no error when rocket lacks start_celebration method."""
        renderer = CelebrationRenderer()
        rocket = MagicMock(spec=[])  # No methods
        renderer.set_components(rocket=rocket)
        renderer.rocket_celebration_enabled = True
        
        # Should not raise AttributeError
        renderer.start_celebration(planet_position=(400, 300))
        
        assert renderer.active == True
    
    def test_handles_rocket_without_update_celebration(self):
        """Test no error when rocket lacks update_celebration method."""
        renderer = CelebrationRenderer()
        rocket = MagicMock(spec=[])  # No methods
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.BLOOMING
        sparkles = MagicMock()
        renderer.set_components(
            planet_bloom=planet_bloom,
            sparkle_effect=sparkles,
            rocket=rocket
        )
        renderer.rocket_celebration_enabled = True
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # Transition to CELEBRATING
        
        # Should not raise AttributeError
        renderer.update(0.1)
        
        assert renderer.state == CelebrationState.CELEBRATING
    
    def test_handles_rocket_without_stop_celebration(self):
        """Test no error when rocket lacks stop_celebration method."""
        renderer = CelebrationRenderer()
        rocket = MagicMock(spec=[])  # No methods
        # Bloom needs to be in FADE_OUT first to transition to COMPLETING
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.FADE_OUT
        sparkles = MagicMock()
        sparkles.is_active.return_value = False
        renderer.set_components(
            planet_bloom=planet_bloom,
            sparkle_effect=sparkles,
            rocket=rocket
        )
        renderer.rocket_celebration_enabled = True
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # CELEBRATING
        renderer.update(0.1)  # COMPLETING
        
        # Now set bloom to IDLE to transition to COMPLETE
        planet_bloom.state = BloomState.IDLE
        
        # Should not raise AttributeError
        renderer.update(0.1)
        
        assert renderer.state == CelebrationState.COMPLETE


class TestEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_multiple_starts(self):
        """Test multiple starts reset celebration."""
        renderer = CelebrationRenderer()
        
        renderer.start_celebration(planet_position=(400, 300))
        renderer.update(0.1)  # Transition to CELEBRATING
        celebration_timer = renderer._celebration_timer
        
        renderer.start_celebration(planet_position=(500, 400))
        
        assert renderer.planet_position == (500, 400)
        assert renderer.state == CelebrationState.STARTING
        assert renderer._celebration_timer == 0.0
    
    def test_update_with_zero_delta_time(self):
        """Test update handles zero delta time."""
        renderer = CelebrationRenderer()
        renderer.start_celebration(planet_position=(400, 300))
        
        # Should not raise error
        renderer.update(0.0)
        
        assert renderer.state == CelebrationState.CELEBRATING
    
    def test_update_with_very_large_delta_time(self):
        """Test update handles very large delta time (jump)."""
        renderer = CelebrationRenderer()
        planet_bloom = MagicMock()
        planet_bloom.state = BloomState.IDLE
        sparkles = MagicMock()
        sparkles.is_active.return_value = False
        renderer.set_components(planet_bloom=planet_bloom, sparkle_effect=sparkles)
        renderer.start_celebration(planet_position=(400, 300))
        
        # Large delta time should not crash and should complete quickly
        renderer.update(100.0)
        
        assert renderer.active == True  # Still celebrating (bloom not in FADE_OUT)
    
    def test_stop_when_already_idle(self):
        """Test stop_celebration when already idle."""
        renderer = CelebrationRenderer()
        
        # Should not raise error
        renderer.stop_celebration()
        
        assert renderer.state == CelebrationState.IDLE
    
    def test_skip_when_already_complete(self):
        """Test skip_celebration when already complete."""
        renderer = CelebrationRenderer()
        
        renderer.start_celebration(planet_position=(400, 300))
        renderer.stop_celebration()  # Complete it
        
        previous_state = renderer.state
        
        # Should not raise error
        renderer.skip_celebration()
        
        # Should still be complete
        assert renderer.state == CelebrationState.IDLE


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
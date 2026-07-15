"""
Integration Tests for Planet Transition Flow (STORY-001-06)

Tests the complete transition workflow between planets:
- Full transition: planet complete → animation → next planet
- Skip animation jumps directly to next planet
- Progress persists after transition
"""

import pytest
from unittest.mock import MagicMock

import sys
sys.path.insert(0, '/home/nathan/repo/word-quest')


@pytest.fixture(scope="session")
def mock_deps():
    """Create mock dependencies for testing."""
    mock_typography = MagicMock()
    mock_audio = MagicMock()
    mock_tracker = MagicMock()
    mock_typography.FONT_DEFAULT = 24
    mock_typography.FONT_SMALL = 18
    mock_typography.FONT_MEDIUM = 32
    mock_typography.FONT_XLARGE = 48
    mock_typography.FONT_TINY = 12
    mock_typography.style_default = "default"
    mock_typography.style_header = "header"
    mock_typography.style_caption = "caption"
    mock_typography.get_font = MagicMock(return_value=MagicMock(render=MagicMock(return_value=MagicMock())))
    return {
        'typography': mock_typography,
        'audio': mock_audio,
        'tracker': mock_tracker
    }


@pytest.fixture(scope="session")
def planet_info_sample():
    """Sample planet info for testing."""
    from src.screens.planet_transition import PlanetInfo
    
    return {
        'mercury': PlanetInfo(
            planet_id="mercury",
            planet_name="Mercury",
            planet_number=1,
            total_planets=12
        ),
        'venus': PlanetInfo(
            planet_id="venus",
            planet_name="Venus",
            planet_number=2,
            total_planets=12
        ),
        'earth': PlanetInfo(
            planet_id="earth",
            planet_name="Earth",
            planet_number=3,
            total_planets=12
        )
    }


class TestPlanetTransitionFlow:
    """Integration tests for planet transition flow."""
    
    def test_full_transition_flow(self, mock_deps, planet_info_sample):
        """Test complete transition from planet completion to next planet."""
        from src.screens.planet_transition import PlanetTransitionScreen
        
        # Setup
        from_planet = planet_info_sample['mercury']
        to_planet = planet_info_sample['venus']
        transition_screen = PlanetTransitionScreen(
            mock_deps['typography'],
            mock_deps['audio']
        )
        
        # Track state changes
        transition_complete_called = False
        
        def on_complete():
            nonlocal transition_complete_called
            transition_complete_called = True
        
        transition_screen.on_transition_complete = on_complete
        
        # Trigger transition
        transition_screen.start_transition(
            from_planet=from_planet,
            to_planet=to_planet,
            galaxy_progress=0.083  # ~1/12 planets
        )
        
        # Verify transition started
        assert transition_screen.is_running == True
        assert transition_screen.animation_progress == 0.0
        assert transition_screen.from_planet == from_planet
        assert transition_screen.to_planet == to_planet
        
        # Simulate animation playing to completion
        transition_screen.update(delta_time=2.0)  # Full duration
        
        # Verify transition completed
        assert transition_screen.is_complete() == True
        assert transition_complete_called == True
        
        # Verify audio was triggered
        mock_deps['audio'].play_sfx.assert_called_once_with("transition")
    
    def test_skip_animation_jumps_to_end(self, mock_deps, planet_info_sample):
        """Test that skipping animation completes immediately."""
        from src.screens.planet_transition import PlanetTransitionScreen
        
        from_planet = planet_info_sample['mercury']
        to_planet = planet_info_sample['venus']
        transition_screen = PlanetTransitionScreen(
            mock_deps['typography'],
            mock_deps['audio']
        )
        
        # Start transition normally
        transition_screen.start_transition(
            from_planet=from_planet,
            to_planet=to_planet,
            galaxy_progress=0.083
        )
        
        # Verify transition started
        assert transition_screen.is_running == True
        assert transition_screen.animation_progress < 1.0
        
        # Simulate partial animation
        transition_screen.update(delta_time=0.5)
        partial_progress = transition_screen.animation_progress
        assert partial_progress > 0.0
        
        # Request skip
        transition_screen.skip_requested = True
        
        # Skip should complete immediately
        transition_screen.update(delta_time=0.01)
        
        # Verify animation jumped to end
        assert transition_screen.animation_progress == 1.0
        assert transition_screen.is_complete() == True
    
    def test_skip_via_event_handler(self, mock_deps, planet_info_sample):
        """Test that SPACE key and click trigger skip."""
        import pygame
        from src.screens.planet_transition import PlanetTransitionScreen
        
        from_planet = planet_info_sample['mercury']
        to_planet = planet_info_sample['venus']
        transition_screen = PlanetTransitionScreen(
            mock_deps['typography'],
            mock_deps['audio']
        )
        
        # Start transition
        transition_screen.start_transition(
            from_planet=from_planet,
            to_planet=to_planet,
            galaxy_progress=0.083,
            skip=False
        )
        
        assert transition_screen.skip_requested == False
        
        # Simulate SPACE key press
        fake_event = MagicMock()
        fake_event.type = pygame.KEYDOWN
        fake_event.key = pygame.K_SPACE
        transition_screen.handle_events([fake_event])
        
        assert transition_screen.skip_requested == True
    
    def test_progress_persists_after_transition(self, mock_deps, planet_info_sample):
        """Test that galaxy progress is maintained across transition."""
        from src.screens.planet_transition import PlanetTransitionScreen
        
        from_planet = planet_info_sample['mercury']
        to_planet = planet_info_sample['venus']
        
        # Mock tracker to return specific galaxy progress
        mock_deps['tracker'].get_galaxy_progress_percent.return_value = 0.167  # 2/12
        
        transition_screen = PlanetTransitionScreen(
            mock_deps['typography'],
            mock_deps['audio']
        )
        
        initial_progress = 0.167
        transition_screen.start_transition(
            from_planet=from_planet,
            to_planet=to_planet,
            galaxy_progress=initial_progress
        )
        
        # Track captured progress
        captured_progress = transition_screen.galaxy_progress
        
        # Complete transition
        transition_screen.update(delta_time=2.0)
        
        # Verify progress was maintained (not reset to 0)
        assert transition_screen.galaxy_progress == captured_progress
    
    def test_galaxy_complete_prevents_transition(self, mock_deps, planet_info_sample):
        """Test that attempting transition beyond last planet is handled."""
        from src.screens.planet_transition import PlanetTransitionScreen
        
        # Create a planet beyond the total (edge case)
        beyond_planet = planet_info_sample['earth']  # planet_number=3
        # Set total to make it beyond
        beyond_planet.total_planets = 2  # Planet 3 beyond total of 2
        
        current_planet = planet_info_sample['mercury']  # planet_number=1
        
        transition_screen = PlanetTransitionScreen(
            mock_deps['typography'],
            mock_deps['audio']
        )
        
        transition_complete_called = False
        
        def on_complete():
            nonlocal transition_complete_called
            transition_complete_called = True
        
        transition_screen.on_transition_complete = on_complete
        
        # Attempt transition to invalid planet
        transition_screen.start_transition(
            from_planet=current_planet,
            to_planet=beyond_planet,
            galaxy_progress=0.167
        )
        
        # Should handle galaxy complete instead of transitioning
        assert transition_screen.is_complete() == True
        assert transition_screen.is_running == False
        # callback should still be called to notify parent
        assert transition_complete_called == True


class TestProgressBarIntegration:
    """Integration tests for progress bar animation."""
    
    def test_progress_bar_animates_smoothly(self, mock_deps):
        """Test that progress bar animation is smooth between frames."""
        from src.ui.animations import ProgressBarAnimator
        
        bar = ProgressBarAnimator()
        
        # Set target to 50%
        bar.set_target(0.5)
        
        # Multiple small updates should approach target smoothly
        for _ in range(10):
            bar.update(delta_time=0.1)
        
        # Should be closer to target than start
        assert bar.progress > 0.0
        assert bar.progress < 0.5  # Not there yet
        
        # More updates should get us closer
        for _ in range(50):
            bar.update(delta_time=0.1)
        
        assert bar.progress >= 0.49  # Very close to 0.5
    
    def test_progress_bar_clamps_values(self, mock_deps):
        """Test that progress bar clamps to valid range."""
        from src.ui.animations import ProgressBarAnimator
        
        bar = ProgressBarAnimator()
        
        # Set invalid targets
        bar.set_target(1.5)  # Above max
        assert bar.target_progress == 1.0
        
        bar.set_target(-0.5)  # Below min
        assert bar.target_progress == 0.0
    
    def test_progress_bar_with_transition_screen(self, mock_deps):
        """Test that transition screen integrates progress bar animator."""
        from src.screens.planet_transition import PlanetTransitionScreen
        from src.screens.planet_transition import PlanetInfo
        
        transition_screen = PlanetTransitionScreen(
            mock_deps['typography'],
            mock_deps['audio']
        )
        
        # After creating components, should have progress bar animator
        assert transition_screen.progress_bar_animator is None  # Not initialized yet
        
        # Start transition - should create animator
        from_planet = PlanetInfo("p1", "Alpha", 1, 12)
        to_planet = PlanetInfo("p2", "Beta", 2, 12)
        
        transition_screen.start_transition(
            from_planet=from_planet,
            to_planet=to_planet,
            galaxy_progress=0.1
        )
        
        assert transition_screen.progress_bar_animator is not None
        assert transition_screen.progress_bar_animator.progress == 0.0


class TestAnimationComponents:
    """Integration tests for animation components working together."""
    
    def test_star_field_motion_with_progress(self):
        """Test star field motion correlates with animation progress."""
        from src.ui.animations import StarField
        
        star_field = StarField(width=800, height=600, num_stars=50)
        
        initial_offset = star_field.motion_offset
        
        # Update with different progress values
        for progress in [0.1, 0.3, 0.5, 0.7, 1.0]:
            star_field.update(progress=progress, delta_time=0.016)
        
        # Motion offset should have increased
        assert star_field.motion_offset > initial_offset
    
    def test_rocket_flame_animates(self, mock_deps):
        """Test rocket flame animation over time."""
        from src.ui.animations import RocketAnimator
        
        rocket = RocketAnimator()
        
        initial_flame = rocket.flame_offset
        initial_direction = rocket.flame_direction
        
        # Update flame over time
        rocket.update(current_time=0.0)
        rocket.update(current_time=0.2)  # 0.2s should trigger animation
        rocket.update(current_time=0.4)
        
        # Flame should have animated (either offset or direction changed)
        assert rocket.flame_offset != initial_flame or rocket.flame_direction != initial_direction
    
    def test_combined_transition_scenario(self, mock_deps, planet_info_sample):
        """Test all animation components working together in transition."""
        from src.screens.planet_transition import PlanetTransitionScreen
        import pygame
        
        pygame.display.init()
        
        from_planet = planet_info_sample['mercury']
        to_planet = planet_info_sample['venus']
        
        transition_screen = PlanetTransitionScreen(
            mock_deps['typography'],
            mock_deps['audio']
        )
        transition_screen.width = 800
        transition_screen.height = 600
        
        # Start transition
        transition_screen.start_transition(
            from_planet=from_planet,
            to_planet=to_planet,
            galaxy_progress=0.083
        )
        
        # Verify all components exist
        assert transition_screen.rocket_animator is not None
        assert transition_screen.star_field is not None
        assert transition_screen.progress_bar_animator is not None
        
        # Run animation loop through entire transition
        delta_time = 0.016  # ~60 FPS
        frames = int(2.0 / delta_time)  # 2 second animation
        
        for frame in range(frames):
            transition_screen.update(delta_time=delta_time)
        
        # Verify components updated during animation
        # Star field should have stars and maintain state
        assert len(transition_screen.star_field.stars) > 0
        assert transition_screen.animation_progress >= 1.0
        
        pygame.display.quit()
        
        # Should complete cleanly
        assert transition_screen.is_complete()


class TestTransitionFeatures:
    """Tests for additional transition features (low priority items)."""
    
    def test_skip_animation_lock_prevents_multiple_triggers(self, mock_deps, planet_info_sample):
        """Test that skip animation lock prevents multiple skip triggers during animation."""
        import pygame
        from src.screens.planet_transition import PlanetTransitionScreen
        
        from_planet = planet_info_sample['mercury']
        to_planet = planet_info_sample['venus']
        transition_screen = PlanetTransitionScreen(
            mock_deps['typography'],
            mock_deps['audio']
        )
        
        # Start transition
        transition_screen.start_transition(
            from_planet=from_planet,
            to_planet=to_planet,
            galaxy_progress=0.083
        )
        
        assert transition_screen._skip_lock == False
        
        # First skip request
        fake_event = MagicMock()
        fake_event.type = pygame.KEYDOWN
        fake_event.key = pygame.K_SPACE
        transition_screen.handle_events([fake_event])
        
        assert transition_screen.skip_requested == True
        assert transition_screen._skip_lock == True  # Lock is set
        
        # Second skip request should be ignored due to lock
        fake_event2 = MagicMock()
        fake_event2.type = pygame.KEYDOWN
        fake_event2.key = pygame.K_SPACE
        transition_screen.handle_events([fake_event2])
        
        # Lock should still be in place
        assert transition_screen._skip_lock == True
        
        # Simulate animation completing (lock should release)
        transition_screen.animation_progress = 1.0
        transition_screen._complete_transition()
        
        # Now lock should be released
        assert transition_screen._skip_lock == False
    
    def test_set_animation_duration(self, mock_deps, planet_info_sample):
        """Test that animation duration can be configured."""
        from src.screens.planet_transition import PlanetTransitionScreen
        
        transition_screen = PlanetTransitionScreen(
            mock_deps['typography'],
            mock_deps['audio']
        )
        
        # Default duration
        assert transition_screen.animation_duration == 2.0
        
        # Set new duration
        transition_screen.set_animation_duration(3.5)
        assert transition_screen.animation_duration == 3.5
        
        # Test clamping to minimum (0.5s)
        transition_screen.set_animation_duration(0.1)
        assert transition_screen.animation_duration == 0.5
        
        # Test clamping to maximum (5.0s)
        transition_screen.set_animation_duration(10.0)
        assert transition_screen.animation_duration == 5.0

    def test_skip_lock_releases_after_animation(self, mock_deps, planet_info_sample):
        """Test that skip lock is automatically released when animation completes."""
        import pygame
        from src.screens.planet_transition import PlanetTransitionScreen
        
        from_planet = planet_info_sample['mercury']
        to_planet = planet_info_sample['venus']
        transition_screen = PlanetTransitionScreen(
            mock_deps['typography'],
            mock_deps['audio']
        )
        
        # Start transition
        transition_screen.start_transition(
            from_planet=from_planet,
            to_planet=to_planet,
            galaxy_progress=0.083
        )
        
        # Request skip
        fake_event = MagicMock()
        fake_event.type = pygame.KEYDOWN
        fake_event.key = pygame.K_SPACE
        transition_screen.handle_events([fake_event])
        
        assert transition_screen._skip_lock == True
        
        # Complete animation
        transition_screen.update(delta_time=2.0)
        
        # Lock should be released after completion
        assert transition_screen._skip_lock == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

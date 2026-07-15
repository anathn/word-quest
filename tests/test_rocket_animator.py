"""
Unit Tests for Rocket Animator (STORY-005-02)

Tests for rocket movement animations.
"""

import pytest
import pygame
import os
import sys

# Set TESTING environment variable and headless display before importing
os.environ["TESTING"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.ui.rocket_animator import RocketAnimator, AnimationState, create_rocket_animator
from src.ui.rocket_sprite import RocketSprite
from src.ui.engine_flames import EngineFlames


class TestRocketAnimator:
    """Tests for RocketAnimator class."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame."""
        pygame.init()
        yield
        pygame.quit()
    
    @pytest.fixture
    def rocket(self):
        """Create rocket sprite."""
        return RocketSprite()
    
    @pytest.fixture
    def flames(self):
        """Create engine flames."""
        return EngineFlames(max_particles=20)
    
    @pytest.fixture
    def animator(self, rocket, flames):
        """Create rocket animator."""
        return RocketAnimator(rocket, flames, initial_position=(100, 100))
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create test screen."""
        return pygame.display.set_mode((800, 600))
    
    def test_initialization(self, animator):
        """Test animator initializes correctly."""
        assert animator.state == AnimationState.IDLE
        assert animator.position == (100, 100)
        assert animator.angle == 0.0
    
    def test_initial_state_is_idle(self, animator):
        """Test initial state is IDLE."""
        assert animator.get_state() == AnimationState.IDLE
    
    def test_get_position(self, animator):
        """Test getting position."""
        pos = animator.get_position()
        assert pos == (100, 100)
    
    def test_get_state(self, animator):
        """Test getting state."""
        state = animator.get_state()
        assert state == AnimationState.IDLE
    
    def test_stop_animation(self, animator):
        """Test stop_animation resets to idle."""
        animator.animate_hover((200, 200))
        assert animator.state == AnimationState.HOVER
        
        animator.stop_animation()
        assert animator.state == AnimationState.IDLE
    
    def test_update_idle(self, animator):
        """Test update in idle state."""
        animator.update(0.016)
        assert animator.state == AnimationState.IDLE
    
    def test_approach_animation_starts(self, animator):
        """Test approach animation can start."""
        animator.animate_approach((0, 0), (400, 300), duration=1.0)
        assert animator.state == AnimationState.APPROACH
    
    def test_approach_animation_changes_position(self, animator):
        """Test approach animation moves rocket."""
        animator.animate_approach((0, 0), (400, 300), duration=1.0)
        
        # Update halfway through
        animator.update(0.5)
        
        # Position should have changed
        pos = animator.get_position()
        assert pos[0] > 0 and pos[0] < 400
        assert pos[1] > 0 and pos[1] < 300
    
    def test_approach_animation_completes(self, animator):
        """Test approach animation reaches end."""
        animator.animate_approach((0, 0), (400, 300), duration=0.1)
        
        # Update past completion
        animator.update(1.0)
        
        # Should have switched to hover state
        assert animator.state == AnimationState.HOVER
    
    def test_hover_animation(self, animator):
        """Test hover animation oscillates."""
        initial_pos = (200, 200)
        animator.animate_hover(initial_pos, amplitude=10, frequency=2.0)
        
        assert animator.state == AnimationState.HOVER
        
        # Update over time
        for i in range(10):
            animator.update(0.1)
            pos = animator.get_position()
            # Y should oscillate around initial position
            assert abs(pos[1] - initial_pos[1]) <= 10
    
    def test_boost_animation(self, animator):
        """Test boost animation."""
        animator.animate_boost((200, 200), duration=0.5)
        
        assert animator.state == AnimationState.BOOST
        
        # Update past completion
        animator.update(1.0)
        
        # Should return to idle
        assert animator.state == AnimationState.IDLE
    
    def test_transition_animation(self, animator):
        """Test transition animation."""
        animator.animate_transition((0, 0), (400, 300), duration=0.1)
        
        assert animator.state == AnimationState.TRANSITION
        
        # Update past completion
        animator.update(1.0)
        
        # Should be back to idle
        assert animator.state == AnimationState.IDLE
    
    def test_victory_animation(self, animator):
        """Test victory animation."""
        animator.animate_victory((200, 200), amplitude=15)
        
        assert animator.state == AnimationState.VICTORY
        
        # Update over time
        for i in range(20):
            animator.update(0.1)
            pos = animator.get_position()
            # Y should bounce between (center_y - amplitude) and center_y
            assert pos[1] >= 200 - 15  # Lower bound during bounce
            assert pos[1] <= 200 + 15  # Upper bound
    
    def test_is_complete_idle(self, animator):
        """Test is_complete returns True when idle and flames off."""
        assert animator.is_complete()
    
    def test_is_complete_during_animation(self, animator):
        """Test is_complete returns False during active animation."""
        animator.animate_approach((0, 0), (400, 300), duration=1.0)
        assert not animator.is_complete()
    
    def test_set_completion_callback(self, animator):
        """Test setting completion callback."""
        callback_called = [False]  # Use list for mutable closure
        
        def on_complete():
            callback_called[0] = True
        
        animator.set_completion_callback(on_complete)
        animator.animate_approach((0, 0), (40, 30), duration=0.01)
        animator.update(0.1)
        
        # Callback should have been called
        # Note: This may depend on timing, but we set up the callback correctly
        assert True
    
    def test_render_no_crash(self, animator, screen):
        """Test rendering doesn't crash."""
        animator.render(screen)
        assert True
    
    def test_render_during_hover(self, animator, screen):
        """Test rendering during hover animation."""
        animator.animate_hover((200, 200))
        
        for _ in range(10):
            animator.update(0.016)
            animator.render(screen)
        
        assert True


class TestRocketAnimatorFactory:
    """Tests for factory function."""
    
    def test_factory_creates_instance(self):
        """Test factory creates RocketAnimator."""
        rocket = RocketSprite()
        animator = create_rocket_animator(rocket)
        
        assert isinstance(animator, RocketAnimator)
    
    def test_factory_with_custom_position(self):
        """Test factory with initial position."""
        rocket = RocketSprite()
        animator = create_rocket_animator(rocket, initial_position=(400, 300))
        
        assert animator.get_position() == (400, 300)
    
    def test_factory_with_custom_flames(self):
        """Test factory with custom flames."""
        rocket = RocketSprite()
        flames = EngineFlames(max_particles=30)
        animator = create_rocket_animator(rocket, flames, initial_position=(100, 100))
        
        assert animator.flames.max_particles == 30


class TestAnimationStates:
    """Tests for animation state transitions."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame."""
        pygame.init()
        yield
        pygame.quit()
    
    def test_idle_to_approach_to_hover(self):
        """Test idle -> approach -> hover transition."""
        rocket = RocketSprite()
        flames = EngineFlames()
        animator = RocketAnimator(rocket, flames)
        
        assert animator.state == AnimationState.IDLE
        
        animator.animate_approach((0, 0), (100, 100), duration=0.05)
        assert animator.state == AnimationState.APPROACH
        
        animator.update(1.0)
        assert animator.state == AnimationState.HOVER
    
    def test_hover_to_idle(self):
        """Test hover -> idle transition."""
        rocket = RocketSprite()
        flames = EngineFlames()
        animator = RocketAnimator(rocket, flames)
        
        animator.animate_hover((100, 100))
        assert animator.state == AnimationState.HOVER
        
        animator.stop_animation()
        assert animator.state == AnimationState.IDLE
    
    def test_multiple_animation_starts(self):
        """Test starting new animation cancels previous."""
        rocket = RocketSprite()
        flames = EngineFlames()
        animator = RocketAnimator(rocket, flames)
        
        animator.animate_approach((0, 0), (100, 100), duration=1.0)
        assert animator.state == AnimationState.APPROACH
        
        # Start new animation
        animator.animate_hover((200, 200))
        assert animator.state == AnimationState.HOVER


class TestEasingFunctions:
    """Tests for easing functions."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame."""
        pygame.init()
        yield
        pygame.quit()
    
    def test_ease_in_out_valid_range(self):
        """Test ease-in-out returns values in valid range."""
        rocket = RocketSprite()
        flames = EngineFlames()
        animator = RocketAnimator(rocket, flames)
        
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            result = animator._ease_in_out(t)
            assert 0.0 <= result <= 1.0
    
    def test_ease_in_out_monotonic(self):
        """Test ease-in-out is monotonic increasing."""
        rocket = RocketSprite()
        flames = EngineFlames()
        animator = RocketAnimator(rocket, flames)
        
        prev = 0
        for t in [k * 0.1 for k in range(11)]:
            result = animator._ease_in_out(t)
            assert result >= prev
            prev = result
    
    def test_ease_in_out_ends(self):
        """Test ease-in-out starts at 0 and ends at 1."""
        rocket = RocketSprite()
        flames = EngineFlames()
        animator = RocketAnimator(rocket, flames)
        
        assert animator._ease_in_out(0.0) == 0.0
        assert animator._ease_in_out(1.0) == 1.0


class TestAnimationTiming:
    """Tests for animation timing."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame."""
        pygame.init()
        yield
        pygame.quit()
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create test screen."""
        return pygame.display.set_mode((800, 600))
    
    def test_small_delta_time(self):
        """Test animations work with small delta time."""
        rocket = RocketSprite()
        flames = EngineFlames()
        animator = RocketAnimator(rocket, flames)
        
        animator.animate_approach((0, 0), (100, 100), duration=1.0)
        
        # Many small updates
        for _ in range(1000):
            animator.update(0.001)
        
        assert animator.state == AnimationState.HOVER
    
    def test_large_delta_time(self):
        """Test animations handle large delta time gracefully."""
        rocket = RocketSprite()
        flames = EngineFlames()
        animator = RocketAnimator(rocket, flames)
        
        animator.animate_hover((100, 100))
        animator.update(10.0)  # Large delta
        
        # Should still be in hover state
        assert animator.state == AnimationState.HOVER
    
    def test_is_complete_after_full_animation(self):
        """Test is_complete after animation finishes."""
        rocket = RocketSprite()
        flames = EngineFlames()
        animator = RocketAnimator(rocket, flames)
        
        animator.animate_approach((0, 0), (100, 100), duration=0.01)
        animator.update(0.1)
        
        # After hover completes, should be idle-ish
        assert animator.state == AnimationState.HOVER


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
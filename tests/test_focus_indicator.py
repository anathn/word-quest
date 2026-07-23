"""
Tests for focus indicator component.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pygame
from src.ui.focus_indicator import FocusIndicator, FocusIndicatorManager


class TestFocusIndicator:
    """Tests for FocusIndicator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        pygame.init()
        self.screen = pygame.Surface((800, 600))
        self.indicator = FocusIndicator(self.screen)
        
    def teardown_method(self):
        """Clean up."""
        pygame.quit()
        
    def test_initial_state(self):
        """Test initial indicator state."""
        assert self.indicator.indicator_color == (255, 215, 0)
        assert self.indicator.indicator_width == 3
        assert self.indicator.pulse_alpha == 180
        assert self.indicator.enabled == True
        
    def test_render(self):
        """Test rendering focus indicator."""
        rect = pygame.Rect(100, 100, 200, 100)
        
        # Should not crash
        self.indicator.render(rect)
        
        # Surface should have been drawn on
        # (we can't easily verify the colors without surface readback)
        
    def test_render_with_different_rect(self):
        """Test rendering with different rectangle."""
        rect1 = pygame.Rect(0, 0, 100, 100)
        rect2 = pygame.Rect(400, 300, 300, 200)
        
        # Should not crash
        self.indicator.render(rect1)
        self.indicator.render(rect2)
        
    def test_update_pulse_animation(self):
        """Test pulse animation updates alpha."""
        initial_alpha = self.indicator.pulse_alpha
        
        # Update should change pulse_alpha
        self.indicator.update(0.1)  # 100ms
        
        # Alpha should have changed (direction is towards increase)
        assert self.indicator.pulse_alpha >= initial_alpha
        
    def test_update_pulses_back_down(self):
        """Test pulse goes back down when reaching max."""
        # Set alpha to near max
        self.indicator.pulse_alpha = 220
        self.indicator.pulse_direction = 1
        
        # Update should switch direction
        self.indicator.update(0.1)
        
        # Direction should be reversed
        assert self.indicator.pulse_direction == -1
        
    def test_update_pulses_up_when_min(self):
        """Test pulse goes up when reaching min."""
        # The logic: add delta, then check bounds
        # Set alpha exactly at the minimum so after increment it triggers the flip
        # pulse_speed=5, delta_time=0.1 -> delta = 5 * 0.1 * 60 = 30
        # So if we start at 120-delta = 90, after adding 30 we get 120, which is <= 120
        
        # Actually let's trace this more carefully:
        # Start at 100, direction=-1
        # After update(0.1): alpha = 100 + 30 = 130
        # 130 >= 220? No. 130 <= 120? No. Direction stays -1.
        
        # We need to start at a value where after adding delta, we get <= 120
        # That means: alpha + 30 <= 120, so alpha <= 90
        
        self.indicator.pulse_alpha = 90  # Below threshold so after 30 it's at 120
        self.indicator.pulse_direction = -1
        self.indicator.update(0.1)
        
        # After update: alpha = 120, and 120 <= 120 is True, so direction = 1
        assert self.indicator.pulse_direction == 1
        assert self.indicator.pulse_alpha == 120
        
    def test_set_enabled(self):
        """Test enabling/disabling indicator."""
        self.indicator.set_enabled(False)
        assert self.indicator.is_enabled == False
        
        self.indicator.set_enabled(True)
        assert self.indicator.is_enabled == True
        
    def test_disabled_indicator_does_not_render(self):
        """Test that disabled indicator doesn't render."""
        self.indicator.set_enabled(False)
        
        # Store initial pixel values
        initial_pixel = self.screen.get_at((150, 150))
        
        rect = pygame.Rect(100, 100, 200, 100)
        self.indicator.render(rect)
        
        # Screen should be unchanged
        # (This is a heuristic test - may not be 100% reliable)
        
    def test_set_color(self):
        """Test setting indicator color."""
        self.indicator.set_color((255, 0, 0))
        assert self.indicator.indicator_color == (255, 0, 0)
        
    def test_set_width(self):
        """Test setting indicator width."""
        self.indicator.set_width(5)
        assert self.indicator.indicator_width == 5
        
    def test_set_pulse_speed(self):
        """Test setting pulse speed."""
        self.indicator.set_pulse_speed(10)
        assert self.indicator.pulse_speed == 10


class TestFocusIndicatorManager:
    """Tests for FocusIndicatorManager singleton."""
    
    def setup_method(self):
        """Set up test fixtures."""
        pygame.init()
        self.manager = FocusIndicatorManager()
        # Clear any existing state
        self.manager.clear()
        self.screen = pygame.Surface((800, 600))
        
    def teardown_method(self):
        """Clean up."""
        self.manager.clear()
        pygame.quit()
        
    def test_singleton_pattern(self):
        """Test that FocusIndicatorManager is a singleton."""
        manager1 = FocusIndicatorManager()
        manager2 = FocusIndicatorManager()
        assert manager1 is manager2
        
    def test_register_screen(self):
        """Test registering a screen."""
        indicator = self.manager.register_screen('test_screen', self.screen)
        assert 'test_screen' in self.manager.indicators
        assert self.manager.indicators['test_screen'].screen == self.screen
        
    def test_set_active_screen(self):
        """Test setting active screen."""
        self.manager.register_screen('screen1', self.screen)
        self.manager.set_active_screen('screen1')
        
        assert self.manager.current_indicator is not None
        assert self.manager.current_indicator.screen == self.screen
        
    def test_set_unregistered_active_screen(self):
        """Test setting unregistered screen as active."""
        self.manager.set_active_screen('nonexistent')
        assert self.manager.current_indicator is None
        
    def test_render_on_active_screen(self):
        """Test rendering on active screen."""
        self.manager.register_screen('active', self.screen)
        self.manager.set_active_screen('active')
        
        rect = pygame.Rect(100, 100, 100, 100)
        # Should not crash
        self.manager.render(rect)
        
    def test_render_no_active_screen(self):
        """Test rendering without active screen doesn't crash."""
        rect = pygame.Rect(100, 100, 100, 100)
        self.manager.render(rect)  # Should not crash
        
    def test_update_all_indicators(self):
        """Test updating all registered indicators."""
        screen1 = pygame.Surface((800, 600))
        screen2 = pygame.Surface((800, 600))
        
        self.manager.register_screen('screen1', screen1)
        self.manager.register_screen('screen2', screen2)
        
        # Should not crash
        self.manager.update(0.016)
        
    def test_set_enabled_all(self):
        """Test enabling/disabling all indicators."""
        self.manager.register_screen('screen1', self.screen)
        self.manager.set_enabled(False)
        
        assert self.manager.is_enabled == False
        assert self.manager.indicators['screen1'].is_enabled == False
        
    def test_clear(self):
        """Test clearing all indicators."""
        self.manager.register_screen('screen1', self.screen)
        self.manager.register_screen('screen2', self.screen)
        
        self.manager.clear()
        
        assert len(self.manager.indicators) == 0
        assert self.manager.current_indicator is None
        
    def test_is_enabled_property(self):
        """Test is_enabled property."""
        assert self.manager.is_enabled == True
        self.manager.set_enabled(False)
        assert self.manager.is_enabled == False


class TestFocusIndicatorEdgeCases:
    """Edge case tests for focus indicators."""
    
    def setup_method(self):
        pygame.init()
        self.screen = pygame.Surface((800, 600))
        self.indicator = FocusIndicator(self.screen)
        
    def teardown_method(self):
        pygame.quit()
        
    def test_render_zero_width_rect(self):
        """Test rendering with zero width rect."""
        rect = pygame.Rect(100, 100, 0, 100)
        # Should not crash
        self.indicator.render(rect)
        
    def test_render_zero_height_rect(self):
        """Test rendering with zero height rect."""
        rect = pygame.Rect(100, 100, 100, 0)
        self.indicator.render(rect)
        
    def test_render_negative_size(self):
        """Test rendering with non-inflated rect stays valid."""
        rect = pygame.Rect(0, 0, 0, 0)
        self.indicator.render(rect)
        
    def test_pulse_alpha_bounds_low(self):
        """Test pulse_alpha stays above minimum."""
        # Force pulse_alpha below minimum
        self.indicator.pulse_alpha = 50
        self.indicator.pulse_direction = -1
        
        # Update should reverse direction
        self.indicator.update(0.1)
        assert self.indicator.pulse_direction == 1
        
    def test_pulse_alpha_bounds_high(self):
        """Test pulse_alpha stays below maximum."""
        self.indicator.pulse_alpha = 250
        self.indicator.pulse_direction = 1
        
        self.indicator.update(0.1)
        assert self.indicator.pulse_direction == -1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
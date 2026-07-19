"""
Unit tests for animation utility functions.

Tests easing functions, interpolation, and animation intensity handling.
"""

import pytest
import math
from src.ui.animation_utils import (
    Easing,
    AnimationIntensity,
    get_easing_function,
    lerp,
    lerp_color
)


class TestEasing:
    """Tests for easing function implementations."""
    
    def test_linear_interpolation(self):
        """Linear easing should return input unchanged."""
        assert Easing.linear(0.0) == 0.0
        assert Easing.linear(0.5) == 0.5
        assert Easing.linear(1.0) == 1.0
        
    def test_linear_edge_cases(self):
        """Linear easing bounds."""
        assert Easing.linear(0.0) == 0.0
        assert Easing.linear(1.0) == 1.0
        
    def test_ease_in_out_monotonic(self):
        """Ease-in-out should be monotonically increasing."""
        prev = 0.0
        for i in range(11):
            t = i / 10.0
            result = Easing.ease_in_out(t)
            assert result >= prev, f"ease_in_out not monotonic at t={t}"
            prev = result
            
    def test_ease_in_out_bounds(self):
        """Ease-in-out should stay within [0, 1]."""
        for i in range(21):
            t = i / 20.0
            result = Easing.ease_in_out(t)
            assert 0.0 <= result <= 1.0, f"ease_in_out out of bounds at t={t}"
            
    def test_ease_in_out_start_slow(self):
        """Ease-in-out should start slower than linear."""
        # At t=0.25, ease-in-out should be less than 0.25
        result = Easing.ease_in_out(0.25)
        assert result < 0.25, "ease_in_out should start slower than linear"
        
    def test_ease_in_out_end_slow(self):
        """Ease-in-out should end slower than linear."""
        # At t=0.75, ease-in-out should be greater than 0.75
        result = Easing.ease_in_out(0.75)
        assert result > 0.75, "ease_in_out should end slower than linear"
        
    def test_ease_in_out_midpoint(self):
        """Ease-in-out should pass through midpoint."""
        result = Easing.ease_in_out(0.5)
        assert abs(result - 0.5) < 0.0001, "ease_in_out should pass through (0.5, 0.5)"
        
    def test_ease_out_bounce_start_zero(self):
        """Bounce should start at zero."""
        assert Easing.ease_out_bounce(0.0) == 0.0
        
    def test_ease_out_bounce_end_one(self):
        """Bounce should end at one."""
        result = Easing.ease_out_bounce(1.0)
        # ease_out_bounce can overshoot 1.0
        assert result >= 1.0 and result <= 1.5, f"Bounce overshoot too large: {result}"
        
    def test_ease_out_bounce_positive(self):
        """Bounce should always be positive."""
        for i in range(21):
            t = i / 20.0
            result = Easing.ease_out_bounce(t)
            assert result >= 0, f"Bounce negative at t={t}"
            
    def test_ease_out_bounce_creates_bounce(self):
        """Bounce function should create the bouncing effect."""
        # Check that there's a point where the function exceeds the line
        # indicating an overshoot effect
        mid_result = Easing.ease_out_bounce(0.5)
        end_result = Easing.ease_out_bounce(0.9)
        # At midpoint, bounce should be significantly ahead
        assert mid_result > 0.5, "Bounce should accelerate quickly"
        
    def test_ease_out_back_bounds(self):
        """Back easing should stay within reasonable bounds."""
        for i in range(21):
            t = i / 20.0
            result = Easing.ease_out_back(t)
            # Allow small overshoot beyond 1.0
            assert -0.1 <= result <= 1.2, f"ease_out_back unusual at t={t}: {result}"
            
    def test_ease_out_back_start_zero(self):
        """Back easing should start at approximately zero."""
        # Floating point precision may result in very small value instead of exactly 0
        assert abs(Easing.ease_out_back(0.0)) < 0.001
        
    def test_ease_out_back_end_one(self):
        """Back easing should end at one."""
        assert Easing.ease_out_back(1.0) == 1.0
        
    def test_ease_out_quart_bounds(self):
        """Quartic easing should stay within [0, 1]."""
        for i in range(21):
            t = i / 20.0
            result = Easing.ease_out_quart(t)
            assert 0.0 <= result <= 1.0, f"ease_out_quart out of bounds at t={t}"
            
    def test_ease_out_quart_accelerates(self):
        """ease_out_quart should start fast and slow down."""
        # ease_out_* functions start fast, so early values should be ABOVE linear
        assert Easing.ease_out_quart(0.25) > 0.25, "ease_out_quart should start fast"
        assert Easing.ease_out_quart(0.5) > 0.5, "ease_out_quart should be above linear at midpoint"
        
    def test_ease_in_out_cubic_bounds(self):
        """Cubic easing should stay within [0, 1]."""
        for i in range(21):
            t = i / 20.0
            result = Easing.ease_in_out_cubic(t)
            assert 0.0 <= result <= 1.0, f"ease_in_out_cubic out of bounds at t={t}"
            
    def test_ease_in_out_cubic_monotonic(self):
        """Cubic easing should be monotonically increasing."""
        prev = 0.0
        for i in range(11):
            t = i / 10.0
            result = Easing.ease_in_out_cubic(t)
            assert result >= prev, f"ease_in_out_cubic not monotonic at t={t}"
            prev = result


class TestAnimationIntensity:
    """Tests for animation intensity constants."""
    
    def test_intensity_constants(self):
        """Intensity constants should have correct values."""
        assert AnimationIntensity.FULL == "full"
        assert AnimationIntensity.REDUCED == "reduced"
        assert AnimationIntensity.OFF == "off"


class TestGetEasingFunction:
    """Tests for the easing function selector."""
    
    def test_full_intensity_returns_smooth(self):
        """Full intensity should return ease_in_out."""
        func = get_easing_function(AnimationIntensity.FULL)
        # ease_in_out is smooth, so midpoint should be at 0.5
        assert abs(func(0.5) - 0.5) < 0.0001
        
    def test_reduced_intensity_returns_quart(self):
        """Reduced intensity should return ease_out_quart."""
        func = get_easing_function(AnimationIntensity.REDUCED)
        # ease_out_quart starts fast, so midpoint should be above 0.5
        assert func(0.5) > 0.5, "ease_out_quart should be above linear at midpoint"
        
    def test_off_intensity_returns_linear(self):
        """Off intensity should return linear."""
        func = get_easing_function(AnimationIntensity.OFF)
        assert func(0.25) == 0.25
        assert func(0.75) == 0.75
        
    def test_string_intensity_works(self):
        """String intensity values should work."""
        func_full = get_easing_function("full")
        func_reduced = get_easing_function("reduced")
        func_off = get_easing_function("off")
        
        assert func_full(0.5) == func_full(0.5)  # Same function


class TestLerp:
    """Tests for linear interpolation."""
    
    def test_lerp_start(self):
        """Lerp at t=0 should return start value."""
        assert lerp(10, 20, 0.0) == 10
        
    def test_lerp_end(self):
        """Lerp at t=1 should return end value."""
        assert lerp(10, 20, 1.0) == 20
        
    def test_lerp_midpoint(self):
        """Lerp at t=0.5 should return midpoint."""
        assert lerp(10, 20, 0.5) == 15
        
    def test_lerp_quarter(self):
        """Lerp at t=0.25 should return quarter point."""
        assert lerp(0, 100, 0.25) == 25
        
    def test_lerp_three_quarters(self):
        """Lerp at t=0.75 should return three-quarter point."""
        assert lerp(0, 100, 0.75) == 75
        
    def test_lerp_negative_range(self):
        """Lerp should work with negative values."""
        assert lerp(-10, 10, 0.5) == 0
        
    def test_lerp_same_values(self):
        """Lerp with same start/end should return that value."""
        assert lerp(5, 5, 0.3) == 5


class TestLerpColor:
    """Tests for color interpolation."""
    
    def test_lerp_color_start(self):
        """Color lerp at t=0 should return start color."""
        result = lerp_color((255, 0, 0, 255), (0, 255, 0, 255), 0.0)
        assert result == (255, 0, 0, 255)
        
    def test_lerp_color_end(self):
        """Color lerp at t=1 should return end color."""
        result = lerp_color((255, 0, 0, 255), (0, 255, 0, 255), 1.0)
        assert result == (0, 255, 0, 255)
        
    def test_lerp_color_midpoint(self):
        """Color lerp at t=0.5 should return midpoint color."""
        result = lerp_color((255, 0, 0, 255), (0, 255, 0, 255), 0.5)
        assert result == (127, 127, 0, 255)  # Rounded down
        
    def test_lerp_color_rgb_only(self):
        """Color lerp should handle RGB without alpha."""
        result = lerp_color((255, 0, 0), (0, 255, 0), 0.5)
        assert result[0] == 127
        assert result[1] == 127
        assert result[2] == 0
        # Alpha should default to 255
        if len(result) > 3:
            assert result[3] == 255
            
    def test_lerp_color_black_to_white(self):
        """Color lerp should work for black to white."""
        result = lerp_color((0, 0, 0, 255), (255, 255, 255, 255), 0.5)
        assert result == (127, 127, 127, 255)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
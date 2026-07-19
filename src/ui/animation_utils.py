"""
Animation utility functions for easing and interpolation.

Provides common easing functions for smooth animations including
fade-in, bounce, and ease-in-out effects.
"""

import math
from typing import Callable


class Easing:
    """Collection of easing functions for smooth animations."""
    
    @staticmethod
    def linear(t: float) -> float:
        """Linear interpolation (no easing)."""
        return t
    
    @staticmethod
    def ease_in_out(t: float) -> float:
        """
        Smooth ease-in-out interpolation.
        
        Starts slow, speeds up in the middle, slows down at end.
        
        Args:
            t: Progress value from 0.0 to 1.0
            
        Returns:
            Interpolated value from 0.0 to 1.0
        """
        if t < 0.5:
            return 2 * t * t
        return 1 - math.pow(-2 * t + 2, 2) / 2
    
    @staticmethod
    def ease_out_bounce(t: float) -> float:
        """
        Bounce effect for letter appearance.
        
        Creates a bouncing ball effect when letter appears.
        
        Args:
            t: Progress value from 0.0 to 1.0
            
        Returns:
            Bounced value from 0.0 to 1.0
        """
        n1 = 7.5625
        d1 = 2.75
        
        if t < 1 / d1:
            return n1 * t * t
        elif t < 2 / d1:
            return n1 * (t - 1.5 / d1) * t + 0.75
        elif t < 2.5 / d1:
            return n1 * (t - 2.25 / d1) * t + 0.9375
        return n1 * (t - 2.625 / d1) * t + 0.984375
    
    @staticmethod
    def ease_out_back(t: float) -> float:
        """
        Slight overshoot/back effect.
        
        Letter appears and slightly overshoots before settling.
        
        Args:
            t: Progress value from 0.0 to 1.0
            
        Returns:
            Back effect value from 0.0 to 1.0
        """
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * math.pow(t - 1, 3) + c1 * math.pow(t - 1, 2)
    
    @staticmethod
    def ease_out_quart(t: float) -> float:
        """
        Ease out quartic function.
        
        Fast start, slows down quickly at end.
        
        Args:
            t: Progress value from 0.0 to 1.0
            
        Returns:
            Interpolated value from 0.0 to 1.0
        """
        return 1 - math.pow(1 - t, 4)
    
    @staticmethod
    def ease_in_out_cubic(t: float) -> float:
        """
        Cubic ease-in-out interpolation.
        
        Smooth cubic curve for natural motion.
        
        Args:
            t: Progress value from 0.0 to 1.0
            
        Returns:
            Interpolated value from 0.0 to 1.0
        """
        if t < 0.5:
            return 4 * t * t * t
        return 1 - math.pow(-2 * t + 2, 3) / 2


class AnimationIntensity:
    """Animation intensity levels for accessibility."""
    
    FULL = "full"
    REDUCED = "reduced"
    OFF = "off"


def get_easing_function(intensity: str) -> Callable[[float], float]:
    """
    Get the appropriate easing function based on animation intensity.
    
    Args:
        intensity: Animation intensity level (full, reduced, off)
        
    Returns:
        Easing function to use
    """
    if intensity == AnimationIntensity.OFF:
        return Easing.linear
    elif intensity == AnimationIntensity.REDUCED:
        return Easing.ease_out_quart
    else:  # FULL
        return Easing.ease_in_out


def lerp(start: float, end: float, t: float) -> float:
    """
    Linear interpolation between two values.
    
    Args:
        start: Starting value
        end: Ending value
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated value
    """
    return start + (end - start) * t


def lerp_color(start_color: tuple, end_color: tuple, t: float) -> tuple:
    """
    Linear interpolation between two colors.
    
    Args:
        start_color: Starting RGBA color tuple
        end_color: Ending RGBA color tuple
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated RGBA color tuple
    """
    return (
        int(lerp(start_color[0], end_color[0], t)),
        int(lerp(start_color[1], end_color[1], t)),
        int(lerp(start_color[2], end_color[2], t)),
        int(lerp(start_color[3], end_color[3], t)) if len(start_color) > 3 and len(end_color) > 3 else 255
    )
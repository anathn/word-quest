"""
Letter renderer for animated text display.

Handles rendering individual letters with fade, scale, and position
animations for engaging word presentation.
"""

import pygame
from typing import Tuple, Optional
from enum import Enum

from .animation_utils import Easing, lerp


class LetterState(Enum):
    """Animation state for a letter."""
    NONE = "none"
    FADE_IN = "fade_in"
    BOUNCE = "bounce"
    COMPLETE = "complete"


class LetterType(Enum):
    """Type of letter for styling purposes."""
    REGULAR = "regular"
    STARTER = "starter"
    HINT = "hint"
    TYPED = "typed"


class LetterRenderer:
    """
    Renders a single letter with animation effects.
    
    Supports fade-in, bounce, scale animations with different
    visual styles for starter letters, hint letters, and typed letters.
    """
    
    # Animation timing (in seconds)
    FADE_DURATION = 0.2  # 200ms fade
    BOUNCE_DURATION = 0.3  # 300ms bounce
    INSTANT_DURATION = 0.1  # 100ms for instant pop
    
    # Visual constants
    BASE_COLOR = (255, 255, 255)  # White
    STARTER_COLOR = (76, 175, 80)  # Green #4CAF50
    HINT_COLOR = (255, 152, 0)  # Orange #FF9800
    TYPED_COLOR = (255, 255, 255)  # White
    
    # Scale factors
    BASE_SCALE = 1.0
    BOUNCE_SCALE = 1.1  # 110% at peak
    POP_SCALE = 1.15  # 115% for instant pop
    
    def __init__(self, char: str, font: pygame.font.Font, size: int = 48):
        """
        Initialize a letter renderer.
        
        Args:
            char: The character to render
            font: Pygame font object
            size: Font size in points
        """
        self.char = char.upper()
        self.font = font
        self.size = size
        
        # Animation state
        self.state = LetterState.NONE
        self.animation_type = "fade_bounce"  # fade_bounce, fade_only, instant
        self.progress = 0.0
        self.start_time = 0.0
        
        # Visual properties
        self.letter_type = LetterType.REGULAR
        self.base_color = LetterRenderer.BASE_COLOR
        
        # Transform properties (updated during animation)
        self.scale = 0.0
        self.opacity = 0.0
        self.offset_y = 0.0  # For bounce effect
        
        # Cached surface
        self._surface: Optional[pygame.Surface] = None
        self._needs_rebuild = True
        
        # Position (set during rendering)
        self.position = (0, 0)
        
    def set_letter_type(self, letter_type: LetterType):
        """
        Set the type of letter (affects styling).
        
        Args:
            letter_type: Type of letter (regular, starter, hint, typed)
        """
        self.letter_type = letter_type
        
        # Set appropriate color
        if letter_type == LetterType.STARTER:
            self.base_color = LetterRenderer.STARTER_COLOR
        elif letter_type == LetterType.HINT:
            self.base_color = LetterRenderer.HINT_COLOR
        else:
            self.base_color = LetterRenderer.BASE_COLOR
            
        self._needs_rebuild = True
        
    def start_animation(self, animation_type: str = "fade_bounce", instant: bool = False):
        """
        Start the letter appearance animation.
        
        Args:
            animation_type: Type of animation (fade_bounce, fade_only, instant)
            instant: If True, show letter immediately without animation
        """
        self.animation_type = animation_type
        self.state = LetterState.FADE_IN
        self.progress = 0.0
        
        if instant:
            self.animation_type = "instant"
            self.progress = 1.0
            self.state = LetterState.COMPLETE
            self.scale = self.BASE_SCALE
            self.opacity = 255
            self.offset_y = 0
            
    def update(self, delta_time: float, intensity: str = "full"):
        """
        Update animation state based on elapsed time.
        
        Args:
            delta_time: Time since last update in milliseconds
            intensity: Animation intensity (full, reduced, off)
        """
        if self.state == LetterState.COMPLETE:
            return
            
        if self.animation_type == "instant":
            self.state = LetterState.COMPLETE
            self.progress = 1.0
            self.scale = self.BASE_SCALE
            self.opacity = 255
            self.offset_y = 0
            return
            
        # Calculate duration based on intensity
        if intensity == "off":
            duration = 0.01  # Virtually instant
        elif intensity == "reduced":
            duration = self.FADE_DURATION
        else:  # full
            duration = self.BOUNCE_DURATION
            
        # Update progress
        delta_seconds = delta_time / 1000.0
        self.progress += delta_seconds / duration
        
        if self.progress >= 1.0:
            self.progress = 1.0
            self.state = LetterState.COMPLETE
            
        # Calculate animation values based on progress and type
        self._calculate_animation_values(intensity)
        
    def _calculate_animation_values(self, intensity: str):
        """
        Calculate scale, opacity, and offset based on animation progress.
        
        Args:
            intensity: Animation intensity level
        """
        if self.animation_type == "instant" or self.state == LetterState.COMPLETE:
            self.scale = self.BASE_SCALE
            self.opacity = 255
            self.offset_y = 0
            return
            
        if intensity == "off":
            # Instant appearance
            self.scale = self.BASE_SCALE
            self.opacity = 255
            self.offset_y = 0
            return
            
        if self.animation_type == "fade_only" or intensity == "reduced":
            # Simple fade without bounce
            ease = Easing.ease_out_quart(self.progress)
            self.opacity = int(ease * 255)
            self.scale = self.BASE_SCALE
            self.offset_y = 0
        else:
            # Fade + bounce animation
            # Opacity uses ease-in-out
            fade_progress = Easing.ease_in_out(self.progress)
            self.opacity = int(fade_progress * 255)
            
            # Scale follows bounce curve
            if self.progress < 1.0:
                bounce_progress = Easing.ease_out_bounce(self.progress)
                self.scale = self.BASE_SCALE + (self.BOUNCE_SCALE - self.BASE_SCALE) * bounce_progress
                # Offset for bounce effect (letter moves up then down)
                self.offset_y = -10 * (1 - bounce_progress)  # Negative y is up in pygame
            else:
                self.scale = self.BASE_SCALE
                self.offset_y = 0
                
    def render(self, screen: pygame.Surface, position: Tuple[int, int]):
        """
        Render the letter to the screen at the given position.
        
        Args:
            screen: Pygame surface to render to
            position: (x, y) position for the letter
        """
        if self.char == "":
            return
            
        self.position = position
        
        # Rebuild surface if needed
        if self._needs_rebuild or self._surface is None:
            self._build_surface()
            
        if self._surface is None:
            return
            
        # Create a copy with the current opacity
        if self.opacity < 255:
            surface_copy = self._surface.copy()
            surface_copy.set_alpha(self.opacity)
        else:
            surface_copy = self._surface
            
        # Apply scale and offset
        if self.scale != self.BASE_SCALE:
            scaled_surface = pygame.transform.smoothscale(
                surface_copy,
                (int(surface_copy.get_width() * self.scale), 
                 int(surface_copy.get_height() * self.scale))
            )
        else:
            scaled_surface = surface_copy
            
        # Calculate final position with offset
        final_x = position[0]
        final_y = position[1] + self.offset_y
        
        # Blit to screen
        screen.blit(scaled_surface, (final_x, final_y))
        
    def _build_surface(self):
        """Build the letter surface with appropriate styling."""
        # Create surface for letter
        self._surface = self.font.render(self.char, True, self.base_color)
        self._needs_rebuild = False
        
    def set_starter_style(self):
        """Apply starter letter style (green tint)."""
        self.set_letter_type(LetterType.STARTER)
        
    def set_hint_style(self):
        """Apply hint-revealed letter style (orange highlight)."""
        self.set_letter_type(LetterType.HINT)
        
    def set_typed_style(self):
        """Apply typed letter style (instant appearance)."""
        self.set_letter_type(LetterType.TYPED)
        self.start_animation("instant", instant=True)
        
    def is_complete(self) -> bool:
        """
        Check if animation is complete.
        
        Returns:
            True if letter has finished animating
        """
        return self.state == LetterState.COMPLETE
        
    def get_width(self) -> int:
        """
        Get the width of the rendered letter.
        
        Returns:
            Width in pixels
        """
        if self._surface:
            return self._surface.get_width()
        return self.font.size(self.char)[0]
        
    def get_height(self) -> int:
        """
        Get the height of the rendered letter.
        
        Returns:
            Height in pixels
        """
        if self._surface:
            return self._surface.get_height()
        return self.font.size(self.char)[1]
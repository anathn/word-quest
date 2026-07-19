"""
Letter animation system manager.

Coordinates letter-by-letter animations for word presentation,
handling timing, sequencing, and lifecycle management.
"""

import pygame
from typing import List, Optional, Tuple
from dataclasses import dataclass

from .letter_renderer import LetterRenderer, LetterType, LetterState
from .animation_utils import AnimationIntensity


@dataclass
class AnimationConfig:
    """Configuration for letter animations."""
    
    # Timing (in seconds)
    animation_duration: float = 0.3  # 300ms per letter
    letter_delay: float = 0.15  # 150ms between letters
    starter_count: int = 2  # Number of starter letters
    
    # Visual
    font_size: int = 48
    letter_spacing: int = 20  # Pixels between letters
    base_color: Tuple[int, int, int] = (255, 255, 255)  # White
    
    # Animation type
    animation_type: str = "fade_bounce"  # fade_bounce, fade_only, instant
    
    # Accessibility
    intensity: str = AnimationIntensity.FULL


class LetterAnimator:
    """
    Manages animation state and timing for letter sequences.
    
    Coordinates letter-by-letter appearance with configurable
    timing, delays, and visual styles for different letter types.
    """
    
    def __init__(self, font: pygame.font.Font, config: Optional[AnimationConfig] = None):
        """
        Initialize the letter animator.
        
        Args:
            font: Pygame font object for rendering letters
            config: Animation configuration (uses defaults if None)
        """
        self.font = font
        self.config = config or AnimationConfig()
        
        # Letter collection
        self.letters: List[LetterRenderer] = []
        self.word = ""
        
        # Animation state
        self.current_index = 0
        self.is_animating = False
        self.last_update_time = 0
        
        # Timing
        self._letter_start_times: List[float] = []
        
    def set_word(self, word: str, starter_count: Optional[int] = None):
        """
        Initialize animator with a word and starter letters.
        
        Args:
            word: The word to animate
            starter_count: Number of starter letters (uses config default if None)
        """
        self.word = word.upper()
        starter_count = starter_count if starter_count is not None else self.config.starter_count
        
        # Create letter renderers
        self.letters = []
        for i, char in enumerate(self.word):
            letter = LetterRenderer(char, self.font, self.config.font_size)
            
            # Set appropriate letter type
            if i < starter_count:
                letter.set_starter_style()
            else:
                letter.set_letter_type(LetterType.REGULAR)
                
            self.letters.append(letter)
            
        # Reset animation state
        self.current_index = 0
        self.is_animating = False
        self._letter_start_times = []
        
    def start_animation(self):
        """Begin letter-by-letter animation sequence."""
        if not self.letters:
            return
            
        self.is_animating = True
        self.current_index = 0
        self.last_update_time = pygame.time.get_ticks()
        
        # Start first letter immediately
        if self.letters:
            self._start_letter(0)
            
    def _start_letter(self, index: int):
        """
        Start animation for a specific letter.
        
        Args:
            index: Index of letter to start
        """
        if index >= len(self.letters):
            return
            
        self._letter_start_times.append(pygame.time.get_ticks())
        self.letters[index].start_animation(self.config.animation_type)
        
    def update(self, deprecated: bool = True):
        """
        DEPRECATED: This method has been replaced by update_advanced().
        
        Updates all letter animations based on elapsed time.
        
        WARNING: This implementation has incorrect timing logic. Please use
        update_advanced() instead which correctly handles letter delays.
        
        Args:
            deprecated: Internal parameter to mark this as deprecated (do not use)
        """
        import warnings
        warnings.warn(
            "LetterAnimator.update() is deprecated. Use update_advanced() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        if not self.is_animating:
            return
            
        current_time = pygame.time.get_ticks()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Update all letters
        for letter in self.letters:
            if not letter.is_complete():
                letter.update(delta_time, self.config.intensity)
        
        # Check if current letter is complete, start next after delay
        if self.current_index < len(self.letters):
            current_letter = self.letters[self.current_index]
            
            if current_letter.is_complete():
                # Check if delay has passed before starting next letter
                if self.current_index > 0:
                    elapsed = current_time - self._letter_start_times[self.current_index - 1]
                    delay_ms = self.config.letter_delay * 1000
                    
                    if elapsed >= delay_ms * self.current_index:
                        self.current_index += 1
                        if self.current_index < len(self.letters):
                            self._start_letter(self.current_index)
                else:
                    # First letter just completed, start second after delay
                    self.current_index += 1
                    if self.current_index < len(self.letters):
                        # Schedule next letter
                        pass  # Will be started when we check again
                        
    def update_advanced(self):
        """
        Advanced update with proper letter delay timing.
        
        Call this each frame to advance animations with correct sequencing.
        """
        if not self.is_animating:
            return
            
        current_time = pygame.time.get_ticks()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Update all incomplete letters
        for letter in self.letters:
            if not letter.is_complete():
                letter.update(delta_time, self.config.intensity)
        
        # Start next letters based on elapsed time since animation began
        animation_start = self._letter_start_times[0] if self._letter_start_times else current_time
        elapsed_since_start = current_time - animation_start
        
        # Calculate which letters should have started by now
        # Letter i should start at i * letter_delay (relative to first letter)
        target_index = 0
        for i in range(len(self.letters)):
            needed_time = i * (self.config.letter_delay * 1000)
            if elapsed_since_start >= needed_time:
                target_index = i + 1
            else:
                break
        
        # Start letters that haven't started yet
        for i in range(min(target_index, len(self.letters))):
            if self.letters[i].state == LetterState.NONE:
                self._start_letter(i)
        
        # Check if all letters are complete
        if all(letter.is_complete() for letter in self.letters):
            self.is_animating = False
            
    def render(self, screen: pygame.Surface, position: Tuple[int, int]):
        """
        Render all letters at the given starting position.
        
        Args:
            screen: Pygame surface to render to
            position: (x, y) position for the first letter
        """
        x = position[0]
        y = position[1]
        
        for letter in self.letters:
            letter.render(screen, (x, y))
            x += letter.get_width() + self.config.letter_spacing
            
    def show_all_instantly(self):
        """
        Skip animation and show all letters immediately.
        
        Useful for accessibility mode or when user wants to see full word.
        """
        for letter in self.letters:
            letter.start_animation("instant", instant=True)
        self.is_animating = False
        
    def show_starter_letters(self):
        """
        Show only starter letters instantly.
        
        Used when starting a word, showing starter hints first.
        """
        starter_count = self.config.starter_count
        for i, letter in enumerate(self.letters):
            if i < starter_count:
                letter.start_animation("fade_bounce", instant=True)
            else:
                # Hide non-starter letters
                letter.opacity = 0
                letter.state = LetterState.NONE
                
    def is_complete(self) -> bool:
        """
        Check if all letters have finished animating.
        
        Returns:
            True if all animations are complete or no animation in progress
        """
        # If no letters exist, it's considered complete
        if not self.letters:
            return True
        # If not animating, check if all letters are either complete or not started
        # (letters with state NONE haven't started yet)
        if not self.is_animating:
            return all(
                letter.is_complete() or letter.state == LetterState.NONE
                for letter in self.letters
            )
        # While animating, all letters must be complete
        return all(letter.is_complete() for letter in self.letters)
        
    def is_animating_letter(self, index: int) -> bool:
        """
        Check if a specific letter is still animating.
        
        Args:
            index: Index of letter to check
            
        Returns:
            True if letter is still animating
        """
        if index >= len(self.letters):
            return False
        return not self.letters[index].is_complete()
        
    def get_completed_count(self) -> int:
        """
        Get number of letters that have completed animating.
        
        Returns:
            Count of completed letters
        """
        return sum(1 for letter in self.letters if letter.is_complete())
        
    def set_intensity(self, intensity: str):
        """
        Set animation intensity for accessibility.
        
        Args:
            intensity: Animation intensity (full, reduced, off)
        """
        self.config.intensity = intensity
        
    def get_word(self) -> str:
        """
        Get the current word being animated.
        
        Returns:
            The word string
        """
        return self.word
        
    def get_letter_count(self) -> int:
        """
        Get number of letters in the word.
        
        Returns:
            Letter count
        """
        return len(self.letters)


def create_letter_animator(font: pygame.font.Font, 
                          starter_count: int = 2,
                          letter_spacing: int = 20,
                          intensity: str = AnimationIntensity.FULL) -> LetterAnimator:
    """
    Factory function to create a configured LetterAnimator.
    
    Args:
        font: Pygame font object
        starter_count: Number of starter letters
        letter_spacing: Pixels between letters
        intensity: Animation intensity level
        
    Returns:
        Configured LetterAnimator instance
    """
    config = AnimationConfig(
        starter_count=starter_count,
        letter_spacing=letter_spacing,
        intensity=intensity
    )
    return LetterAnimator(font, config)
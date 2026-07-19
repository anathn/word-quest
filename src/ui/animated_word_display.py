"""
Animated Word Display UI Component

Renders words with letter-by-letter animations including
fade-in, bounce effects, and distinct styles for different letter types.
"""

from typing import Optional, List, Tuple, Callable
import pygame

from .letter_animator import LetterAnimator, AnimationConfig, create_letter_animator
from .letter_renderer import LetterRenderer, LetterType, LetterState
from .animation_utils import AnimationIntensity


class AnimatedWordDisplay:
    """
    Displays words with engaging letter animations.
    
    Features:
    - Letter-by-letter appearance with fade and bounce
    - Starter letters with green tint
    - Hint-revealed letters with orange highlight
    - Typed letters with instant pop
    - Accessibility settings support
    """
    
    # Default configuration
    DEFAULT_FONT_SIZE = 48
    DEFAULT_LETTER_SPACING = 20
    DEFAULT_STARTER_COUNT = 2
    
    def __init__(self, typography, config: Optional[AnimationConfig] = None):
        """
        Initialize the animated word display.
        
        Args:
            typography: Typography instance for font access
            config: Optional animation configuration
        """
        self.typography = typography
        self.config = config or AnimationConfig(
            font_size=self.DEFAULT_FONT_SIZE,
            letter_spacing=self.DEFAULT_LETTER_SPACING,
            starter_count=self.DEFAULT_STARTER_COUNT
        )
        
        # Get font from typography
        self.font = self.typography.style_headline.font
        
        # Create letter animator
        self.animator: Optional[LetterAnimator] = None
        
        # Word state
        self.current_word = ""
        self.starter_count = self.config.starter_count
        
        # Animation state
        self.is_animating = False
        self.animation_complete = False
        
        # Position
        self.position = (0, 0)
        
    def set_word(self, word: str, starter_count: Optional[int] = None):
        """
        Set the word to display with optional starter letters.
        
        Args:
            word: The word to animate
            starter_count: Number of starter letters (uses config default if None)
        """
        self.current_word = word.upper()
        self.starter_count = starter_count if starter_count is not None else self.config.starter_count
        
        # Create animator with the word
        self.animator = create_letter_animator(
            font=self.font,
            starter_count=self.starter_count,
            letter_spacing=self.config.letter_spacing,
            intensity=self.config.intensity
        )
        self.animator.set_word(word, self.starter_count)
        
        self.animation_complete = False
        
    def start_animation(self):
        """Start the letter-by-letter animation."""
        if self.animator:
            self.is_animating = True
            self.animation_complete = False
            self.animator.start_animation()
            
    def update(self):
        """
        Update animation state (call each frame).
        
        Should be called with the time delta since last frame.
        """
        if self.animator and self.is_animating:
            self.animator.update_advanced()
            
            if self.animator.is_complete():
                self.is_animating = False
                self.animation_complete = True
                
    def render(self, screen: pygame.Surface, position: Tuple[int, int]):
        """
        Render the word at the given position.
        
        Args:
            screen: Pygame surface to render to
            position: (x, y) position for the first letter
        """
        if self.animator:
            self.animator.render(screen, position)
            self.position = position
            
    def show_all_instantly(self):
        """Show all letters immediately without animation."""
        if self.animator:
            self.animator.show_all_instantly()
            self.is_animating = False
            self.animation_complete = True
            
    def show_starter_letters(self):
        """Show only starter letters initially."""
        if self.animator:
            self.animator.show_starter_letters()
            
    def reveal_letter(self, index: int):
        """
        Reveal a specific letter with hint style.
        
        Args:
            index: Index of the letter to reveal
        """
        if self.animator and index < len(self.animator.letters):
            letter = self.animator.letters[index]
            letter.set_hint_style()
            letter.start_animation("fade_bounce")
            
    def set_letter_as_hint(self, index: int):
        """
        Mark a letter as revealed by hint (for future animations).
        
        Args:
            index: Index of the letter
        """
        if self.animator and index < len(self.animator.letters):
            self.animator.letters[index].set_hint_style()
            
    def add_typed_letter(self, index: int, char: str):
        """
        Add a typed letter at the specified index.
        
        Args:
            index: Index where the letter was typed
            char: The character that was typed
        """
        if self.animator and index < len(self.animator.letters):
            letter = self.animator.letters[index]
            letter.char = char.upper()
            letter.set_typed_style()
            letter._needs_rebuild = True  # Force surface rebuild
            
    def set_full_word(self, revealed_indices: set):
        """
        Set the full word display with revealed letters.
        
        Args:
            revealed_indices: Set of indices that are revealed
        """
        if not self.animator:
            return
            
        for i, letter in enumerate(self.animator.letters):
            if i in revealed_indices:
                # If it's a starter letter, keep starter style
                if i < self.starter_count:
                    letter.set_starter_style()
                else:
                    letter.set_hint_style()
            else:
                letter.set_letter_type(LetterType.REGULAR)
                
    def is_complete(self) -> bool:
        """
        Check if all letters have finished animating.
        
        Returns:
            True if animation is complete
        """
        if self.animator:
            return self.animator.is_complete()
        return True
        
    def get_completed_count(self) -> int:
        """
        Get the number of letters that have completed animating.
        
        Returns:
            Count of completed letters
        """
        if self.animator:
            return self.animator.get_completed_count()
        return 0
        
    def set_intensity(self, intensity: str):
        """
        Set animation intensity for accessibility.
        
        Args:
            intensity: Animation intensity (full, reduced, off)
        """
        self.config.intensity = intensity
        if self.animator:
            self.animator.set_intensity(intensity)
            
    def reset(self):
        """Reset the display to initial state."""
        self.animator = None
        self.current_word = ""
        self.is_animating = False
        self.animation_complete = False
        
    def get_word(self) -> str:
        """Get the current word."""
        return self.current_word
        
    def get_letter_count(self) -> int:
        """Get the number of letters in the word."""
        if self.animator:
            return self.animator.get_letter_count()
        return 0
        
    def get_width(self) -> int:
        """
        Get the total width of the word display.
        
        Returns:
            Width in pixels
        """
        if self.animator and self.animator.letters:
            total = 0
            for letter in self.animator.letters:
                total += letter.get_width() + self.config.letter_spacing
            return total - self.config.letter_spacing  # Remove last spacing
        return 0
        
    def get_height(self) -> int:
        """
        Get the height of the word display.
        
        Returns:
            Height in pixels
        """
        if self.animator and self.animator.letters:
            return max(letter.get_height() for letter in self.animator.letters)
        return self.font.get_height()


def create_animated_word_display(typography, 
                                font_size: int = 48,
                                letter_spacing: int = 20,
                                starter_count: int = 2,
                                intensity: str = AnimationIntensity.FULL) -> AnimatedWordDisplay:
    """
    Factory function to create an AnimatedWordDisplay.
    
    Args:
        typography: Typography instance
        font_size: Font size for letters
        letter_spacing: Spacing between letters
        starter_count: Default number of starter letters
        intensity: Animation intensity level
        
    Returns:
        Configured AnimatedWordDisplay instance
    """
    config = AnimationConfig(
        font_size=font_size,
        letter_spacing=letter_spacing,
        starter_count=starter_count,
        intensity=intensity
    )
    return AnimatedWordDisplay(typography, config)
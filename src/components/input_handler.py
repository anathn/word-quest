"""
Input Handler Component

Processes keyboard events and manages input state for spelling challenges.
Supports both physical keyboard and on-screen keyboard input.
"""

from typing import Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import time


class InputState(Enum):
    """States for input handling."""
    EMPTY = "empty"
    TYPING = "typing"
    COMPLETE = "complete"
    SUBMITTED = "submitted"


@dataclass
class InputEvent:
    """Represents an input event."""
    event_type: str  # 'char', 'backspace', 'submit', 'invalid'
    character: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class InputHandler:
    """
    Handles keyboard input for spelling challenges.
    
    Features:
    - Physical keyboard event processing
    - On-screen keyboard support
    - Input validation
    - Character filtering (A-Z only)
    - Length limiting
    - Real-time input state tracking
    """
    
    def __init__(self, max_length: int):
        """
        Initialize the input handler.
        
        Args:
            max_length: Maximum number of characters allowed
        """
        self.max_length = max_length
        self.input_text = ""
        self.state = InputState.EMPTY
        self.last_input_time = 0
        self.input_history: List[InputEvent] = []
        
        # Callbacks for state changes
        self.on_input_changed: Optional[Callable] = None
        self.on_invalid_input: Optional[Callable] = None
        self.on_submit: Optional[Callable] = None
        self.on_complete: Optional[Callable] = None
    
    def handle_keydown(self, key: str, unicode_char: Optional[str] = None) -> Optional[InputEvent]:
        """
        Handle a key down event from physical keyboard.
        
        Args:
            key: The pygame key constant name (e.g., 'K_a', 'K_BACKSPACE')
            unicode_char: The actual character from event.unicode
            
        Returns:
            InputEvent if input was processed, None otherwise
        """
        current_time = time.time()
        
        # Handle special keys
        if key == 'K_BACKSPACE':
            return self._handle_backspace(current_time)
        elif key == 'K_RETURN' or key == 'K_KP_ENTER':
            return self._handle_submit(current_time)
        elif key == 'K_DELETE':
            return self._handle_backspace(current_time)  # Delete acts like backspace
        elif key == 'K_ESCAPE':
            self.clear()
            return InputEvent(event_type='clear', timestamp=current_time)
        
        # Handle character input
        if unicode_char and len(unicode_char) == 1:
            return self._handle_character(unicode_char, current_time)
        
        return None
    
    def handle_virtual_key(self, character: str) -> Optional[InputEvent]:
        """
        Handle input from on-screen/virtual keyboard.
        
        Args:
            character: The character to add
            
        Returns:
            InputEvent if input was processed, None otherwise
        """
        current_time = time.time()
        
        if character == 'BACKSPACE':
            return self._handle_backspace(current_time)
        elif character == 'ENTER' or character == 'SUBMIT':
            return self._handle_submit(current_time)
        elif character == 'CLEAR':
            self.clear()
            return InputEvent(event_type='clear', timestamp=current_time)
        else:
            return self._handle_character(character, current_time)
    
    def _handle_character(self, char: str, current_time: float) -> Optional[InputEvent]:
        """Handle a character input."""
        from src.utils.validators import InputValidator
        
        # Check if we've reached the limit
        if len(self.input_text) >= self.max_length:
            if self.on_invalid_input:
                self.on_invalid_input("max_length")
            return InputEvent(event_type='invalid', character=char, timestamp=current_time)
        
        # Validate character
        if not InputValidator.is_valid_character(char):
            if self.on_invalid_input:
                self.on_invalid_input(char)
            return InputEvent(event_type='invalid', character=char, timestamp=current_time)
        
        # Add character
        self.input_text += char.lower()
        self.last_input_time = current_time
        
        # Update state
        if len(self.input_text) >= self.max_length:
            self.state = InputState.COMPLETE
            if self.on_complete:
                self.on_complete(self.input_text)
        else:
            self.state = InputState.TYPING
        
        # Record event
        event = InputEvent(event_type='char', character=char, timestamp=current_time)
        self.input_history.append(event)
        
        # Notify listeners
        if self.on_input_changed:
            self.on_input_changed(self.input_text)
        
        return event
    
    def _handle_backspace(self, current_time: float) -> Optional[InputEvent]:
        """Handle backspace key."""
        if not self.input_text:
            return None
        
        self.input_text = self.input_text[:-1]
        self.state = InputState.TYPING if self.input_text else InputState.EMPTY
        
        event = InputEvent(event_type='backspace', timestamp=current_time)
        self.input_history.append(event)
        
        if self.on_input_changed:
            self.on_input_changed(self.input_text)
        
        return event
    
    def _handle_submit(self, current_time: float) -> Optional[InputEvent]:
        """Handle submit action."""
        if not self.input_text:
            return None
        
        self.state = InputState.SUBMITTED
        
        event = InputEvent(event_type='submit', timestamp=current_time)
        self.input_history.append(event)
        
        if self.on_submit:
            self.on_submit(self.input_text)
        
        return event
    
    def get_input(self) -> str:
        """Get the current input text."""
        return self.input_text
    
    def get_input_length(self) -> int:
        """Get the current input length."""
        return len(self.input_text)
    
    def get_remaining_length(self) -> int:
        """Get the number of characters that can still be entered."""
        return max(0, self.max_length - len(self.input_text))
    
    def is_complete(self) -> bool:
        """Check if input has reached maximum length."""
        return len(self.input_text) >= self.max_length
    
    def is_empty(self) -> bool:
        """Check if input is empty."""
        return len(self.input_text) == 0
    
    def clear(self):
        """Clear all input."""
        self.input_text = ""
        self.state = InputState.EMPTY
        
        if self.on_input_changed:
            self.on_input_changed(self.input_text)
    
    def reset(self):
        """Reset the input handler to initial state."""
        self.clear()
        self.input_history = []
        self.last_input_time = 0
    
    def set_input(self, text: str):
        """
        Set input text directly (for testing or restoration).
        
        Args:
            text: The text to set
        """
        from src.utils.validators import InputValidator
        
        # Sanitize input
        self.input_text = InputValidator.sanitize_input(text.lower())
        
        # Truncate if necessary
        if len(self.input_text) > self.max_length:
            self.input_text = self.input_text[:self.max_length]
        
        # Update state
        if len(self.input_text) >= self.max_length:
            self.state = InputState.COMPLETE
        elif len(self.input_text) > 0:
            self.state = InputState.TYPING
        else:
            self.state = InputState.EMPTY
        
        if self.on_input_changed:
            self.on_input_changed(self.input_text)


class InputDisplay:
    """
    Handles the visual display of input letters.
    
    Features:
    - Letter rendering with animations
    - Cursor blinking
    - Placeholder display
    - Shake animation for invalid input feedback
    """
    
    def __init__(self, max_length: int, letter_spacing: int = 10):
        """
        Initialize the input display.
        
        Args:
            max_length: Maximum number of letters to display
            letter_spacing: Additional spacing between letters in pixels
        """
        self.max_length = max_length
        self.letter_spacing = letter_spacing
        self.letters: List[str] = []
        self.cursor_visible = True
        self.cursor_blink_rate = 1.0  # Hz
        self.last_blink_time = 0
        
        # Animation state
        self.animating_letters: List[dict] = []  # Letters with animation state
        
        # Shake animation state
        self.shake_active = False
        self.shake_progress = 0.0
        self.shake_duration = 0.3  # 300ms
        self.shake_intensity = 5  # pixels
        self.shake_start_time = 0
    
    def update(self, current_time: float):
        """
        Update display state (call each frame).
        
        Args:
            current_time: Current time in seconds
        """
        # Update cursor blink
        if current_time - self.last_blink_time >= (1.0 / self.cursor_blink_rate):
            self.cursor_visible = not self.cursor_visible
            self.last_blink_time = current_time
        
        # Update letter animations
        for anim in self.animating_letters:
            if anim.get('type') == 'fade_in':
                anim['progress'] = min(1.0, anim['progress'] + 0.1)
        
        # Update shake animation
        if self.shake_active:
            elapsed = current_time - self.shake_start_time
            self.shake_progress = elapsed / self.shake_duration
            if self.shake_progress >= 1.0:
                self.shake_active = False
                self.shake_progress = 0.0
    
    def set_letters(self, letters: List[str]):
        """
        Set the letters to display.
        
        Args:
            letters: List of letter characters
        """
        self.letters = letters[:self.max_length]
        
        # Add fade-in animation for new letters
        self.animating_letters = [
            {'letter': letter, 'progress': 0.0, 'type': 'fade_in'}
            for letter in self.letters
        ]
    
    def add_letter(self, letter: str):
        """
        Add a letter with animation.
        
        Args:
            letter: The letter to add
        """
        if len(self.letters) < self.max_length:
            self.letters.append(letter.lower())
            self.animating_letters.append({
                'letter': letter.lower(),
                'progress': 0.0,
                'type': 'fade_in'
            })
    
    def remove_letter(self):
        """Remove the last letter with animation."""
        if self.letters:
            self.letters.pop()
            if self.animating_letters:
                self.animating_letters.pop()
    
    def clear(self):
        """Clear all letters."""
        self.letters = []
        self.animating_letters = []
    
    def get_display_letters(self) -> List[str]:
        """Get the current letters for display."""
        return self.letters.copy()
    
    def is_cursor_visible(self) -> bool:
        """Check if cursor should be visible."""
        return self.cursor_visible
    
    def get_placeholder_count(self) -> int:
        """Get the number of placeholder slots remaining."""
        return max(0, self.max_length - len(self.letters))
    
    def trigger_shake(self):
        """
        Trigger a shake animation for invalid input feedback.
        
        This creates a subtle shake effect to indicate that
        the user's input was invalid or rejected.
        """
        self.shake_active = True
        self.shake_progress = 0.0
        import time
        self.shake_start_time = time.time()
    
    def get_shake_offset(self, current_time: float = None) -> tuple:
        """
        Get the current shake offset for rendering.
        
        Args:
            current_time: Current time in seconds (optional, uses time.time() if not provided)
            
        Returns:
            Tuple of (offset_x, offset_y) for applying to render position
        """
        if not self.shake_active:
            return (0, 0)
        
        if current_time is None:
            import time
            current_time = time.time()
        
        # Calculate progress (0 to 1)
        elapsed = current_time - self.shake_start_time
        progress = elapsed / self.shake_duration
        
        if progress >= 1.0:
            return (0, 0)
        
        # Calculate shake offset using sine wave for smooth oscillation
        # Multiple oscillations within the shake duration
        import math
        oscillations = 3  # Number of back-and-forth movements
        angle = progress * math.pi * 2 * oscillations
        offset_x = math.sin(angle) * self.shake_intensity * (1 - progress)  # Fade out intensity
        
        return (offset_x, 0)


# Factory function
def create_input_handler(max_length: int) -> InputHandler:
    """
    Create an InputHandler instance.
    
    Args:
        max_length: Maximum input length
        
    Returns:
        Configured InputHandler instance
    """
    return InputHandler(max_length)

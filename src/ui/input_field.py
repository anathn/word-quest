"""
Input field component with keyboard navigation support.

Provides text input that works with keyboard navigation.
"""

from typing import Optional, Callable, List
import pygame

from src.components.keyboard_navigator import Focusable
from src.ui.focus_indicator import FocusIndicator


class InputField(Focusable):
    """
    Text input field with keyboard support.
    
    Features:
    - Keyboard focus and activation
    - Text input from keyboard
    - Character limit
    - Optional password mode
    - Placeholder text
    """
    
    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        placeholder: str = "",
        max_length: int = 100,
        password: bool = False,
        on_change: Optional[Callable[[str], None]] = None,
        tab_index: int = 0
    ):
        """
        Initialize input field.
        
        Args:
            x: X position
            y: Y position
            width: Field width
            height: Field height
            placeholder: Hint text when empty
            max_length: Maximum characters allowed
            password: Whether to hide text with asterisks
            on_change: Callback when text changes
            tab_index: Tab order index
        """
        super().__init__()
        
        self.rect = pygame.Rect(x, y, width, height)
        self.placeholder = placeholder
        self.max_length = max_length
        self.password = password
        self.on_change_callback = on_change
        self._tab_index = tab_index
        
        # Text state
        self._text = ""
        self._cursor_visible = True
        self._cursor_blink_timer = 0
        self._cursor_position = 0
        self._selected_text = ""  # For future selection support
        
        # Colors
        self.color_background = (40, 40, 60)
        self.color_background_focused = (50, 50, 80)
        self.color_border = (100, 100, 150)
        self.color_border_focused = (255, 215, 0)  # Gold when focused
        self.color_text = (255, 255, 255)
        self.color_placeholder = (120, 120, 150)
        self.color_cursor = (255, 255, 255)
        self.color_selected = (100, 100, 150)
        
        # Font
        self.font = pygame.font.Font(None, 36)
        self.border_radius = 6
        self.border_width = 2
        
        # Editor mode - only allow alphanumeric
        self.editor_mode = False
        self._allowed_chars = set()
        
        # Cursor blinking
        self.cursor_blink_interval = 0.5  # seconds
        self._last_cursor_update = 0
        
    def on_focus(self) -> None:
        """Called when the input field receives focus."""
        self._cursor_blink_timer = 0
        
    def on_focus_lost(self) -> None:
        """Called when the input field loses focus."""
        self._cursor_visible = False
        
    def on_activate(self) -> None:
        """Called when activated - usually does nothing for input fields."""
        pass
        
    def on_key_down(self, key: int) -> bool:
        """
        Handle key press while focused.
        
        Args:
            key: Pygame key constant
            
        Returns:
            True if the key was handled
        """
        if not self.enabled:
            return False
            
        # Handle special keys
        if key == pygame.K_BACKSPACE:
            self._delete_previous()
            return True
            
        elif key == pygame.K_DELETE:
            self._delete_current()
            return True
            
        elif key == pygame.K_LEFT:
            self._move_cursor_left()
            return True
            
        elif key == pygame.K_RIGHT:
            self._move_cursor_right()
            return True
            
        elif key == pygame.K_HOME:
            self._move_cursor_home()
            return True
            
        elif key == pygame.K_END:
            self._move_cursor_end()
            return True
            
        return False
        
    def handle_text_input(self, text: str) -> bool:
        """
        Handle text input event.
        
        Args:
            text: Text to insert
            
        Returns:
            True if text was inserted
        """
        if not self.enabled or not self.is_focused:
            return False
            
        if len(self._text) + len(text) > self.max_length:
            return False
            
        # Insert text at cursor position
        self._text = (
            self._text[:self._cursor_position] + 
            text + 
            self._text[self._cursor_position:]
        )
        self._cursor_position += len(text)
        
        # Trigger change callback
        if self.on_change_callback:
            self.on_change_callback(self._text)
            
        return True
        
    def _delete_previous(self) -> None:
        """Delete character before cursor."""
        if self._cursor_position > 0:
            self._text = (
                self._text[:self._cursor_position - 1] + 
                self._text[self._cursor_position:]
            )
            self._cursor_position -= 1
            if self.on_change_callback:
                self.on_change_callback(self._text)
                
    def _delete_current(self) -> None:
        """Delete character at cursor position."""
        if self._cursor_position < len(self._text):
            self._text = (
                self._text[:self._cursor_position] + 
                self._text[self._cursor_position + 1:]
            )
            if self.on_change_callback:
                self.on_change_callback(self._text)
                
    def _move_cursor_left(self) -> None:
        """Move cursor one character left."""
        if self._cursor_position > 0:
            self._cursor_position -= 1
            
    def _move_cursor_right(self) -> None:
        """Move cursor one character right."""
        if self._cursor_position < len(self._text):
            self._cursor_position += 1
            
    def _move_cursor_home(self) -> None:
        """Move cursor to beginning."""
        self._cursor_position = 0
        
    def _move_cursor_end(self) -> None:
        """Move cursor to end."""
        self._cursor_position = len(self._text)
        
    def draw(self, screen: pygame.Surface, focus_indicator: Optional[FocusIndicator] = None) -> None:
        """
        Draw the input field.
        
        Args:
            screen: Pygame surface to draw on
            focus_indicator: Optional FocusIndicator for cursor rendering
        """
        # Draw background
        color = self.color_background_focused if self.is_focused else self.color_background
        pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
        
        # Draw border
        border_color = self.color_border_focused if self.is_focused else self.color_border
        pygame.draw.rect(
            screen, 
            border_color, 
            self.rect, 
            width=self.border_width, 
            border_radius=self.border_radius
        )
        
        # Determine what text to display
        if self.password:
            display_text = "*" * len(self._text) if self._text else ""
        elif self._text:
            display_text = self._text
        elif self.placeholder:
            display_text = self.placeholder
        else:
            display_text = ""
            self._draw_placeholder(screen)
            return
            
        # Render text
        text_surface = self.font.render(display_text, True, self.color_text)
        text_x = self.rect.x + 8  # Padding
        
        # Clip to field width
        clip_rect = self.rect.inflate(-16, 0)
        screen.set_clip(clip_rect)
        screen.blit(text_surface, (text_x, self.rect.y + (self.rect.height - text_surface.get_height()) // 2))
        screen.set_clip(None)
        
        # Draw cursor if focused and visible
        if self.is_focused and self._cursor_visible:
            self._draw_cursor(screen)
            
        # Draw focus indicator
        if self.is_focused and focus_indicator:
            focus_indicator.render(self.rect)
            
    def _draw_placeholder(self, screen: pygame.Surface) -> None:
        """Draw placeholder text."""
        text_surface = self.font.render(self.placeholder, True, self.color_placeholder)
        text_x = self.rect.x + 8
        text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))
        
    def _draw_cursor(self, screen: pygame.Surface) -> None:
        """Draw the text cursor."""
        # Calculate cursor position
        text_before_cursor = self._text[:self._cursor_position]
        if self.password:
            text_before_cursor = "*" * len(text_before_cursor)
            
        text_surface = self.font.render(text_before_cursor, True, self.color_text)
        cursor_x = self.rect.x + 8 + text_surface.get_width()
        cursor_y = self.rect.y + (self.rect.height - self.font.get_height()) // 2
        cursor_height = self.font.get_height()
        
        # Draw cursor line
        pygame.draw.line(
            screen,
            self.color_cursor,
            (cursor_x, cursor_y),
            (cursor_x, cursor_y + cursor_height),
            width=2
        )
        
    def update(self, delta_time: float) -> None:
        """
        Update input field state (cursor blinking).
        
        Args:
            delta_time: Time since last update in seconds
        """
        if not self.is_focused:
            self._cursor_visible = False
            return
            
        # Update cursor blink timer
        self._cursor_blink_timer += delta_time
        if self._cursor_blink_timer >= self.cursor_blink_interval:
            self._cursor_blink_timer = 0
            self._cursor_visible = not self._cursor_visible
            
    @property
    def text(self) -> str:
        """Get the current text."""
        return self._text
        
    @text.setter
    def text(self, value: str) -> None:
        """Set the text content."""
        if len(value) > self.max_length:
            value = value[:self.max_length]
        self._text = value
        self._cursor_position = len(value)
        if self.on_change_callback:
            self.on_change_callback(value)
            
    def clear(self) -> None:
        """Clear the input field."""
        self._text = ""
        self._cursor_position = 0
        if self.on_change_callback:
            self.on_change_callback("")
            
    @property
    def enabled(self) -> bool:
        """Check if input field is enabled."""
        return self._can_focus
        
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set enabled state."""
        self._can_focus = value
        
    def set_editor_mode(self, enabled: bool = True, allowed_chars: Optional[str] = None) -> None:
        """
        Set editor mode for restricted character input.
        
        Args:
            enabled: Enable editor mode
            allowed_chars: String of allowed characters (optional)
        """
        self.editor_mode = enabled
        if allowed_chars:
            self._allowed_chars = set(allowed_chars)
        else:
            # Default to alphanumeric
            import string
            self._allowed_chars = set(string.ascii_letters + string.digits)


def create_input_field(
    placeholder: str = "",
    x: int = 0,
    y: int = 0,
    width: int = 300,
    height: int = 40,
    max_length: int = 100,
    password: bool = False,
    on_change: Optional[Callable[[str], None]] = None,
    tab_index: int = 0
) -> InputField:
    """
    Factory function for creating input fields.
    
    Args:
        placeholder: Hint text
        x: X position
        y: Y position
        width: Field width
        height: Field height
        max_length: Maximum characters
        password: Hide input
        on_change: Change callback
        tab_index: Tab order
        
    Returns:
        Configured InputField instance
    """
    return InputField(
        x=x, y=y, width=width, height=height,
        placeholder=placeholder, max_length=max_length,
        password=password, on_change=on_change, tab_index=tab_index
    )
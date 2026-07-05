"""
On-Screen Keyboard Component

Provides a virtual QWERTY keyboard for touch devices and tablet deployments.
Supports character input, backspace, and submit functionality.
"""

from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass

from src.ui.typography import Typography, TextStyle

# Pygame is optional - will be imported when needed
pygame = None
try:
    import pygame
except ImportError:
    pass  # Graceful fallback for test environments


@dataclass
class KeyboardKey:
    """Represents a single key on the on-screen keyboard."""
    label: str
    character: str  # The character sent when pressed (empty for special keys)
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    is_special: bool = False
    key_type: str = "normal"  # "normal", "backspace", "submit", "shift"


@dataclass
class KeyboardLayout:
    """Represents the complete keyboard layout."""
    keys: List[KeyboardKey]
    key_width: int
    key_height: int
    key_spacing: int
    row_spacing: int


class OnScreenKeyboard:
    """
    On-screen QWERTY keyboard for touch input.
    
    Features:
    - Standard QWERTY layout
    - Backspace and Submit keys
    - Visual feedback on key press
    - Touch/click event handling
    - Responsive sizing
    """
    
    # Key labels for QWERTY layout
    LAYOUT_ROWS = [
        ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
        ['BACKSPACE', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', 'SUBMIT']
    ]
    
    def __init__(
        self,
        typography: Typography,
        screen_width: int = 800,
        screen_height: int = 600,
        on_key_press: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the on-screen keyboard.
        
        Args:
            typography: Typography instance for rendering
            screen_width: Screen width for responsive layout
            screen_height: Screen height for positioning
            on_key_press: Callback when a key is pressed
        """
        self.typography = typography
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.on_key_press = on_key_press
        
        # Keyboard dimensions (responsive)
        self.keyboard_width = min(700, screen_width - 40)
        self.keyboard_height = 240
        self.key_height = 50
        self.key_spacing = 6
        self.row_spacing = 8
        
        # Calculate key width based on available space
        self.key_width = (self.keyboard_width - (10 * self.key_spacing)) / 10
        
        # Keyboard position (centered at bottom of screen)
        self.keyboard_x = (screen_width - self.keyboard_width) // 2
        self.keyboard_y = screen_height - self.keyboard_height - 20
        
        # Build keyboard layout
        self.layout: Optional[KeyboardLayout] = None
        self.visible_keys: List[KeyboardKey] = []
        self.pressed_key: Optional[KeyboardKey] = None
        
        self._build_layout()
        
        # Styling
        self.key_normal_color = (50, 50, 80)      # Dark blue-gray
        self.key_pressed_color = (80, 80, 120)    # Lighter blue-gray
        self.key_special_color = (255, 153, 0)    # Orange accent
        self.key_submit_color = (0, 200, 83)      # Green
        self.key_text_color = (255, 255, 255)     # White
        
        self.border_color = (100, 100, 150)
        self.border_width = 2
        
        # Animation state
        self.animation_progress = 0.0
        self.is_visible = True
    
    def _build_layout(self) -> None:
        """Build the keyboard layout with key positions."""
        self.visible_keys = []
        
        for row_idx, row_labels in enumerate(self.LAYOUT_ROWS):
            y = self.keyboard_y + row_idx * (self.key_height + self.row_spacing)
            
            # Center each row
            row_width = len(row_labels) * self.key_width + (len(row_labels) - 1) * self.key_spacing
            x = self.keyboard_x + (self.keyboard_width - row_width) // 2
            
            for label in row_labels:
                # Determine key type
                is_special = label in ['BACKSPACE', 'SUBMIT']
                key_type = 'normal'
                character = label.lower() if not is_special else ''
                
                if label == 'BACKSPACE':
                    key_type = 'backspace'
                    character = 'BACKSPACE'
                elif label == 'SUBMIT':
                    key_type = 'submit'
                    character = 'SUBMIT'
                
                key = KeyboardKey(
                    label=label,
                    character=character,
                    x=x,
                    y=y,
                    width=self.key_width,
                    height=self.key_height,
                    is_special=is_special,
                    key_type=key_type
                )
                
                self.visible_keys.append(key)
                x += self.key_width + self.key_spacing
        
        self.layout = KeyboardLayout(
            keys=self.visible_keys,
            key_width=self.key_width,
            key_height=self.key_height,
            key_spacing=self.key_spacing,
            row_spacing=self.row_spacing
        )
    
    def set_screen_size(self, width: int, height: int) -> None:
        """
        Update keyboard size for screen resize.
        
        Args:
            width: New screen width
            height: New screen height
        """
        self.screen_width = width
        self.screen_height = height
        self._recalculate_layout()
    
    def _recalculate_layout(self) -> None:
        """Recalculate keyboard layout after size change."""
        self.keyboard_width = min(700, self.screen_width - 40)
        self.keyboard_x = (self.screen_width - self.keyboard_width) // 2
        self.key_width = (self.keyboard_width - (10 * self.key_spacing)) / 10
        self._build_layout()
    
    def handle_event(self, event: 'pygame.event.Event') -> bool:
        """
        Handle pygame events (mouse/touch).
        
        Args:
            event: The pygame event to handle
            
        Returns:
            True if the event was handled (key press)
        """
        if not self.is_visible or pygame is None:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_click(event.pos[0], event.pos[1])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.pressed_key = None
            return False
        
        return False
    
    def _handle_click(self, x: int, y: int) -> bool:
        """
        Handle a mouse/touch click.
        
        Args:
            x: Click x coordinate
            y: Click y coordinate
            
        Returns:
            True if a key was pressed
        """
        for key in self.visible_keys:
            if self._is_point_in_key(x, y, key):
                self.pressed_key = key
                return self._on_key_pressed(key)
        
        return False
    
    def _is_point_in_key(self, x: int, y: int, key: KeyboardKey) -> bool:
        """Check if a point is within a key's bounds."""
        return (
            key.x <= x <= key.x + key.width and
            key.y <= y <= key.y + key.height
        )
    
    def _on_key_pressed(self, key: KeyboardKey) -> bool:
        """
        Process a key press.
        
        Args:
            key: The pressed key
            
        Returns:
            True if the key press was handled
        """
        if key.key_type == 'backspace':
            if self.on_key_press:
                self.on_key_press('BACKSPACE')
            return True
        elif key.key_type == 'submit':
            if self.on_key_press:
                self.on_key_press('SUBMIT')
            return True
        elif key.key_type == 'normal':
            if self.on_key_press and key.character:
                self.on_key_press(key.character)
            return True
        
        return False
    
    def render(self, screen: any) -> None:
        """
        Render the keyboard to the screen.
        
        Args:
            screen: The pygame Surface to render to
        """
        if not self.is_visible or pygame is None:
            return
        
        # Draw keyboard background
        self._draw_background(screen)
        
        # Draw all keys
        for key in self.visible_keys:
            self._draw_key(screen, key)
    
    def _draw_background(self, screen: any) -> None:
        """Draw the keyboard background."""
        import pygame
        
        # Keyboard background
        bg_rect = pygame.Rect(
            self.keyboard_x - 10,
            self.keyboard_y - 10,
            self.keyboard_width + 20,
            self.keyboard_height + 20
        )
        pygame.draw.rect(screen, (30, 30, 50), bg_rect, border_radius=10)
        pygame.draw.rect(
            screen, self.border_color, bg_rect, 
            self.border_width, border_radius=10
        )
    
    def _draw_key(self, screen: any, key: KeyboardKey) -> None:
        """Draw a single key."""
        import pygame
        
        # Determine key color
        if key == self.pressed_key:
            color = self.key_pressed_color
        elif key.key_type == 'backspace':
            color = self.key_special_color
        elif key.key_type == 'submit':
            color = self.key_submit_color
        else:
            color = self.key_normal_color
        
        # Draw key background
        key_rect = pygame.Rect(key.x, key.y, key.width, key.height)
        pygame.draw.rect(screen, color, key_rect, border_radius=5)
        pygame.draw.rect(screen, (150, 150, 200), key_rect, 1, border_radius=5)
        
        # Draw key label
        self._draw_key_label(screen, key)
    
    def _draw_key_label(self, screen: any, key: KeyboardKey) -> None:
        """Draw the label text on a key."""
        if pygame is None:
            return
        
        import pygame
        
        # Choose appropriate font size
        if len(key.label) > 6:  # Special keys like BACKSPACE
            font_size = 16
        elif len(key.label) > 3:
            font_size = 20
        else:
            font_size = 32
        
        font = pygame.font.SysFont("Arial", font_size, bold=True)
        label_surface = font.render(key.label, True, self.key_text_color)
        
        # Center the label
        label_x = key.x + (key.width - label_surface.get_width()) // 2
        label_y = key.y + (key.height - label_surface.get_height()) // 2
        
        screen.blit(label_surface, (label_x, label_y))
    
    def get_key_at_position(self, x: int, y: int) -> Optional[KeyboardKey]:
        """
        Get the key at a specific position.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            The KeyboardKey at the position, or None
        """
        for key in self.visible_keys:
            if self._is_point_in_key(x, y, key):
                return key
        return None
    
    def show(self) -> None:
        """Show the keyboard."""
        self.is_visible = True
    
    def hide(self) -> None:
        """Hide the keyboard."""
        self.is_visible = False
    
    def toggle(self) -> None:
        """Toggle keyboard visibility."""
        self.is_visible = not self.is_visible


# Factory function for creating the keyboard
def create_on_screen_keyboard(
    typography: Optional[Typography] = None,
    screen_width: int = 800,
    screen_height: int = 600,
    on_key_press: Optional[Callable[[str], None]] = None
) -> OnScreenKeyboard:
    """
    Create an OnScreenKeyboard instance.
    
    Args:
        typography: Optional Typography instance
        screen_width: Screen width
        screen_height: Screen height
        on_key_press: Callback for key presses
        
    Returns:
        Configured OnScreenKeyboard instance
    """
    from src.ui.typography import get_typography
    
    return OnScreenKeyboard(
        typography=typography or get_typography(),
        screen_width=screen_width,
        screen_height=screen_height,
        on_key_press=on_key_press
    )

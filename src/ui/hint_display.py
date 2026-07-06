"""
Hint Display UI Component

Renders hint text and revealed letters with animations.
Provides visual feedback for the hint escalation system.
"""

from typing import Optional, List, Tuple, Set
from dataclasses import dataclass
import time
import math


# Color constants (matching project design)
HINT_BUTTON_COLOR = (33, 150, 243)       # Blue #2196F3
HINT_BUTTON_DISABLED = (128, 128, 128)   # Gray
REVEALED_LETTER_COLOR = (76, 175, 80)    # Green #4CAF50
HINT_TEXT_COLOR = (255, 255, 255)        # White
HINT_BG_COLOR = (0, 0, 0, 180)           # Semi-transparent black

# Animation constants
HINT_FADE_DURATION = 0.3  # 300ms fade in
HINT_SCALE_FACTOR = 1.1   # Slight scale-up on reveal


@dataclass
class HintRenderData:
    """Data needed to render a hint."""
    hint_text: str
    revealed_pattern: str
    alpha: int  # 0-255 transparency
    scale: float
    x: int
    y: int


class HintDisplay:
    """
    Renders hints and revealed letters on screen.
    
    Features:
    - Fade-in animation for hints
    - Visual distinction for revealed letters
    - "Need Help?" button rendering
    - Accessibility-friendly sizing
    """
    
    def __init__(self, typography, screen_width: int = 800, screen_height: int = 600):
        """
        Initialize the hint display.
        
        Args:
            typography: Typography instance for text rendering
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.typography = typography
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Layout
        self.hint_area_y = 350  # Y position for hint text
        self.button_x = 100     # X position for help button
        self.button_y = 450     # Y position for help button
        self.button_width = 180
        self.button_height = 64
        
        # Animation state
        self.hint_alpha = 0  # Current alpha for hint text
        self.hint_scale = 1.0
        self.fade_start_time = 0.0
        self.animation_active = False
        
        # Current hint state
        self.current_hint_text = ""
        self.revealed_pattern = ""
        self.revealed_indices: Set[int] = set()
        self.word_text = ""
        
        # Button state
        self.help_button_enabled = False
        self.button_hovered = False
        self.button_pressed = False
        
        # Callbacks
        self.on_help_clicked: Optional[callable] = None
    
    def set_word(self, word_text: str):
        """
        Set the current word for hint display.
        
        Args:
            word_text: The spelling word
        """
        self.word_text = word_text.upper()
        self.revealed_indices.clear()
        # Build pattern with spaces between characters
        self.revealed_pattern = ' '.join(['_'] * len(word_text))
    
    def show_hint(self, hint_text: str, revealed_indices: Set[int]):
        """
        Display a new hint with animation.
        
        Args:
            hint_text: The hint message to display
            revealed_indices: Set of letter indices that are now revealed
        """
        self.current_hint_text = hint_text
        self.revealed_indices = revealed_indices.copy()
        self.revealed_pattern = self._build_revealed_pattern()
        
        # Start fade-in animation
        self.animation_active = True
        self.hint_alpha = 0
        self.hint_scale = 1.0
        self.fade_start_time = 0.0  # Relative start time (set on first update)
    
    def _build_revealed_pattern(self) -> str:
        """Build the revealed letter pattern string."""
        if not self.word_text:
            return ""
        
        result = []
        for i, letter in enumerate(self.word_text):
            if i in self.revealed_indices:
                result.append(letter)
            else:
                result.append('_')
        return ' '.join(result)
    
    def enable_help_button(self):
        """Enable the "Need Help?" button."""
        self.help_button_enabled = True
    
    def disable_help_button(self):
        """Disable the "Need Help?" button."""
        self.help_button_enabled = False
        self.button_hovered = False
        self.button_pressed = False
    
    def check_button_click(self, mouse_x: int, mouse_y: int) -> bool:
        """
        Check if the help button was clicked.
        
        Args:
            mouse_x: Mouse X position
            mouse_y: Mouse Y position
            
        Returns:
            True if button was clicked
        """
        if not self.help_button_enabled:
            return False
        
        # Check bounds
        in_bounds = (
            self.button_x <= mouse_x <= self.button_x + self.button_width and
            self.button_y <= mouse_y <= self.button_y + self.button_height
        )
        
        if in_bounds:
            self.button_hovered = True
            self.button_pressed = True
            if self.on_help_clicked:
                self.on_help_clicked()
            return True
        
        self.button_hovered = False
        self.button_pressed = False
        return False
    
    def update(self, current_time: float):
        """
        Update animation state (call each frame).
        
        Args:
            current_time: Elapsed time in seconds since animation started
        """
        if self.animation_active:
            elapsed = current_time  # current_time is elapsed time
            
            # Fade in over 300ms
            if elapsed < HINT_FADE_DURATION:
                self.hint_alpha = int(255 * (elapsed / HINT_FADE_DURATION))
                # Slight scale animation
                self.hint_scale = 1.0 + 0.1 * math.sin(elapsed * math.pi / HINT_FADE_DURATION)
            else:
                self.hint_alpha = 255
                self.hint_scale = 1.0
                self.animation_active = False
    
    def render(self, screen) -> List[Tuple]:
        """
        Render hints and button on screen.
        
        Args:
            screen: Pygame surface to render to
            
        Returns:
            List of (surface, position) tuples for blitting
        """
        rendered = []
        
        # Render hint text if available
        if self.current_hint_text:
            rendered.extend(self._render_hint_text(screen))
        
        # Render revealed letters in word display
        if self.revealed_indices:
            rendered.extend(self._render_revealed_letters(screen))
        
        # Render help button
        rendered.extend(self._render_help_button(screen))
        
        return rendered
    
    def _render_hint_text(self, screen) -> List[Tuple]:
        """Render the hint message text."""
        import pygame
        
        rendered = []
        
        # Create semi-transparent background
        bg_width = self.screen_width - 40
        bg_height = 80
        bg_x = 20
        bg_y = self.hint_area_y - 20
        
        bg_surf = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
        bg_surf.fill(HINT_BG_COLOR)
        bg_surf.set_alpha(self.hint_alpha)
        rendered.append((bg_surf, (bg_x, bg_y)))
        
        # Render hint text
        style = self.typography.style_body_text
        font = style.font
        
        # Split text into lines if needed
        hint_lines = self._wrap_text(self.current_hint_text, font, bg_width - 20)
        
        y_offset = bg_y + 20
        for line in hint_lines:
            text_surf = font.render(line, True, HINT_TEXT_COLOR)
            text_surf.set_alpha(self.hint_alpha)
            
            # Center horizontally
            text_x = bg_x + (bg_width - text_surf.get_width()) // 2
            rendered.append((text_surf, (text_x, y_offset)))
            y_offset += font.get_height() + 5
        
        return rendered
    
    def _render_revealed_letters(self, screen) -> List[Tuple]:
        """Render revealed letters with special styling."""
        # This is typically handled by the main word display
        # but can be used for additional hint overlays
        return []
    
    def _render_help_button(self, screen) -> List[Tuple]:
        """Render the "Need Help?" button."""
        import pygame
        
        rendered = []
        
        if not self.help_button_enabled:
            return rendered
        
        # Determine button color based on state
        if self.button_pressed:
            button_color = (28, 131, 212)  # Darker blue (pressed)
        elif self.button_hovered:
            button_color = (59, 166, 247)  # Lighter blue (hover)
        else:
            button_color = HINT_BUTTON_COLOR
        
        # Draw button background with rounded corners
        button_surf = pygame.Surface((self.button_width, self.button_height), pygame.SRCALPHA)
        
        # Rounded rectangle
        corner_radius = 8
        pygame.draw.rect(
            button_surf, 
            (*button_color, 255), 
            (0, 0, self.button_width, self.button_height),
            border_radius=corner_radius
        )
        
        # Add subtle border
        border_color = (255, 255, 255, 100)
        pygame.draw.rect(
            button_surf,
            border_color,
            (0, 0, self.button_width, self.button_height),
            width=2,
            border_radius=corner_radius
        )
        
        rendered.append((button_surf, (self.button_x, self.button_y)))
        
        # Render button text
        style = self.typography.style_button_text
        font = style.font
        
        # Add question mark icon
        text = "? Need Help?"
        text_surf = font.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(
            center=(
                self.button_x + self.button_width // 2,
                self.button_y + self.button_height // 2
            )
        )
        rendered.append((text_surf, text_rect.topleft))
        
        return rendered
    
    def _wrap_text(self, text: str, font, max_width: int) -> List[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else [text]
    
    def get_button_bounds(self) -> Tuple[int, int, int, int]:
        """
        Get the button bounding box.
        
        Returns:
            (x, y, width, height) tuple
        """
        return (self.button_x, self.button_y, self.button_width, self.button_height)
    
    def reset(self):
        """Reset the hint display to initial state."""
        self.current_hint_text = ""
        self.revealed_pattern = ""
        self.revealed_indices.clear()
        self.hint_alpha = 0
        self.hint_scale = 1.0
        self.animation_active = False
        self.help_button_enabled = False
        self.button_hovered = False
        self.button_pressed = False
        self.word_text = ""


# Factory function
def create_hint_display(typography, screen_width: int = 800, screen_height: int = 600) -> HintDisplay:
    """
    Create a HintDisplay instance.
    
    Args:
        typography: Typography instance
        screen_width: Screen width
        screen_height: Screen height
        
    Returns:
        Configured HintDisplay instance
    """
    return HintDisplay(typography, screen_width, screen_height)

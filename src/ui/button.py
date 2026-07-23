"""
Button UI component with keyboard navigation support.

Provides interactive button elements that work with both mouse and keyboard input.
"""

from typing import Optional, Callable
import pygame

from src.components.keyboard_navigator import Focusable
from src.ui.focus_indicator import FocusIndicator


class Button(Focusable):
    """
    Interactive button with keyboard and mouse support.
    
    Features:
    - Keyboard focus with visual indicator
    - Mouse hover effects
    - Click and Enter/Space activation
    - Optional icon support
    """
    
    def __init__(
        self, 
        x: int, 
        y: int, 
        width: int, 
        height: int, 
        text: str,
        on_click: Optional[Callable] = None,
        tab_index: int = 0
    ):
        """
        Initialize a button.
        
        Args:
            x: X position
            y: Y position
            width: Button width
            height: Button height
            text: Button label
            on_click: Callback when button is clicked
            tab_index: Tab order index
        """
        super().__init__()
        
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.on_click_callback = on_click
        self._tab_index = tab_index
        
        # State
        self.is_hovered = False
        self.is_pressed = False
        
        # Colors
        self.color_default = (100, 100, 120)      # Dark blue-gray
        self.color_hover = (120, 120, 140)        # Lighter
        self.color_focus = (140, 140, 180)        # Blue tint for focus
        self.color_pressed = (80, 80, 100)        # Darker when pressed
        self.color_disabled = (60, 60, 70)        # Gray when disabled
        self.color_text = (255, 255, 255)         # White text
        self.color_text_disabled = (150, 150, 150)  # Gray text when disabled
        
        # Border
        self.border_color = (180, 180, 200)
        self.border_width = 2
        
        # Font
        self.font = pygame.font.Font(None, 36)
        self.bold_font = pygame.font.Font(None, 40)
        
        # Corner radius
        self.border_radius = 8
        
        # Enabled state
        self._enabled = True
        
        # Animation
        self._scale = 1.0
        self._target_scale = 1.0
        
    def on_focus(self) -> None:
        """Called when the button receives focus."""
        pass
        
    def on_focus_lost(self) -> None:
        """Called when the button loses focus."""
        self.is_hovered = False
        
    def on_activate(self) -> None:
        """Called when the button is activated (Enter/Space)."""
        if self.enabled:
            self._trigger_click()
        
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
            
        if key == pygame.K_SPACE:
            self._trigger_click()
            return True
        return False
    
    def _trigger_click(self) -> None:
        """Fire the click callback."""
        if self.on_click_callback:
            try:
                self.on_click_callback()
            except Exception as e:
                from src.logging_config import get_logger
                logger = get_logger(__name__)
                logger.error(f"Button click callback error: {e}")
                
    def handle_mouse_event(self, event: pygame.event.Event) -> bool:
        """
        Handle mouse events.
        
        Args:
            event: Pygame mouse event
            
        Returns:
            True if the event was handled
        """
        if not self.enabled:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            return self.is_hovered
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:  # Left click
                self.is_pressed = True
                return True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.is_pressed and self.is_hovered and event.button == 1:
                self.is_pressed = False
                self._trigger_click()
                return True
            self.is_pressed = False
            
        return False
        
    def draw(self, screen: pygame.Surface, focus_indicator: Optional[FocusIndicator] = None) -> None:
        """
        Draw the button.
        
        Args:
            screen: Pygame surface to draw on
            focus_indicator: Optional FocusIndicator for rendering focus outline
        """
        # Determine color based on state
        if not self.enabled:
            color = self.color_disabled
            text_color = self.color_text_disabled
        elif self.is_pressed:
            color = self.color_pressed
        elif self.is_focused:
            color = self.color_focus
        elif self.is_hovered:
            color = self.color_hover
        else:
            color = self.color_default
            
        # Draw button background
        pygame.draw.rect(screen, color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(
            screen, 
            self.border_color, 
            self.rect, 
            width=self.border_width, 
            border_radius=self.border_radius
        )
        
        # Draw text
        text_color = self.color_text if self.enabled else self.color_text_disabled
        font = self.bold_font if self.is_focused else self.font
        
        # Make text bold if focused for extra visibility
        text_surface = font.render(self.text, True, text_color)
        text_x = self.rect.x + (self.rect.width - text_surface.get_width()) // 2
        text_y = self.rect.y + (self.rect.height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))
        
        # Draw focus indicator if focused
        if self.is_focused and focus_indicator:
            focus_indicator.render(self.rect)
    
    @property
    def enabled(self) -> bool:
        """Check if button is enabled."""
        return self._enabled
        
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set button enabled state."""
        self._enabled = value
        if not value:
            self.is_hovered = False
            self.is_pressed = False
            
    def set_text(self, text: str) -> None:
        """
        Set the button text.
        
        Args:
            text: New button label
        """
        self.text = text
        
    def set_position(self, x: int, y: int) -> None:
        """
        Set button position.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.rect.x = x
        self.rect.y = y
        
    def set_size(self, width: int, height: int) -> None:
        """
        Set button size.
        
        Args:
            width: Button width
            height: Button height
        """
        self.rect.width = width
        self.rect.height = height
        
    def contains_point(self, x: int, y: int) -> bool:
        """
        Check if a point is within the button.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            True if the point is inside the button
        """
        return self.rect.collidepoint(x, y)


def create_button(
    text: str,
    x: int = 0,
    y: int = 0,
    width: int = 200,
    height: int = 50,
    on_click: Optional[Callable] = None,
    tab_index: int = 0
) -> Button:
    """
    Factory function for creating buttons.
    
    Args:
        text: Button label
        x: X position
        y: Y position
        width: Button width
        height: Button height
        on_click: Click callback
        tab_index: Tab order index
        
    Returns:
        Configured Button instance
    """
    return Button(x, y, width, height, text, on_click, tab_index)
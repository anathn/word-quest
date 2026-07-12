"""
Bonus Message Display (STORY-004-02)

Renders celebration messages for streak bonus milestones.
Shows animated text for golden rocket boost and planet discovery.
"""

import pygame
import math
from typing import Optional, Tuple


class BonusMessage:
    """
    Displays celebration messages for streak bonuses.
    
    Features:
    - Fade in/out animation
    - Center screen positioning
    - Golden/yellow color scheme for 3-word streak
    - White with gold outline for 5-word streak
    - 2-2.5 second display duration
    
    Messages:
    - "3-word streak! GOLDEN BOOST!" - Golden rocket milestone
    - "5-word streak! NEW PLANET DISCOVERED!" - Planet discovery milestone
    """
    
    # Colors
    GOLDEN_YELLOW = (255, 215, 0)       # #FFD700 for 3-word streak
    WHITE = (255, 255, 255)              # White for 5-word streak
    GOLD_OUTLINE = (255, 215, 0)         # Gold outline for 5-word streak
    DARK_BG = (0, 0, 0, 180)             # Semi-transparent background
    
    # Font sizes
    FONT_SIZE_SMALL = 48                  # For 3-word streak
    FONT_SIZE_LARGE = 56                  # For 5-word streak
    
    # Timing
    FADE_IN_MS = 200                      # 0.2 seconds fade in
    FADE_OUT_MS = 300                     # 0.3 seconds fade out
    DISPLAY_DURATION_MS = 2000            # 2 seconds display (3-word)
    DISPLAY_DURATION_5WORD_MS = 2500      # 2.5 seconds display (5-word)
    
    # Visual effects
    PULSE_SPEED = 2.0                     # Pulse animation speed
    
    def __init__(self, screen: pygame.Surface, message: str, is_five_word: bool = False):
        """
        Initialize the bonus message display.
        
        Args:
            screen: Pygame surface for rendering
            message: Message text to display
            is_five_word: True for 5-word streak (larger, outlined text)
        """
        self.screen = screen
        self.message = message
        self.is_five_word = is_five_word
        
        # Timing state
        self.elapsed = 0.0
        self.duration = self.DISPLAY_DURATION_5WORD_MS if is_five_word else self.DISPLAY_DURATION_MS
        
        # Font setup
        self.font_size = self.FONT_SIZE_LARGE if is_five_word else self.FONT_SIZE_SMALL
        self.font = pygame.font.Font(None, self.font_size)
        
        # Position (center screen)
        self.position = (
            screen.get_width() // 2,
            screen.get_height() // 2
        )
        
        # Aphlama state
        self.alpha = 0
        self.fade_in_complete = False
        
        # Render cached surface
        self._text_surface: Optional[pygame.Surface] = None
        self._render_text()
    
    def _render_text(self):
        """Render the message text and cache it."""
        if self.is_five_word:
            # Render with gold outline for 5-word streak
            self._render_text_with_outline()
        else:
            # Simple golden text for 3-word streak
            self._text_surface = self.font.render(self.message, True, self.GOLDEN_YELLOW)
    
    def _render_text_with_outline(self):
        """
        Render text with gold outline effect.
        
        For 5-word streak: white text with gold outline
        """
        # Create surface large enough for outline
        outline_offset = 2
        base_surface = self.font.render(self.message, True, self.WHITE)
        
        # Create larger surface for outline
        width = base_surface.get_width() + outline_offset * 4
        height = base_surface.get_height() + outline_offset * 4
        combined = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Render outline (multiple layers for thicker effect)
        outline_color = (*self.GOLD_OUTLINE, 255)
        for dx in [-outline_offset, -outline_offset+1, 0, outline_offset-1, outline_offset]:
            for dy in [-outline_offset, -outline_offset+1, 0, outline_offset-1, outline_offset]:
                if dx != 0 or dy != 0:
                    offset_surface = self.font.render(self.message, True, outline_color)
                    combined.blit(offset_surface, (
                        width // 2 - base_surface.get_width() // 2 + dx,
                        height // 2 - base_surface.get_height() // 2 + dy
                    ))
        
        # Blit white text on top
        combined.blit(
            base_surface,
            (width // 2 - base_surface.get_width() // 2,
             height // 2 - base_surface.get_height() // 2)
        )
        
        self._text_surface = combined
    
    def update(self, dt: float):
        """
        Update message state.
        
        Args:
            dt: Time delta in seconds
        """
        self.elapsed += dt
        
        # Fade in
        if not self.fade_in_complete:
            fade_in_time = self.FADE_IN_MS / 1000.0
            progress = self.elapsed / fade_in_time
            self.alpha = min(255, int(progress * 255))
            
            if self.elapsed >= fade_in_time:
                self.fade_in_complete = True
        
        # Fade out
        fade_out_start = self.duration / 1000.0 - (self.FADE_OUT_MS / 1000.0)
        if self.elapsed >= fade_out_start:
            fade_progress = (self.elapsed - fade_out_start) / (self.FADE_OUT_MS / 1000.0)
            self.alpha = max(0, int((1 - fade_progress) * 255))
    
    def render(self):
        """
        Render the message on screen.
        
        Only renders if alpha > 0 and text surface exists.
        """
        if self.alpha <= 0 or not self._text_surface:
            return
        
        # Create surface with current alpha
        surface = self._text_surface.copy()
        surface.set_alpha(self.alpha)
        
        # Draw semi-transparent background for better readability
        bg_padding = 20
        bg_rect = pygame.Rect(
            self.position[0] - surface.get_width() // 2 - bg_padding,
            self.position[1] - surface.get_height() // 2 - bg_padding,
            surface.get_width() + bg_padding * 2,
            surface.get_height() + bg_padding * 2
        )
        
        # Create and blit background
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_alpha = int(100 * (self.alpha / 255.0))
        pygame.draw.rect(
            bg_surface,
            (*self.DARK_BG[:3], bg_alpha),
            pygame.Rect(0, 0, bg_rect.width, bg_rect.height),
            border_radius=10
        )
        self.screen.blit(bg_surface, bg_rect.topleft)
        
        # Calculate pulse scale for subtle effect
        pulse = 1.0 + 0.05 * math.sin(self.elapsed * self.PULSE_SPEED * math.pi * 2)
        scaled_surface = pygame.transform.scale(
            surface,
            (int(surface.get_width() * pulse), int(surface.get_height() * pulse))
        )
        
        # Center the text
        x = self.position[0] - scaled_surface.get_width() // 2
        y = self.position[1] - scaled_surface.get_height() // 2
        
        self.screen.blit(scaled_surface, (x, y))
    
    def is_complete(self) -> bool:
        """
        Check if message display is complete.
        
        Returns:
            True if fade out has finished
        """
        return self.elapsed >= self.duration / 1000.0
    
    def set_alpha(self, alpha: int):
        """
        Manually set alpha for external control.
        
        Args:
            alpha: Alpha value 0-255
        """
        self.alpha = max(0, min(255, alpha))


# Factory functions
def create_golden_boost_message(screen: pygame.Surface, message: str = "3-word streak! GOLDEN BOOST!") -> BonusMessage:
    """
    Create a bonus message for 3-word streak (golden boost).
    
    Args:
        screen: Pygame surface for rendering
        message: Optional custom message
        
    Returns:
        Configured BonusMessage instance
    
    Example:
        >>> # Create and use a golden boost message
        >>> screen = pygame.display.set_mode((800, 600))
        >>> message = create_golden_boost_message(screen, "3-word streak! GOLDEN BOOST!")
        >>> 
        >>> # In your game loop:
        >>> message.update(dt)  # Update each frame
        >>> message.render()     # Render each frame
        >>> if message.is_complete():
        ...     # Message finished, handle cleanup if needed
        ...     pass
    """
    return BonusMessage(screen, message, is_five_word=False)


def create_planet_discovery_message(
    screen: pygame.Surface,
    message: str = "5-word streak! NEW PLANET DISCOVERED!"
) -> BonusMessage:
    """
    Create a bonus message for 5-word streak (planet discovery).
    
    Args:
        screen: Pygame surface for rendering
        message: Optional custom message
        
    Returns:
        Configured BonusMessage instance
    
    Example:
        >>> # Create and use a planet discovery message
        >>> screen = pygame.display.set_mode((800, 600))
        >>> message = create_planet_discovery_message(screen, "5-word streak! NEW PLANET DISCOVERED!")
        >>> 
        >>> # In your game loop:
        >>> message.update(dt)  # Update each frame
        >>> message.render()     # Render each frame
        >>> if message.is_complete():
        ...     # Message finished, handle cleanup if needed
        ...     pass
    """
    return BonusMessage(screen, message, is_five_word=True)
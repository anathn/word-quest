"""
Progress Display Component (STORY-002-03)

Displays the words mastered counter in X/Y format with real-time updates.
"""

import pygame
from typing import Tuple, Optional
from src.components.progress_tracker import ProgressTracker


class ProgressDisplay:
    """
    Renders the words mastered counter UI component.
    
    Displays progress as "X/Y words" format with real-time updates
    and visual feedback when a new word is mastered.
    """
    
    # Colors
    WHITE = (255, 255, 255)
    GREEN = (76, 175, 80)  # #4CAF50 for mastery flash
    DARK_BG = (0, 0, 0, 180)  # Semi-transparent black
    TEXT_COLOR = WHITE
    
    def __init__(
        self,
        progress_tracker: ProgressTracker,
        font_size: int = 36,
        position: Tuple[int, int] = (0, 0)
    ):
        """
        Initialize the progress display.
        
        Args:
            progress_tracker: ProgressTracker instance for getting progress data
            font_size: Font size for the counter text (default 36)
            position: Default position (top-right corner) as (x, y)
        """
        self.tracker = progress_tracker
        self.position = position
        self.font = pygame.font.Font(None, font_size)
        
        # Flash animation state (STORY-002-03)
        self._flash_start_time: Optional[float] = None
        self._flash_duration = 0.5  # 500ms flash
        
        # Track last mastered count to detect changes
        self._last_mastered_count: Optional[int] = None
    
    def set_position(self, position: Tuple[int, int]):
        """
        Set the display position.
        
        Args:
            position: New position as (x, y)
        """
        self.position = position
    
    def trigger_mastery_flash(self):
        """
        Trigger the green flash animation when a word is mastered.
        """
        self._flash_start_time = pygame.time.get_ticks() / 1000.0
    
    def _is_flashing(self) -> bool:
        """Check if the mastery flash is currently active."""
        if self._flash_start_time is None:
            return False
        
        current_time = pygame.time.get_ticks() / 1000.0
        return (current_time - self._flash_start_time) < self._flash_duration
    
    def render(self, screen, position: Optional[Tuple[int, int]] = None):
        """
        Render the progress counter on the screen.
        
        Args:
            screen: Pygame surface to render on
            position: Optional position override, uses default if None
        """
        current_pos = position if position else self.position
        
        # Get progress text
        progress_text = self.tracker.get_progress_text()
        
        # Determine text color based on flash state
        if self._is_flashing():
            text_color = self.GREEN
        else:
            self._flash_start_time = None  # Reset flash
            text_color = self.TEXT_COLOR
        
        # Render text
        text_surface = self.font.render(progress_text, True, text_color)
        
        # Get text dimensions for positioning
        text_rect = text_surface.get_rect()
        
        # Calculate position (top-right corner by default)
        if current_pos == (0, 0):
            # Top-right corner with padding
            screen_rect = screen.get_rect()
            text_rect.topright = (screen_rect.right - 20, 20)
        else:
            text_rect.topleft = current_pos
        
        # Draw semi-transparent background for readability
        bg_padding = 8
        bg_rect = text_rect.inflate(bg_padding * 2, bg_padding * 2)
        
        # Create a temporary surface for the background with alpha
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        bg_surface.fill(self.DARK_BG)
        screen.blit(bg_surface, bg_rect)
        
        # Render text on top
        screen.blit(text_surface, text_rect)
    
    def update(self):
        """
        Update the display state.
        
        Checks for progress changes and triggers animations as needed.
        This should be called each frame during the game loop.
        """
        # Check if a new word was mastered
        current_mastered = self.tracker.get_mastered_count()
        
        if self._last_mastered_count is not None and current_mastered > self._last_mastered_count:
            # A word was mastered, trigger flash
            self.trigger_mastery_flash()
        
        self._last_mastered_count = current_mastered


# Factory function
def create_progress_display(
    progress_tracker: ProgressTracker,
    font_size: int = 36,
    position: Tuple[int, int] = (0, 0)
) -> ProgressDisplay:
    """
    Create a ProgressDisplay instance.
    
    Args:
        progress_tracker: ProgressTracker instance
        font_size: Font size for counter text
        position: Default position
        
    Returns:
        Configured ProgressDisplay instance
    """
    return ProgressDisplay(
        progress_tracker=progress_tracker,
        font_size=font_size,
        position=position
    )
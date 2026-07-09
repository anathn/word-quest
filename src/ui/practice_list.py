"""
Practice List UI Component

Displays words needing practice sorted by attempts (most challenging first).
Created for STORY-002-05: Words Needing Practice List.
"""

from typing import List, Dict, Optional, Callable
import pygame
from pygame.locals import *


class PracticeListDisplay:
    """
    UI component for displaying words needing practice.
    
    Features:
    - Shows list of words sorted by attempts (most first)
    - Orange accent color (not red - too negative)
    - Encouraging tone for students
    - Raw data view for parents
    - Empty state message when all words mastered
    """
    
    # Constants for configuration
    DEFAULT_MAX_ITEMS = 10
    MAX_ITEMS_VISIBLE = 8
    MAX_ATTEMPTS_FOR_ENCOURAGEMENT = 3
    
    # Color scheme (STORY-002-05 requirements)
    ORANGE_ACCENT = (255, 152, 0)  # #FF9800 - Encouraging, not red
    BACKGROUND = (30, 30, 60)      # Deep space blue
    TEXT_LIGHT = (255, 255, 255)
    TEXT_DARK = (200, 200, 200)
    HIGHLIGHT = (255, 200, 100)
    
    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        view_type: str = "parent"  # "parent" or "student"
    ):
        """
        Initialize the practice list display.
        
        Args:
            screen_width: Width of the display area
            screen_height: Height of the display area
            view_type: "parent" for raw data view, "student" for encouraging view
            
        Raises:
            ValueError: If view_type is not "parent" or "student"
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        # Validate view_type parameter
        if view_type not in ("parent", "student"):
            raise ValueError(f"view_type must be 'parent' or 'student', got '{view_type}'")
        self.view_type = view_type
        
        # Fonts
        self.title_font = pygame.font.Font(None, 36)
        self.word_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 24)
        
        # List positioning
        self.list_x = 50
        self.list_y = 80
        self.item_height = 40
        self.max_items_visible = self.MAX_ITEMS_VISIBLE
        
        # Current practice data
        self.practice_words: List[Dict] = []
        self.title_text = self._get_title()
        
        # Callback for word selection (future enhancement)
        self.on_word_selected: Optional[Callable[[str], None]] = None
    
    def _get_title(self) -> str:
        """Get title based on view type."""
        if self.view_type == "student":
            return "Let's Practice These!"
        else:
            return "Words Needing Practice:"
    
    def set_practice_words(self, words: List[Dict]):
        """
        Set the list of words needing practice.
        
        Args:
            words: List of word dictionaries from ProgressTracker.get_words_needing_practice()
        """
        self.practice_words = words
        self.title_text = self._get_title()
    
    def render(self, screen: pygame.Surface):
        """
        Render the practice list on the screen.
        
        Args:
            screen: Pygame surface to render on
        """
        # Draw title
        title_surf = self.title_font.render(self.title_text, True, self.ORANGE_ACCENT)
        screen.blit(title_surf, (self.list_x, self.list_y - 40))
        
        # Check if list is empty
        if not self.practice_words:
            self._render_empty_state(screen)
            return
        
        # Draw list items
        for i, word_data in enumerate(self.practice_words[:self.max_items_visible]):
            self._render_item(screen, word_data, i)
        
        # Draw "more items" indicator if needed
        if len(self.practice_words) > self.max_items_visible:
            more_text = f"...and {len(self.practice_words) - self.max_items_visible} more"
            more_surf = self.small_font.render(more_text, True, self.TEXT_DARK)
            screen.blit(more_surf, (self.list_x, self.list_y + i * self.item_height + 10))
    
    def _render_empty_state(self, screen: pygame.Surface):
        """
        Render empty state message.
        
        Args:
            screen: Pygame surface to render on
        """
        # Get encouraging message (matches story specification)
        if self.view_type == "student":
            message = "Great job! Keep it up!"
        else:
            message = "Great job! No words need practice."
        
        # Render message
        msg_surf = self.small_font.render(message, True, self.TEXT_DARK)
        msg_rect = msg_surf.get_rect(center=(self.list_x + 200, self.list_y + 60))
        screen.blit(msg_surf, msg_rect)
    
    def _render_item(self, screen: pygame.Surface, word_data: Dict, index: int):
        """
        Render a single practice list item.
        
        Args:
            screen: Pygame surface to render on
            word_data: Word dictionary with 'word', 'attempts', 'label'
            index: Item index in the list
        """
        y_pos = self.list_y + index * self.item_height
        
        # Draw item background (subtle highlight)
        item_rect = pygame.Rect(self.list_x - 10, y_pos - 5, 300, self.item_height - 5)
        pygame.draw.rect(screen, (50, 50, 80), item_rect, border_radius=5)
        
        # Draw number
        num_text = f"{index + 1}."
        num_surf = self.small_font.render(num_text, True, self.ORANGE_ACCENT)
        screen.blit(num_surf, (self.list_x, y_pos))
        
        # Draw word and attempts
        if self.view_type == "student":
            # Student view: encouraging format
            word = word_data['word']
            attempts = word_data['attempts']
            
            # Word text
            word_surf = self.word_font.render(word, True, self.TEXT_LIGHT)
            screen.blit(word_surf, (self.list_x + 30, y_pos))
            
            # Encouraging message based on attempts
            if attempts == 1:
                encouragement = "(you're getting closer!)"
            elif attempts <= self.MAX_ATTEMPTS_FOR_ENCOURAGEMENT:
                encouragement = "(keep trying!)"
            else:
                encouragement = "(you can do it!)"
            
            enc_surf = self.small_font.render(encouragement, True, self.TEXT_DARK)
            screen.blit(enc_surf, (self.list_x + 30 + word_surf.get_width(), y_pos + 5))
        else:
            # Parent view: raw data format
            label = word_data['label']
            label_surf = self.word_font.render(label, True, self.TEXT_LIGHT)
            screen.blit(label_surf, (self.list_x + 30, y_pos))
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle mouse click events for word selection.
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled, False otherwise
        """
        if event.type == MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            # Check if click is on a list item
            for i, word_data in enumerate(self.practice_words[:self.max_items_visible]):
                y_pos = self.list_y + i * self.item_height
                item_rect = pygame.Rect(self.list_x - 10, y_pos - 5, 300, self.item_height - 5)
                
                if item_rect.collidepoint(mouse_pos):
                    # Word selected - trigger callback if set
                    if self.on_word_selected:
                        self.on_word_selected(word_data['word'])
                    return True
        
        return False
    
    def update(self, delta_time: float):
        """
        Update component state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        # No animation needed for MVP
        pass


def create_practice_list(
    screen_width: int,
    screen_height: int,
    view_type: str = "parent"
) -> PracticeListDisplay:
    """
    Factory function to create a PracticeListDisplay.
    
    Args:
        screen_width: Width of the display area
        screen_height: Height of the display area
        view_type: "parent" or "student"
        
    Returns:
        Configured PracticeListDisplay instance
    """
    return PracticeListDisplay(
        screen_width=screen_width,
        screen_height=screen_height,
        view_type=view_type
    )
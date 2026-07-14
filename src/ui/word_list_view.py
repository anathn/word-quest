"""Word list view UI component for displaying and managing words."""
import pygame
from typing import Optional, Callable, List
from src.models.word_entry import WordEntry, Difficulty
from src.words.word_list_manager import WordListManager


class WordListView:
    """Display and interact with a word list."""
    
    # Color scheme
    COLOR_BACKGROUND = pygame.Color("#2c3e50")
    COLOR_ROW_HOVER = pygame.Color("#34495e")
    COLOR_ROW_SELECTED = pygame.Color("#3d566e")
    COLOR_TEXT = pygame.Color("#ecf0f1")
    COLOR_TEXT_DIM = pygame.Color("#95a5a6")
    COLOR_BORDER = pygame.Color("#7f8c8d")
    
    # Difficulty colors
    COLOR_BEGINNER = pygame.Color("#27ae60")  # Green
    COLOR_MEDIUM = pygame.Color("#f39c12")    # Orange/Yellow
    COLOR_ADVANCED = pygame.Color("#e74c3c")  # Red
    
    # Difficulty badge colors for text contrast
    BADGE_TEXT_BEGINNER = pygame.Color("#ffffff")
    BADGE_TEXT_MEDIUM = pygame.Color("#ffffff")
    BADGE_TEXT_ADVANCED = pygame.Color("#ffffff")
    
    def __init__(
        self, 
        rect: pygame.Rect,
        manager: WordListManager,
        profile_id: str,
        on_edit: Callable[[str], None],
        on_delete: Callable[[str], None],
        font: Optional[pygame.font.Font] = None
    ):
        """Initialize the word list view.
        
        Args:
            rect: Position and size of the view.
            manager: WordListManager instance for data access.
            profile_id: Student profile ID.
            on_edit: Callback when edit is requested (receives word_id).
            on_delete: Callback when delete is requested (receives word_id).
            font: Pygame font for rendering text.
        """
        self.rect = rect
        self.manager = manager
        self.profile_id = profile_id
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.font = font or pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        self.header_font = pygame.font.Font(None, 42)
        
        self.words: List[WordEntry] = []
        self.visible_words: List[WordEntry] = []
        self.selected_word: Optional[WordEntry] = None
        self.hovered_word: Optional[WordEntry] = None
        
        self.scroll_y = 0
        self.row_height = 50
        self.row_spacing = 2
        
        self.search_text = ""
        self.selected_difficulty: Optional[Difficulty] = None
        
        self._load_words()
        self._setup_ui_elements()
    
    def _setup_ui_elements(self):
        """Set up button regions for interaction."""
        # Search box
        self.search_box_rect = pygame.Rect(
            self.rect.x + 20,
            self.rect.y + 15,
            200,
            36
        )
        
        # Difficulty filter buttons
        self.difficulty_buttons = {}
        button_x = self.search_box_rect.right + 40
        button_y = self.rect.y + 15
        button_width = 100
        button_height = 36
        
        for i, diff in enumerate([Difficulty.BEGINNER, Difficulty.MEDIUM, Difficulty.ADVANCED]):
            btn_rect = pygame.Rect(button_x + i * (button_width + 10), button_y, button_width, button_height)
            self.difficulty_buttons[diff] = btn_rect
        
        # All words button
        self.all_words_button = pygame.Rect(button_x + 3 * (button_width + 10), button_y, 60, 36)
        
        # List area
        list_top = self.rect.y + 60
        self.list_rect = pygame.Rect(
            self.rect.x + 20,
            list_top,
            self.rect.width - 40,
            self.rect.height - 75
        )
        
        # Action buttons area
        self.edit_button_rect: Optional[pygame.Rect] = None
        self.delete_button_rect: Optional[pygame.Rect] = None
    
    def _load_words(self):
        """Load words from the manager."""
        self.words = self.manager.get_words(self.profile_id)
        self._apply_filters()
    
    def _apply_filters(self):
        """Apply search and difficulty filters."""
        self.visible_words = self.manager.get_words(
            self.profile_id,
            difficulty=self.selected_difficulty,
            search_terms=self.search_text if self.search_text else None
        )
        
        # Reset selection if not in filtered list
        if self.selected_word and self.selected_word not in self.visible_words:
            self.selected_word = None
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame events.
        
        Args:
            event: Pygame event to handle.
            
        Returns:
            True if event was handled, False otherwise.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_mouse_click(event)
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event)
        elif event.type == pygame.KEYDOWN:
            return self._handle_keypress(event)
        
        return False
    
    def _handle_mouse_click(self, event: pygame.event.Event) -> bool:
        """Handle mouse click events."""
        # Check difficulty filter buttons
        for diff, rect in self.difficulty_buttons.items():
            if rect.collidepoint(event.pos):
                self.selected_difficulty = diff
                self.search_text = ""  # Clear search when changing filter
                self._apply_filters()
                return True
        
        # Check "All" button
        if self.all_words_button.collidepoint(event.pos):
            self.selected_difficulty = None
            self.search_text = ""
            self._apply_filters()
            return True
        
        # Check search box
        if self.search_box_rect.collidepoint(event.pos):
            # Focus on search box (simplified - no text input yet)
            return True
        
        # Check list area for word selection
        if self.list_rect.collidepoint(event.pos):
            # Calculate which row was clicked
            y_offset = event.pos[1] - self.list_rect.y - self.scroll_y
            row_index = int(y_offset // self.row_height)
            
            if 0 <= row_index < len(self.visible_words):
                word = self.visible_words[row_index]
                
                # Check if edit button was clicked
                if self.edit_button_rect and self.edit_button_rect.collidepoint(event.pos):
                    self.on_edit(word.id)
                    return True
                
                # Check if delete button was clicked
                if self.delete_button_rect and self.delete_button_rect.collidepoint(event.pos):
                    self.on_delete(word.id)
                    return True
                
                # Select the word
                self.selected_word = word
                return True
        
        # Click outside list - deselect
        if not self.list_rect.collidepoint(event.pos):
            self.selected_word = None
        
        return False
    
    def _handle_mouse_motion(self, event: pygame.event.Event):
        """Handle mouse motion events."""
        if self.list_rect.collidepoint(event.pos):
            # Calculate which row is hovered
            y_offset = event.pos[1] - self.list_rect.y - self.scroll_y
            row_index = int(y_offset // self.row_height)
            
            if 0 <= row_index < len(self.visible_words):
                self.hovered_word = self.visible_words[row_index]
            else:
                self.hovered_word = None
        else:
            self.hovered_word = None
    
    def _handle_keypress(self, event: pygame.event.Event) -> bool:
        """Handle keypress events."""
        if event.key == pygame.K_UP:
            # Move selection up
            if self.selected_word:
                idx = self.visible_words.index(self.selected_word) if self.selected_word in self.visible_words else -1
                if idx > 0:
                    self.selected_word = self.visible_words[idx - 1]
            return True
        
        elif event.key == pygame.K_DOWN:
            # Move selection down
            if self.selected_word:
                try:
                    idx = self.visible_words.index(self.selected_word)
                    if idx < len(self.visible_words) - 1:
                        self.selected_word = self.visible_words[idx + 1]
                except ValueError:
                    if self.visible_words:
                        self.selected_word = self.visible_words[0]
            else:
                if self.visible_words:
                    self.selected_word = self.visible_words[0]
            return True
        
        elif event.key == pygame.K_DELETE and self.selected_word:
            self.on_delete(self.selected_word.id)
            return True
        
        return False
    
    def update_search_filter(self, search_text: str):
        """Update the search filter text.
        
        Args:
            search_text: Text to search for.
        """
        self.search_text = search_text
        self._apply_filters()
    
    def set_difficulty_filter(self, difficulty: Optional[Difficulty]):
        """Set the difficulty filter.
        
        Args:
            difficulty: Difficulty to filter by, or None for all.
        """
        self.selected_difficulty = difficulty
        self._apply_filters()
    
    def get_selected_word(self) -> Optional[WordEntry]:
        """Get the currently selected word."""
        return self.selected_word
    
    def refresh(self):
        """Reload words from storage."""
        self._load_words()
    
    def draw(self, screen: pygame.Surface):
        """Draw the word list view.
        
        Args:
            screen: Pygame surface to draw on.
        """
        # Draw background
        pygame.draw.rect(screen, self.COLOR_BACKGROUND, self.rect)
        pygame.draw.rect(screen, self.COLOR_BORDER, self.rect, 2)
        
        # Draw title
        title = "Word List"
        title_surf = self.header_font.render(title, True, self.COLOR_TEXT)
        screen.blit(title_surf, (self.rect.x + 20, self.rect.y + 5))
        
        # Draw word count
        total = self.manager.get_word_count(self.profile_id)
        count_text = f"Total: {total['total']} (Beginner: {total['beginner']}, Medium: {total['medium']}, Advanced: {total['advanced']})"
        count_surf = self.small_font.render(count_text, True, self.COLOR_TEXT_DIM)
        screen.blit(count_surf, (self.rect.x + 20, self.rect.y + self.header_font.get_height()))
        
        # Draw search box
        pygame.draw.rect(screen, self.COLOR_TEXT, self.search_box_rect, 2)
        search_label = "Search..."
        search_surf = self.small_font.render(search_label, True, self.COLOR_TEXT_DIM)
        screen.blit(search_surf, (self.search_box_rect.x + 10, self.search_box_rect.y + 4))
        
        # Draw difficulty filter buttons
        for diff, rect in self.difficulty_buttons.items():
            color = self._get_difficulty_color(diff)
            selected = self.selected_difficulty == diff
            
            # Draw button background
            if selected:
                pygame.draw.rect(screen, color, rect)
            else:
                pygame.draw.rect(screen, self.COLOR_ROW_HOVER, rect)
            pygame.draw.rect(screen, self.COLOR_BORDER, rect, 2)
            
            # Draw button text
            text = diff.value.capitalize()
            text_surf = self.small_font.render(text, True, self.BADGE_TEXT_MEDIUM)
            screen.blit(text_surf, (rect.x + 10, rect.y + 8))
        
        # Draw "All" button
        all_rect = self.all_words_button
        selected = self.selected_difficulty is None
        if selected:
            pygame.draw.rect(screen, self.COLOR_TEXT, all_rect)
        else:
            pygame.draw.rect(screen, self.COLOR_ROW_HOVER, all_rect)
        pygame.draw.rect(screen, self.COLOR_BORDER, all_rect, 2)
        text_surf = self.small_font.render("All", True, 
            self.COLOR_BACKGROUND if selected else self.COLOR_TEXT)
        screen.blit(text_surf, (all_rect.x + 15, all_rect.y + 8))
        
        # Draw word list
        self._draw_word_list(screen)
    
    def _get_difficulty_color(self, difficulty: Difficulty) -> pygame.Color:
        """Get the color for a difficulty level."""
        colors = {
            Difficulty.BEGINNER: self.COLOR_BEGINNER,
            Difficulty.MEDIUM: self.COLOR_MEDIUM,
            Difficulty.ADVANCED: self.COLOR_ADVANCED
        }
        return colors[difficulty]
    
    def _draw_word_list(self, screen: pygame.Surface):
        """Draw the scrollable word list area."""
        # Calculate area for list
        list_area = pygame.Rect(
            self.list_rect.x,
            self.list_rect.y,
            self.list_rect.width,
            len(self.visible_words) * (self.row_height + self.row_spacing)
        )
        
        # Draw each visible word row
        y_offset = 0
        for i, word in enumerate(self.visible_words):
            row_rect = pygame.Rect(
                self.list_rect.x,
                self.list_rect.y + y_offset,
                self.list_rect.width,
                self.row_height
            )
            
            # Row background
            if word == self.selected_word:
                pygame.draw.rect(screen, self.COLOR_ROW_SELECTED, row_rect)
            elif word == self.hovered_word:
                pygame.draw.rect(screen, self.COLOR_ROW_HOVER, row_rect)
            else:
                pygame.draw.rect(screen, self.COLOR_BACKGROUND, row_rect)
            
            # Row border
            pygame.draw.line(screen, self.COLOR_BORDER, 
                (row_rect.left, row_rect.bottom - 1), 
                (row_rect.right, row_rect.bottom - 1))
            
            # Draw word spelling
            spelling_surf = self.font.render(word.spelling, True, self.COLOR_TEXT)
            screen.blit(spelling_surf, (row_rect.x + 10, row_rect.y + 10))
            
            # Draw definition (truncated)
            definition = word.definition[:30] + "..." if len(word.definition) > 30 else word.definition
            definition_surf = self.small_font.render(definition, True, self.COLOR_TEXT_DIM)
            screen.blit(definition_surf, (row_rect.x + 150, row_rect.y + 10))
            
            # Draw difficulty badge
            badge_color = self._get_difficulty_color(word.difficulty)
            badge_text = word.difficulty.value.capitalize()
            badge_rect = pygame.Rect(row_rect.right - 150, row_rect.y + 10, 100, 26)
            pygame.draw.rect(screen, badge_color, badge_rect)
            badge_surf = self.small_font.render(badge_text, True, pygame.Color("#ffffff"))
            # Center text in badge
            text_x = badge_rect.x + (badge_rect.width - badge_surf.get_width()) // 2
            screen.blit(badge_surf, (text_x, badge_rect.y))
            
            # Draw edit button
            edit_x = row_rect.right - 70
            edit_y = row_rect.y + 8
            edit_rect = pygame.Rect(edit_x, edit_y, 40, 30)
            pygame.draw.rect(screen, self.COLOR_MEDIUM, edit_rect)
            edit_surf = self.small_font.render("Edit", True, pygame.Color("#ffffff"))
            screen.blit(edit_surf, (edit_x + 5, edit_y + 3))
            
            # Store edit button rect for click detection
            if word == self.selected_word:
                self.edit_button_rect = edit_rect
            
            # Draw delete button
            delete_x = edit_x + 45
            delete_y = row_rect.y + 8
            delete_rect = pygame.Rect(delete_x, delete_y, 40, 30)
            pygame.draw.rect(screen, self.COLOR_ADVANCED, delete_rect)
            delete_surf = self.small_font.render("Del", True, pygame.Color("#ffffff"))
            screen.blit(delete_surf, (delete_x + 5, delete_y + 3))
            
            # Store delete button rect for click detection
            if word == self.selected_word:
                self.delete_button_rect = delete_rect
            
            y_offset += self.row_height + self.row_spacing
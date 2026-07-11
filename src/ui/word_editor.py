"""Word editor dialog for adding and editing custom words."""
import pygame
from typing import Optional, Callable
from src.models.word_entry import WordEntry, Difficulty
from src.words.word_list_manager import WordListManager


class WordEditor:
    """Dialog for adding or editing a word entry."""
    
    # Color scheme
    COLOR_BACKGROUND = pygame.Color("#2c3e50")
    COLOR_MODAL = pygame.Color("rgba(0, 0, 0, 180)")
    COLOR_FORM_BG = pygame.Color("#34495e")
    COLOR_TEXT = pygame.Color("#ecf0f1")
    COLOR_TEXT_DIM = pygame.Color("#95a5a6")
    COLOR_BORDER = pygame.Color("#7f8c8d")
    COLOR_INPUT_BG = pygame.Color("#1a252f")
    COLOR_INPUT_FOCUS = pygame.Color("#3498db")
    
    # Difficulty colors
    COLOR_BEGINNER = pygame.Color("#27ae60")
    COLOR_MEDIUM = pygame.Color("#f39c12")
    COLOR_ADVANCED = pygame.Color("#e74c3c")
    
    def __init__(
        self,
        screen_rect: pygame.Rect,
        manager: WordListManager,
        profile_id: str,
        on_save: Callable[[WordEntry], None],
        on_cancel: Callable[[], None],
        word_to_edit: Optional[WordEntry] = None,
        font: Optional[pygame.font.Font] = None
    ):
        """Initialize the word editor.
        
        Args:
            screen_rect: Parent screen rectangle for centering.
            manager: WordListManager instance.
            profile_id: Student profile ID.
            on_save: Callback when word is saved.
            on_cancel: Callback when dialog is cancelled.
            word_to_edit: Existing word to edit, or None for new word.
            font: Pygame font for rendering.
        """
        self.screen_rect = screen_rect
        self.manager = manager
        self.profile_id = profile_id
        self.on_save = on_save
        self.on_cancel = on_cancel
        self.word_to_edit = word_to_edit
        self.font = font or pygame.font.Font(None, 36)
        self.header_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 28)
        
        # Form state
        self.spelling = word_to_edit.spelling if word_to_edit else ""
        self.definition = word_to_edit.definition if word_to_edit else ""
        self.difficulty = word_to_edit.difficulty if word_to_edit else Difficulty.MEDIUM
        self.error_message = ""
        
        # Focus state
        self.active_field = "spelling"  # "spelling", "definition", "difficulty"
        self.cursor_visible = True
        self.cursor_blink_timer = 0
        
        # Form layout
        self._setup_layout()
    
    def _setup_layout(self):
        """Set up form element positions and sizes."""
        # Dialog size
        dialog_width = 500
        dialog_height = 400
        dialog_x = (self.screen_rect.width - dialog_width) // 2
        dialog_y = (self.screen_rect.height - dialog_height) // 2
        
        self.dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Modal overlay
        self.modal_rect = self.screen_rect
        
        # Title
        self.title_rect = pygame.Rect(
            self.dialog_rect.x,
            self.dialog_rect.y + 20,
            self.dialog_rect.width,
            40
        )
        
        # Spellling field
        field_y = self.dialog_rect.y + 80
        label_width = 100
        input_width = 350
        
        self.spelling_label_rect = pygame.Rect(
            self.dialog_rect.x + 30,
            field_y - 5,
            label_width,
            30
        )
        self.spelling_input_rect = pygame.Rect(
            self.dialog_rect.x + 30 + label_width + 10,
            field_y,
            input_width,
            40
        )
        
        # Definition field
        field_y += 60
        self.definition_label_rect = pygame.Rect(
            self.dialog_rect.x + 30,
            field_y - 5,
            label_width,
            30
        )
        self.definition_input_rect = pygame.Rect(
            self.dialog_rect.x + 30 + label_width + 10,
            field_y,
            input_width,
            60
        )
        
        # Difficulty field
        field_y += 80
        self.difficulty_label_rect = pygame.Rect(
            self.dialog_rect.x + 30,
            field_y - 5,
            label_width,
            30
        )
        self.difficulty_buttons = {}
        button_x = self.dialog_rect.x + 30 + label_width + 10
        button_width = 100
        button_height = 35
        
        for i, diff in enumerate([Difficulty.BEGINNER, Difficulty.MEDIUM, Difficulty.ADVANCED]):
            btn_rect = pygame.Rect(button_x + i * (button_width + 10), field_y, button_width, button_height)
            self.difficulty_buttons[diff] = btn_rect
        
        # Error message area
        self.error_rect = pygame.Rect(
            self.dialog_rect.x + 30,
            field_y + 50,
            input_width + label_width + 10,
            30
        )
        
        # Button area
        button_y = self.dialog_rect.bottom - 60
        cancel_rect = pygame.Rect(
            self.dialog_rect.centerx - 120,
            button_y,
            100,
            40
        )
        save_rect = pygame.Rect(
            self.dialog_rect.centerx + 20,
            button_y,
            100,
            40
        )
        
        self.cancel_button_rect = cancel_rect
        self.save_button_rect = save_rect
        
        # Track text input position for cursor
        self._update_text_position()
    
    def _update_text_position(self):
        """Update cursor position calculations."""
        pass  # Simplified - cursor position not rendered in this version
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle pygame events.
        
        Args:
            event: Pygame event to handle.
            
        Returns:
            True if event was handled, False otherwise.
        """
        if event.type == pygame.KEYDOWN:
            return self._handle_keypress(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_mouse_click(event)
        
        return False
    
    def _handle_keypress(self, event: pygame.event.Event) -> bool:
        """Handle keypress events."""
        if event.key == pygame.K_ESCAPE:
            self.on_cancel()
            return True
        
        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            # Save on Enter if no error
            if not self.error_message:
                self._save_word()
            return True
        
        # Handle typing in active field
        if self.active_field in ["spelling", "definition"]:
            if event.key == pygame.K_BACKSPACE:
                if self.active_field == "spelling":
                    self.spelling = self.spelling[:-1]
                else:
                    self.definition = self.definition[:-1]
                self.error_message = ""
                
            elif event.unicode and event.unicode.isprintable():
                if self.active_field == "spelling":
                    # Only allow letters and hyphens
                    if event.unicode.isalpha() or event.unicode == '-':
                        self.spelling += event.unicode
                        self.error_message = ""
                else:
                    self.definition += event.unicode
                    self.error_message = ""
            
            elif event.key == pygame.K_TAB:
                # Move to next field
                if self.active_field == "spelling":
                    self.active_field = "definition"
                else:
                    self.active_field = "spelling"
                return True
        
        return False
    
    def _handle_mouse_click(self, event: pygame.event.Event) -> bool:
        """Handle mouse click events."""
        # Check cancel button
        if self.cancel_button_rect.collidepoint(event.pos):
            self.on_cancel()
            return True
        
        # Check save button
        if self.save_button_rect.collidepoint(event.pos):
            if not self.error_message:
                self._save_word()
            return True
        
        # Check spelling input
        if self.spelling_input_rect.collidepoint(event.pos):
            self.active_field = "spelling"
            return True
        
        # Check definition input
        if self.definition_input_rect.collidepoint(event.pos):
            self.active_field = "definition"
            return True
        
        # Check difficulty buttons
        for diff, rect in self.difficulty_buttons.items():
            if rect.collidepoint(event.pos):
                self.difficulty = diff
                self.error_message = ""
                return True
        
        return False
    
    def _save_word(self):
        """Save the word and close dialog."""
        try:
            if self.word_to_edit:
                # Update existing word
                word = self.manager.update_word(
                    self.profile_id,
                    self.word_to_edit.id,
                    spelling=self.spelling,
                    definition=self.definition,
                    difficulty=self.difficulty
                )
            else:
                # Create new word
                word = self.manager.add_word(
                    self.profile_id,
                    self.spelling,
                    self.definition,
                    self.difficulty
                )
            
            self.on_save(word)
            
        except ValueError as e:
            self.error_message = str(e)
    
    def get_difficulty_color(self, difficulty: Difficulty) -> pygame.Color:
        """Get color for difficulty level."""
        colors = {
            Difficulty.BEGINNER: self.COLOR_BEGINNER,
            Difficulty.MEDIUM: self.COLOR_MEDIUM,
            Difficulty.ADVANCED: self.COLOR_ADVANCED
        }
        return colors[difficulty]
    
    def draw(self, screen: pygame.Surface):
        """Draw the word editor dialog.
        
        Args:
            screen: Pygame surface to draw on.
        """
        # Draw modal overlay
        modal_surf = pygame.Surface((self.modal_rect.width, self.modal_rect.height))
        modal_surf.fill(self.COLOR_MODAL)
        screen.blit(modal_surf, (0, 0))
        
        # Draw dialog background
        pygame.draw.rect(screen, self.COLOR_FORM_BG, self.dialog_rect)
        pygame.draw.rect(screen, self.COLOR_BORDER, self.dialog_rect, 3)
        
        # Draw title
        title = "Edit Word" if self.word_to_edit else "Add Word"
        title_surf = self.header_font.render(title, True, self.COLOR_TEXT)
        screen.blit(title_surf, (self.dialog_rect.centerx - title_surf.get_width() // 2, 
                                 self.dialog_rect.y + 15))
        
        # Draw spelling field
        self._draw_input_field(
            screen,
            "Spelling:",
            self.spelling_label_rect,
            self.spelling_input_rect,
            self.spelling,
            self.active_field == "spelling"
        )
        
        # Draw definition field
        self._draw_input_field(
            screen,
            "Definition:",
            self.definition_label_rect,
            self.definition_input_rect,
            self.definition,
            self.active_field == "definition",
            multiline=True
        )
        
        # Draw difficulty selector
        self._draw_difficulty_selector(screen)
        
        # Draw error message
        if self.error_message:
            error_surf = self.small_font.render(self.error_message, True, self.COLOR_ADVANCED)
            screen.blit(error_surf, (self.error_rect.x, self.error_rect.y))
        
        # Draw buttons
        self._draw_button(screen, self.cancel_button_rect, "Cancel", self.COLOR_BORDER)
        self._draw_button(screen, self.save_button_rect, "Save", self.COLOR_BEGINNER)
    
    def _draw_input_field(
        self, 
        screen: pygame.Surface,
        label: str,
        label_rect: pygame.Rect,
        input_rect: pygame.Rect,
        text: str,
        is_active: bool,
        multiline: bool = False
    ):
        """Draw an input field with label."""
        # Draw label
        label_surf = self.font.render(label, True, self.COLOR_TEXT)
        screen.blit(label_surf, (label_rect.x, label_rect.y))
        
        # Draw input background
        bg_color = self.COLOR_INPUT_BG if not is_active else self.COLOR_INPUT_FOCUS
        pygame.draw.rect(screen, bg_color, input_rect)
        pygame.draw.rect(screen, self.COLOR_BORDER, input_rect, 2)
        
        # Draw placeholder if empty
        if not text:
            placeholder = self.small_font.render("Enter text...", True, self.COLOR_TEXT_DIM)
            screen.blit(placeholder, (input_rect.x + 10, input_rect.y + 8))
        else:
            # Truncate if too long
            display_text = text[:50] + "..." if len(text) > 50 else text
            text_surf = self.small_font.render(display_text, True, self.COLOR_TEXT)
            screen.blit(text_surf, (input_rect.x + 10, input_rect.y + 8))
        
        # Draw cursor if active
        if is_active:
            cursor_rect = pygame.Rect(input_rect.right - 3, input_rect.y + 10, 2, 24)
            pygame.draw.rect(screen, self.COLOR_TEXT, cursor_rect)
    
    def _draw_difficulty_selector(self, screen: pygame.Surface):
        """Draw difficulty level selector buttons."""
        # Draw label
        label_surf = self.font.render("Difficulty:", True, self.COLOR_TEXT)
        screen.blit(label_surf, (self.difficulty_label_rect.x, self.difficulty_label_rect.y))
        
        # Draw buttons
        for diff, rect in self.difficulty_buttons.items():
            # Button background
            is_selected = self.difficulty == diff
            bg_color = self.get_difficulty_color(diff) if is_selected else self.COLOR_INPUT_BG
            pygame.draw.rect(screen, bg_color, rect)
            pygame.draw.rect(screen, self.COLOR_BORDER, rect, 2)
            
            # Button text
            text = diff.value.capitalize()
            text_surf = self.small_font.render(text, True, pygame.Color("#ffffff"))
            screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, 
                                   rect.y + 8))
    
    def _draw_button(
        self, 
        screen: pygame.Surface, 
        rect: pygame.Rect, 
        text: str, 
        color: pygame.Color
    ):
        """Draw a button."""
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, self.COLOR_BORDER, rect, 2)
        
        text_surf = self.font.render(text, True, pygame.Color("#ffffff"))
        screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, 
                               rect.centery - text_surf.get_height() // 2))
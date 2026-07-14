"""Bulk word import dialog for adding multiple words at once."""
import pygame
from typing import Optional, Callable, List
from src.models.word_entry import Difficulty
from src.words.word_list_manager import WordListManager


class BulkImporter:
    """Dialog for bulk importing words from text."""
    
    # Color scheme
    COLOR_BACKGROUND = pygame.Color("#2c3e50")
    COLOR_MODAL = pygame.Color(0, 0, 0, 180)
    COLOR_FORM_BG = pygame.Color("#34495e")
    COLOR_TEXT = pygame.Color("#ecf0f1")
    COLOR_TEXT_DIM = pygame.Color("#95a5a6")
    COLOR_BORDER = pygame.Color("#7f8c8d")
    COLOR_INPUT_BG = pygame.Color("#1a252f")
    COLOR_SUCCESS = pygame.Color("#27ae60")
    COLOR_ERROR = pygame.Color("#e74c3c")
    
    # Difficulty colors
    COLOR_BEGINNER = pygame.Color("#27ae60")
    COLOR_MEDIUM = pygame.Color("#f39c12")
    COLOR_ADVANCED = pygame.Color("#e74c3c")
    
    def __init__(
        self,
        screen_rect: pygame.Rect,
        manager: WordListManager,
        profile_id: str,
        on_close: Callable[[bool], None],  # True if words were added
        font: Optional[pygame.font.Font] = None
    ):
        """Initialize the bulk importer.
        
        Args:
            screen_rect: Parent screen rectangle for centering.
            manager: WordListManager instance.
            profile_id: Student profile ID.
            on_close: Callback when dialog is closed.
            font: Pygame font for rendering.
        """
        self.screen_rect = screen_rect
        self.manager = manager
        self.profile_id = profile_id
        self.on_close = on_close
        self.font = font or pygame.font.Font(None, 36)
        self.header_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 28)
        
        # Import state
        self.input_text = ""
        self.difficulty = Difficulty.MEDIUM
        self.is_processing = False
        self.import_result = None  # (added_count, failed_count, added_words)
        self.error_message = ""
        
        # Layout
        self._setup_layout()
    
    def _setup_layout(self):
        """Set up dialog layout."""
        # Dialog size
        dialog_width = 600
        dialog_height = 500
        dialog_x = (self.screen_rect.width - dialog_width) // 2
        dialog_y = (self.screen_rect.height - dialog_height) // 2
        
        self.dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        self.modal_rect = self.screen_rect
        
        # Title
        self.title_rect = pygame.Rect(
            self.dialog_rect.x,
            self.dialog_rect.y + 20,
            self.dialog_rect.width,
            40
        )
        
        # Instructions
        self.instructions_rect = pygame.Rect(
            self.dialog_rect.x + 30,
            self.dialog_rect.y + 70,
            dialog_width - 60,
            60
        )
        
        # Text input area
        input_y = self.dialog_rect.y + 130
        self.text_input_rect = pygame.Rect(
            self.dialog_rect.x + 30,
            input_y,
            dialog_width - 60,
            220
        )
        
        # Difficulty selector
        diff_y = input_y + 230
        self.difficulty_label_rect = pygame.Rect(
            self.dialog_rect.x + 30,
            diff_y - 5,
            100,
            30
        )
        self.difficulty_buttons = {}
        button_x = self.dialog_rect.x + 140
        button_width = 100
        button_height = 35
        
        for i, diff in enumerate([Difficulty.BEGINNER, Difficulty.MEDIUM, Difficulty.ADVANCED]):
            btn_rect = pygame.Rect(button_x + i * (button_width + 10), diff_y, button_width, button_height)
            self.difficulty_buttons[diff] = btn_rect
        
        # Status/result area
        status_y = diff_y + 50
        self.status_rect = pygame.Rect(
            self.dialog_rect.x + 30,
            status_y,
            dialog_width - 60,
            40
        )
        
        # Example text
        example_y = status_y + 50
        self.example_rect = pygame.Rect(
            self.dialog_rect.x + 30,
            example_y,
            dialog_width - 60,
            60
        )
        
        # Button area
        button_y = self.dialog_rect.bottom - 70
        cancel_rect = pygame.Rect(
            self.dialog_rect.centerx - 150,
            button_y,
            120,
            40
        )
        import_rect = pygame.Rect(
            self.dialog_rect.centerx + 30,
            button_y,
            120,
            40
        )
        
        self.cancel_button_rect = cancel_rect
        self.import_button_rect = import_rect
        
        # Selection info for text input
        self.text_selection_start = 0
        self.text_selection_end = 0
    
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
            if not self.is_processing:
                self.on_close(False)
            return True
        
        # Only accept text input if not processing
        if not self.is_processing:
            if event.key == pygame.K_BACKSPACE:
                if event.mod & pygame.KMOD_CTRL:
                    # Delete word - simplified: just clear
                    self.input_text = ""
                elif self.input_text:
                    self.input_text = self.input_text[:-1]
                    self.error_message = ""
                    self.import_result = None
            
            elif event.unicode and event.unicode.isprintable():
                self.input_text += event.unicode
                self.error_message = ""
                self.import_result = None
            
            elif event.key == pygame.K_TAB:
                # Cycle through difficulties
                if self.difficulty == Difficulty.BEGINNER:
                    self.difficulty = Difficulty.MEDIUM
                elif self.difficulty == Difficulty.MEDIUM:
                    self.difficulty = Difficulty.ADVANCED
                else:
                    self.difficulty = Difficulty.BEGINNER
                self.error_message = ""
                self.import_result = None
        
        return False
    
    def _handle_mouse_click(self, event: pygame.event.Event) -> bool:
        """Handle mouse click events."""
        # Check cancel button (only if not processing)
        if self.cancel_button_rect.collidepoint(event.pos) and not self.is_processing:
            self.on_close(False)
            return True
        
        # Check import button
        if self.import_button_rect.collidepoint(event.pos):
            if not self.is_processing:
                self._import_words()
            return True
        
        # Check text input area
        if self.text_input_rect.collidepoint(event.pos) and not self.is_processing:
            # Set cursor position (simplified - just focus)
            return True
        
        # Check difficulty buttons
        for diff, rect in self.difficulty_buttons.items():
            if rect.collidepoint(event.pos):
                self.difficulty = diff
                self.error_message = ""
                self.import_result = None
                return True
        
        return False
    
    def _import_words(self):
        """Process the bulk import."""
        if not self.input_text.strip():
            self.error_message = "Please enter at least one word"
            return
        
        self.is_processing = True
        self.error_message = ""
        
        try:
            added, failed, words = self.manager.add_bulk_words(
                self.profile_id,
                self.input_text,
                self.difficulty
            )
            self.import_result = (added, failed, words)
            
            if added == 0:
                self.error_message = "No valid words were imported"
            
        except Exception as e:
            self.error_message = f"Import failed: {str(e)}"
            self.import_result = None
        
        self.is_processing = False
    
    def get_difficulty_color(self, difficulty: Difficulty) -> pygame.Color:
        """Get color for difficulty level."""
        colors = {
            Difficulty.BEGINNER: self.COLOR_BEGINNER,
            Difficulty.MEDIUM: self.COLOR_MEDIUM,
            Difficulty.ADVANCED: self.COLOR_ADVANCED
        }
        return colors[difficulty]
    
    def draw(self, screen: pygame.Surface):
        """Draw the bulk import dialog.
        
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
        title = "Import Words"
        title_surf = self.header_font.render(title, True, self.COLOR_TEXT)
        screen.blit(title_surf, (self.dialog_rect.centerx - title_surf.get_width() // 2, 
                                 self.dialog_rect.y + 15))
        
        # Draw instructions
        instructions = "Enter words, one per line. Optionally add definition after a space."
        instructions_surf = self.small_font.render(instructions, True, self.COLOR_TEXT)
        # Wrap text
        wrapped = self._wrap_text(instructions, self.instructions_rect.width)
        for i, line in enumerate(wrapped[:2]):
            line_surf = self.small_font.render(line, True, self.COLOR_TEXT_DIM)
            screen.blit(line_surf, (self.instructions_rect.x, self.instructions_rect.y + i * 24))
        
        # Draw text input area
        self._draw_text_input(screen)
        
        # Draw difficulty selector
        self._draw_difficulty_selector(screen)
        
        # Draw status/result
        self._draw_status(screen)
        
        # Draw example
        self._draw_example(screen)
        
        # Draw buttons
        if self.is_processing:
            # Show progress indicator
            progress_surf = self.header_font.render("Processing...", True, self.COLOR_TEXT)
            screen.blit(progress_surf, (self.dialog_rect.centerx - progress_surf.get_width() // 2,
                                       self.dialog_rect.bottom - 90))
        else:
            self._draw_button(screen, self.cancel_button_rect, "Cancel", self.COLOR_BORDER)
            self._draw_button(screen, self.import_button_rect, "Import", self.COLOR_SUCCESS)
    
    def _wrap_text(self, text: str, max_width: int) -> list:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if self.small_font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _draw_text_input(self, screen: pygame.Surface):
        """Draw the text input area."""
        # Background
        pygame.draw.rect(screen, self.COLOR_INPUT_BG, self.text_input_rect)
        pygame.draw.rect(screen, self.COLOR_BORDER, self.text_input_rect, 2)
        
        # Placeholder
        if not self.input_text:
            placeholder = "apple A red fruit\nbanana A yellow fruit\ncherry A small red fruit"
            placeholder_surf = self.small_font.render(placeholder, True, self.COLOR_TEXT_DIM)
            screen.blit(placeholder_surf, (self.text_input_rect.x + 10, self.text_input_rect.y + 10))
        else:
            # Display input text (scroll if needed)
            y_offset = self.text_input_rect.y + 10
            max_lines = abs(self.text_input_rect.height // 24)
            lines = self.input_text.split("\n")[:max_lines]
            
            for i, line in enumerate(lines):
                display = line[:50] + "..." if len(line) > 50 else line
                line_surf = self.small_font.render(display, True, self.COLOR_TEXT)
                screen.blit(line_surf, (self.text_input_rect.x + 10, y_offset + i * 24))
        
        # Cursor if active
        cursor_surf = pygame.Surface((2, 24))
        cursor_surf.fill(self.COLOR_TEXT)
        cursor_x = self.text_input_rect.x + 10
        text_lines = self.input_text.split("\n")[:10]
        last_line = text_lines[-1] if text_lines else ""
        cursor_x += self.small_font.size(last_line)[0]
        cursor_y = self.text_input_rect.y + 10 + len(text_lines) * 24
        
        if cursor_y - self.text_input_rect.y < self.text_input_rect.height:
            screen.blit(cursor_surf, (cursor_x, cursor_y))
    
    def _draw_difficulty_selector(self, screen: pygame.Surface):
        """Draw difficulty level selector."""
        # Label
        label = "Set difficulty for all words:"
        label_surf = self.font.render(label, True, self.COLOR_TEXT)
        screen.blit(label_surf, (self.difficulty_label_rect.x, self.difficulty_label_rect.y))
        
        # Buttons
        for diff, rect in self.difficulty_buttons.items():
            is_selected = self.difficulty == diff
            bg_color = self.get_difficulty_color(diff) if is_selected else self.COLOR_INPUT_BG
            pygame.draw.rect(screen, bg_color, rect)
            pygame.draw.rect(screen, self.COLOR_BORDER, rect, 2)
            
            text = diff.value.capitalize()
            text_surf = self.small_font.render(text, True, pygame.Color("#ffffff"))
            screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2, rect.y + 8))
    
    def _draw_status(self, screen: pygame.Surface):
        """Draw import status/result."""
        if self.import_result:
            added, failed, _ = self.import_result
            
            if added > 0 and failed == 0:
                # Success
                color = self.COLOR_SUCCESS
                msg = f"✓ Successfully imported {added} word{'s' if added > 1 else ''}"
            elif added > 0 and failed > 0:
                # Partial success
                color = self.COLOR_MEDIUM
                msg = f"✓ Imported {added} word{'s' if added > 1 else ''}, {failed} failed"
            else:
                # Failure
                color = self.COLOR_ERROR
                msg = "✗ No words imported"
        elif self.error_message:
            color = self.COLOR_ERROR
            msg = self.error_message
        else:
            color = self.COLOR_TEXT_DIM
            msg = "Click 'Import' to add words"
        
        status_surf = self.small_font.render(msg, True, color)
        screen.blit(status_surf, (self.status_rect.x, self.status_rect.y))
    
    def _draw_example(self, screen: pygame.Surface):
        """Draw example format."""
        example_title = "Example format:"
        title_surf = self.small_font.render(example_title, True, self.COLOR_TEXT_DIM)
        screen.blit(title_surf, (self.example_rect.x, self.example_rect.y))
        
        example_lines = [
            "APPLE A red fruit",
            "BANANA A yellow fruit",
            "CHERRY"  # No definition
        ]
        
        for i, line in enumerate(example_lines):
            line_surf = self.small_font.render(line, True, self.small_font.size(line)[0])
            screen.blit(line_surf, (self.example_rect.x, self.example_rect.y + 25 + i * 22))
    
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
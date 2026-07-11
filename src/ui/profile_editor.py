"""
Profile Editor Component (STORY-003-02)

Form for creating and editing student profiles.
"""

import pygame
from typing import Tuple, Optional, Callable
from src.profiles.profile_manager import ProfileManager
from src.ui.avatar_selector import AvatarSelector


class ProfileEditor:
    """
    UI component for creating and editing student profiles.
    
    Provides a form with name input field and avatar selection grid.
    Supports both create and edit modes.
    
    Attributes:
        profile_manager: ProfileManager instance for CRUD operations
        mode: "create" or "edit"
        editing_profile_id: Profile ID being edited (if in edit mode)
    """
    
    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    BG_COLOR = (26, 26, 62)  # Deep space blue
    INPUT_BG = (40, 40, 60)
    INPUT_BORDER = (100, 100, 140)
    INPUT_FOCUS_BORDER = (76, 175, 80)  # Green
    ERROR_COLOR = (244, 67, 54)  # Red
    BUTTON_COLOR = (76, 175, 80)  # Green
    BUTTON_TEXT = (255, 255, 255)
    
    # Layout
    PADDING = 30
    INPUT_HEIGHT = 40
    BUTTON_HEIGHT = 40
    BUTTON_WIDTH = 120
    
    def __init__(
        self,
        profile_manager: ProfileManager,
        mode: str = "create",
        editing_profile_id: Optional[str] = None,
        center_position: Optional[Tuple[int, int]] = None
    ):
        """
        Initialize the profile editor.
        
        Args:
            profile_manager: ProfileManager instance
            mode: "create" or "edit"
            editing_profile_id: Profile ID for edit mode
            center_position: Center position for the editor
        """
        if mode not in ("create", "edit"):
            raise ValueError("Mode must be 'create' or 'edit'")
        
        self.profile_manager = profile_manager
        self.mode = mode
        self.editing_profile_id = editing_profile_id
        self.center_position = center_position or (400, 300)
        
        # Form state
        self.name_text = ""
        self.name_error: Optional[str] = None
        self.avatar_selector: Optional[AvatarSelector] = None
        self.show_avatar_selector = False
        self.input_active = False
        
        # Event callbacks
        self.on_save: Optional[Callable] = None
        self.on_cancel: Optional[Callable] = None
        
        # Load existing profile in edit mode
        self.existing_profile = None
        if mode == "edit" and editing_profile_id:
            self.existing_profile = profile_manager.get_profile(editing_profile_id)
            if self.existing_profile:
                self.name_text = self.existing_profile.name
                # Will initialize avatar selector after first render
        
        # Calculate dimensions
        self._calculate_dimensions()
    
    def _calculate_dimensions(self):
        """Calculate editor dimensions."""
        # Width determined by avatar selector (max of dialog width or input width)
        input_width = 300
        self.editor_width = max(400, input_width + 2 * self.PADDING)
        self.editor_height = 350  # Fixed height for now
        
        self.top_left = (
            self.center_position[0] - self.editor_width // 2,
            self.center_position[1] - self.editor_height // 2
        )
        
        # Input bounds
        self.input_rect = pygame.Rect(
            self.top_left[0] + self.PADDING,
            self.top_left[1] + 80,
            self.editor_width - 2 * self.PADDING,
            self.INPUT_HEIGHT
        )
        
        # Button positions
        save_button_x = self.top_left[0] + self.editor_width - self.BUTTON_WIDTH - self.PADDING
        cancel_button_x = save_button_x - self.BUTTON_WIDTH - 20
        
        self.save_button_rect = pygame.Rect(
            save_button_x,
            self.top_left[1] + self.editor_height - self.BUTTON_HEIGHT - self.PADDING,
            self.BUTTON_WIDTH,
            self.BUTTON_HEIGHT
        )
        
        self.cancel_button_rect = pygame.Rect(
            cancel_button_x,
            self.top_left[1] + self.editor_height - self.BUTTON_HEIGHT - self.PADDING,
            self.BUTTON_WIDTH,
            self.BUTTON_HEIGHT
        )
    
    def _init_avatar_selector(self):
        """Initialize the avatar selector."""
        if self.avatar_selector is None:
            avatar_center = (
                self.center_position[0],
                self.top_left[1] + 180
            )
            self.avatar_selector = AvatarSelector(
                avatar_ids=self.profile_manager.get_avatar_options(),
                center_position=avatar_center
            )
            
            # Set initial selection in edit mode
            if self.existing_profile and self.mode == "edit":
                self.avatar_selector.selected_avatar = self.existing_profile.avatar_id
    
    def set_name_text(self, text: str):
        """
        Set the name input text.
        
        Args:
            text: New text for the name field
        """
        self.name_text = text
        self.name_error = None
    
    def get_name_text(self) -> str:
        """Get the current name input text."""
        return self.name_text
    
    def handle_event(self, event: pygame.Event) -> Optional[str]:
        """
        Handle pygame events for the profile editor.
        
        Args:
            event: Pygame event to handle
            
        Returns:
            "save" if saved, "cancel" if cancelled, None otherwise
        """
        result = None
        
        # Handle text input
        if event.type == pygame.KEYDOWN:
            if self.input_active:
                if event.key == pygame.K_BACKSPACE:
                    self.name_text = self.name_text[:-1]
                elif event.key == pygame.K_RETURN:
                    result = self._try_save()
                else:
                    # Add character (limit to 30)
                    if len(self.name_text) < 30 and event.unicode:
                        self.name_text += event.unicode
            
            elif event.key == pygame.K_RETURN:
                result = self._try_save()
            elif event.key == pygame.K_ESCAPE:
                result = "cancel"
                if self.on_cancel:
                    self.on_cancel()
        
        # Handle mouse events
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                
                # Check input field
                if self.input_rect.collidepoint(mouse_pos):
                    self.input_active = True
                else:
                    self.input_active = False
                
                # Check buttons
                if self.save_button_rect.collidepoint(mouse_pos):
                    result = self._try_save()
                elif self.cancel_button_rect.collidepoint(mouse_pos):
                    result = "cancel"
                    if self.on_cancel:
                        self.on_cancel()
        
        # Handle avatar selector events (if visible)
        if self.show_avatar_selector and self.avatar_selector:
            selected = self.avatar_selector.handle_event(event)
            if selected:
                self.show_avatar_selector = False
        
        return result
    
    def _try_save(self) -> Optional[str]:
        """
        Attempt to save the profile.
        
        Returns:
            "save" if successful, None if validation failed
        """
        # Pre-sanitize name to match model validation
        from src.models.student_profile import StudentProfile
        
        sanitized = self.name_text.strip()
        
        # Validate name using model's constants
        if not sanitized:
            self.name_error = "Name is required"
            return None
        
        if len(sanitized) > StudentProfile.MAX_NAME_LENGTH:
            self.name_error = f"Name too long (max {StudentProfile.MAX_NAME_LENGTH} characters)"
            return None
        
        # Check avatar selection
        if not self.avatar_selector or not self.avatar_selector.selected_avatar:
            self.name_error = "Please select an avatar"
            return None
        
        avatar_id = self.avatar_selector.selected_avatar
        
        try:
            if self.mode == "create":
                # Create new profile
                self.profile_manager.create_profile(
                    name=self.name_text.strip(),
                    avatar_id=avatar_id
                )
            else:
                # Update existing profile
                if self.editing_profile_id:
                    self.profile_manager.update_profile(
                        profile_id=self.editing_profile_id,
                        name=self.name_text.strip(),
                        avatar_id=avatar_id
                    )
            
            if self.on_save:
                self.on_save()
            
            return "save"
        
        except ValueError as e:
            self.name_error = str(e)
            return None
    
    def render(self, screen: pygame.Surface):
        """
        Render the profile editor.
        
        Args:
            screen: Pygame surface to render on
        """
        # Initialize avatar selector if needed
        self._init_avatar_selector()
        
        # Draw background
        bg_rect = pygame.Rect(
            self.top_left[0] - 10,
            self.top_left[1] - 10,
            self.editor_width + 20,
            self.editor_height + 20
        )
        pygame.draw.rect(screen, (40, 40, 60), bg_rect, border_radius=10)
        pygame.draw.rect(screen, self.WHITE, bg_rect, 2, border_radius=10)
        
        # Draw title
        title = "Edit Student" if self.mode == "edit" else "New Student"
        font = pygame.font.Font(None, 36)
        title_surface = font.render(title, True, self.WHITE)
        title_rect = title_surface.get_rect(
            center=(self.center_position[0], self.top_left[1] + 25)
        )
        screen.blit(title_surface, title_rect)
        
        # Draw name label
        label_font = pygame.font.Font(None, 24)
        label_surface = label_font.render("Student Name:", True, self.WHITE)
        label_rect = label_surface.get_rect(
            left=self.top_left[0] + self.PADDING,
            bottom=self.input_rect.top - 5
        )
        screen.blit(label_surface, label_rect)
        
        # Draw name input
        input_bg_color = self.INPUT_BG
        border_color = self.INPUT_FOCUS_BORDER if self.input_active else self.INPUT_BORDER
        
        pygame.draw.rect(screen, input_bg_color, self.input_rect, border_radius=5)
        pygame.draw.rect(screen, border_color, self.input_rect, 2, border_radius=5)
        
        # Render text
        text_font = pygame.font.Font(None, 28)
        text_surface = text_font.render(self.name_text, True, self.WHITE)
        text_rect = text_surface.get_rect(
            left=self.input_rect.left + 10,
            centery=self.input_rect.centery
        )
        screen.blit(text_surface, text_rect)
        
        # Draw cursor if input active
        if self.input_active:
            cursor_x = text_rect.right + 2
            cursor_height = 24
            pygame.draw.line(
                screen, self.WHITE,
                (cursor_x, self.input_rect.centery - cursor_height // 2),
                (cursor_x, self.input_rect.centery + cursor_height // 2),
                2
            )
        
        # Draw error message
        if self.name_error:
            error_font = pygame.font.Font(None, 22)
            error_surface = error_font.render(self.name_error, True, self.ERROR_COLOR)
            error_rect = error_surface.get_rect(
                left=self.input_rect.left,
                top=self.input_rect.bottom + 5
            )
            screen.blit(error_surface, error_rect)
        
        # Draw avatar selector button
        avatar_button_rect = pygame.Rect(
            self.input_rect.left,
            self.input_rect.bottom + 40,
            200,
            self.BUTTON_HEIGHT
        )
        
        pygame.draw.rect(screen, self.BUTTON_COLOR, avatar_button_rect, border_radius=5)
        avatar_btn_text = label_font.render("Select Avatar", True, self.BUTTON_TEXT)
        avatar_btn_text_rect = avatar_btn_text.get_rect(center=avatar_button_rect.center)
        screen.blit(avatar_btn_text, avatar_btn_text_rect)
        
        # Draw "Selected" indicator if avatar chosen
        if self.avatar_selector and self.avatar_selector.selected_avatar:
            selected_label = label_font.render(
                f"Selected: {self.avatar_selector.selected_avatar.title()}",
                True, self.BUTTON_COLOR
            )
            selected_rect = selected_label.get_rect(
                left=avatar_button_rect.right + 10,
                centery=avatar_button_rect.centery
            )
            screen.blit(selected_label, selected_rect)
        
        # Draw buttons
        self._draw_button(screen, self.save_button_rect, "Save")
        self._draw_button(screen, self.cancel_button_rect, "Cancel")
        
        # Draw avatar selector overlay if visible
        if self.show_avatar_selector and self.avatar_selector:
            self.avatar_selector.render(screen, "Select Avatar")
    
    def _draw_button(self, screen: pygame.Surface, rect: pygame.Rect, text: str):
        """
        Draw a button.
        
        Args:
            screen: Pygame surface
            rect: Button rectangle
            text: Button label
        """
        # Button background
        pygame.draw.rect(screen, self.BUTTON_COLOR, rect, border_radius=5)
        
        # Button text
        font = pygame.font.Font(None, 24)
        text_surface = font.render(text, True, self.BUTTON_TEXT)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)
    
    def show_avatar_selection(self):
        """Show the avatar selection dialog."""
        if self.avatar_selector:
            self.show_avatar_selector = True


def create_profile_editor(
    profile_manager: ProfileManager,
    mode: str = "create",
    editing_profile_id: Optional[str] = None,
    center_position: Optional[Tuple[int, int]] = None
) -> ProfileEditor:
    """
    Factory function to create a ProfileEditor.
    
    Args:
        profile_manager: ProfileManager instance
        mode: "create" or "edit"
        editing_profile_id: Profile ID for edit mode
        center_position: Center position for the editor
        
    Returns:
        Configured ProfileEditor instance
    """
    editor = ProfileEditor(
        profile_manager=profile_manager,
        mode=mode,
        editing_profile_id=editing_profile_id,
        center_position=center_position
    )
    return editor
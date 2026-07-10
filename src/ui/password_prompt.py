"""
Password Prompt UI Component

Implements STORY-003-01: Parent Authentication

Provides a modal dialog for password entry with:
- Masked input (dots/asterisks)
- Error message display
- Enter key submission
- Esc key cancellation
"""

import pygame
from typing import Optional, Callable, Tuple

from src.auth.session_manager import SessionManager


class PasswordPrompt:
    """
    Modal password entry dialog.
    
    Features:
    - Centered modal overlay covering the screen
    - Masked password input (dots for each character)
    - Submit button with Enter key support
    - Cancel button with Esc key support
    - Error message display
    - Lockout message display
    - Keyboard accessible
    
    Visual Design:
    - Dark overlay with centered white dialog box
    - Password field shows dots (•) for each character
    - Error messages in red text
    - Consistent game UI button styling
    """
    
    # Colors
    COLOR_OVERLAY = (0, 0, 0, 180)  # Semi-transparent black
    COLOR_BG = (255, 255, 255)
    COLOR_TEXT = (50, 50, 70)
    COLOR_TEXT_LIGHT = (150, 150, 170)
    COLOR_ERROR = (244, 67, 54)
    COLOR_INPUT_BORDER = (189, 189, 189)
    COLOR_INPUT_FOCUS = (66, 165, 245)
    COLOR_BUTTON = (66, 165, 245)
    COLOR_BUTTON_HOVER = (33, 150, 243)
    COLOR_BUTTON_TEXT = (255, 255, 255)
    
    def __init__(
        self,
        session_manager: SessionManager,
        screen_width: int = 800,
        screen_height: int = 600,
        on_success: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None
    ):
        """
        Initialize the password prompt.
        
        Args:
            session_manager: SessionManager for authentication
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            on_success: Callback when authentication succeeds
            on_cancel: Callback when prompt is cancelled
        """
        self.session_manager = session_manager
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Callbacks
        self.on_success = on_success
        self.on_cancel = on_cancel
        
        # UI state
        self._password: str = ""
        self._error_message: str = ""
        self._is_locked_out: bool = False
        self._active: bool = False
        
        # UI elements
        self._dialog_rect: Optional[pygame.Rect] = None
        self._input_rect: Optional[pygame.Rect] = None
        self._submit_rect: Optional[pygame.Rect] = None
        self._cancel_rect: Optional[pygame.Rect] = None
        
        # Selection state
        self._hover_submit: bool = False
        self._hover_cancel: bool = False
        
        # Fonts
        self._title_font: Optional[pygame.font.Font] = None
        self._body_font: Optional[pygame.font.Font] = None
        self._input_font: Optional[pygame.font.Font] = None
        self._hint_font: Optional[pygame.font.Font] = None
        
        # Input handling
        self._input_active: bool = False
    
    def _init_fonts(self):
        """Initialize Pygame fonts."""
        if self._title_font is None:
            try:
                self._title_font = pygame.font.SysFont('arial', 24, bold=True)
                self._body_font = pygame.font.SysFont('arial', 16)
                self._input_font = pygame.font.SysFont('courier', 20)
                self._hint_font = pygame.font.SysFont('arial', 12)
            except:
                self._title_font = pygame.font.Font(None, 24)
                self._body_font = pygame.font.Font(None, 16)
                self._input_font = pygame.font.Font(None, 20)
                self._hint_font = pygame.font.Font(None, 12)
    
    def _calculate_layout(self):
        """Calculate UI element positions."""
        # Dialog box: 400x280 centered
        dialog_width = 400
        dialog_height = 280
        dialog_x = (self.screen_width - dialog_width) // 2
        dialog_y = (self.screen_height - dialog_height) // 2
        
        self._dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        
        # Input field: 300x40, centered
        input_width = 300
        input_height = 40
        input_x = dialog_x + (dialog_width - input_width) // 2
        input_y = dialog_y + 120
        self._input_rect = pygame.Rect(input_x, input_y, input_width, input_height)
        
        # Submit button: 120x35
        submit_width = 120
        submit_height = 35
        submit_x = dialog_x + 50
        submit_y = dialog_y + 180
        self._submit_rect = pygame.Rect(submit_x, submit_y, submit_width, submit_height)
        
        # Cancel button: 120x35
        cancel_x = dialog_x + dialog_width - 170
        cancel_y = dialog_y + 180
        self._cancel_rect = pygame.Rect(cancel_x, cancel_y, submit_width, submit_height)
    
    def activate(self):
        """Activate the password prompt."""
        self._active = True
        self._password = ""
        self._error_message = ""
        self._input_active = True
        self._init_fonts()
        self._calculate_layout()
    
    def deactivate(self):
        """Deactivate the password prompt."""
        self._active = False
        self._password = ""
        self._error_message = ""
        self._input_active = False
    
    def is_active(self) -> bool:
        """Check if prompt is currently active."""
        return self._active
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events.
        
        Args:
            event: Pygame event to handle
            
        Returns:
            True if event was handled, False otherwise
        """
        if not self._active:
            return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                self._submit_password()
                return True
            elif event.key == pygame.K_ESCAPE:
                self._cancelPassword()
                return True
            elif event.key == pygame.K_BACKSPACE:
                self._password = self._password[:-1]
                return True
            elif event.key == pygame.K_TAB:
                # Toggle between buttons
                self._input_active = False
                return True
            elif len(event.unicode) == 1 and event.unicode.isprintable():
                # Only allow printable characters
                self._password += event.unicode
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            # Update hover state
            pos = event.pos
            self._hover_submit = self._submit_rect.collidepoint(pos) if self._submit_rect else False
            self._hover_cancel = self._cancel_rect.collidepoint(pos) if self._cancel_rect else False
            self._input_active = self._input_rect.collidepoint(pos) if self._input_rect else False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                pos = event.pos
                if self._submit_rect and self._submit_rect.collidepoint(pos):
                    self._submit_password()
                    return True
                elif self._cancel_rect and self._cancel_rect.collidepoint(pos):
                    self._cancelPassword()
                    return True
                elif self._input_rect and self._input_rect.collidepoint(pos):
                    self._input_active = True
                    return True
                else:
                    self._input_active = False
        
        return False
    
    def _submit_password(self):
        """Submit password for authentication."""
        if self._is_locked_out:
            return
        
        success, message = self.session_manager.authenticate(self._password)
        
        if success:
            # Clear error and call success callback
            self._error_message = ""
            if self.on_success:
                self.on_success()
        else:
            # Update error message
            self._error_message = message
            self._password = ""  # Clear for retry
            
            # Check if locked out
            if "locked" in message.lower():
                self._is_locked_out = True
    
    def _cancelPassword(self):
        """Cancel the password prompt."""
        if self.on_cancel:
            self.on_cancel()
        self.deactivate()
    
    def render(self, screen: pygame.Surface):
        """
        Render the password prompt to the screen.
        
        Args:
            screen: Pygame surface to render to
        """
        if not self._active:
            return
        
        self._init_fonts()
        self._calculate_layout()
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill(self.COLOR_OVERLAY)
        screen.blit(overlay, (0, 0))
        
        # Draw dialog box
        if self._dialog_rect:
            # White background
            pygame.draw.rect(screen, self.COLOR_BG, self._dialog_rect, border_radius=8)
            # Border
            pygame.draw.rect(
                screen, self.COLOR_INPUT_FOCUS, self._dialog_rect, 2, border_radius=8
            )
        
        # Draw title
        if self._title_font and self._dialog_rect:
            title = "Parent Settings"
            title_surf = self._title_font.render(title, True, self.COLOR_TEXT)
            title_rect = title_surf.get_rect(centerx=self._dialog_rect.centerx, top=self._dialog_rect.y + 20)
            screen.blit(title_surf, title_rect)
        
        # Draw instruction
        if self._body_font and self._dialog_rect:
            instruction = "Enter password to continue:"
            instr_surf = self._body_font.render(instruction, True, self.COLOR_TEXT)
            instr_rect = instr_surf.get_rect(centerx=self._dialog_rect.centerx, top=self._dialog_rect.y + 60)
            screen.blit(instr_surf, instr_rect)
        
        # Draw lockout message
        if self._is_locked_out and self._dialog_rect:
            # Get remaining time
            remaining = self.session_manager._get_lockout_remaining_seconds()
            minutes, seconds = divmod(remaining, 60)
            lockout_msg = f"Locked. Try again in {minutes:02d}:{seconds:02d}"
            
            if self._body_font:
                lockout_surf = self._body_font.render(lockout_msg, True, self.COLOR_TEXT_LIGHT)
                lockout_rect = lockout_surf.get_rect(centerx=self._dialog_rect.centerx, top=self._dialog_rect.y + 220)
                screen.blit(lockout_surf, lockout_rect)
        
        # Draw input field
        if self._input_rect and self._input_font:
            # Input background
            bg_color = self.COLOR_BG if not self._input_active else (240, 248, 255)
            pygame.draw.rect(screen, bg_color, self._input_rect, border_radius=4)
            
            # Input border
            border_color = self.COLOR_INPUT_FOCUS if self._input_active else self.COLOR_INPUT_BORDER
            pygame.draw.rect(screen, border_color, self._input_rect, 2, border_radius=4)
            
            # Render masked password (dots)
            if self._password:
                masked = "•" * len(self._password)
                password_surf = self._input_font.render(masked, True, self.COLOR_TEXT)
                password_rect = password_surf.get_rect(left=self._input_rect.x + 10, centery=self._input_rect.centery)
                screen.blit(password_surf, password_rect)
            
            # Cursor blink (only when active and password empty or at end)
            if self._input_active and pygame.time.get_ticks() % 1000 < 500:
                cursor_x = self._input_rect.x + 10
                cursor_height = self._input_font.get_height()
                pygame.draw.line(
                    screen, self.COLOR_TEXT,
                    (cursor_x, self._input_rect.centery - cursor_height // 2),
                    (cursor_x, self._input_rect.centery + cursor_height // 2),
                    2
                )
        
        # Draw error message
        if self._error_message and self._body_font and self._dialog_rect:
            error_surf = self._body_font.render(self._error_message, True, self.COLOR_ERROR)
            error_rect = error_surf.get_rect(centerx=self._dialog_rect.centerx, top=self._input_rect.bottom + 10)
            screen.blit(error_surf, error_rect)
        
        # Draw buttons
        self._draw_button(screen, self._submit_rect, "Submit", self._hover_submit)
        self._draw_button(screen, self._cancel_rect, "Cancel", self._hover_cancel)
        
        # Draw hint for first-time setup
        if not self.session_manager.password_manager.has_password_set() and self._hint_font:
            hint = "First time? Set password in parent settings"
            hint_surf = self._hint_font.render(hint, True, self.COLOR_TEXT_LIGHT)
            hint_rect = hint_surf.get_rect(centerx=self._dialog_rect.centerx, bottom=self._dialog_rect.y + 70)
            screen.blit(hint_surf, hint_rect)
    
    def _draw_button(
        self,
        screen: pygame.Surface,
        rect: Optional[pygame.Rect],
        text: str,
        is_hovered: bool
    ):
        """
        Draw a button.
        
        Args:
            screen: Pygame surface to render to
            rect: Button rectangle
            text: Button text
            is_hovered: Whether mouse is hovering button
        """
        if not rect:
            return
        
        color = self.COLOR_BUTTON_HOVER if is_hovered else self.COLOR_BUTTON
        hover_color = self.COLOR_BUTTON_HOVER
        
        # Button background
        pygame.draw.rect(screen, color, rect, border_radius=4)
        
        # Button border
        pygame.draw.rect(screen, self.COLOR_INPUT_BORDER, rect, 2, border_radius=4)
        
        # Button text
        if self._hint_font:
            text_surf = self._hint_font.render(text, True, self.COLOR_BUTTON_TEXT)
            text_rect = text_surf.get_rect(center=rect.center)
            screen.blit(text_surf, text_rect)


def create_password_prompt(
    session_manager: SessionManager,
    screen_width: int = 800,
    screen_height: int = 600,
    on_success: Optional[Callable] = None,
    on_cancel: Optional[Callable] = None
) -> PasswordPrompt:
    """
    Factory function to create a PasswordPrompt.
    
    Args:
        session_manager: SessionManager for authentication
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        on_success: Callback when authentication succeeds
        on_cancel: Callback when prompt is cancelled
        
    Returns:
        Configured PasswordPrompt instance
    """
    return PasswordPrompt(
        session_manager=session_manager,
        screen_width=screen_width,
        screen_height=screen_height,
        on_success=on_success,
        on_cancel=on_cancel
    )
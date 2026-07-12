"""
Email Configuration Panel

UI component for configuring weekly email notifications.
Implements STORY-003-06: Email Notification Configuration
"""

import pygame
from typing import Optional, Callable, Tuple
from datetime import time

from src.email.email_config import EmailConfig, DayOfWeek
from src.email.email_service import EmailService


class EmailConfigPanel:
    """
    UI panel for email notification configuration.
    
    Features:
    - Enable/disable email notifications
    - Email address input with validation
    - Day/time selection for scheduled emails
    - GDPR consent checkbox
    - Test email button
    - Save/cancel actions
    
    Example:
        panel = EmailConfigPanel(config, service)
        panel.render(screen)
        panel.handle_event(event)
    """
    
    # Colors
    COLOR_BG = (250, 250, 255)
    COLOR_CARD = (255, 255, 255)
    COLOR_TEXT = (50, 50, 70)
    COLOR_TEXT_LIGHT = (100, 100, 120)
    COLOR_BORDER = (200, 200, 220)
    COLOR_ACCENT = (76, 175, 80)
    COLOR_ACCENT_LIGHT = (100, 189, 100)
    COLOR_ERROR = (244, 67, 54)
    COLOR_WARNING = (255, 152, 0)
    COLOR_CHECKBOX_ICON = (76, 175, 80)
    
    # Layout
    PADDING = 20
    SECTION_SPACING = 25
    INPUT_HEIGHT = 40
    BUTTON_HEIGHT = 40
    CHECKBOX_SIZE = 24
    
    def __init__(self, email_config: EmailConfig, email_service: EmailService,
                 width: int = 500, on_save: Optional[Callable] = None):
        """
        Initialize email configuration panel.
        
        Args:
            email_config: EmailConfig instance to configure
            email_service: EmailService instance for sending emails
            width: Panel width in pixels
            on_save: Optional callback when save is clicked
        """
        self.email_config = email_config
        self.email_service = email_service
        self.width = width
        self.height = 450
        self.on_save = on_save
        
        # State
        self._enabled = email_config.enabled
        self._email_address = email_config.email_address
        self._send_day = email_config.send_day
        self._send_time = email_config.send_time
        self._consent_given = email_config.consent_date is not None
        self._validation_message = ""
        self._validation_type = ""  # "error", "success", or ""
        
        # UI state
        self._show_consent_dialog = False
        self._test_email_result: Optional[Tuple[bool, str]] = None
        self._hovered_button: Optional[str] = None  # "save", "cancel", "test"
        
        # Input focus
        self._email_input_active = False
        self._email_input_text = email_config.email_address
        
        # Fonts (initialized on first render)
        self._title_font: Optional[pygame.font.Font] = None
        self._header_font: Optional[pygame.font.Font] = None
        self._body_font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None
        
        # UI element rects (calculated on render)
        self._enabled_checkbox_rect: Optional[pygame.Rect] = None
        self._email_input_rect: Optional[pygame.Rect] = None
        self._day_dropdown_rect: Optional[pygame.Rect] = None
        self._time_input_rect: Optional[pygame.Rect] = None
        self._consent_checkbox_rect: Optional[pygame.Rect] = None
        
        # Button rects
        self._save_button_rect: Optional[pygame.Rect] = None
        self._cancel_button_rect: Optional[pygame.Rect] = None
        self._test_button_rect: Optional[pygame.Rect] = None
    
    def _init_fonts(self):
        """Initialize Pygame fonts."""
        if self._title_font is None:
            try:
                self._title_font = pygame.font.SysFont('arial', 18, bold=True)
                self._header_font = pygame.font.SysFont('arial', 14, bold=True)
                self._body_font = pygame.font.SysFont('arial', 13)
                self._small_font = pygame.font.SysFont('arial', 11)
            except Exception:
                self._title_font = pygame.font.Font(None, 18)
                self._header_font = pygame.font.Font(None, 14)
                self._body_font = pygame.font.Font(None, 13)
                self._small_font = pygame.font.Font(None, 11)
    
    def render(self, surface: pygame.Surface):
        """
        Render the email configuration panel.
        
        Args:
            surface: Pygame surface to render to
        """
        self._init_fonts()
        
        # Clear background
        surface.fill(self.COLOR_BG)
        
        # Draw title
        self._draw_title(surface)
        
        # Draw content
        self._draw_content(surface)
        
        # Draw buttons
        self._draw_action_buttons(surface)
        
        # Draw validation message
        if self._validation_message:
            self._draw_validation_message(surface)
    
    def _draw_title(self, surface: pygame.Surface):
        """Draw panel title."""
        if self._title_font:
            title = "Email Notification Settings"
            title_surf = self._title_font.render(title, True, self.COLOR_TEXT)
            surface.blit(title_surf, (self.PADDING, self.PADDING))
    
    def _draw_content(self, surface: pygame.Surface):
        """Draw configuration controls."""
        y_offset = self.PADDING + 50
        
        # Enable/disable toggle
        y_offset = self._draw_enabled_toggle(surface, y_offset)
        
        # Only show full config if enabled
        if self._enabled:
            y_offset = self._draw_email_address_input(surface, y_offset)
            y_offset = self._draw_schedule_section(surface, y_offset)
            y_offset = self._draw_consent_checkbox(surface, y_offset)
            
            # Test email button
            y_offset = self._draw_test_button(surface, y_offset)
    
    def _draw_enabled_toggle(self, surface: pygame.Surface, y: int) -> int:
        """Draw enable/disable toggle."""
        if not self._title_font:
            return y
        
        # Checkbox
        checkbox_x = self.PADDING
        checkbox_y = y
        
        self._enabled_checkbox_rect = pygame.Rect(
            checkbox_x, checkbox_y, self.CHECKBOX_SIZE, self.CHECKBOX_SIZE
        )
        
        # Draw checkbox background
        checkbox_color = self.COLOR_ACCENT if self._enabled else self.COLOR_BORDER
        pygame.draw.rect(surface, checkbox_color, self._enabled_checkbox_rect, border_radius=4)
        
        # Draw checkmark if enabled
        if self._enabled:
            self._draw_checkmark(surface, self._enabled_checkbox_rect)
        
        # Label
        y_offset = checkbox_y + 5
        label_surf = self._body_font.render(
            "Enable weekly email progress reports", True, self.COLOR_TEXT
        )
        surface.blit(label_surf, (checkbox_x + self.CHECKBOX_SIZE + 10, y_offset))
        
        return y + 50
    
    def _draw_checkmark(self, surface: pygame.Surface, rect: pygame.Rect):
        """Draw checkmark inside checkbox."""
        if not self._body_font:
            return
        
        checkmark_surf = self._body_font.render("✓", True, (255, 255, 255))
        checkmark_rect = checkmark_surf.get_rect(center=rect.center)
        surface.blit(checkmark_surf, checkmark_rect)
    
    def _draw_email_address_input(self, surface: pygame.Surface, y: int) -> int:
        """Draw email address input field."""
        if not self._header_font:
            return y
        
        # Section header
        header_surf = self._header_font.render("Email Address", True, self.COLOR_TEXT)
        surface.blit(header_surf, (self.PADDING, y))
        
        y += 30
        
        # Input field
        input_x = self.PADDING
        input_y = y
        input_width = self.width - 2 * self.PADDING
        
        self._email_input_rect = pygame.Rect(
            input_x, input_y, input_width, self.INPUT_HEIGHT
        )
        
        # Input background
        input_color = (255, 255, 255) if self._email_input_active else self.COLOR_CARD
        pygame.draw.rect(surface, input_color, self._email_input_rect, border_radius=4)
        pygame.draw.rect(
            surface,
            self.COLOR_ACCENT if self._email_input_active else self.COLOR_BORDER,
            self._email_input_rect, 2, border_radius=4
        )
        
        # Input text
        display_text = self._email_input_text
        if self._email_input_active:
            # Add cursor
            display_text += "|"
        
        text_surf = self._body_font.render(display_text, True, self.COLOR_TEXT)
        surface.blit(text_surf, (input_x + 10, input_y + 8))
        
        # Placeholder if empty
        if not self._email_input_text:
            placeholder_surf = self._small_font.render(
                "Enter parent's email address", True, self.COLOR_TEXT_LIGHT
            )
            surface.blit(placeholder_surf, (input_x + 10, input_y + 8))
        
        return y + 70
    
    def _draw_schedule_section(self, surface: pygame.Surface, y: int) -> int:
        """Draw email schedule configuration."""
        if not self._header_font:
            return y
        
        # Section header
        header_surf = self._header_font.render("Email Schedule", True, self.COLOR_TEXT)
        surface.blit(header_surf, (self.PADDING, y))
        y += 30
        
        # Day selection
        if not self._body_font:
            return y
        
        day_label_surf = self._small_font.render(
            "Send on:", True, self.COLOR_TEXT_LIGHT
        )
        surface.blit(day_label_surf, (self.PADDING, y))
        
        # Day dropdown
        day_x = self.PADDING + 80
        day_y = y - 5
        day_width = 150
        
        self._day_dropdown_rect = pygame.Rect(
            day_x, day_y, day_width, self.INPUT_HEIGHT
        )
        
        current_day_name = self.email_config.DAY_NAMES.get(self._send_day, "Monday")
        day_surf = self._body_font.render(current_day_name, True, self.COLOR_TEXT)
        
        # Draw dropdown background
        pygame.draw.rect(surface, self.COLOR_CARD, self._day_dropdown_rect, border_radius=4)
        pygame.draw.rect(surface, self.COLOR_BORDER, self._day_dropdown_rect, 2, border_radius=4)
        surface.blit(day_surf, (day_x + 10, day_y + 8))
        
        # Time selection
        if not self._body_font:
            return y
        
        time_label_surf = self._small_font.render(
            "Send at:", True, self.COLOR_TEXT_LIGHT
        )
        time_x = self.PADDING + 240
        surface.blit(time_label_surf, (time_x, y))
        
        # Time input
        time_y = y - 5
        time_width = 120
        
        self._time_input_rect = pygame.Rect(
            time_x + 70, time_y, time_width, self.INPUT_HEIGHT
        )
        
        time_str = f"{self._send_time.hour:02d}:{self._send_time.minute:02d}"
        time_surf = self._body_font.render(time_str, True, self.COLOR_TEXT)
        
        pygame.draw.rect(surface, self.COLOR_CARD, self._time_input_rect, border_radius=4)
        pygame.draw.rect(surface, self.COLOR_BORDER, self._time_input_rect, 2, border_radius=4)
        surface.blit(time_surf, (time_x + 80, time_y + 8))
        
        return y + 60
    
    def _draw_consent_checkbox(self, surface: pygame.Surface, y: int) -> int:
        """Draw GDPR consent checkbox."""
        if not self._title_font:
            return y
        
        # Checkbox
        checkbox_x = self.PADDING
        checkbox_y = y
        
        self._consent_checkbox_rect = pygame.Rect(
            checkbox_x, checkbox_y, self.CHECKBOX_SIZE, self.CHECKBOX_SIZE
        )
        
        # Draw checkbox background
        checkbox_color = self.COLOR_ACCENT if self._consent_given else self.COLOR_BORDER
        pygame.draw.rect(surface, checkbox_color, self._consent_checkbox_rect, border_radius=4)
        
        # Draw checkmark if consented
        if self._consent_given:
            self._draw_checkmark(surface, self._consent_checkbox_rect)
        
        # Label
        label_y = checkbox_y + 3
        
        if self._body_font:
            consent_label = "I consent to receiving weekly progress emails"
            consent_surf = self._body_font.render(consent_label, True, self.COLOR_TEXT)
            surface.blit(consent_surf, (checkbox_x + self.CHECKBOX_SIZE + 10, label_y))
        
        return y + 50
    
    def _draw_test_button(self, surface: pygame.Surface, y: int) -> int:
        """Draw test email button."""
        if not self._body_font:
            return y
        
        button_x = self.PADDING
        button_y = y
        button_width = 150
        
        self._test_button_rect = pygame.Rect(
            button_x, button_y, button_width, self.BUTTON_HEIGHT
        )
        
        # Button background
        is_hovered = self._test_button_rect.collidepoint(pygame.mouse.get_pos())
        button_color = self.COLOR_ACCENT_LIGHT if is_hovered else self.COLOR_ACCENT
        
        pygame.draw.rect(surface, button_color, self._test_button_rect, border_radius=4)
        pygame.draw.rect(surface, self.COLOR_BORDER, self._test_button_rect, 2, border_radius=4)
        
        # Button text
        test_surf = self._body_font.render("Send Test Email", True, (255, 255, 255))
        test_rect = test_surf.get_rect(center=self._test_button_rect.center)
        surface.blit(test_surf, test_rect)
        
        # Test result message
        if self._test_email_result:
            success, message = self._test_email_result
            result_color = self.COLOR_ACCENT if success else self.COLOR_ERROR
            
            result_surf = self._small_font.render(message, True, result_color)
            surface.blit(result_surf, (button_x, button_y + self.BUTTON_HEIGHT + 5))
        
        return y + 100
    
    def _draw_action_buttons(self, surface: pygame.Surface):
        """Draw Save and Cancel buttons."""
        button_height = 45
        button_width = 120
        button_y = self.height - 80
        
        # Save button
        self._save_button_rect = pygame.Rect(
            self.width - button_width - self.PADDING - 10, button_y, button_width, button_height
        )
        
        is_save_hovered = self._save_button_rect.collidepoint(pygame.mouse.get_pos())
        save_color = self.COLOR_ACCENT_LIGHT if is_save_hovered else self.COLOR_ACCENT
        
        pygame.draw.rect(surface, save_color, self._save_button_rect, border_radius=4)
        pygame.draw.rect(surface, self.COLOR_BORDER, self._save_button_rect, 2, border_radius=4)
        
        if self._body_font:
            save_surf = self._body_font.render("Save", True, (255, 255, 255))
            save_rect = save_surf.get_rect(center=self._save_button_rect.center)
            surface.blit(save_surf, save_rect)
        
        # Cancel button
        self._cancel_button_rect = pygame.Rect(
            self.width - button_width - self.PADDING - 10 - (button_width + 10), button_y,
            button_width, button_height
        )
        
        is_cancel_hovered = self._cancel_button_rect.collidepoint(pygame.mouse.get_pos())
        cancel_color = (200, 200, 200) if is_cancel_hovered else (180, 180, 180)
        
        pygame.draw.rect(surface, cancel_color, self._cancel_button_rect, border_radius=4)
        pygame.draw.rect(surface, self.COLOR_BORDER, self._cancel_button_rect, 2, border_radius=4)
        
        if self._body_font:
            cancel_surf = self._body_font.render("Cancel", True, (50, 50, 50))
            cancel_rect = cancel_surf.get_rect(center=self._cancel_button_rect.center)
            surface.blit(cancel_surf, cancel_rect)
    
    def _draw_validation_message(self, surface: pygame.Surface):
        """Draw validation error/success message."""
        if not self._body_font:
            return
        
        color = self.COLOR_ERROR if self._validation_type == "error" else self.COLOR_ACCENT
        
        msg_surf = self._body_font.render(self._validation_message, True, color)
        msg_rect = msg_surf.get_rect(center=(self.width // 2, self.height - 25))
        
        # Background for message
        padding = 5
        bg_rect = msg_rect.inflate(padding * 2, padding * 2)
        pygame.draw.rect(surface, self.COLOR_CARD, bg_rect, border_radius=4)
        surface.blit(msg_surf, msg_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events.
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_mouse_click(event.pos)
        
        if event.type == pygame.KEYDOWN and self._email_input_active:
            self._handle_key_input(event)
            return True
        
        if event.type == pygame.MOUSEMOTION:
            self._hovered_button = None
            # Check for button hovers
            if self._save_button_rect and self._save_button_rect.collidepoint(event.pos):
                self._hovered_button = "save"
            elif self._cancel_button_rect and self._cancel_button_rect.collidepoint(event.pos):
                self._hovered_button = "cancel"
            elif self._test_button_rect and self._test_button_rect.collidepoint(event.pos):
                self._hovered_button = "test"
        
        return False
    
    def _handle_mouse_click(self, pos: tuple) -> bool:
        """Handle mouse click events."""
        # Enabled checkbox
        if self._enabled_checkbox_rect and self._enabled_checkbox_rect.collidepoint(pos):
            self._toggle_enabled()
            return True
        
        # Email input field
        if self._email_input_rect and self._email_input_rect.collidepoint(pos):
            self._email_input_active = True
            return True
        
        # Clicked outside email input - deactivate
        if self._email_input_rect and not self._email_input_rect.collidepoint(pos):
            self._email_input_active = False
            return True
        
        # Day dropdown - would open day selector (simplified for MVP)
        if self._day_dropdown_rect and self._day_dropdown_rect.collidepoint(pos):
            self._show_day_selector()
            return True
        
        # Consent checkbox
        if self._consent_checkbox_rect and self._consent_checkbox_rect.collidepoint(pos):
            self._consent_given = not self._consent_given
            return True
        
        # Test email button
        if self._test_button_rect and self._test_button_rect.collidepoint(pos):
            self._send_test_email()
            return True
        
        # Save button
        if self._save_button_rect and self._save_button_rect.collidepoint(pos):
            return self._handle_save()
        
        # Cancel button
        if self._cancel_button_rect and self._cancel_button_rect.collidepoint(pos):
            self._handle_cancel()
            return True
        
        return False
    
    def _handle_key_input(self, event: pygame.event.Event):
        """Handle keyboard input for email field."""
        if event.key == pygame.K_RETURN:
            self._email_input_active = False
        elif event.key == pygame.K_ESCAPE:
            self._email_input_active = False
        elif event.key == pygame.K_BACKSPACE:
            self._email_input_text = self._email_input_text[:-1]
        elif event.key == pygame.K_DELETE:
            self._email_input_text = ""
        elif event.key == pygame.K_a and event.mod & pygame.KMOD_CTRL:
            self._email_input_text = ""  # Ctrl+A clears for simplicity
        elif len(event.unicode) == 1 and event.unicode.isprintable():
            # Basic ASCII filter
            if event.unicode.isprintable():
                self._email_input_text += event.unicode
    
    def _toggle_enabled(self):
        """Toggle email enabled state."""
        self._enabled = not self._enabled
        if not self._enabled:
            self._consent_given = False
    
    def _show_day_selector(self):
        """Show day selector (simplified - just cycle days for MVP)."""
        # Find next day
        next_day_value = (self._send_day.value + 1) % 7
        self._send_day = DayOfWeek(next_day_value)
    
    def _send_test_email(self):
        """Send test email."""
        # Validate configuration first
        is_valid, message = self._validate_config()
        if not is_valid:
            self._validation_message = message
            self._validation_type = "error"
            return
        
        # Send test email
        success, test_message = self.email_service.send_test_email(self._email_address)
        self._test_email_result = (success, test_message)
    
    def _validate_config(self) -> tuple[bool, str]:
        """
        Validate current configuration.
        
        Returns:
            Tuple of (is_valid, message)
        """
        if self._enabled:
            if not self._email_input_text:
                return False, "Email address is required"
            
            # Basic format check
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, self._email_input_text):
                return False, "Invalid email format"
            
            if not self._consent_given:
                return False, "GDPR consent is required"
        
        return True, "Configuration valid"
    
    def _handle_save(self) -> bool:
        """
        Handle save button click.
        
        Returns:
            True if save successful
        """
        is_valid, message = self._validate_config()
        if not is_valid:
            self._validation_message = message
            self._validation_type = "error"
            return False
        
        # Update configuration
        self.email_config.enabled = self._enabled
        if self._enabled:
            self.email_config.email_address = self._email_input_text
            self.email_config.send_day = self._send_day
            self.email_config.send_time = self._send_time
            
            if not self.email_config.consent_date:
                self.email_config.record_consent()
            
            # Calculate next scheduled time
            self.email_config._calculate_next_scheduled(datetime.now())
        
        # Save configuration
        self.email_config.save()
        
        # Clear validation
        self._validation_message = ""
        self._validation_type = ""
        
        # Callback
        if self.on_save:
            self.on_save()
        
        return True
    
    def _handle_cancel(self):
        """Handle cancel button click - revert changes."""
        self._enabled = self.email_config.enabled
        self._email_input_text = self.email_config.email_address
        self._send_day = self.email_config.send_day
        self._send_time = self.email_config.send_time
        self._consent_given = self.email_config.consent_date is not None
        self._validation_message = ""
        self._test_email_result = None
    
    def get_rect(self) -> pygame.Rect:
        """
        Get panel bounding rectangle.
        
        Returns:
            Rect covering the panel
        """
        return pygame.Rect(0, 0, self.width, self.height)
    
    def reset_test_result(self):
        """Clear test email result."""
        self._test_email_result = None


from datetime import datetime


def create_email_config_panel(
    email_config: EmailConfig,
    email_service: EmailService,
    width: int = 500,
    on_save: Optional[Callable] = None
) -> EmailConfigPanel:
    """
    Factory function to create an EmailConfigPanel.
    
    Args:
        email_config: EmailConfig instance
        email_service: EmailService instance
        width: Panel width
        on_save: Optional save callback
        
    Returns:
        Configured EmailConfigPanel
    """
    return EmailConfigPanel(email_config, email_service, width, on_save)
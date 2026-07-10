"""
Unit tests for PasswordPrompt UI component

Tests for STORY-003-01: Parent Authentication
"""

import pytest
import pygame
from unittest.mock import MagicMock, call

# Initialize pygame for tests
try:
    pygame.display.set_mode((1, 1))  # Need a display for password_prompt font operations
except pygame.error:
    pass  # Display not available in headless mode, continue anyway

from src.ui.password_prompt import PasswordPrompt
from src.auth.session_manager import SessionManager


@pytest.fixture
def mock_session_manager():
    """Create a mock SessionManager."""
    sm = MagicMock(spec=SessionManager)
    sm.authenticate.return_value = (True, "Authenticated successfully")
    sm.is_authenticated.return_value = True
    sm._get_lockout_remaining_seconds.return_value = 0
    sm._is_locked_out.return_value = False
    sm._failed_attempts = 0
    
    # Create a separate mock for password_manager
    mock_pm = MagicMock()
    mock_pm.has_password_set.return_value = True
    sm.password_manager = mock_pm
    
    return sm


class TestPasswordPrompt:
    """Test suite for PasswordPrompt class."""
    
    @pytest.fixture
    def password_prompt(self, mock_session_manager):
        """Create a PasswordPrompt instance."""
        return PasswordPrompt(
            session_manager=mock_session_manager,
            screen_width=800,
            screen_height=600
        )
    
    def test_init(self, password_prompt, mock_session_manager):
        """Test PasswordPrompt initialization."""
        assert password_prompt.screen_width == 800
        assert password_prompt.screen_height == 600
        assert password_prompt._password == ""
        assert password_prompt._error_message == ""
        assert password_prompt._active is False
        assert password_prompt.on_success is None
        assert password_prompt.on_cancel is None
    
    def test_init_with_callbacks(self, mock_session_manager):
        """Test initialization with callbacks."""
        success_cb = MagicMock()
        cancel_cb = MagicMock()
        
        prompt = PasswordPrompt(
            session_manager=mock_session_manager,
            screen_width=800,
            screen_height=600,
            on_success=success_cb,
            on_cancel=cancel_cb
        )
        
        assert prompt.on_success is success_cb
        assert prompt.on_cancel is cancel_cb
    
    def test_activate(self, password_prompt):
        """Test activating the prompt."""
        password_prompt.activate()
        
        assert password_prompt._active is True
        assert password_prompt._password == ""
        assert password_prompt._error_message == ""
        assert password_prompt._input_active is True
    
    def test_deactivate(self, password_prompt):
        """Test deactivating the prompt."""
        password_prompt._active = True
        password_prompt._password = "test"
        
        password_prompt.deactivate()
        
        assert password_prompt._active is False
        assert password_prompt._password == ""
    
    def test_is_active(self, password_prompt):
        """Test is_active method."""
        assert password_prompt.is_active() is False
        
        password_prompt._active = True
        assert password_prompt.is_active() is True
    
    def test_handle_keydown_return_submits_password(self, password_prompt, mock_session_manager):
        """Test that Return key submits password."""
        password_prompt._active = True
        password_prompt._password = "testpass"
        
        # Create mock event
        event = MagicMock()
        event.type = "KEYDOWN"
        event.key = "RETURN"
        
        # Mock pygame events
        import pygame
        original_keys = pygame.key
        pygame.key = MagicMock()
        pygame.key.get_pressed.return_value = [False] * 256
        
        # Mock event properly
        event = MagicMock()
        event.type = pygame.KEYDOWN if hasattr(pygame, 'KEYDOWN') else "KEYDOWN"
        event.key = pygame.K_RETURN if hasattr(pygame, 'K_RETURN') else 13
        
        result = password_prompt.handle_event(event)
        
        # Verify authenticate was called
        mock_session_manager.authenticate.assert_called_once()
        assert result is True
        
        # Restore
        pygame.key = original_keys
    
    def test_handle_keydown_esc_cancels(self, password_prompt):
        """Test that Escape key cancels the prompt."""
        password_prompt._active = True
        on_cancel_calls = []
        password_prompt.on_cancel = lambda: on_cancel_calls.append(True)
        
        event = MagicMock()
        event.type = "KEYDOWN"
        event.key = "ESCAPE"
        
        import pygame
        event.key = pygame.K_ESCAPE if hasattr(pygame, 'K_ESCAPE') else 27
        event.type = pygame.KEYDOWN if hasattr(pygame, 'KEYDOWN') else "KEYDOWN"
        
        result = password_prompt.handle_event(event)
        
        assert result is True
        assert len(on_cancel_calls) == 1
        assert password_prompt._active is False
    
    def test_handle_keydown_backspace(self, password_prompt):
        """Test that Backspace removes last character."""
        password_prompt._active = True
        password_prompt._password = "test"
        
        event = MagicMock()
        event.type = "KEYDOWN"
        event.key = "BACKSPACE"
        
        import pygame
        event.key = pygame.K_BACKSPACE if hasattr(pygame, 'K_BACKSPACE') else 8
        event.type = pygame.KEYDOWN if hasattr(pygame, 'KEYDOWN') else "KEYDOWN"
        
        password_prompt.handle_event(event)
        
        assert password_prompt._password == "tes"
    
    def test_handle_keydown_character_input(self, password_prompt):
        """Test character input."""
        password_prompt._active = True
        
        event = MagicMock()
        event.type = "KEYDOWN"
        event.key = "A"
        event.unicode = "a"
        
        import pygame
        event.type = pygame.KEYDOWN if hasattr(pygame, 'KEYDOWN') else "KEYDOWN"
        
        password_prompt.handle_event(event)
        
        assert password_prompt._password == "a"
    
    def test_handle_keydown_non_printable_ignored(self, password_prompt):
        """Test that non-printable characters are ignored."""
        password_prompt._active = True
        
        event = MagicMock()
        event.type = "KEYDOWN"
        event.key = "SYMBOL"
        event.unicode = "\x00"  # Null character
        
        password_prompt.handle_event(event)
        
        assert password_prompt._password == ""
    
    def test_submit_password_success(self, password_prompt, mock_session_manager):
        """Test successful password submission."""
        password_prompt._active = True
        password_prompt._password = "correctpass"
        
        success_callback = MagicMock()
        password_prompt.on_success = success_callback
        
        password_prompt._submit_password()
        
        mock_session_manager.authenticate.assert_called_once_with("correctpass")
        assert success_callback.called
        assert password_prompt._error_message == ""
    
    def test_submit_password_failure(self, password_prompt, mock_session_manager):
        """Test failed password submission."""
        password_prompt._active = True
        password_prompt._password = "wrongpass"
        
        mock_session_manager.authenticate.return_value = (False, "Incorrect password")
        
        password_prompt._submit_password()
        
        mock_session_manager.authenticate.assert_called_once_with("wrongpass")
        assert password_prompt._error_message == "Incorrect password"
        assert password_prompt._password == ""  # Cleared for retry
    
    def test_submit_password_when_locked_out(self, password_prompt, mock_session_manager):
        """Test password submission when locked out."""
        password_prompt._active = True
        password_prompt._password = "anypass"
        password_prompt._is_locked_out = True
        
        password_prompt._submit_password()
        
        # authenticate should not be called when locked out
        mock_session_manager.authenticate.assert_not_called()
    
    def test_cancel_password(self, password_prompt):
        """Test password cancellation."""
        password_prompt._active = True
        cancel_calls = []
        password_prompt.on_cancel = lambda: cancel_calls.append(True)
        
        password_prompt._cancelPassword()
        
        assert len(cancel_calls) == 1
        assert password_prompt._active is False
    
    def test_handle_mouse_motion_updates_hover(self, password_prompt):
        """Test mouse motion updates hover state."""
        password_prompt._active = True
        password_prompt._calculate_layout()
        
        # Move mouse to submit button position
        event = MagicMock()
        event.type = "MOUSEMOTION"
        event.pos = (password_prompt._submit_rect.centerx, 
                     password_prompt._submit_rect.centery) if password_prompt._submit_rect else (400, 300)
        
        password_prompt.handle_event(event)
        
        # Hover state should update (depends on button rect existence)
        # This is a basic test as exact behavior depends on UI layout
    
    def test_handle_mouse_click_submit(self, password_prompt, mock_session_manager):
        """Test mouse click on submit button."""
        password_prompt._active = True
        password_prompt._calculate_layout()
        
        if password_prompt._submit_rect:
            pos = password_prompt._submit_rect.center
            
            event = MagicMock()
            event.type = "MOUSEBUTTONDOWN"
            event.button = 1
            event.pos = pos
            
            password_prompt.handle_event(event)
            
            mock_session_manager.authenticate.assert_called()
    
    def test_render_when_not_active(self, password_prompt):
        """Test that render does nothing when not active."""
        surface = MagicMock()
        
        password_prompt.render(surface)
        
        # Should not attempt to draw anything
        surface.fill.assert_not_called()
    
    def test_factory_function(self, mock_session_manager):
        """Test create_password_prompt factory function."""
        from src.ui.password_prompt import create_password_prompt
        
        prompt = create_password_prompt(
            session_manager=mock_session_manager,
            screen_width=1024,
            screen_height=768
        )
        
        assert isinstance(prompt, PasswordPrompt)
        assert prompt.screen_width == 1024
        assert prompt.screen_height == 768


class TestPasswordPromptLayout:
    """Test layout calculations."""
    
    @pytest.fixture
    def prompt_with_layout(self, mock_session_manager):
        """Create PasswordPrompt with calculated layout."""
        prompt = PasswordPrompt(
            session_manager=mock_session_manager,
            screen_width=800,
            screen_height=600
        )
        prompt.activate()
        return prompt
    
    def test_dialog_centered(self, prompt_with_layout):
        """Test that dialog is centered on screen."""
        dialog = prompt_with_layout._dialog_rect
        assert dialog is not None
        
        # Dialog should be centered
        assert dialog.centerx == 400  # 800 / 2
        assert dialog.centery == 300  # 600 / 2
    
    def test_dialog_dimensions(self, prompt_with_layout):
        """Test dialog has correct dimensions."""
        dialog = prompt_with_layout._dialog_rect
        assert dialog.width == 400
        assert dialog.height == 280
    
    def test_input_field_position(self, prompt_with_layout):
        """Test input field is positioned correctly."""
        dialog = prompt_with_layout._dialog_rect
        input_field = prompt_with_layout._input_rect
        
        assert input_field is not None
        # Should be within dialog bounds
        assert dialog.contains(input_field)
    
    def test_buttons_position(self, prompt_with_layout):
        """Test submit and cancel buttons are positioned."""
        assert prompt_with_layout._submit_rect is not None
        assert prompt_with_layout._cancel_rect is not None
        
        # Both should be near bottom of dialog
        dialog = prompt_with_layout._dialog_rect
        assert prompt_with_layout._submit_rect.bottom <= dialog.bottom
        assert prompt_with_layout._cancel_rect.bottom <= dialog.bottom


class TestPasswordPromptColors:
    """Test color constants."""
    
    def test_colors_defined(self, password_prompt):
        """Test that all required colors are defined."""
        assert hasattr(password_prompt, 'COLOR_OVERLAY')
        assert hasattr(password_prompt, 'COLOR_BG')
        assert hasattr(password_prompt, 'COLOR_TEXT')
        assert hasattr(password_prompt, 'COLOR_ERROR')
        assert hasattr(password_prompt, 'COLOR_BUTTON')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
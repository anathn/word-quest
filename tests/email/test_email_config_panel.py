"""
Tests for EmailConfigPanel

Implements STORY-003-06: Email Notification Configuration
"""

import os

# Set environment variables BEFORE pygame import (conftest.py also sets these)
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pytest
import pygame
from datetime import datetime, time

# NOTE: pygame initialization is handled by conftest.py session-scoped fixture
# Do NOT initialize pygame at module level to avoid conflicts with xdist workers

from src.email.email_config import EmailConfig, DayOfWeek
from src.email.email_service import EmailService
from src.ui.email_config_panel import EmailConfigPanel


class TestEmailConfigPanelInit:
    """Test EmailConfigPanel initialization."""
    
    def test_basic_initialization(self):
        """Test basic panel creation."""
        config = EmailConfig()
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        
        panel = EmailConfigPanel(config, service)
        
        assert panel.email_config == config
        assert panel.email_service == service
        assert panel.width == 500
        assert panel.height == 450
        assert panel._enabled == config.enabled
        assert panel._email_address == config.email_address
    
    def test_initial_state_from_config(self):
        """Test panel initial state matches config."""
        config = EmailConfig(
            enabled=True,
            email_address="parent@example.com",
            send_day=DayOfWeek.FRIDAY,
            send_time=time(18, 0),
            consent_date=datetime.now()
        )
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        
        panel = EmailConfigPanel(config, service)
        
        assert panel._enabled is True
        assert panel._email_address == "parent@example.com"
        assert panel._send_day == DayOfWeek.FRIDAY
        assert panel._send_time == time(18, 0)
        assert panel._consent_given is True


class TestEmailConfigPanelRendering:
    """Test panel rendering."""
    
    def setup_method(self):
        """Ensure pygame is properly initialized for rendering tests."""
        # pygame is already initialized at module level
        pass
    
    def teardown_method(self):
        """Cleanup after tests."""
        pass  # Don't quit pygame to avoid conflicts
    
    def test_render_creates_fonts(self):
        """Test that render initializes fonts."""
        config = EmailConfig()
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        panel = EmailConfigPanel(config, service)
        
        surface = pygame.Surface((500, 450))
        panel.render(surface)
        
        assert panel._title_font is not None
        assert panel._header_font is not None
        assert panel._body_font is not None
    
    def test_render_enabled_panel(self):
        """Test rendering enabled email config panel."""
        config = EmailConfig(
            enabled=True,
            email_address="test@example.com",
            consent_date=datetime.now()
        )
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        panel = EmailConfigPanel(config, service)
        
        surface = pygame.Surface((500, 450))
        panel.render(surface)
        
        # Just verify no errors occur
        assert surface is not None
    
    def test_get_rect(self):
        """Test panel rect calculation."""
        config = EmailConfig()
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        panel = EmailConfigPanel(config, service)
        
        rect = panel.get_rect()
        
        assert rect.width == 500
        assert rect.height == 450


class TestEmailConfigPanelValidation:
    """Test panel validation logic."""
    
    def test_validate_disabled_config(self):
        """Test validation of disabled config."""
        config = EmailConfig(enabled=False)
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        panel = EmailConfigPanel(config, service)
        
        is_valid, message = panel._validate_config()
        
        assert is_valid is True
    
    def test_validate_enabled_no_email(self):
        """Test validation fails when enabled but no email."""
        config = EmailConfig(enabled=True)
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        panel = EmailConfigPanel(config, service)
        panel._enabled = True
        
        is_valid, message = panel._validate_config()
        
        assert is_valid is False
        assert "email" in message.lower()
    
    def test_validate_enabled_invalid_email(self):
        """Test validation fails with invalid email format."""
        config = EmailConfig()
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        panel = EmailConfigPanel(config, service)
        panel._enabled = True
        panel._email_input_text = "invalid"
        
        is_valid, message = panel._validate_config()
        
        assert is_valid is False
        assert "format" in message.lower()
    
    def test_validate_enabled_no_consent(self):
        """Test validation fails without consent."""
        config = EmailConfig()
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        panel = EmailConfigPanel(config, service)
        panel._enabled = True
        panel._email_input_text = "test@example.com"
        panel._consent_given = False
        
        is_valid, message = panel._validate_config()
        
        assert is_valid is False
        assert "consent" in message.lower()
    
    def test_validate_full_config(self):
        """Test validation passes with complete config."""
        config = EmailConfig()
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        panel = EmailConfigPanel(config, service)
        panel._enabled = True
        panel._email_input_text = "test@example.com"
        panel._consent_given = True
        
        is_valid, message = panel._validate_config()
        
        assert is_valid is True


class TestEmailConfigPanelActions:
    """Test panel user actions."""
    
    def test_toggle_enabled(self):
        """Test toggling enabled state."""
        config = EmailConfig(enabled=False)
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        panel = EmailConfigPanel(config, service)
        
        panel._toggle_enabled()
        assert panel._enabled is True
        
        panel._toggle_enabled()
        assert panel._enabled is False
    
    def test_toggle_enabled_clears_consent(self):
        """Test disabling also clears consent."""
        config = EmailConfig(
            enabled=True,
            consent_date=datetime.now()
        )
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        panel = EmailConfigPanel(config, service)
        
        panel._enabled = True
        panel._consent_given = True
        panel._toggle_enabled()
        
        assert panel._enabled is False
        assert panel._consent_given is False  # Should be cleared per implementation
    
    def test_save_cancel_restore_state(self):
        """Test cancel restores original state."""
        original_config = EmailConfig(
            enabled=True,
            email_address="original@example.com",
            send_day=DayOfWeek.MONDAY
        )
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        panel = EmailConfigPanel(original_config, service)
        
        # Modify panel state
        panel._enabled = False
        panel._email_input_text = "modified@example.com"
        
        # Cancel should restore
        panel._handle_cancel()
        
        assert panel._enabled is True
        assert panel._email_input_text == "original@example.com"


class TestEmailConfigPanelCallback:
    """Test panel callback functionality."""
    
    def test_on_save_callback(self):
        """Test save triggers callback."""
        config = EmailConfig(
            enabled=True,
            email_address="test@example.com",
            consent_date=datetime.now()
        )
        service = EmailService("smtp.test.com", 587, "user", "pass", "sender@test.com")
        
        callback_called = False
        def on_save():
            nonlocal callback_called
            callback_called = True
        
        panel = EmailConfigPanel(config, service, on_save=on_save)
        
        # Mock validation to pass
        panel._validation_message = ""
        
        result = panel._handle_save()
        
        assert callback_called is True
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
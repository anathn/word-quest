"""
Authenticated Parent Dashboard

Implements STORY-003-01: Parent Authentication

This module provides a wrapper around the ParentDashboardScreen that handles:
- Password authentication before access
- Session timeout management
- Re-authentication on timeout
- Integration with the main game loop
"""

import pygame
from typing import Dict, List, Optional, Callable

from src.auth.session_manager import SessionManager
from src.auth.password_manager import PasswordManager
from src.auth.auth_config import AuthConfig
from src.ui.password_prompt import PasswordPrompt
from src.screens.parent_dashboard import ParentDashboardScreen, create_parent_dashboard


class AuthenticatedParentDashboard:
    """
    Manages authenticated access to the parent dashboard.
    
    This class wraps the ParentDashboardScreen to provide:
    - Password authentication gateway
    - Session timeout handling
    - Automatic re-authentication on timeout
    - Integration with game event loop
    
    Usage:
        dashboard = AuthenticatedParentDashboard(session_manager, analytics_data)
        
        # In game loop:
        dashboard.handle_event(event)  # Handle all pygame events
        dashboard.render(screen)       # Render appropriate screen
    """
    
    # States
    STATE_LOCKED = "locked"
    STATE_AUTHENTICATING = "authenticating"
    STATE_AUTHENTICATED = "authenticated"
    
    def __init__(
        self,
        sessions: List[Dict],
        screen_width: int = 800,
        screen_height: int = 600,
        session_manager: Optional[SessionManager] = None,
        on_logout: Optional[Callable] = None
    ):
        """
        Initialize the authenticated parent dashboard.
        
        Args:
            sessions: List of session data dictionaries for analytics
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            session_manager: SessionManager instance (creates default if None)
            on_logout: Callback when user logs out
        """
        self.sessions = sessions
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.on_logout = on_logout
        
        # Initialize authentication components
        if session_manager is None:
            password_manager = PasswordManager()
            self.session_manager = SessionManager(password_manager=password_manager)
        else:
            self.session_manager = session_manager
        
        # State management
        self._state = self.STATE_LOCKED
        
        # UI components
        self.password_prompt: Optional[PasswordPrompt] = None
        self.dashboard_screen: Optional[ParentDashboardScreen] = None
        
        # Initialize password prompt
        self._init_password_prompt()
    
    def _init_password_prompt(self):
        """Initialize the password prompt UI component."""
        def on_auth_success():
            self._state = self.STATE_AUTHENTICATED
            self._create_dashboard()
        
        def on_cancel():
            self._state = self.STATE_LOCKED
        
        # Note: is_setup_mode=False for regular auth (will be set to True in _show_first_time_setup)
        self.password_prompt = PasswordPrompt(
            session_manager=self.session_manager,
            screen_width=self.screen_width,
            screen_height=self.screen_height,
            on_success=on_auth_success,
            on_cancel=on_cancel,
            is_setup_mode=False
        )
    
    def _create_dashboard(self):
        """Create the parent dashboard screen."""
        self.dashboard_screen = create_parent_dashboard(
            sessions=self.sessions,
            screen_width=self.screen_width,
            screen_height=self.screen_height
        )
    
    def activate(self):
        """Activate the dashboard (show password prompt)."""
        if not self.session_manager.password_manager.has_password_set():
            # First-time setup - show password creation flow
            self._show_first_time_setup()
            return
        
        self._state = self.STATE_AUTHENTICATING
        self.password_prompt.activate()
    
    def _show_first_time_setup(self):
        """Show password creation wizard for first-time users."""
        self._state = self.STATE_AUTHENTICATING
        # Reinitialize password prompt in setup mode
        self.password_prompt = PasswordPrompt(
            session_manager=self.session_manager,
            screen_width=self.screen_width,
            screen_height=self.screen_height,
            on_success=self._on_setup_complete,
            on_cancel=self._cancel_setup,
            is_setup_mode=True
        )
        self.password_prompt.activate()
    
    def _on_setup_complete(self):
        """Callback when first-time password setup is complete."""
        self._state = self.STATE_AUTHENTICATED
        self._create_dashboard()
    
    def _cancel_setup(self):
        """Callback when setup is cancelled."""
        self._state = self.STATE_LOCKED
        self.password_prompt.deactivate()
    
    def deactivate(self):
        """Deactivate the dashboard (logout)."""
        self.session_manager.logout()
        self._state = self.STATE_LOCKED
        self.password_prompt.deactivate()
        self.dashboard_screen = None
        
        if self.on_logout:
            self.on_logout()
    
    def render(self, screen: pygame.Surface):
        """
        Render the current state of the dashboard.
        
        Args:
            screen: Pygame surface to render to
        """
        if self._state == self.STATE_LOCKED:
            # Show password prompt
            if self.password_prompt:
                self.password_prompt.render(screen)
        
        elif self._state == self.STATE_AUTHENTICATING:
            # Still showing password prompt
            if self.password_prompt:
                self.password_prompt.render(screen)
        
        elif self._state == self.STATE_AUTHENTICATED:
            # Check session
            if not self.session_manager.check_session():
                # Session timed out - re-authenticate
                self._state = self.STATE_AUTHENTICATING
                self.password_prompt.activate()
                if self.password_prompt:
                    self.password_prompt.render(screen)
            else:
                # Session valid - render dashboard
                if self.dashboard_screen:
                    self.dashboard_screen.render(screen)
                    self.dashboard_screen.draw(screen)
        
        self.session_manager.record_activity()
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events.
        
        Args:
            event: Pygame event to handle
            
        Returns:
            True if event was handled by this component
        """
        # Handle password prompt events when authenticating
        if self._state in (self.STATE_LOCKED, self.STATE_AUTHENTICATING):
            if self.password_prompt:
                handled = self.password_prompt.handle_event(event)
                if handled:
                    return True
        
        # Handle dashboard events when authenticated
        if self._state == self.STATE_AUTHENTICATED:
            # Check for logout (e.g., Escape key or logout button)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.deactivate()
                return True
            
            if self.dashboard_screen:
                self.dashboard_screen.handle_event(event)
                return True
        
        return False
    
    def handle_mouse_motion(self, pos: tuple):
        """
        Handle mouse movement for hover effects.
        
        Args:
            pos: Mouse position (x, y)
        """
        if self._state in (self.STATE_LOCKED, self.STATE_AUTHENTICATING):
            if self.password_prompt:
                # PasswordPrompt handles its own mouse motion via handle_event
                pass
        elif self._state == self.STATE_AUTHENTICATED:
            if self.dashboard_screen:
                self.dashboard_screen.handle_mouse_motion(pos)
    
    def handle_mouse_click(self, pos: tuple):
        """
        Handle mouse click.
        
        Args:
            pos: Mouse position (x, y)
        """
        if self._state in (self.STATE_LOCKED, self.STATE_AUTHENTICATING):
            # PasswordPrompt handles its own clicks via handle_event
            pass
        elif self._state == self.STATE_AUTHENTICATED:
            if self.dashboard_screen:
                self.dashboard_screen.handle_mouse_click(pos)
    
    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated."""
        return self._state == self.STATE_AUTHENTICATED and self.session_manager.is_authenticated()
    
    def get_state(self) -> str:
        """Get current dashboard state."""
        return self._state
    
    def set_password(self, new_password: str) -> bool:
        """
        Set a new password (for first-time setup or password change).
        
        Args:
            new_password: New password to set
            
        Returns:
            True if password set successfully
        """
        return self.session_manager.password_manager.set_password(new_password)
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """
        Change password after verifying old password.
        
        Args:
            old_password: Current password
            new_password: New password
            
        Returns:
            True if password changed successfully
        """
        # Verify old password
        if not self.session_manager.password_manager.validate_password(old_password):
            return False
        
        return self.session_manager.password_manager.set_password(new_password)


def create_authenticated_parent_dashboard(
    sessions: List[Dict],
    screen_width: int = 800,
    screen_height: int = 600,
    session_manager: Optional[SessionManager] = None,
    on_logout: Optional[Callable] = None
) -> AuthenticatedParentDashboard:
    """
    Factory function to create an AuthenticatedParentDashboard.
    
    Args:
        sessions: List of session data dictionaries
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        session_manager: Optional SessionManager instance
        on_logout: Optional callback for logout
        
    Returns:
        Configured AuthenticatedParentDashboard instance
    """
    return AuthenticatedParentDashboard(
        sessions=sessions,
        screen_width=screen_width,
        screen_height=screen_height,
        session_manager=session_manager,
        on_logout=on_logout
    )
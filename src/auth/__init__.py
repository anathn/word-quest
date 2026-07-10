"""
Authentication module for parent authentication.

Implements STORY-003-01: Parent Authentication

This module provides:
- PasswordManager: Password hashing and validation
- SessionManager: Session timeout and authentication state
- AuthConfig: Authentication configuration

Note: PasswordPrompt is in src.ui.password_prompt to avoid circular imports.
"""

from src.auth.password_manager import PasswordManager
from src.auth.session_manager import SessionManager
from src.auth.auth_config import AuthConfig

__all__ = [
    "PasswordManager",
    "SessionManager",
    "AuthConfig",
]
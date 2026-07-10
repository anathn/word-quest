"""
Session Manager

Implements STORY-003-01: Parent Authentication

Manages authentication state including:
- Session timeout tracking
- Failed attempt counting
- Account lockout logic
- Activity tracking
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple

from src.auth.password_manager import PasswordManager
from src.auth.auth_config import AuthConfig


class SessionManager:
    """
    Manages authentication session state and security.
    
    Features:
    - Session timeout after period of inactivity
    - Failed attempt tracking with lockout
    - Activity timestamp tracking
    - Thread-safe authentication state
    
    Attributes:
        config: AuthConfig instance with timeout/lockout settings
        password_manager: PasswordManager for password validation
        _authenticated: Current authentication state
        _last_activity: Timestamp of last activity
        _failed_attempts: Number of consecutive failed attempts
        _lockout_until: Timestamp when lockout expires (if locked)
    """
    
    def __init__(
        self,
        timeout_minutes: int = 10,
        max_attempts: int = 5,
        lockout_minutes: int = 15,
        password_manager: Optional[PasswordManager] = None,
        config: Optional[AuthConfig] = None
    ):
        """
        Initialize the SessionManager.
        
        Args:
            timeout_minutes: Session timeout in minutes (default: 10)
            max_attempts: Max failed attempts before lockout (default: 5)
            lockout_minutes: Lockout duration in minutes (default: 15)
            password_manager: PasswordManager instance
            config: AuthConfig instance
        """
        # Use provided config or create defaults
        if config is not None:
            self.timeout_minutes = config.session_timeout_minutes
            self.max_attempts = config.max_failed_attempts
            self.lockout_minutes = config.lockout_duration_minutes
        else:
            self.timeout_minutes = timeout_minutes
            self.max_attempts = max_attempts
            self.lockout_minutes = lockout_minutes
        
        self.password_manager = password_manager or PasswordManager()
        
        # Authentication state
        self._authenticated: bool = False
        self._last_activity: Optional[datetime] = None
        self._failed_attempts: int = 0
        self._lockout_until: Optional[datetime] = None
    
    def authenticate(self, password: str) -> Tuple[bool, str]:
        """
        Attempt authentication with provided password.
        
        Checks lockout status first, then validates password.
        Updates failed attempt count and lockout state as needed.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if not configured yet (first-time setup)
        if not self.password_manager.has_password_set():
            return (False, "Password not configured. Please set up in parent settings.")
        
        # Check if locked out
        if self._is_locked_out():
            remaining = self._get_lockout_remaining_seconds()
            minutes, seconds = divmod(remaining, 60)
            return (
                False,
                f"Too many failed attempts. Try again in {minutes:02d}:{seconds:02d}"
            )
        
        # Attempt password validation
        if self.password_manager.validate_password(password):
            # Success - reset failed attempts and set auth state
            self._authenticated = True
            self._last_activity = datetime.now()
            self._failed_attempts = 0
            return (True, "Authenticated successfully")
        else:
            # Failed - increment counter and check for lockout
            self._failed_attempts += 1
            
            if self._failed_attempts >= self.max_attempts:
                # Trigger lockout
                self._lockout_until = datetime.now() + timedelta(
                    minutes=self.lockout_minutes
                )
                return (
                    False,
                    f"Too many failed attempts. Account locked for {self.lockout_minutes} minutes"
                )
            else:
                attempts_left = self.max_attempts - self._failed_attempts
                return (
                    False,
                    f"Incorrect password. {attempts_left} attempt{'s' if attempts_left > 1 else ''} remaining"
                )
    
    def check_session(self) -> bool:
        """
        Check if current session is still valid.
        
        Updates last activity timestamp and checks for timeout.
        
        Returns:
            True if session is valid, False if timed out
        """
        if not self._authenticated:
            return False
        
        # Check for timeout
        if self._is_timed_out():
            self._authenticated = False
            self._last_activity = None
            return False
        
        # Update activity timestamp
        self._last_activity = datetime.now()
        return True
    
    def is_authenticated(self) -> bool:
        """
        Check current authentication state.
        
        Performs session check before returning state.
        
        Returns:
            True if authenticated and session valid, False otherwise
        """
        if self._authenticated:
            return self.check_session()
        return False
    
    def logout(self):
        """End current session and clear authentication state."""
        self._authenticated = False
        self._last_activity = None
        self._failed_attempts = 0
        self._lockout_until = None
    
    def record_activity(self):
        """Record user activity to reset session timeout timer."""
        if self._authenticated:
            self._last_activity = datetime.now()
    
    def _is_locked_out(self) -> bool:
        """
        Check if account is currently locked out.
        
        Returns:
            True if locked out, False otherwise
        """
        if self._lockout_until is None:
            return False
        
        if datetime.now() >= self._lockout_until:
            # Lockout expired - reset
            self._lockout_until = None
            self._failed_attempts = 0
            return False
        
        return True
    
    def _is_timed_out(self) -> bool:
        """
        Check if session has timed out.
        
        Returns:
            True if session timed out, False otherwise
        """
        if self._last_activity is None:
            return True
        
        timeout = timedelta(minutes=self.timeout_minutes)
        return datetime.now() - self._last_activity > timeout
    
    def _get_lockout_remaining_seconds(self) -> int:
        """
        Get remaining lockout time in seconds.
        
        Returns:
            Seconds remaining in lockout (0 if not locked)
        """
        if self._lockout_until is None:
            return 0
        
        remaining = self._lockout_until - datetime.now()
        return max(0, int(remaining.total_seconds()))
    
    def get_failed_attempts(self) -> int:
        """
        Get current failed attempt count.
        
        Returns:
            Number of consecutive failed attempts
        """
        return self._failed_attempts
    
    def get_attempts_remaining(self) -> int:
        """
        Get remaining attempts before lockout.
        
        Returns:
            Number of attempts before lockout (0 if locked)
        """
        if self._is_locked_out():
            return 0
        return max(0, self.max_attempts - self._failed_attempts)
    
    def get_session_info(self) -> dict:
        """
        Get current session information.
        
        Returns:
            Dictionary with session details
        """
        return {
            "authenticated": self.is_authenticated(),
            "failed_attempts": self._failed_attempts,
            "attempts_remaining": self.get_attempts_remaining(),
            "is_locked_out": self._is_locked_out(),
            "lockout_remaining_seconds": self._get_lockout_remaining_seconds(),
            "session_timeout_minutes": self.timeout_minutes,
        }
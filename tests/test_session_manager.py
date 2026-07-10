"""
Unit tests for SessionManager

Tests for STORY-003-01: Parent Authentication
"""

from datetime import datetime, timedelta
import pytest
from unittest.mock import MagicMock, patch
from src.auth.session_manager import SessionManager
from src.auth.password_manager import PasswordManager


@pytest.fixture
def mock_password_manager():
    """Create a mock PasswordManager for testing."""
    pm = MagicMock(spec=PasswordManager)
    pm.validate_password.return_value = True
    pm.has_password_set.return_value = True
    return pm


class TestSessionManager:
    """Test suite for SessionManager class."""
    
    @pytest.fixture
    def session_manager(self, mock_password_manager):
        """Create a SessionManager with mocked dependencies."""
        return SessionManager(
            timeout_minutes=10,
            max_attempts=5,
            lockout_minutes=15,
            password_manager=mock_password_manager
        )
    
    def test_init_default_values(self):
        """Test SessionManager initialization with default values."""
        sm = SessionManager()
        assert sm.timeout_minutes == 10
        assert sm.max_attempts == 5
        assert sm.lockout_minutes == 15
        assert sm._authenticated is False
        assert sm._failed_attempts == 0
    
    def test_init_custom_values(self):
        """Test SessionManager initialization with custom values."""
        sm = SessionManager(timeout_minutes=5, max_attempts=3, lockout_minutes=30)
        assert sm.timeout_minutes == 5
        assert sm.max_attempts == 3
        assert sm.lockout_minutes == 30
    
    def test_authenticate_success(self, session_manager, mock_password_manager):
        """Test successful authentication."""
        success, message = session_manager.authenticate("correctpass")
        
        assert success is True
        assert "Authenticated" in message
        assert session_manager.is_authenticated() is True
        assert session_manager._failed_attempts == 0
    
    def test_authenticate_failure_wrong_password(self, session_manager, mock_password_manager):
        """Test authentication failure with wrong password."""
        mock_password_manager.validate_password.return_value = False
        
        success, message = session_manager.authenticate("wrongpass")
        
        assert success is False
        assert "Incorrect password" in message
        assert session_manager._failed_attempts == 1
        assert session_manager.is_authenticated() is False
    
    def test_authenticate_no_password_set(self, session_manager, mock_password_manager):
        """Test authentication when no password is configured."""
        mock_password_manager.has_password_set.return_value = False
        
        success, message = session_manager.authenticate("anypass")
        
        assert success is False
        assert "not configured" in message.lower()
    
    def test_authenticate_lockout_triggered(self, session_manager, mock_password_manager):
        """Test that lockout triggers after max failed attempts."""
        mock_password_manager.validate_password.return_value = False
        
        # 4 failures (should not lock out yet)
        for i in range(4):
            success, message = session_manager.authenticate("wrong")
            assert success is False
        
        assert session_manager._failed_attempts == 4
        assert session_manager._lockout_until is None
        
        # 5th failure - should lock out
        session_manager.password_manager.has_password_set.return_value = True
        success, message = session_manager.authenticate("wrong")
        
        assert success is False
        assert "locked" in message.lower()
        assert session_manager._is_locked_out() is True
    
    def test_authenticate_during_lockout(self, session_manager, mock_password_manager):
        """Test authentication attempt during lockout."""
        mock_password_manager.validate_password.return_value = False
        
        # Trigger lockout
        for _ in range(5):
            session_manager.authenticate("wrong")
        
        assert session_manager._is_locked_out() is True
        
        # Try to authenticate during lockout
        success, message = session_manager.authenticate("anypass")
        
        assert success is False
        assert "try again" in message.lower() or "locked" in message.lower()
        assert "Try again" in message
    
    def test_authenticate_after_lockout_expires(self, session_manager, mock_password_manager):
        """Test authentication after lockout period expires."""
        mock_password_manager.validate_password.return_value = False
        
        # Trigger lockout
        for _ in range(5):
            session_manager.authenticate("wrong")
        
        assert session_manager._is_locked_out() is True
        
        # Simulate lockout expiration by setting _lockout_until to past
        session_manager._lockout_until = datetime.now() - timedelta(minutes=20)
        
        # This should reset lockout
        success, message = session_manager.authenticate("correct")
        mock_password_manager.validate_password.return_value = True
        
        # After expiration, should allow attempt
        # Note: The actual authentication result depends on password validation
        # The lockout check should pass now
        assert session_manager._is_locked_out() is False
    
    def test_check_session_valid(self, session_manager):
        """Test session check when session is valid."""
        session_manager._authenticated = True
        session_manager._last_activity = datetime.now()
        
        result = session_manager.check_session()
        
        assert result is True
        assert session_manager.is_authenticated() is True
    
    def test_check_session_timeout(self, session_manager):
        """Test session check when session timed out."""
        session_manager._authenticated = True
        session_manager._last_activity = datetime.now() - timedelta(minutes=15)
        
        result = session_manager.check_session()
        
        assert result is False
        assert session_manager.is_authenticated() is False
        assert session_manager._authenticated is False
    
    def test_check_session_not_authenticated(self, session_manager):
        """Test session check when not authenticated."""
        session_manager._authenticated = False
        
        result = session_manager.check_session()
        
        assert result is False
    
    def test_logout_clears_state(self, session_manager):
        """Test that logout clears all authentication state."""
        session_manager._authenticated = True
        session_manager._last_activity = datetime.now()
        session_manager._failed_attempts = 3
        session_manager._lockout_until = datetime.now() + timedelta(minutes=10)
        
        session_manager.logout()
        
        assert session_manager._authenticated is False
        assert session_manager._last_activity is None
        assert session_manager._failed_attempts == 0
        assert session_manager._lockout_until is None
    
    def test_record_activity_updates_timestamp(self, session_manager):
        """Test that recording activity updates last activity time."""
        session_manager._authenticated = True
        session_manager._last_activity = datetime.now() - timedelta(minutes=5)
        
        session_manager.record_activity()
        
        # Should be within last second of now
        assert (datetime.now() - session_manager._last_activity).seconds < 2
    
    def test_record_activity_not_authenticated(self, session_manager):
        """Test that recording activity only works when authenticated."""
        session_manager._authenticated = False
        session_manager._last_activity = None
        
        session_manager.record_activity()
        
        assert session_manager._last_activity is None
    
    def test_get_attempts_remaining(self, session_manager):
        """Test getting remaining attempts before lockout."""
        assert session_manager.get_attempts_remaining() == 5
        
        # Simulate 2 failed attempts
        session_manager._failed_attempts = 2
        assert session_manager.get_attempts_remaining() == 3
    
    def test_get_attempts_remaining_locked_out(self, session_manager):
        """Test remaining attempts when locked out."""
        session_manager._failed_attempts = 5
        session_manager._lockout_until = datetime.now() + timedelta(minutes=10)
        
        assert session_manager.get_attempts_remaining() == 0
    
    def test_get_session_info(self, session_manager):
        """Test getting session information."""
        session_manager._authenticated = True
        session_manager._failed_attempts = 2
        session_manager._last_activity = datetime.now()  # Set recent activity to prevent timeout
        
        info = session_manager.get_session_info()
        
        assert info["authenticated"] is True
        assert info["failed_attempts"] == 2
        assert info["attempts_remaining"] == 3
        assert info["is_locked_out"] is False
        assert "lockout_remaining_seconds" in info
        assert info["session_timeout_minutes"] == 10


class TestSessionTimeout:
    """Test session timeout functionality."""
    
    @pytest.fixture
    def short_timeout_manager(self, mock_password_manager):
        """Create SessionManager with short timeout for testing."""
        return SessionManager(
            timeout_minutes=1,  # 1 minute timeout
            max_attempts=5,
            lockout_minutes=15,
            password_manager=mock_password_manager
        )
    
    def test_session_expires_after_timeout(self, short_timeout_manager):
        """Test that session expires after configured timeout."""
        short_timeout_manager._authenticated = True
        short_timeout_manager._last_activity = datetime.now() - timedelta(minutes=2)
        
        assert short_timeout_manager.check_session() is False
    
    def test_session_valid_before_timeout(self, short_timeout_manager):
        """Test that session is still valid before timeout."""
        short_timeout_manager._authenticated = True
        short_timeout_manager._last_activity = datetime.now() - timedelta(seconds=30)
        
        assert short_timeout_manager.check_session() is True


class TestLockoutBehavior:
    """Test lockout behavior in detail."""
    
    def test_lockout_duration(self, mock_password_manager):
        """Test that lockout lasts for configured duration."""
        sm = SessionManager(
            timeout_minutes=10,
            max_attempts=3,
            lockout_minutes=2,  # 2 minute lockout
            password_manager=mock_password_manager
        )
        
        mock_password_manager.validate_password.return_value = False
        
        # Trigger lockout
        for _ in range(3):
            sm.authenticate("wrong")
        
        assert sm._is_locked_out() is True
        assert sm._get_lockout_remaining_seconds() > 0
        
        # Verify lockout duration is approximately 2 minutes
        remaining = sm._get_lockout_remaining_seconds()
        assert 100 < remaining < 130  # Allow some tolerance


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_timeout(self):
        """Test behavior with zero timeout (immediate expiry)."""
        pm = MagicMock(spec=PasswordManager)
        pm.has_password_set.return_value = True
        pm.validate_password.return_value = True
        
        sm = SessionManager(timeout_minutes=0, password_manager=pm)
        
        success, _ = sm.authenticate("pass")
        assert success is True
        
        # Session should immediately timeout
        assert sm.check_session() is False
    
    def test_max_attempts_one(self):
        """Test with max_attempts set to 1."""
        pm = MagicMock(spec=PasswordManager)
        pm.has_password_set.return_value = True
        pm.validate_password.return_value = False
        
        sm = SessionManager(max_attempts=1, password_manager=pm)
        
        # First failure should lock out
        success, message = sm.authenticate("wrong")
        assert success is False
        assert sm._is_locked_out() is True
    
    def test_consecutive_failures_reset_on_success(self, mock_password_manager):
        """Test that failed attempt counter resets on successful auth."""
        mock_password_manager.validate_password.return_value = False
        
        sm = SessionManager(max_attempts=5, password_manager=mock_password_manager)
        
        # 2 failures
        sm.authenticate("wrong")
        sm.authenticate("wrong")
        assert sm._failed_attempts == 2
        
        # Success should reset
        mock_password_manager.validate_password.return_value = True
        sm.authenticate("correct")
        assert sm._failed_attempts == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
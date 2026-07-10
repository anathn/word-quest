"""
Unit tests for PasswordManager

Tests for STORY-003-01: Parent Authentication
"""

import os
import json
import tempfile
import pytest
from src.auth.password_manager import PasswordManager


class TestPasswordManager:
    """Test suite for PasswordManager class."""
    
    @pytest.fixture
    def temp_config(self):
        """Create a temporary config file for testing."""
        temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(temp_dir, "test_auth_config.json")
        
        # Create empty config
        with open(config_path, 'w') as f:
            json.dump({"password_hash": None, "salt": None}, f)
        
        yield config_path
        
        # Cleanup
        os.remove(config_path)
        os.rmdir(temp_dir)
    
    def test_init_creates_config_if_missing(self, temp_config):
        """Test that initialization creates config if it doesn't exist."""
        # Remove the config
        os.remove(temp_config)
        
        # Initialize PasswordManager - should create config
        pm = PasswordManager(temp_config)
        
        # Verify config was created
        assert os.path.exists(temp_config)
        
        with open(temp_config, 'r') as f:
            data = json.load(f)
        
        assert "password_hash" in data
        assert "salt" in data
    
    def test_has_password_set_returns_false_when_no_password(self, temp_config):
        """Test has_password_set returns False when no password is set."""
        pm = PasswordManager(temp_config)
        assert pm.has_password_set() is False
    
    def test_has_password_set_returns_true_when_password_set(self, temp_config):
        """Test has_password_set returns True when password is configured."""
        pm = PasswordManager(temp_config)
        pm.set_password("test123")
        assert pm.has_password_set() is True
    
    def test_set_password_hashes_with_salt(self, temp_config):
        """Test that setting password generates salt and hash."""
        pm = PasswordManager(temp_config)
        
        result = pm.set_password("test123")
        assert result is True
        
        # Verify config contains hash and salt
        with open(temp_config, 'r') as f:
            data = json.load(f)
        
        assert data["password_hash"] is not None
        assert data["salt"] is not None
        assert len(data["salt"]) == 64  # 32 bytes = 64 hex chars
        assert len(data["password_hash"]) == 64  # SHA-256 = 64 hex chars
    
    def test_validate_password_correct(self, temp_config):
        """Test validation with correct password."""
        pm = PasswordManager(temp_config)
        pm.set_password("test123")
        
        assert pm.validate_password("test123") is True
    
    def test_validate_password_incorrect(self, temp_config):
        """Test validation with incorrect password."""
        pm = PasswordManager(temp_config)
        pm.set_password("test123")
        
        assert pm.validate_password("wrongpassword") is False
    
    def test_validate_password_empty(self, temp_config):
        """Test validation with empty password."""
        pm = PasswordManager(temp_config)
        pm.set_password("test123")
        
        assert pm.validate_password("") is False
    
    def test_validate_password_no_password_set(self, temp_config):
        """Test validation when no password is configured."""
        pm = PasswordManager(temp_config)
        
        assert pm.validate_password("anything") is False
    
    def test_set_password_different_salts(self, temp_config):
        """Test that each password set generates a new salt."""
        pm = PasswordManager(temp_config)
        
        pm.set_password("password1")
        with open(temp_config, 'r') as f:
            data1 = json.load(f)
        salt1 = data1["salt"]
        
        pm.set_password("password2")
        with open(temp_config, 'r') as f:
            data2 = json.load(f)
        salt2 = data2["salt"]
        
        assert salt1 != salt2
    
    def test_old_password_does_not_work_after_change(self, temp_config):
        """Test that old password is rejected after password change."""
        pm = PasswordManager(temp_config)
        pm.set_password("oldpass")
        
        # Change password
        pm.set_password("newpass")
        
        # Old password should not work
        assert pm.validate_password("oldpass") is False
        # New password should work
        assert pm.validate_password("newpass") is True
    
    def test_change_password_with_old_password_verification(self, temp_config):
        """Test password change with old password verification."""
        pm = PasswordManager(temp_config)
        pm.set_password("current")
        
        # This tests the PasswordManager - actual change_password is in SessionManager
        # Just verify we can set a new password
        pm.set_password("updated")
        assert pm.validate_password("updated") is True
        assert pm.validate_password("current") is False
    
    def test_set_password_none_raises_error(self, temp_config):
        """Test that setting None password fails gracefully."""
        pm = PasswordManager(temp_config)
        result = pm.set_password(None)
        assert result is False
    
    def test_set_password_empty_string_fails(self, temp_config):
        """Test that setting empty string password fails."""
        pm = PasswordManager(temp_config)
        result = pm.set_password("")
        assert result is False
    
    def test_unicode_password_supported(self, temp_config):
        """Test that unicode passwords are supported."""
        pm = PasswordManager(temp_config)
        result = pm.set_password("пароль123你好")
        assert result is True
        assert pm.validate_password("пароль123你好") is True
    
    def test_special_characters_in_password(self, temp_config):
        """Test passwords with special characters."""
        pm = PasswordManager(temp_config)
        password = "P@ssw0rd!#$%"
        pm.set_password(password)
        assert pm.validate_password(password) is True
    
    def test_long_password_supported(self, temp_config):
        """Test that long passwords are supported."""
        pm = PasswordManager(temp_config)
        long_password = "a" * 1000
        pm.set_password(long_password)
        assert pm.validate_password(long_password) is True
    
    def test_case_sensitive_password(self, temp_config):
        """Test that password comparison is case-sensitive."""
        pm = PasswordManager(temp_config)
        pm.set_password("Password")
        
        assert pm.validate_password("Password") is True
        assert pm.validate_password("password") is False
        assert pm.validate_password("PASSWORD") is False
    
    def test_persistence_across_instances(self, temp_config):
        """Test that password persists across PasswordManager instances."""
        # First instance sets password
        pm1 = PasswordManager(temp_config)
        pm1.set_password("testpass")
        
        # Second instance should validate the same password
        pm2 = PasswordManager(temp_config)
        assert pm2.validate_password("testpass") is True
    
    def test_corrupt_config_file_fallback(self, temp_config):
        """Test handling of corrupt config file."""
        # Write corrupt JSON
        with open(temp_config, 'w') as f:
            f.write("not valid json {{{")
        
        pm = PasswordManager(temp_config)
        # Should not crash, should treat as no password set
        assert pm.has_password_set() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
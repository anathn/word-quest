"""
Password Manager

Implements STORY-003-01: Parent Authentication

Handles password hashing, validation, and secure storage using:
- Salted SHA-256 hashing
- Secure config file storage
- Password change functionality
"""

import hashlib
import json
import os
from typing import Optional


class PasswordManager:
    """
    Manages password hashing, storage, and validation.
    
    Features:
    - Salted SHA-256 password hashing
    - Secure storage in config file
    - Password change functionality
    - First-time setup detection
    
    Security Note:
    While not production-grade cryptographic security, this prevents
    casual unauthorized access by children as per the MVP requirements.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the PasswordManager.
        
        Args:
            config_path: Optional path to auth config file
        """
        self.config_file = config_path or os.path.join(
            os.path.expanduser("~/.word_quest"),
            "auth_config.json"
        )
        self._ensure_config_exists()
    
    def _generate_salt(self) -> str:
        """
        Generate a random salt for password hashing.
        
        Returns:
            Hex-encoded random salt (32 bytes = 64 hex chars)
        """
        return os.urandom(32).hex()
    
    def _hash_password(self, password: str, salt: str) -> str:
        """
        Hash password with salt using SHA-256.
        
        Args:
            password: Plain text password to hash
            salt: Salt to use for hashing
            
        Returns:
            Hex-encoded SHA-256 hash
        """
        # Combine password and salt, then hash
        combined = (password + salt).encode('utf-8')
        return hashlib.sha256(combined).hexdigest()
    
    def _ensure_config_exists(self):
        """Create default config if it doesn't exist."""
        config_dir = os.path.dirname(self.config_file)
        os.makedirs(config_dir, exist_ok=True)
        
        if not os.path.exists(self.config_file):
            # Create empty config file
            with open(self.config_file, 'w') as f:
                json.dump({"password_hash": None, "salt": None}, f, indent=2)
    
    def _load_config(self) -> dict:
        """
        Load configuration from file.
        
        Returns:
            Dictionary containing auth config data
        """
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Return empty config on error
            return {"password_hash": None, "salt": None}
    
    def _save_config(self, data: dict) -> bool:
        """
        Save configuration to file.
        
        Args:
            data: Configuration data to save
            
        Returns:
            True if save successful, False otherwise
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except (IOError, OSError) as e:
            print(f"Failed to save auth config: {e}")
            return False
    
    def has_password_set(self) -> bool:
        """
        Check if a password has been set.
        
        Returns:
            True if password is configured, False otherwise
        """
        config = self._load_config()
        return config.get("password_hash") is not None
    
    def set_password(self, new_password: str) -> bool:
        """
        Set or update the parent password.
        
        Generates a new salt and hashes the password before storing.
        
        Args:
            new_password: Plain text password to set
            
        Returns:
            True if password set successfully, False otherwise
        """
        if not new_password:
            return False
        
        # Generate new salt and hash
        salt = self._generate_salt()
        hashed = self._hash_password(new_password, salt)
        
        # Save to config
        data = {
            "password_hash": hashed,
            "salt": salt
        }
        
        return self._save_config(data)
    
    def validate_password(self, password: str) -> bool:
        """
        Check if provided password matches stored hash.
        
        Args:
            password: Plain text password to validate
            
        Returns:
            True if password matches, False otherwise
        """
        if not password:
            return False
        
        config = self._load_config()
        
        stored_hash = config.get("password_hash")
        stored_salt = config.get("salt")
        
        if stored_hash is None or stored_salt is None:
            # No password set
            return False
        
        # Hash the provided password with stored salt
        computed_hash = self._hash_password(password, stored_salt)
        
        # Compare hashes (simple string comparison)
        return computed_hash == stored_hash
    
    def change_password(self, old_password: str, new_password: str) -> bool:
        """
        Change password after verifying old password.
        
        Args:
            old_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if password changed successfully, False otherwise
        """
        # Verify old password first
        if not self.validate_password(old_password):
            return False
        
        # Set new password
        return self.set_password(new_password)
    
    def reset_password(self, new_password: str) -> bool:
        """
        Reset password without old password verification.
        
        This should only be used for recovery scenarios (e.g., parent email reset).
        
        Args:
            new_password: New password to set
            
        Returns:
            True if password reset successfully, False otherwise
        """
        return self.set_password(new_password)
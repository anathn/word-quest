"""
Authentication Configuration

Implements STORY-003-01: Parent Authentication

Configuration settings for authentication system including:
- Session timeout duration
- Maximum failed attempts before lockout
- Lockout duration
- Config file paths
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AuthConfig:
    """
    Authentication configuration settings.
    
    Attributes:
        session_timeout_minutes: How long a session lasts before timeout
        max_failed_attempts: Number of failed attempts before lockout
        lockout_duration_minutes: How long the lockout lasts
        config_dir: Directory to store auth configuration
        config_file: Full path to config file
    """
    session_timeout_minutes: int = 10
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 15
    config_dir: str = field(default_factory=lambda: os.path.expanduser("~/.word_quest"))
    config_file: str = field(default_factory=lambda: os.path.expanduser("~/.word_quest/auth_config.json"))
    
    def __post_init__(self):
        """Ensure config directory exists."""
        os.makedirs(self.config_dir, exist_ok=True)
    
    @property
    def lockout_duration_seconds(self) -> int:
        """Return lockout duration in seconds."""
        return self.lockout_duration_minutes * 60
    
    @property
    def session_timeout_seconds(self) -> int:
        """Return session timeout in seconds."""
        return self.session_timeout_minutes * 60
    
    def get_default_config(self) -> dict:
        """Return default configuration as dictionary."""
        return {
            "session_timeout_minutes": self.session_timeout_minutes,
            "max_failed_attempts": self.max_failed_attempts,
            "lockout_duration_minutes": self.lockout_duration_minutes,
        }

    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> "AuthConfig":
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Optional override for config file path
            
        Returns:
            AuthConfig instance with loaded settings
        """
        import json
        
        path = config_path or os.path.join(
            os.path.expanduser("~/.word_quest"),
            "auth_config.json"
        )
        
        # Use default if file doesn't exist
        if not os.path.exists(path):
            return cls()
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
            
            return cls(
                session_timeout_minutes=data.get("session_timeout_minutes", 10),
                max_failed_attempts=data.get("max_failed_attempts", 5),
                lockout_duration_minutes=data.get("lockout_duration_minutes", 15),
            )
        except (json.JSONDecodeError, IOError):
            # Return default on corrupt file
            return cls()
    
    def save_to_file(self, config_path: Optional[str] = None) -> bool:
        """
        Save configuration to JSON file.
        
        Args:
            config_path: Optional override for config file path
            
        Returns:
            True if save successful, False otherwise
        """
        import json
        
        path = config_path or self.config_file
        
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, "w") as f:
                json.dump(self.get_default_config(), f, indent=2)
            
            return True
        except (IOError, OSError) as e:
            print(f"Failed to save auth config: {e}")
            return False
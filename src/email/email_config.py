"""
Email Configuration Management

Stores and validates email notification settings for parent reports.
Implements STORY-003-06: Email Notification Configuration
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import Optional
import re
import os
import json
import hashlib
import base64


class DayOfWeek(Enum):
    """Days of the week for email scheduling."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


@dataclass
class EmailConfig:
    """
    Email notification configuration.
    
    Attributes:
        enabled: Whether email notifications are enabled
        email_address: Parent's email address
        send_day: Day of week to send emails
        send_time: Time of day to send emails
        consent_date: Date when GDPR consent was given
        last_sent: Timestamp of last email sent
        next_scheduled: Timestamp of next scheduled email
        config_path: Path to configuration file
    """
    enabled: bool = False
    email_address: str = ""
    send_day: DayOfWeek = DayOfWeek.MONDAY
    send_time: time = time(8, 0)  # 8:00 AM default
    consent_date: Optional[datetime] = None
    last_sent: Optional[datetime] = None
    next_scheduled: Optional[datetime] = None
    config_path: str = field(default="data/email_config.json")
    
    # Encryption key (initialized after dataclass init)
    _key: Optional[bytes] = field(init=False, default=None)
    
    def __post_init__(self):
        """Initialize encryption key after dataclass initialization."""
        if self._key is None:
            self._key = self._load_or_generate_encryption_key()
    
    # Day name mapping for display
    DAY_NAMES = {
        DayOfWeek.MONDAY: "Monday",
        DayOfWeek.TUESDAY: "Tuesday",
        DayOfWeek.WEDNESDAY: "Wednesday",
        DayOfWeek.THURSDAY: "Thursday",
        DayOfWeek.FRIDAY: "Friday",
        DayOfWeek.SATURDAY: "Saturday",
        DayOfWeek.SUNDAY: "Sunday"
    }
    
    def _load_or_generate_encryption_key(self) -> bytes:
        """
        Load or generate encryption key for data protection.
        
        Returns:
            Bytes key for base64 encoding
        """
        key_path = os.path.join(os.path.dirname(self.config_path), ".email_enc_key")
        
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        else:
            # Generate a new 32-byte key
            key = os.urandom(32)
            
            # Secure directory permissions
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, mode=0o700, exist_ok=True)
            elif config_dir:
                os.chmod(config_dir, 0o700)
            
            # Save key with secure permissions
            with open(key_path, "wb") as f:
                f.write(key)
            os.chmod(key_path, 0o600)
            
            return key
    
    def _encrypt_data(self, data: str) -> str:
        """
        Encrypt string data using XOR with key and base64 encode.
        
        Args:
            data: Plain text string
            
        Returns:
            Base64 encoded encrypted string
        """
        data_bytes = data.encode('utf-8')
        key = self._key
        encrypted = bytes([data_bytes[i] ^ key[i % len(key)] for i in range(len(data_bytes))])
        return base64.b64encode(encrypted).decode('utf-8')
    
    def _decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt string data from base64 and XOR.
        
        Args:
            encrypted_data: Base64 encoded encrypted string
            
        Returns:
            Decrypted plain text string
        """
        encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
        key = self._key
        decrypted = bytes([encrypted_bytes[i] ^ key[i % len(key)] for i in range(len(encrypted_bytes))])
        return decrypted.decode('utf-8')
    
    def _encrypt_dict(self, data: dict, sensitive_fields: list) -> dict:
        """
        Encrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary to encrypt
            sensitive_fields: List of field names to encrypt
            
        Returns:
            Dictionary with encrypted fields
        """
        result = data.copy()
        for field_name in sensitive_fields:
            if field_name in result and result[field_name]:
                result[field_name] = self._encrypt_data(str(result[field_name]))
        return result
    
    def _decrypt_dict(self, data: dict, sensitive_fields: list) -> dict:
        """
        Decrypt specific fields in a dictionary.
        
        Args:
            data: Dictionary with encrypted fields
            sensitive_fields: List of field names to decrypt
            
        Returns:
            Dictionary with decrypted fields
        """
        result = data.copy()
        for field_name in sensitive_fields:
            if field_name in result and result[field_name]:
                try:
                    result[field_name] = self._decrypt_data(str(result[field_name]))
                except Exception:
                    # Decryption failed, clear the field
                    result[field_name] = None
        return result

    def is_valid(self) -> tuple[bool, str]:
        """
        Validate the email configuration.
        
        Returns:
            Tuple of (is_valid, message)
        """
        if not self.enabled:
            return True, "Email notifications disabled"
        
        if not self.email_address:
            return False, "Email address required when enabled"
        
        if not self._validate_email_format(self.email_address):
            return False, "Invalid email format"
        
        if not self.consent_date:
            return False, "GDPR consent required"
        
        return True, "Configuration valid"
    
    def _validate_email_format(self, email: str) -> bool:
        """
        Validate email format with comprehensive security checks.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email format is valid
            
        Security:
            - Maximum length check (254 chars standard limit)
            - Local part length check (64 chars max)
            - Control character rejection
            - Strict regex pattern
            - ReDoS protection (no catastrophic backtracking)
        """
        # Maximum total length check (RFC 5321 standard)
        if len(email) > 254:
            return False
        
        # Check for null bytes and control characters
        if any(ord(c) < 32 or c == '\x00' for c in email):
            return False
        
        # Split into local and domain parts
        if '@' not in email:
            return False
        
        parts = email.rsplit('@', 1)  # rsplit to handle @ in local part correctly
        if len(parts) != 2:
            return False
        
        local_part, domain_part = parts
        
        # Local part length check (RFC 5321 standard)
        if len(local_part) > 64 or not local_part:
            return False
        
        # Domain part length check
        if len(domain_part) > 255 or not domain_part:
            return False
        
        # Check for consecutive dots in local part
        if '..' in local_part:
            return False
        
        # Check for leading/trailing dots in local part
        if local_part.startswith('.') or local_part.endswith('.'):
            return False
        
        # Validate domain has at least one dot and valid TLD
        if '.' not in domain_part:
            return False
        
        domain_parts = domain_part.split('.')
        if any(len(part) > 63 or not part for part in domain_parts):
            return False
        
        # Check TLD length (minimum 2 characters)
        if len(domain_parts[-1]) < 2:
            return False
        
        # Strict regex with ReDoS protection
        # This pattern avoids catastrophic backtracking
        pattern = r'^[a-zA-Z0-9](\.?[a-zA-Z0-9_+\-])*@[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'
        
        return bool(re.match(pattern, email))
    
    def toggle_enabled(self):
        """Toggle the enabled state."""
        self.enabled = not self.enabled
    
    def set_email_address(self, address: str) -> tuple[bool, str]:
        """
        Set and validate email address.
        
        Args:
            address: Email address to set
            
        Returns:
            Tuple of (success, message)
        """
        if not address:
            self.email_address = ""
            return True, "Email address cleared"
        
        if not self._validate_email_format(address):
            return False, "Invalid email format"
        
        self.email_address = address
        return True, "Email address saved"
    
    def set_send_schedule(self, day: DayOfWeek, send_time: time):
        """
        Set the email schedule.
        
        Args:
            day: Day of week to send
            send_time: Time of day to send
        """
        self.send_day = day
        self.send_time = send_time
    
    def record_consent(self):
        """Record GDPR consent timestamp."""
        self.consent_date = datetime.now()
    
    def record_email_sent(self):
        """Record that an email was sent."""
        now = datetime.now()
        self.last_sent = now
        # Schedule next email (next occurrence of send_day)
        self._calculate_next_scheduled(now)
    
    def _calculate_next_scheduled(self, from_date: datetime):
        """
        Calculate the next scheduled email date.
        
        Args:
            from_date: Reference date for calculation
        """
        current_weekday = from_date.weekday()
        target_weekday = self.send_day.value
        
        # Calculate days until next scheduled day
        days_ahead = target_weekday - current_weekday
        if days_ahead < 0:
            days_ahead += 7
        
        # If today is the scheduled day and time hasn't passed, send today
        if days_ahead == 0:
            schedule_time = datetime.combine(from_date.date(), self.send_time)
            if from_date.time() < self.send_time:
                self.next_scheduled = schedule_time
            else:
                # Already passed today, schedule for next week
                from datetime import timedelta
                next_week = from_date + timedelta(days=7)
                self.next_scheduled = datetime.combine(next_week.date(), self.send_time)
        else:
            from datetime import timedelta
            next_date = from_date + timedelta(days=days_ahead)
            self.next_scheduled = datetime.combine(next_date.date(), self.send_time)
    
    def clear_consent(self):
        """Clear GDPR consent (user opted out)."""
        self.consent_date = None
        self.enabled = False
    
    def to_dict(self) -> dict:
        """
        Serialize configuration to dictionary.
        
        Returns:
            Dictionary representation of config
        """
        return {
            "enabled": self.enabled,
            "email_address": self.email_address,
            "send_day": self.send_day.value,
            "send_time": {"hour": self.send_time.hour, "minute": self.send_time.minute},
            "consent_date": self.consent_date.isoformat() if self.consent_date else None,
            "last_sent": self.last_sent.isoformat() if self.last_sent else None,
            "next_scheduled": self.next_scheduled.isoformat() if self.next_scheduled else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "EmailConfig":
        """
        Create EmailConfig from dictionary.
        
        Args:
            data: Dictionary with config data
            
        Returns:
            EmailConfig instance
        """
        config = cls()
        config.enabled = data.get("enabled", False)
        config.email_address = data.get("email_address", "")
        config.send_day = DayOfWeek(data.get("send_day", 0))
        
        time_data = data.get("send_time", {})
        if time_data:
            config.send_time = time(
                hour=time_data.get("hour", 8),
                minute=time_data.get("minute", 0)
            )
        
        consent_str = data.get("consent_date")
        if consent_str:
            config.consent_date = datetime.fromisoformat(consent_str)
        
        last_sent_str = data.get("last_sent")
        if last_sent_str:
            config.last_sent = datetime.fromisoformat(last_sent_str)
        
        next_sched_str = data.get("next_scheduled")
        if next_sched_str:
            config.next_scheduled = datetime.fromisoformat(next_sched_str)
        
        return config
    
    def save(self):
        """
        Save configuration to file with encryption.
        
        Security:
            - Sensitive fields are encrypted before storage
            - File permissions are set to 0o600
            - Directory permissions are set to 0o700
        """
        # Ensure directory exists with secure permissions
        config_dir = os.path.dirname(self.config_path)
        if config_dir:
            os.makedirs(config_dir, mode=0o700, exist_ok=True)
            os.chmod(config_dir, 0o700)
        
        # Encrypt sensitive fields
        data = self.to_dict()
        sensitive_fields = ["email_address"]
        encrypted_data = self._encrypt_dict(data, sensitive_fields)
        
        # Write with secure permissions
        with open(self.config_path, "w") as f:
            json.dump(encrypted_data, f, indent=2)
        
        # Set file permissions to owner read/write only
        os.chmod(self.config_path, 0o600)
    
    @classmethod
    def load(cls, config_path: str = "data/email_config.json") -> "EmailConfig":
        """
        Load configuration from file with decryption.
        
        Args:
            config_path: Path to config file
            
        Returns:
            EmailConfig instance (or default if file doesn't exist)
        """
        if not os.path.exists(config_path):
            return cls()
        
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            
            # Create config instance with the correct config_path so it uses the right encryption key
            # We need to bypass __post_init__ key initialization and set it properly
            config = cls.__new__(cls)  # Create without calling __init__
            config._key = None
            # Now load the key from the correct path
            config.config_path = config_path
            config._key = config._load_or_generate_encryption_key()
            
            # Decrypt sensitive fields
            sensitive_fields = ["email_address"]
            decrypted_data = config._decrypt_dict(data, sensitive_fields)
            
            # Now populate the config from the decrypted data
            config.enabled = decrypted_data.get("enabled", False)
            config.email_address = decrypted_data.get("email_address", "")
            config.send_day = DayOfWeek(decrypted_data.get("send_day", 0))
            
            time_data = decrypted_data.get("send_time", {})
            if time_data:
                config.send_time = time(
                    hour=time_data.get("hour", 8),
                    minute=time_data.get("minute", 0)
                )
            else:
                config.send_time = time(8, 0)
            
            consent_str = decrypted_data.get("consent_date")
            if consent_str:
                config.consent_date = datetime.fromisoformat(consent_str)
            else:
                config.consent_date = None
            
            last_sent_str = decrypted_data.get("last_sent")
            if last_sent_str:
                config.last_sent = datetime.fromisoformat(last_sent_str)
            else:
                config.last_sent = None
            
            next_sched_str = decrypted_data.get("next_scheduled")
            if next_sched_str:
                config.next_scheduled = datetime.fromisoformat(next_sched_str)
            else:
                config.next_scheduled = None
            
            config.config_path = config_path
            return config
        except (json.JSONDecodeError, KeyError, ValueError, Exception) as e:
            # Return default config on error (including decryption failure)
            return cls()


def create_email_config(config_path: str = "data/email_config.json") -> EmailConfig:
    """
    Factory function to create and load email config.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        EmailConfig instance
    """
    return EmailConfig.load(config_path)
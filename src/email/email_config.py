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
        Validate email format using regex.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email format is valid
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
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
        Save configuration to file.
        
        Note: In production, this should use encryption.
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Save with basic encoding (MVP - not encrypted)
        with open(self.config_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, config_path: str = "data/email_config.json") -> "EmailConfig":
        """
        Load configuration from file.
        
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
            config = cls.from_dict(data)
            config.config_path = config_path
            return config
        except (json.JSONDecodeError, KeyError, ValueError):
            # Return default config on error
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
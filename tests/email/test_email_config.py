"""
Tests for EmailConfig

Implements STORY-003-06: Email Notification Configuration
"""

import pytest
import os
import json
from datetime import datetime, time, timedelta

from src.email.email_config import EmailConfig, DayOfWeek


class TestEmailConfigValidation:
    """Test email format validation."""
    
    def test_valid_email_formats(self):
        """Valid email formats should pass validation."""
        valid_emails = [
            "test@example.com",
            "parent@gmail.com",
            "user.name@domain.org",
            "user+tag@example.co.uk"
        ]
        
        config = EmailConfig()
        
        for email in valid_emails:
            is_valid, _ = config.is_valid()  # Will fail because not enabled
            # Test format validation directly
            assert config._validate_email_format(email), f"Should accept: {email}"
    
    def test_invalid_email_formats(self):
        """Invalid email formats should fail validation."""
        invalid_emails = [
            "invalid",
            "@example.com",
            "test@",
            "test example.com",
            "test@.com"
        ]
        
        config = EmailConfig()
        
        for email in invalid_emails:
            assert not config._validate_email_format(email), f"Should reject: {email}"
    
    def test_disabled_config_is_valid(self):
        """Disabled config should be valid even without email address."""
        config = EmailConfig(enabled=False)
        is_valid, message = config.is_valid()
        
        assert is_valid
        assert "disabled" in message.lower()
    
    def test_enabled_config_requires_email(self):
        """Enabled config must have email address."""
        config = EmailConfig(enabled=True, email_address="")
        is_valid, message = config.is_valid()
        
        assert not is_valid
        assert "email" in message.lower()
    
    def test_enabled_config_requires_consent(self):
        """Enabled config with email must have consent."""
        config = EmailConfig(
            enabled=True,
            email_address="test@example.com",
            consent_date=None
        )
        is_valid, message = config.is_valid()
        
        assert not is_valid
        assert "consent" in message.lower()
    
    def test_valid_full_config(self):
        """Fully configured email should be valid."""
        config = EmailConfig(
            enabled=True,
            email_address="parent@example.com",
            consent_date=datetime.now()
        )
        is_valid, message = config.is_valid()
        
        assert is_valid
        assert message == "Configuration valid"


class TestEmailConfigModification:
    """Test email configuration modifications."""
    
    def test_toggle_enabled(self):
        """Test toggling enabled state."""
        config = EmailConfig(enabled=False)
        config.toggle_enabled()
        assert config.enabled is True
        
        config.toggle_enabled()
        assert config.enabled is False
    
    def test_set_email_address_valid(self):
        """Test setting valid email address."""
        config = EmailConfig()
        success, message = config.set_email_address("parent@test.com")
        
        assert success
        assert config.email_address == "parent@test.com"
    
    def test_set_email_address_invalid(self):
        """Test setting invalid email address."""
        config = EmailConfig()
        success, message = config.set_email_address("invalid")
        
        assert not success
        assert config.email_address == ""
    
    def test_set_email_address_empty(self):
        """Test clearing email address."""
        config = EmailConfig(email_address="test@example.com")
        success, message = config.set_email_address("")
        
        assert success
        assert config.email_address == ""
    
    def test_set_send_schedule(self):
        """Test setting email schedule."""
        config = EmailConfig()
        new_time = time(18, 30)  # 6:30 PM
        config.set_send_schedule(DayOfWeek.FRIDAY, new_time)
        
        assert config.send_day == DayOfWeek.FRIDAY
        assert config.send_time == new_time
    
    def test_record_consent(self):
        """Test recording consent timestamp."""
        config = EmailConfig()
        config.record_consent()
        
        assert config.consent_date is not None
        assert isinstance(config.consent_date, datetime)
    
    def test_clear_consent(self):
        """Test clearing consent also disables emails."""
        config = EmailConfig(
            enabled=True,
            consent_date=datetime.now()
        )
        config.clear_consent()
        
        assert config.consent_date is None
        assert config.enabled is False


class TestEmailConfigPersistence:
    """Test email configuration save/load."""
    
    def test_save_and_load(self, tmp_path):
        """Test saving and loading configuration."""
        config_path = tmp_path / "email_config.json"
        
        config = EmailConfig(
            enabled=True,
            email_address="test@example.com",
            send_day=DayOfWeek.WEDNESDAY,
            send_time=time(9, 0),
            consent_date=datetime(2026, 7, 1, 10, 0),
            config_path=str(config_path)
        )
        config.save()
        
        # Load from file
        loaded = EmailConfig.load(str(config_path))
        
        assert loaded.enabled is True
        assert loaded.email_address == "test@example.com"
        assert loaded.send_day == DayOfWeek.WEDNESDAY
        assert loaded.send_time.hour == 9
        assert loaded.send_time.minute == 0
    
    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file returns default config."""
        config = EmailConfig.load("/nonexistent/path/config.json")
        
        assert config.enabled is False
        assert config.email_address == ""
    
    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON returns default config."""
        config_path = tmp_path / "email_config.json"
        config_path.write_text("invalid json content")
        
        config = EmailConfig.load(str(config_path))
        
        assert config.enabled is False
    
    def test_to_dict_roundtrip(self):
        """Test dictionary serialization roundtrip."""
        original = EmailConfig(
            enabled=True,
            email_address="user@example.com",
            send_day=DayOfWeek.SUNDAY,
            send_time=time(7, 30),
            consent_date=datetime(2026, 6, 15, 14, 30),
            last_sent=datetime(2026, 7, 5, 8, 0),
            next_scheduled=datetime(2026, 7, 12, 7, 30)
        )
        
        data = original.to_dict()
        loaded = EmailConfig.from_dict(data)
        
        assert loaded.enabled == original.enabled
        assert loaded.email_address == original.email_address
        assert loaded.send_day == original.send_day
        assert loaded.send_time == original.send_time
        assert loaded.consent_date == original.consent_date
        assert loaded.last_sent == original.last_sent
        assert loaded.next_scheduled == original.next_scheduled


class TestEmailScheduleCalculation:
    """Test next scheduled email calculation."""
    
    def test_next_scheduled_future_day(self):
        """Test scheduling for future day of week."""
        config = EmailConfig(
            enabled=True,
            send_day=DayOfWeek.FRIDAY,
            send_time=time(8, 0)
        )
        
        # Wednesday reference
        reference = datetime(2026, 7, 8, 10, 0)  # Wednesday
        config._calculate_next_scheduled(reference)
        
        # Should be Friday of same week
        assert config.next_scheduled.day == 10  # July 10 is Friday
        assert config.next_scheduled.hour == 8
    
    def test_next_scheduled_past_today(self):
        """Test scheduling when today's time has passed."""
        config = EmailConfig(
            enabled=True,
            send_day=DayOfWeek.WEDNESDAY,
            send_time=time(8, 0)
        )
        
        # Wednesday but time passed
        reference = datetime(2026, 7, 8, 10, 0)  # Wednesday 10 AM
        config._calculate_next_scheduled(reference)
        
        # Should be next week
        assert config.next_scheduled.day == 15  # Next Wednesday
        assert config.next_scheduled.hour == 8
    
    def test_next_scheduled_future_today(self):
        """Test scheduling when today's time hasn't passed."""
        config = EmailConfig(
            enabled=True,
            send_day=DayOfWeek.WEDNESDAY,
            send_time=time(18, 0)
        )
        
        # Wednesday but time not passed
        reference = datetime(2026, 7, 8, 10, 0)  # Wednesday 10 AM
        config._calculate_next_scheduled(reference)
        
        # Should be today
        assert config.next_scheduled.day == 8  # Same Wednesday
        assert config.next_scheduled.hour == 18
    
    def test_next_scheduled_sunday_to_monday(self):
        """Test scheduling spanning week boundary."""
        config = EmailConfig(
            enabled=True,
            send_day=DayOfWeek.MONDAY,
            send_time=time(8, 0)
        )
        
        # Sunday reference
        reference = datetime(2026, 7, 5, 10, 0)  # Sunday
        config._calculate_next_scheduled(reference)
        
        # Should be next Monday
        assert config.next_scheduled.weekday() == 0  # Monday
        assert config.next_scheduled.day == 6  # July 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
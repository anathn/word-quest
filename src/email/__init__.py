"""
Email notification subsystem for Word Quest.

Provides email configuration, sending, and scheduling for weekly progress reports.
Implements STORY-003-06: Email Notification Configuration
"""

from src.email.email_config import EmailConfig, DayOfWeek
from src.email.email_service import EmailService
from src.email.email_scheduler import EmailScheduler

__all__ = [
    "EmailConfig",
    "DayOfWeek",
    "EmailService",
    "EmailScheduler",
]
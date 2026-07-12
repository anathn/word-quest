"""
Email Scheduler

Background scheduler for automated weekly progress email reports.
Implements STORY-003-06: Email Notification Configuration
"""

import threading
import time as time_module
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.email.email_config import EmailConfig
    from src.email.email_service import EmailService
    from src.analytics.weekly_summary import WeeklySummaryGenerator


class EmailScheduler:
    """
    Background scheduler for automated email reports.
    
    Checks hourly if it's time to send a scheduled email.
    Runs in a daemon thread so it doesn't block application exit.
    
    Example:
        scheduler = EmailScheduler(config, service, summary_generator)
        scheduler.start()
        # ... later ...
        scheduler.stop()
    """
    
    def __init__(self, email_config: "EmailConfig", email_service: "EmailService",
                 summary_generator: "WeeklySummaryGenerator",
                 current_student_provider=None):
        """
        Initialize email scheduler.
        
        Args:
            email_config: EmailConfig instance with settings
            email_service: EmailService instance for sending
            summary_generator: WeeklySummaryGenerator for creating content
            current_student_provider: Optional callable that returns current student ID
        """
        self.email_config = email_config
        self.email_service = email_service
        self.summary_generator = summary_generator
        self.current_student_provider = current_student_provider
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_check: Optional[datetime] = None
    
    def start(self):
        """Start the background scheduler thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        print("Email scheduler started")
    
    def stop(self):
        """Stop the background scheduler thread."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        print("Email scheduler stopped")
    
    def _run_scheduler(self):
        """Background thread loop that checks and sends emails."""
        while self._running:
            self._last_check = datetime.now()
            
            if self._should_send_email():
                self._send_scheduled_email()
            
            # Sleep for 1 hour (3600 seconds)
            time_module.sleep(3600)
    
    def _should_send_email(self) -> bool:
        """
        Check if it's time to send the scheduled email.
        
        Returns:
            True if email should be sent
        """
        if not self.email_config.enabled:
            return False
        
        if not self.email_config.consent_date:
            return False
        
        if not self.email_config.email_address:
            return False
        
        now = datetime.now()
        today_weekday = now.weekday()
        
        # Check if today is the selected day
        if today_weekday != self.email_config.send_day.value:
            return False
        
        # Check if we've already sent this week
        if self.email_config.last_sent:
            last_sent_week = self.email_config.last_sent.isocalendar()[1]
            current_week = now.isocalendar()[1]
            current_year = now.isocalendar()[0]
            
            if last_sent_week == current_week and self.email_config.last_sent.year == current_year:
                return False
        
        # Check if it's past the scheduled time
        current_time = datetime.combine(now.date(), self.email_config.send_time)
        return now >= current_time
    
    def _send_scheduled_email(self):
        """Send the scheduled weekly progress email."""
        # Get current student ID
        student_id = self._get_current_student_id()
        
        if not student_id:
            print("No student selected, skipping email")
            return
        
        try:
            # Generate weekly summary
            from datetime import date
            summary = self.summary_generator.generate_summary(student_id, date.today())
            
            # Create report data
            summary_data = {
                "words_mastered": summary.words_mastered,
                "accuracy_rate": summary.accuracy_rate,
                "total_attempts": self._get_total_attempts(student_id),
                "total_time_minutes": summary.total_time_minutes,
                "words_mastered_list": summary.words_mastered_list
            }
            
            # Get student name
            student_name = self._get_student_name(student_id)
            
            # Send email
            success, message = self.email_service.send_weekly_report(
                self.email_config.email_address,
                student_name,
                summary_data
            )
            
            if success:
                self.email_config.record_email_sent()
                self.email_config.save()
                print(f"Weekly report sent successfully to {self.email_config.email_address}")
            else:
                print(f"Failed to send weekly report: {message}")
        
        except Exception as e:
            print(f"Error sending scheduled email: {e}")
    
    def _get_current_student_id(self) -> str:
        """
        Get the current student ID.
        
        Returns:
            Student ID string or empty string if not found
        """
        if self.current_student_provider:
            try:
                return self.current_student_provider() or ""
            except Exception:
                return ""
        return ""
    
    def _get_student_name(self, student_id: str) -> str:
        """
        Get student name by ID.
        
        Args:
            student_id: Student identifier
            
        Returns:
            Student name or "Student" as fallback
        """
        try:
            from src.profiles.profile_manager import ProfileManager
            profile_manager = ProfileManager()
            profile = profile_manager.get_profile(student_id)
            if profile:
                return profile.name
        except Exception:
            pass
        return "Student"
    
    def _get_total_attempts(self, student_id: str) -> int:
        """
        Get total attempts for student this week.
        
        Args:
            student_id: Student identifier
            
        Returns:
            Total attempts count
        """
        try:
            session_count = self.summary_generator.get_weekly_session_count(student_id)
            # Estimate: average 10 attempts per session
            return session_count * 10
        except Exception:
            return 0
    
    def check_and_send_now(self) -> tuple[bool, str]:
        """
        Manually trigger email send (for testing).
        
        Returns:
            Tuple of (success, message)
        """
        if not self.email_config.enabled:
            return False, "Email notifications not enabled"
        
        student_id = self._get_current_student_id()
        if not student_id:
            return False, "No student selected"
        
        try:
            from datetime import date
            summary = self.summary_generator.generate_summary(student_id, date.today())
            
            summary_data = {
                "words_mastered": summary.words_mastered,
                "accuracy_rate": summary.accuracy_rate,
                "total_attempts": self._get_total_attempts(student_id),
                "total_time_minutes": summary.total_time_minutes,
                "words_mastered_list": summary.words_mastered_list
            }
            
            student_name = self._get_student_name(student_id)
            success, message = self.email_service.send_weekly_report(
                self.email_config.email_address,
                student_name,
                summary_data
            )
            
            if success:
                self.email_config.record_email_sent()
                self.email_config.save()
                return True, "Test email sent successfully"
            else:
                return False, message
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_next_scheduled_time(self) -> Optional[datetime]:
        """
        Get the next scheduled email time.
        
        Returns:
            Next scheduled datetime or None if not enabled
        """
        if not self.email_config.enabled:
            return None
        
        return self.email_config.next_scheduled
    
    def is_ready_to_configure(self) -> bool:
        """
        Check if config is ready for initial setup.
        
        Returns:
            True if email service credentials are available
        """
        try:
            # Try to load credentials
            from src.email.email_service import EmailService
            EmailService.from_config()
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False


def create_email_scheduler(
    email_config: "EmailConfig",
    email_service: "EmailService",
    summary_generator: "WeeklySummaryGenerator",
    current_student_provider=None
) -> EmailScheduler:
    """
    Factory function to create an EmailScheduler.
    
    Args:
        email_config: EmailConfig instance
        email_service: EmailService instance
        summary_generator: WeeklySummaryGenerator instance
        current_student_provider: Optional callable for getting current student ID
        
    Returns:
        Configured EmailScheduler
    """
    return EmailScheduler(
        email_config=email_config,
        email_service=email_service,
        summary_generator=summary_generator,
        current_student_provider=current_student_provider
    )
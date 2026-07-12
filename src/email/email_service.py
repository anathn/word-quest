"""
Email Service

Handles email sending via SMTP for weekly progress reports.
Implements STORY-003-06: Email Notification Configuration
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
import os


class EmailService:
    """
    Email sending service for progress reports.
    
    Supports SMTP with TLS encryption.
    
    Example:
        service = EmailService.from_config("data/email_credentials.json")
        success = service.send_test_email("parent@example.com")
    """
    
    def __init__(self, smtp_host: str, smtp_port: int,
                 username: str, password: str, sender_email: str):
        """
        Initialize email service.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP username
            password: SMTP password
            sender_email: Email address to send from
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender_email = sender_email
    
    @classmethod
    def from_config(cls, config_path: str = "data/email_credentials.json") -> "EmailService":
        """
        Create EmailService from configuration file.
        
        Args:
            config_path: Path to credentials file
            
        Returns:
            Configured EmailService instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            KeyError: If required fields missing
        """
        import json
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Email config not found: {config_path}")
        
        with open(config_path, "r") as f:
            config = json.load(f)
        
        return cls(
            smtp_host=config["smtp_host"],
            smtp_port=config["smtp_port"],
            username=config["username"],
            password=config["password"],
            sender_email=config["sender_email"]
        )
    
    def send_email(self, to_email: str, subject: str,
                   html_content: str, text_content: Optional[str] = None) -> bool:
        """
        Send email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML version of email body
            text_content: Plain text version (optional)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.sender_email
            msg["To"] = to_email
            
            # Attach text version
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)
            
            # Attach HTML version
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)
            
            # Add unsubscribe header
            msg["List-Unsubscribe"] = f"<mailto:unsubscribe@wordquest.example.com?subject=Unsubscribe>"
            
            # Create secure connection and send
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(self.username, self.password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            return True
        
        except smtplib.SMTPAuthenticationError:
            print("Email authentication failed")
            return False
        except smtplib.SMTPConnectError:
            print("Failed to connect to SMTP server")
            return False
        except smtplib.SMTPException as e:
            print(f"SMTP error: {e}")
            return False
        except Exception as e:
            print(f"Email send failed: {e}")
            return False
    
    def send_test_email(self, to_email: str) -> Tuple[bool, str]:
        """
        Send test email to verify configuration.
        
        Args:
            to_email: Email address to send test to
            
        Returns:
            Tuple of (success, message)
        """
        subject = "Word Quest - Test Email"
        
        html_content = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .header { background-color: #4CAF50; color: white; padding: 20px; }
                .content { padding: 20px; }
                .footer { background-color: #f1f1f1; padding: 10px; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Word Quest Test Email</h2>
            </div>
            <div class="content">
                <p>This is a <strong>test email</strong> from Word Quest!</p>
                <p>If you received this, your email configuration is working correctly.</p>
                <p>You will receive weekly progress summaries on this email address.</p>
            </div>
            <div class="footer">
                <p>Word Quest - Spelling Adventure</p>
                <p>
                    <a href="mailto:unsubscribe@wordquest.example.com?subject=Unsubscribe">Unsubscribe</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = """
        Word Quest - Test Email
        
        This is a test email from Word Quest!
        
        If you received this, your email configuration is working correctly.
        You will receive weekly progress summaries on this email address.
        
        ---
        Word Quest - Spelling Adventure
        To unsubscribe, email unsubscribe@wordquest.example.com with subject "Unsubscribe"
        """
        
        success = self.send_email(to_email, subject, html_content, text_content)
        
        if success:
            return True, "Test email sent successfully to " + to_email
        else:
            return False, "Failed to send test email. Check SMTP configuration."
    
    def send_weekly_report(self, to_email: str, student_name: str,
                           summary_data: dict) -> Tuple[bool, str]:
        """
        Send weekly progress report email.
        
        Args:
            to_email: Parent's email address
            student_name: Name of the student
            summary_data: Dictionary of weekly summary statistics
            
        Returns:
            Tuple of (success, message)
        """
        subject = f"Word Quest Weekly Progress - {student_name}"
        
        # Generate email content from template
        html_content = self._generate_report_html(student_name, summary_data)
        text_content = self._generate_report_text(student_name, summary_data)
        
        success = self.send_email(to_email, subject, html_content, text_content)
        
        if success:
            return True, "Weekly report sent successfully"
        else:
            return False, "Failed to send weekly report"
    
    def _generate_report_html(self, student_name: str, summary: dict) -> str:
        """
        Generate HTML report email.
        
        Args:
            student_name: Name of the student
            summary: Weekly summary data
            
        Returns:
            HTML email content
        """
        words_mastered = summary.get("words_mastered", 0)
        accuracy = summary.get("accuracy_rate", 0)
        attempts = summary.get("total_attempts", 0)
        time_practiced = summary.get("total_time_minutes", 0)
        
        words_list = summary.get("words_mastered_list", [])
        words_list_html = "".join(f"<li>{word}</li>" for word in words_list)
        
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .metric {{ background-color: #f5f5f5; padding: 10px; margin: 5px 0; border-radius: 4px; }}
                .footer {{ background-color: #f1f1f1; padding: 10px; font-size: 12px; color: #666; margin-top: 20px; }}
                ul {{ color: #4CAF50; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Weekly Progress Report</h2>
                <p>Student: {student_name}</p>
            </div>
            <div class="content">
                <p>Here's {student_name}'s progress this week:</p>
                
                <div class="metric">
                    <strong>Words Mastered:</strong> {words_mastered}
                </div>
                <div class="metric">
                    <strong>Accuracy Rate:</strong> {accuracy:.0%}
                </div>
                <div class="metric">
                    <strong>Total Attempts:</strong> {attempts}
                </div>
                <div class="metric">
                    <strong>Time Practiced:</strong> {int(time_practiced)} minutes
                </div>
                
                {f'<h3>Words Mastered This Week</h3><ul>{words_list_html}</ul>' if words_list else ''}
                
                <p>Keep up the great work!</p>
            </div>
            <div class="footer">
                <p>Word Quest - Spelling Adventure</p>
                <p>
                    <a href="mailto:unsubscribe@wordquest.example.com?subject=Unsubscribe">Unsubscribe</a>
                </p>
            </div>
        </body>
        </html>
        """
    
    def _generate_report_text(self, student_name: str, summary: dict) -> str:
        """
        Generate plain text report email.
        
        Args:
            student_name: Name of the student
            summary: Weekly summary data
            
        Returns:
            Plain text email content
        """
        words_mastered = summary.get("words_mastered", 0)
        accuracy = summary.get("accuracy_rate", 0)
        attempts = summary.get("total_attempts", 0)
        time_practiced = summary.get("total_time_minutes", 0)
        words_list = summary.get("words_mastered_list", [])
        
        words_list_text = "\n".join(f"  - {word}" for word in words_list)
        
        return f"""
Word Quest Weekly Progress Report
Student: {student_name}

This Week's Progress:
- Words Mastered: {words_mastered}
- Accuracy Rate: {accuracy:.0%}
- Total Attempts: {attempts}
- Time Practiced: {int(time_practiced)} minutes

{words_list_text if words_list else 'No words mastered this week.'}

Keep up the great work!

---
Word Quest - Spelling Adventure
To unsubscribe, email unsubscribe@wordquest.example.com with subject "Unsubscribe"
"""


def create_test_email_service() -> EmailService:
    """
    Create a test email service with mock credentials.
    
    Returns:
        EmailService configured for testing
    """
    # These are placeholder values - use real credentials in production
    return EmailService(
        smtp_host="smtp.example.com",
        smtp_port=587,
        username="noreply@wordquest.example.com",
        password="test_password",
        sender_email="noreply@wordquest.example.com"
    )
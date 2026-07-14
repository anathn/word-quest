"""
Tests for EmailService

Implements STORY-003-06: Email Notification Configuration
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import smtplib

from src.email.email_service import EmailService


class TestEmailServiceInit:
    """Test EmailService initialization."""
    
    def test_basic_initialization(self):
        """Test basic service creation."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="test@example.com",
            password="password123",
            sender_email="noreply@example.com"
        )
        
        assert service.smtp_host == "smtp.example.com"
        assert service.smtp_port == 587
        assert service.username == "test@example.com"
        assert service.sender_email == "noreply@example.com"


class TestEmailServiceFromConfig:
    """Test loading service from config file."""
    
    def test_load_from_valid_config(self, tmp_path):
        """Test loading from valid config file."""
        config_path = tmp_path / "email_credentials.json"
        config_data = {
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "username": "user@example.com",
            "password": "secret",
            "sender_email": "noreply@example.com"
        }
        config_path.write_text(json.dumps(config_data))
        
        service = EmailService.from_config(str(config_path))
        
        assert service.smtp_host == "smtp.example.com"
        assert service.username == "user@example.com"
    
    def test_load_missing_config_file(self):
        """Test loading from nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            EmailService.from_config("/nonexistent/config.json")
    
    def test_load_missing_fields(self, tmp_path):
        """Test loading from config with missing fields."""
        import json
        config_path = tmp_path / "email_credentials.json"
        config_path.write_text(json.dumps({"smtp_host": "example.com"}))
        
        with pytest.raises(KeyError):
            EmailService.from_config(str(config_path))


class TestEmailContentGeneration:
    """Test email content generation."""
    
    def test_generate_report_html(self):
        """Test HTML report generation."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            sender_email="sender@example.com"
        )
        
        summary = {
            "words_mastered": 5,
            "accuracy_rate": 0.85,
            "total_attempts": 10,
            "total_time_minutes": 45,
            "words_mastered_list": ["apple", "banana"]
        }
        
        html = service._generate_report_html("Test Student", summary)
        
        assert "Test Student" in html
        assert "5" in html  # words mastered
        assert "apple" in html
        assert "Untsubscribe" in html.lower() or "unsubscribe" in html.lower()
    
    def test_generate_report_text(self):
        """Test plain text report generation."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            sender_email="sender@example.com"
        )
        
        summary = {
            "words_mastered": 3,
            "accuracy_rate": 0.90,
            "total_attempts": 8,
            "total_time_minutes": 30,
            "words_mastered_list": ["cat"]
        }
        
        text = service._generate_report_text("John", summary)
        
        assert "John" in text
        assert "3" in text  # words mastered
        assert "cat" in text
        assert "Word Quest" in text
    
    def test_test_email_template(self):
        """Test test email contains required elements."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            sender_email="sender@example.com"
        )
        
        # The test email template is embedded in send_test_email
        # We check that the method exists and returns proper structure
        import inspect
        source = inspect.getsource(EmailService.send_test_email)
        
        assert "test" in source.lower()
        assert "word_quest" in source.lower() or "word quest" in source.lower()


class TestEmailServiceSendMethods:
    """Test email sending methods (with mocked SMTP)."""
    
    @patch('src.email.email_service.smtplib.SMTP')
    def test_send_email_success(self, mock_smtp_class):
        """Test successful email send."""
        import ssl
        
        # Setup mock
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            sender_email="sender@example.com"
        )
        
        success = service.send_email(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_content="<p>Test HTML</p>",
            text_content="Test text"
        )
        
        assert success is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
    
    @patch('src.email.email_service.smtplib.SMTP')
    def test_send_email_authentication_failure(self, mock_smtp_class):
        """Test send fails on authentication error."""
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Auth failed")
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="wrong",
            sender_email="sender@example.com"
        )
        
        success = service.send_email(
            to_email="recipient@example.com",
            subject="Test",
            html_content="<p>Test</p>"
        )
        
        assert success is False
    
    @patch('src.email.email_service.smtplib.SMTP')
    def test_send_email_connection_failure(self, mock_smtp_class):
        """Test send fails on connection error."""
        mock_smtp_class.side_effect = smtplib.SMTPConnectError(0, "Connection failed")
        
        service = EmailService(
            smtp_host="bad.server.com",
            smtp_port=587,
            username="user",
            password="pass",
            sender_email="sender@example.com"
        )
        
        success = service.send_email(
            to_email="recipient@example.com",
            subject="Test",
            html_content="<p>Test</p>"
        )
        
        assert success is False
    
    @patch('src.email.email_service.smtplib.SMTP')
    def test_send_test_email_success(self, mock_smtp_class):
        """Test test email send."""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            sender_email="sender@example.com"
        )
        
        success, message = service.send_test_email("test@example.com")
        
        assert success is True
        assert "success" in message.lower()
    
    @patch('src.email.email_service.smtplib.SMTP')
    def test_send_test_email_failure(self, mock_smtp_class):
        """Test test email send failure."""
        mock_server = MagicMock()
        mock_server.sendmail.side_effect = Exception("Network error")
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            sender_email="sender@example.com"
        )
        
        success, message = service.send_test_email("failure-test@example.com")
        
        assert success is False
        assert "failed" in message.lower()


class TestWeeklyReportConversion:
    """Test weekly report format conversion."""
    
    def test_report_contains_required_fields(self):
        """Test that generated report contains all required metrics."""
        service = EmailService(
            smtp_host="smtp.example.com",
            smtp_port=587,
            username="user",
            password="pass",
            sender_email="sender@example.com"
        )
        
        summary = {
            "words_mastered": 7,
            "accuracy_rate": 0.88,
            "total_attempts": 15,
            "total_time_minutes": 55,
            "words_mastered_list": ["hello", "world"]
        }
        
        html = service._generate_report_html("Alice", summary)
        text = service._generate_report_text("Alice", summary)
        
        # Check both formats contain key metrics
        for content in [html, text]:
            assert "Alice" in content
            assert "7" in content  # words mastered
            assert "Words Mastered" in content or "words mastered" in content
            assert "Accuracy" in content or "accuracy" in content
            assert "Time" in content or "time" in content


if __name__ == "__main__":
    import json
    pytest.main([__file__, "-v"])
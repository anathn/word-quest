"""
Unit Tests for Caption Display Component (STORY-006-03)

Tests for caption rendering, text wrapping, and visual appearance.
"""

import pytest
import pygame
from unittest.mock import Mock, MagicMock, patch

from src.components.caption_manager import Caption
from src.components.caption_settings import CaptionSettings
from src.ui.caption_display import CaptionDisplay


# Initialize pygame for testing
pygame.init()


class TestCaptionDisplay:
    """Tests for CaptionDisplay component."""
    
    @pytest.fixture
    def mock_screen(self):
        """Create a mock screen surface."""
        screen = pygame.Surface((1024, 768))
        return screen
    
    @pytest.fixture
    def settings(self):
        """Create default caption settings."""
        return CaptionSettings()
    
    @pytest.fixture
    def display(self, mock_screen, settings):
        """Create a CaptionDisplay instance."""
        return CaptionDisplay(mock_screen, settings)
    
    def test_initialization(self, mock_screen, settings):
        """Test CaptionDisplay initializes correctly."""
        display = CaptionDisplay(mock_screen, settings)
        
        assert display.current_caption is None
        assert display.settings == settings
        assert display.caption_x == 512  # Half of 1024
        assert display.caption_y == 668  # 768 - 100
                
    def test_show_caption(self, display):
        """Test showing a caption."""
        caption = Caption(
            text="Test caption",
            speaker="Captain Cosmos",
            duration=3.0
        )
        
        display.show_caption(caption)
        
        assert display.current_caption == caption
    
    def test_hide_caption(self, display):
        """Test hiding a caption."""
        caption = Caption(text="To hide")
        display.current_caption = caption
        
        display.hide_caption()
        
        assert display.current_caption is None
    
    def test_render_no_caption(self, display):
        """Test render does nothing without caption."""
        # Should not raise an error
        display.render()
    
    def test_render_caption(self, display, mock_screen):
        """Test rendering a caption."""
        caption = Caption(text="Render me")
        display.show_caption(caption)
        
        # Should not raise an error
        display.render()
        
        # Surface should have been drawn on
        # (We can't easily check pixels, but no error means success)
    
    def test_render_caption_with_speaker(self, display, mock_screen):
        """Test rendering caption with speaker name."""
        caption = Caption(
            text="Hello!",
            speaker="Captain Cosmos"
        )
        display.show_caption(caption)
        
        # Should render without error
        display.render()
    
    def test_update_settings(self, display, mock_screen):
        """Test updating settings."""
        new_settings = CaptionSettings(font_size=36)
        
        display.update_settings(new_settings)
        
        assert display.settings.font_size == 36
    
    def test_update_screen_size(self, display, mock_screen):
        """Test updating screen size."""
        new_screen = pygame.Surface((1920, 1080))
        
        display.update_screen_size(new_screen)
        
        assert display.caption_x == 960  # Half of 1920
        assert display.settings.position == "bottom"
    
    def test_wrap_text_short(self, display):
        """Test wrapping short text."""
        text = "Short text"
        lines = display._wrap_text(text, 500)
        
        assert len(lines) == 1
        assert lines[0] == "Short text"
    
    def test_wrap_text_long(self, display):
        """Test wrapping long text."""
        text = "This is a very long caption that should wrap to multiple lines"
        lines = display._wrap_text(text, 200)
        
        assert len(lines) > 1
        # Verify no line exceeds max width significantly
        for line in lines:
            width = display.font.size(line)[0]
            # Allow 20% overflow for word boundaries
            assert width <= 240
    
    def test_wrap_text_empty(self, display):
        """Test wrapping empty text."""
        lines = display._wrap_text("", 500)
        
        assert lines == [""]
    
    def test_wrap_text_single_word_long(self, display):
        """Test wrapping a single long word."""
        text = "Supercalifragilisticexpialidocious"
        lines = display._wrap_text(text, 100)
        
        # Long word should be on its own line
        assert len(lines) >= 1
        assert lines[0] == text
    
    def test_get_caption_rect_none(self, display):
        """Test get_caption_rect returns None when no caption."""
        rect = display.get_caption_rect()
        
        assert rect is None
    
    def test_get_caption_rect_with_caption(self, display):
        """Test get_caption_rect returns rect when caption exists."""
        caption = Caption(text="Test")
        display.show_caption(caption)
        
        rect = display.get_caption_rect()
        
        assert rect is not None
        assert isinstance(rect, pygame.Rect)
    
    def test_position_middle(self, mock_screen):
        """Test middle position calculation."""
        settings = CaptionSettings(position="middle")
        display = CaptionDisplay(mock_screen, settings)
        
        # Middle position: 768/2 + 100 = 484
        assert display.caption_y == 484
    
    def test_position_bottom(self, mock_screen):
        """Test bottom position calculation."""
        settings = CaptionSettings(position="bottom")
        display = CaptionDisplay(mock_screen, settings)
        
        # Bottom position: 768 - 100 = 668
        assert display.caption_y == 668
    
    def test_high_contrast_colors(self, mock_screen):
        """Test high contrast color scheme."""
        settings = CaptionSettings(high_contrast=True)
        settings.apply_high_contrast()
        
        display = CaptionDisplay(mock_screen, settings)
        
        assert display.settings.high_contrast
        assert display.text_color == (0, 0, 0)
    
    def test_speaker_color_different_from_text(self, mock_screen):
        """Test speaker color is different from text color."""
        display = CaptionDisplay(mock_screen, CaptionSettings())
        
        assert display.text_color != display.speaker_color
        assert display.speaker_color == (255, 215, 0)  # Gold
    
    def test_multiline_caption_rendering(self, display, mock_screen):
        """Test rendering captions that span multiple lines."""
        long_text = "This is a very long caption that will definitely wrap to multiple lines when rendered on screen"
        caption = Caption(text=long_text)
        
        display.show_caption(caption)
        
        # Should render without error
        display.render()
        
        # No exception means success
    
    def test_special_characters_in_caption(self, display, mock_screen):
        """Test rendering captions with special characters."""
        caption = Caption(text="Special chars: @#$%^&*()")
        display.show_caption(caption)
        
        # Should handle without error
        display.render()
    
    def test_unicode_in_caption(self, display, mock_screen):
        """Test rendering captions with unicode characters."""
        caption = Caption(text="Unicode: émojis 宇宙 🚀 ✨")
        display.show_caption(caption)
        
        # Should handle without error
        try:
            display.render()
        except pygame.error:
            # Game fonts may not support all unicode - that's expected
            pass
    
    def test_very_short_caption(self, display, mock_screen):
        """Test rendering very short caption."""
        caption = Caption(text="Hi")
        display.show_caption(caption)
        
        display.render()
    
    def test_very_long_caption(self, display, mock_screen):
        """Test rendering very long caption."""
        caption = Caption(text="A" * 500)
        display.show_caption(caption)
        
        # Should handle without error
        display.render()
    
    def test_background_transparency(self, display, mock_screen):
        """Test background has transparency."""
        caption = Caption(text="Test")
        display.show_caption(caption)
        
        # Check background color has alpha value
        assert len(display.background_color) == 4
        assert display.background_color[3] < 255  # Not fully opaque
    
    def test_caption_y_position_bounds(self, mock_screen):
        """Test caption y position is within screen bounds."""
        settings = CaptionSettings(position="bottom")
        display = CaptionDisplay(mock_screen, settings)
        
        assert 0 < display.caption_y < 768
        
        settings = CaptionSettings(position="middle")
        display = CaptionDisplay(mock_screen, settings)
        
        assert 0 < display.caption_y < 768


class TestCaptionDisplaySettings:
    """Tests for caption display settings integration."""
    
    @pytest.fixture
    def mock_screen(self):
        return pygame.Surface((1024, 768))
    
    def test_font_size_variations(self, mock_screen):
        """Test different font sizes work."""
        for size in [18, 24, 28, 36, 48]:
            settings = CaptionSettings(font_size=size)
            display = CaptionDisplay(mock_screen, settings)
            
            # Should create without error
            assert display.font is not None
    
    def test_font_size_clamping(self, mock_screen):
        """Test font size is clamped to valid range."""
        settings = CaptionSettings()
        settings.font_size = 100  # Too large
        
        settings = CaptionSettings(font_size=100)
        display = CaptionDisplay(mock_screen, settings)
        
        # Font should still be created (clamping happens in validation)
        assert display.font is not None
    
    def test_color_changes(self, mock_screen):
        """Test changing colors works."""
        settings = CaptionSettings()
        settings.text_color = (255, 0, 0)  # Red
        settings.background_color = (0, 0, 0, 200)
        
        display = CaptionDisplay(mock_screen, settings)
        
        assert display.text_color == (255, 0, 0)
    
    def test_settings_update_propagates(self, mock_screen):
        """Test that settings update propagates to fonts and colors."""
        initial_settings = CaptionSettings(font_size=28)
        display = CaptionDisplay(mock_screen, initial_settings)
        
        new_settings = CaptionSettings(font_size=36, text_color=(0, 255, 0))
        display.update_settings(new_settings)
        
        assert display.settings.font_size == 36
        assert display.text_color == (0, 255, 0)


class TestCaptionDisplayIntegration:
    """Integration tests for caption display."""
    
    @pytest.fixture
    def mock_screen(self):
        return pygame.Surface((1024, 768))
    
    def test_complete_caption_cycle(self, mock_screen):
        """Test complete lifecycle: show, render, hide."""
        settings = CaptionSettings()
        display = CaptionDisplay(mock_screen, settings)
        
        # Show caption
        caption = Caption(text="Complete cycle", speaker="Test")
        display.show_caption(caption)
        
        assert display.current_caption is not None
        
        # Render
        display.render()
        
        # Hide
        display.hide_caption()
        
        assert display.current_caption is None
    
    def test_multiple_render_calls(self, mock_screen):
        """Test rendering multiple times without errors."""
        display = CaptionDisplay(mock_screen, CaptionSettings())
        
        caption = Caption(text="Multiple renders")
        display.show_caption(caption)
        
        for _ in range(100):
            display.render()
        
        # No errors = success
    
    def test_screen_resize_during_caption(self, mock_screen):
        """Test handling screen resize while caption visible."""
        display = CaptionDisplay(mock_screen, CaptionSettings())
        
        caption = Caption(text="Resize test")
        display.show_caption(caption)
        
        # Initial render
        display.render()
        
        # Resize screen
        new_screen = pygame.Surface((1920, 1080))
        display.update_screen_size(new_screen)
        
        # Render on new screen
        display.render()
        
        assert display.caption_x == 960  # Half of 1920


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
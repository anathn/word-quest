"""
Unit tests for Typography component.

Tests cover:
- Text style configuration
- Contrast ratio calculation
- WCAG compliance checking
- Text measurement
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ui.typography import Typography, TextStyle, get_typography, reset_typography


class TestTextStyle(unittest.TestCase):
    """Tests for the TextStyle dataclass."""
    
    def test_default_values(self):
        """Test default style values."""
        style = TextStyle()
        self.assertEqual(style.font_name, "Arial")
        self.assertEqual(style.font_size, 24)
        self.assertEqual(style.color, (255, 255, 255))
        self.assertFalse(style.bold)
        self.assertIsNone(style.highlight_color)
    
    def test_custom_values(self):
        """Test custom style values."""
        style = TextStyle(
            font_name="Helvetica",
            font_size=48,
            color=(255, 0, 0),
            bold=True,
            italic=True,
            highlight_color=(255, 255, 0)
        )
        self.assertEqual(style.font_name, "Helvetica")
        self.assertEqual(style.font_size, 48)
        self.assertEqual(style.color, (255, 0, 0))
        self.assertTrue(style.bold)
        self.assertTrue(style.italic)
        self.assertEqual(style.highlight_color, (255, 255, 0))


class TestTypography(unittest.TestCase):
    """Tests for the Typography class."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_typography()
        self.typography = Typography()
    
    def test_init(self):
        """Test typography initialization."""
        self.assertIsNotNone(self.typography)
        self.assertTrue(self.typography._initialized)
    
    def test_predefined_styles(self):
        """Test predefined style properties."""
        # Check that predefined styles exist and have expected properties
        self.assertEqual(self.typography.style_word_display.font_size, 72)
        self.assertEqual(self.typography.style_word_display.color, (255, 255, 255))
        
        self.assertEqual(self.typography.style_starter_letters.font_size, 84)
        self.assertEqual(self.typography.style_starter_letters.highlight_color, (255, 215, 0))
        
        self.assertEqual(self.typography.style_definition.font_size, 28)
        self.assertEqual(self.typography.style_definition.color, (204, 204, 204))
    
    def test_color_constants(self):
        """Test color constant definitions."""
        self.assertEqual(self.typography.SPACE_BLUE, (26, 26, 62))
        self.assertEqual(self.typography.WHITE, (255, 255, 255))
        self.assertEqual(self.typography.YELLOW_HIGHLIGHT, (255, 215, 0))
        self.assertEqual(self.typography.LIGHT_GRAY, (204, 204, 204))
    
    def test_contrast_ratio_white_on_black(self):
        """Test contrast ratio calculation for high contrast colors."""
        # White on black should have maximum contrast (~21:1)
        ratio = self.typography.check_contrast_ratio(
            (255, 255, 255),  # White
            (0, 0, 0)         # Black
        )
        self.assertGreater(ratio, 20.0)
        self.assertLess(ratio, 21.5)
    
    def test_contrast_ratio_same_color(self):
        """Test contrast ratio for same colors."""
        ratio = self.typography.check_contrast_ratio(
            (128, 128, 128),
            (128, 128, 128)
        )
        self.assertEqual(ratio, 1.0)
    
    def test_contrast_ratio_white_on_space_blue(self):
        """Test contrast ratio for game's primary color scheme."""
        # White text on space blue background
        ratio = self.typography.check_contrast_ratio(
            (255, 255, 255),      # White
            (26, 26, 62)          # Space blue
        )
        self.assertGreater(ratio, 4.5)  # Should meet WCAG AA
    
    def test_meets_wcag_aa_high_contrast(self):
        """Test WCAG AA compliance for high contrast colors."""
        self.assertTrue(self.typography.meets_wcag_aa(
            (255, 255, 255),  # White
            (0, 0, 0)         # Black
        ))
    
    def test_meets_wcag_aa_low_contrast(self):
        """Test WCAG AA compliance for low contrast colors."""
        # Light gray on white - should fail
        self.assertFalse(self.typography.meets_wcag_aa(
            (200, 200, 200),  # Light gray
            (255, 255, 255)   # White
        ))
    
    def test_meets_wcag_aa_game_colors(self):
        """Test WCAG AA compliance for game's color scheme."""
        # White on space blue should pass
        self.assertTrue(self.typography.meets_wcag_aa(
            (255, 255, 255),
            (26, 26, 62)
        ))
        
        # Light gray on space blue should pass
        self.assertTrue(self.typography.meets_wcag_aa(
            (204, 204, 204),
            (26, 26, 62)
        ))
    
    def test_measure_text_fallback(self):
        """Test text measurement when pygame not available."""
        style = TextStyle(font_size=24)
        width, height = self.typography.measure_text("Hello", style)
        
        # Should return estimated values even without pygame
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)
    
    def test_wrap_text(self):
        """Test text wrapping functionality."""
        style = TextStyle(font_size=24)
        long_text = "This is a long sentence that should be wrapped to multiple lines."
        
        # Wrap to narrow width
        lines = self.typography.wrap_text(long_text, style, max_width=100)
        self.assertGreater(len(lines), 1)  # Should wrap to multiple lines
        
        # Wrap to wide width
        lines = self.typography.wrap_text(long_text, style, max_width=1000)
        self.assertEqual(len(lines), 1)  # Should fit on one line
    
    def test_wrap_text_empty(self):
        """Test wrapping empty text."""
        style = TextStyle(font_size=24)
        lines = self.typography.wrap_text("", style, max_width=100)
        self.assertEqual(lines, [])
    
    def test_font_cache(self):
        """Test font caching behavior."""
        style1 = TextStyle(font_name="Arial", font_size=24, bold=False)
        style2 = TextStyle(font_name="Arial", font_size=24, bold=False)
        
        # Same style should use cache (same object reference in cache)
        font1 = self.typography.get_font(style1)
        font2 = self.typography.get_font(style2)
        
        # When pygame is available, both should be retrievable
        # When pygame is not available, both will be None (graceful fallback)
        if self.typography._pygame_loaded:
            self.assertIsNotNone(font1)
            self.assertIsNotNone(font2)
        else:
            # Graceful fallback when pygame not available
            self.assertIsNone(font1)
            self.assertIsNone(font2)


class TestTypographySingleton(unittest.TestCase):
    """Tests for the Typography singleton pattern."""
    
    def test_get_typography_returns_singleton(self):
        """Test that get_typography returns the same instance."""
        reset_typography()
        
        typography1 = get_typography()
        typography2 = get_typography()
        
        self.assertIs(typography1, typography2)
    
    def test_reset_typography(self):
        """Test resetting the singleton."""
        reset_typography()
        typography1 = get_typography()
        reset_typography()
        typography2 = get_typography()
        
        self.assertIsNot(typography1, typography2)


class TestAccessibilityCompliance(unittest.TestCase):
    """Tests for accessibility compliance features."""
    
    def setUp(self):
        """Set up test fixtures."""
        reset_typography()
        self.typography = Typography()
    
    def test_all_predefined_styles_meet_wcag_aa(self):
        """Test that all predefined styles meet WCAG AA on space blue background."""
        background = self.typography.SPACE_BLUE
        
        # Test each predefined style
        styles_to_test = [
            ('word_display', self.typography.style_word_display),
            ('starter_letters', self.typography.style_starter_letters),
            ('definition', self.typography.style_definition),
            ('context_sentence', self.typography.style_context_sentence),
            ('input_letters', self.typography.style_input_letters),
            ('button_text', self.typography.style_button_text),
            ('success', self.typography.style_success),
            ('error', self.typography.style_error),
        ]
        
        for name, style in styles_to_test:
            with self.subTest(style_name=name):
                is_compliant = self.typography.meets_wcag_aa(style.color, background)
                self.assertTrue(
                    is_compliant,
                    f"Style '{name}' with color {style.color} does not meet WCAG AA on space blue background"
                )
    
    def test_success_error_colors_distinct(self):
        """Test that success and error colors are visually distinct."""
        success = self.typography.SUCCESS_GREEN
        error = (255, 100, 100)  # Lighter red for better contrast
        
        # They should be different
        self.assertNotEqual(success, error)
        
        # Both should have good contrast on space blue
        self.assertTrue(self.typography.meets_wcag_aa(success, self.typography.SPACE_BLUE))
        self.assertTrue(self.typography.meets_wcag_aa(error, self.typography.SPACE_BLUE))


if __name__ == '__main__':
    unittest.main()

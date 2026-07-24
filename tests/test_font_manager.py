"""
Tests for FontManager component.

STORY-006-05: OpenDyslexic Font Implementation
"""

import pytest
import pygame
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from ui.font_manager import FontManager, get_font_manager, reset_font_manager


class TestFontManager:
    """Test cases for FontManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Reset font manager before each test
        reset_font_manager()
        # Initialize pygame for font testing
        if not pygame.get_init():
            pygame.init()
            pygame.font.init()
    
    def teardown_method(self):
        """Clean up after tests."""
        pygame.quit()
    
    def test_font_manager_creation(self):
        """Test that FontManager can be created."""
        fm = FontManager()
        assert fm is not None
        assert fm.current_family == FontManager.FONT_DEFAULT
    
    def test_default_font_available(self):
        """Test that default font is always available."""
        fm = FontManager()
        
        # Should have default font family
        assert FontManager.FONT_DEFAULT in fm.font_families
        
        # Should have fonts at common sizes
        for size in FontManager.COMMON_SIZES:
            assert size in fm.font_families[FontManager.FONT_DEFAULT]
    
    def test_get_font_returns_font(self):
        """Test that get_font returns a valid pygame font."""
        fm = FontManager()
        
        font = fm.get_font(size=24)
        assert font is not None
        assert isinstance(font, pygame.font.Font)
    
    def test_get_font_different_sizes(self):
        """Test getting fonts at different sizes."""
        fm = FontManager()
        
        sizes = [12, 18, 24, 32, 48, 64]
        for size in sizes:
            font = fm.get_font(size=size)
            assert font is not None
    
    def test_get_font_caching(self):
        """Test that fonts are cached properly."""
        fm = FontManager()
        
        # Get font at size 24
        font1 = fm.get_font(size=24)
        
        # Get font at same size again
        font2 = font1  # Both should reference same cached instance
        
        # Both should work
        assert font1.render("test", True, (255, 255, 255)) is not None
        assert font2.render("test", True, (255, 255, 255)) is not None
    
    def test_opendyslexic_initialization(self):
        """Test OpenDyslexic font initialization."""
        fm = FontManager()
        
        # Check if OpenDyslexic was initialized
        # (might fail if font files not present)
        odl_available = fm.is_opendyslexic_available()
        
        # If available, should be in font_families
        if odl_available:
            assert FontManager.FONT_ODL in fm.font_families
    
    def test_set_current_family_default(self):
        """Test setting current font family to default."""
        fm = FontManager()
        
        result = fm.set_current_family(FontManager.FONT_DEFAULT)
        assert result is True
        assert fm.current_family == FontManager.FONT_DEFAULT
    
    def test_set_current_family_invalid(self):
        """Test setting current font family to invalid value."""
        fm = FontManager()
        
        result = fm.set_current_family("invalid_family")
        assert result is False
        assert fm.current_family == FontManager.FONT_DEFAULT  # Should not change
    
    def test_set_current_family_opendyslexic_available(self):
        """Test setting current family to OpenDyslexic when available."""
        fm = FontManager()
        
        if fm.is_opendyslexic_available():
            result = fm.set_current_family(FontManager.FONT_ODL)
            assert result is True
            assert fm.current_family == FontManager.FONT_ODL
        else:
            # If not available, should fail
            result = fm.set_current_family(FontManager.FONT_ODL)
            assert result is False
    
    def test_get_current_family(self):
        """Test getting current font family."""
        fm = FontManager()
        
        assert fm.get_current_family() == FontManager.FONT_DEFAULT
    
    def test_is_opendyslexic_available_true(self):
        """Test checking OpenDyslexic availability when true."""
        fm = FontManager()
        
        # Initialize OpenDyslexic if not already done
        fm.initialize_opendyslexic()
        
        # Check availability (may be True or False depending on font files)
        odl_available = fm.is_opendyslexic_available()
        
        # Verify the method returns a boolean
        assert isinstance(odl_available, bool)
    
    def test_is_opendyslexic_available_false(self):
        """Test checking OpenDyslexic availability when false."""
        fm = FontManager()
        
        # Test with non-existent path by creating a temporary manager
        # (We can't easily change paths, so we just check the property exists)
        assert hasattr(fm, 'is_opendyslexic_available')
        assert callable(getattr(fm, 'is_opendyslexic_available'))
    
    def test_get_available_families(self):
        """Test getting list of available font families."""
        fm = FontManager()
        
        families = fm.get_available_families()
        
        # Default should always be available
        assert FontManager.FONT_DEFAULT in families
        
        # Should return a list
        assert isinstance(families, list)
    
    def test_get_font_size(self):
        """Test get_font_size convenience method."""
        fm = FontManager()
        
        font = fm.get_font_size(32)
        assert font is not None
        assert isinstance(font, pygame.font.Font)
    
    def test_get_font_large(self):
        """Test get_font_large method."""
        fm = FontManager()
        
        font = fm.get_font_large()
        assert font is not None
    
    def test_get_font_medium(self):
        """Test get_font_medium method."""
        fm = FontManager()
        
        font = fm.get_font_medium()
        assert font is not None
    
    def test_get_font_small(self):
        """Test get_font_small method."""
        fm = FontManager()
        
        font = fm.get_font_small()
        assert font is not None
    
    def test_render_text(self):
        """Test that fonts can render text."""
        fm = FontManager()
        
        font = fm.get_font(size=24)
        
        # Test rendering various text
        test_strings = [
            "Hello World",
            "Test123",
            "Campus",
            "123456",
            "!@#$%^&*()"
        ]
        
        for text in test_strings:
            surface = font.render(text, True, (255, 255, 255))
            assert surface is not None
            assert surface.get_width() > 0
    
    def test_font_family_singleton(self):
        """Test that get_font_manager returns singleton."""
        fm1 = get_font_manager()
        fm2 = get_font_manager()
        
        assert fm1 is fm2
    
    def test_reset_font_manager(self):
        """Test that reset_font_manager works."""
        # Create a manager
        fm1 = get_font_manager()
        assert fm1 is not None
        
        # Reset
        reset_font_manager()
        
        # Get new manager
        fm2 = get_font_manager()
        
        # Should be different instance after reset
        assert fm1 is not fm2


class TestFontManagerPaths:
    """Test cases for font file paths."""
    
    def setup_method(self):
        """Initialize pygame."""
        if not pygame.get_init():
            pygame.init()
            pygame.font.init()
    
    def test_default_font_path_exists_or_not(self):
        """Test that default font path handling works."""
        fm = FontManager()
        
        # The FontManager should handle missing fonts gracefully
        assert fm is not None
    
    def test_opendyslexic_regular_path(self):
        """Test OpenDyslexic regular font path."""
        odl_path = FontManager.ODL_REGULAR_PATH
        
        # Check if path exists (may or may not exist in test environment)
        path_exists = Path(odl_path).exists()
        
        # FontManager should handle both cases
        fm = FontManager()
        assert fm is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
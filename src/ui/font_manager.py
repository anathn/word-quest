"""
Font management for Word Quest.

Provides centralized font loading, caching, and switching with support for
OpenDyslexic font as an accessibility feature for students with dyslexia.

STORY-006-05: OpenDyslexic Font Implementation
"""

import pygame
from typing import Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FontManager:
    """
    Manages game fonts with support for multiple font families.
    
    Supports:
    - Default game font (system/pygame default)
    - OpenDyslexic font for accessibility (dyslexia-friendly)
    - Font caching at multiple sizes for performance
    - Graceful fallback if custom fonts unavailable
    
    Attributes:
        FONT_DEFAULT: Constant for default font family
        FONT_ODL: Constant for OpenDyslexic font family
    """
    
    # Font family names
    FONT_DEFAULT = "default"
    FONT_ODL = "opendyslexic"  # OpenDyslexic
    
    # Font file paths (relative to project root)
    DEFAULT_FONT_PATH = "assets/fonts/Roboto-Regular.ttf"
    ODL_REGULAR_PATH = "assets/fonts/OpenDyslexic-Regular.ttf"
    ODL_BOLD_PATH = "assets/fonts/OpenDyslexic-Bold.ttf"
    
    # Common font sizes to cache
    COMMON_SIZES = [18, 24, 32, 48, 64]
    
    def __init__(self):
        """Initialize font manager with default font."""
        self.font_families: Dict[str, Dict[int, pygame.font.Font]] = {}
        self.current_family = self.FONT_DEFAULT
        self.opendyslexic_available = False
        
        # Ensure default font is always available
        self._ensure_default_font()
        
        # Try to initialize OpenDyslexic font
        self.initialize_opendyslexic()
        
        logger.info(f"FontManager initialized. OpenDyslexic available: {self.opendyslexic_available}")
    
    def _ensure_default_font(self) -> None:
        """
        Ensure default font is always available.
        
        Tries to load custom default font, falls back to pygame default.
        """
        self.font_families[self.FONT_DEFAULT] = {}
        
        try:
            # Try loading custom default font
            if Path(self.DEFAULT_FONT_PATH).exists():
                for size in self.COMMON_SIZES:
                    self.font_families[self.FONT_DEFAULT][size] = pygame.font.Font(
                        self.DEFAULT_FONT_PATH, size
                    )
                logger.debug(f"Loaded custom default font from {self.DEFAULT_FONT_PATH}")
            else:
                # Use pygame default as fallback
                for size in self.COMMON_SIZES:
                    self.font_families[self.FONT_DEFAULT][size] = pygame.font.Font(None, size)
                logger.debug("Using pygame default font (no custom font found)")
        except Exception as e:
            logger.warning(f"Could not load custom default font: {e}. Using pygame default.")
            # Ultimate fallback
            for size in self.COMMON_SIZES:
                self.font_families[self.FONT_DEFAULT][size] = pygame.font.Font(None, size)
    
    def initialize_opendyslexic(self) -> bool:
        """
        Initialize OpenDyslexic font family.
        
        Loads both regular and bold variations at common sizes.
        
        Returns:
            True if OpenDyslexic font loaded successfully, False otherwise.
        """
        try:
            if self.FONT_ODL not in self.font_families:
                self.font_families[self.FONT_ODL] = {}
            
            # Check if font files exist
            if not Path(self.ODL_REGULAR_PATH).exists():
                logger.warning(f"OpenDyslexic regular font not found at {self.ODL_REGULAR_PATH}")
                self.opendyslexic_available = False
                return False
            
            # Load regular fonts at common sizes
            for size in self.COMMON_SIZES:
                try:
                    self.font_families[self.FONT_ODL][size] = pygame.font.Font(
                        self.ODL_REGULAR_PATH, size
                    )
                except Exception as e:
                    logger.warning(f"Could not load OpenDyslexic at size {size}: {e}")
                    # Fallback to default font size
                    self.font_families[self.FONT_ODL][size] = pygame.font.Font(None, size)
            
            self.opendyslexic_available = True
            logger.info("OpenDyslexic font initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenDyslexic font: {e}")
            self.opendyslexic_available = False
            return False
    
    def get_font(self, family: str = None, size: int = 24, 
                bold: bool = False, italic: bool = False) -> pygame.font.Font:
        """
        Get font for specified family and size.
        
        Args:
            family: Font family name (default uses current_family)
            size: Font size in pixels
            bold: Whether to use bold variant (for OpenDyslexic)
            italic: Italic not currently supported (ignored)
            
        Returns:
            pygame.font.Font object
            
        Note:
            pygame doesn't support synthetic bold/italic, so for OpenDyslexic
            we have a separate bold font file. For other fonts, bold parameter
            is ignored and regular font is returned.
        """
        family = family or self.current_family
        
        # Validate family
        if family not in self.font_families:
            logger.warning(f"Font family '{family}' not found, falling back to default")
            family = self.FONT_DEFAULT
        
        # Load font at requested size if not cached
        if size not in self.font_families[family]:
            self._load_font_to_cache(family, size, bold)
        
        return self.font_families[family].get(size, self._get_fallback_font(size))
    
    def _load_font_to_cache(self, family: str, size: int, bold: bool = False) -> None:
        """
        Load font at specified size and cache it.
        
        Args:
            family: Font family name
            size: Font size in pixels
            bold: Whether to use bold variant
        """
        try:
            if family == self.FONT_ODL:
                # Use bold file if requested and available
                if bold and Path(self.ODL_BOLD_PATH).exists():
                    path = self.ODL_BOLD_PATH
                else:
                    path = self.ODL_REGULAR_PATH
            else:
                path = self.DEFAULT_FONT_PATH
            
            # Try to load custom font
            if Path(path).exists():
                font = pygame.font.Font(path, size)
            else:
                # Fall back to pygame default
                font = pygame.font.Font(None, size)
            
            self.font_families[family][size] = font
            
        except Exception as e:
            logger.warning(f"Could not load font {family} at size {size}: {e}")
            # Ultimate fallback
            self.font_families[family][size] = pygame.font.Font(None, size)
    
    def _get_fallback_font(self, size: int) -> pygame.font.Font:
        """
        Get fallback font (pygame default).
        
        Args:
            size: Font size in pixels
            
        Returns:
            pygame.font.Font object using pygame's built-in font
        """
        return pygame.font.Font(None, size)
    
    def set_current_family(self, family: str) -> bool:
        """
        Set current font family.
        
        Args:
            family: Font family name to use
            
        Returns:
            True if family exists and was set, False otherwise
        """
        if family in self.font_families and len(self.font_families[family]) > 0:
            self.current_family = family
            logger.info(f"Font family changed to: {family}")
            return True
        
        logger.warning(f"Cannot set font family '{family}': not available")
        return False
    
    def get_current_family(self) -> str:
        """
        Get current font family.
        
        Returns:
            Current font family name
        """
        return self.current_family
    
    def is_opendyslexic_available(self) -> bool:
        """
        Check if OpenDyslexic font is loaded and available.
        
        Returns:
            True if OpenDyslexic is available, False otherwise
        """
        return self.opendyslexic_available
    
    def get_available_families(self) -> list:
        """
        Get list of available font families.
        
        Returns:
            List of font family names that are available
        """
        return [
            family for family, fonts in self.font_families.items()
            if len(fonts) > 0
        ]
    
    def get_font_size(self, size: int = 24) -> pygame.font.Font:
        """
        Convenience method to get font at specified size using current family.
        
        Args:
            size: Font size in pixels
            
        Returns:
            pygame.font.Font object
        """
        return self.get_font(family=self.current_family, size=size)
    
    def get_font_large(self) -> pygame.font.Font:
        """
        Get large font using current family.
        
        Returns:
            pygame.font.Font object at 48px
        """
        return self.get_font_size(48)
    
    def get_font_medium(self) -> pygame.font.Font:
        """
        Get medium font using current family.
        
        Returns:
            pygame.font.Font object at 32px
        """
        return self.get_font_size(32)
    
    def get_font_small(self) -> pygame.font.Font:
        """
        Get small font using current family.
        
        Returns:
            pygame.font.Font object at 18px
        """
        return self.get_font_size(18)
    
    def reload_fonts(self) -> None:
        """
        Reload all fonts from disk.
        
        Useful if font files have been replaced while game is running.
        """
        logger.info("Reloading all fonts...")
        
        # Clear cached fonts
        for family in list(self.font_families.keys()):
            self.font_families[family] = {}
        
        # Reinitialize
        self._ensure_default_font()
        self.initialize_opendyslexic()
        
        logger.info("Font reload complete")


# Global font instance
_font_instance: Optional[FontManager] = None


def get_font_manager() -> FontManager:
    """
    Get or create the global font manager instance.
    
    Returns:
        Global FontManager instance
    """
    global _font_instance
    if _font_instance is None:
        _font_instance = FontManager()
    return _font_instance


def reset_font_manager() -> None:
    """Reset the global font manager instance."""
    global _font_instance
    _font_instance = None
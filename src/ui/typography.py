"""
Typography Module

Provides text rendering utilities with font support for the game.
Handles font loading, text measurement, and styled text rendering.
"""

from typing import Optional, Tuple, List
from dataclasses import dataclass
import os
import threading


@dataclass
class TextStyle:
    """Represents text styling configuration."""
    font_name: str = "Arial"
    font_size: int = 24
    color: Tuple[int, int, int] = (255, 255, 255)  # White
    bold: bool = False
    italic: bool = False
    underline: bool = False
    shadow: bool = False
    shadow_color: Tuple[int, int, int] = (0, 0, 0)
    shadow_offset: Tuple[int, int] = (2, 2)
    background_color: Optional[Tuple[int, int, int]] = None
    highlight_color: Optional[Tuple[int, int, int]] = None


class Typography:
    """
    Manages text rendering and font operations.
    
    Features:
    - Font loading and caching
    - Text measurement and wrapping
    - Styled text rendering
    - WCAG 2.1 AA contrast compliance checking
    """
    
    # Predefined color constants
    SPACE_BLUE = (26, 26, 62)       # #1a1a3e
    WHITE = (255, 255, 255)
    YELLOW_HIGHLIGHT = (255, 215, 0)  # #FFD700
    LIGHT_GRAY = (204, 204, 204)      # #CCCCCC
    SUCCESS_GREEN = (0, 200, 83)
    ERROR_RED = (255, 100, 100)       # Lighter red for WCAG compliance
    ORANGE_ACCENT = (255, 153, 0)
    
    # Font sizes
    FONT_TINY = 18
    FONT_SMALL = 24
    FONT_MEDIUM = 36
    FONT_LARGE = 48
    FONT_XLARGE = 60
    FONT_HUGE = 72
    FONT_MASSIVE = 84
    
    def __init__(self, fonts_dir: Optional[str] = None):
        """
        Initialize the typography system.
        
        Args:
            fonts_dir: Directory containing custom font files.
                      Defaults to WORDQUEST_DATA_DIR/fonts or 'assets/fonts'.
        """
        base_dir = os.environ.get('WORDQUEST_DATA_DIR', 'src/data')
        self.fonts_dir = fonts_dir or os.path.join(base_dir, "fonts")
        self.font_cache: dict = {}
        self._pygame_loaded = False
        self._initialized = False
        
        # Try to initialize pygame
        self._init_pygame()
    
    def _init_pygame(self):
        """Initialize pygame if available."""
        try:
            import pygame
            if not pygame.get_init():
                pygame.init()
            self._pygame_loaded = True
            self._initialized = True
        except ImportError:
            print("Warning: pygame not available. Typography in text-only mode.")
            self._pygame_loaded = False
            self._initialized = True
    
    def get_font(self, style: TextStyle) -> any:
        """
        Get a pygame Font object for the given style.
        
        Args:
            style: The TextStyle configuration
            
        Returns:
            A pygame Font object or None if pygame not available
        """
        if not self._pygame_loaded:
            return None
        
        import pygame
        
        cache_key = (style.font_name, style.font_size, style.bold, style.italic)
        
        if cache_key not in self.font_cache:
            try:
                # Try to load from custom fonts directory first
                font_path = os.path.join(self.fonts_dir, f"{style.font_name}.ttf")
                if os.path.exists(font_path):
                    font = pygame.font.Font(font_path, style.font_size)
                else:
                    # Fall back to system fonts
                    font = pygame.font.SysFont(style.font_name, style.font_size, style.bold, style.italic)
                
                self.font_cache[cache_key] = font
            except Exception as e:
                print(f"Error loading font: {e}")
                # Fallback to default font
                self.font_cache[cache_key] = pygame.font.Font(None, style.font_size)
        
        return self.font_cache[cache_key]
    
    def render_text(self, text: str, style: TextStyle, antialias: bool = True) -> any:
        """
        Render text to a pygame Surface.
        
        Args:
            text: The text to render
            style: The TextStyle configuration
            antialias: Whether to use antialiasing
            
        Returns:
            A pygame Surface with the rendered text
        """
        if not self._pygame_loaded:
            return None
        
        import pygame
        
        font = self.get_font(style)
        if font is None:
            return None
        
        # Create surface for text
        text_surface = font.render(text, antialias, style.color)
        
        # Add background if specified
        if style.background_color:
            bg_surface = pygame.Surface(text_surface.get_size())
            bg_surface.fill(style.background_color)
            bg_surface.blit(text_surface, (0, 0))
            text_surface = bg_surface
        
        # Add highlight if specified
        if style.highlight_color:
            highlight_surface = pygame.Surface(text_surface.get_size())
            highlight_surface.fill(style.highlight_color)
            highlight_surface.set_alpha(100)  # Semi-transparent
            text_surface.blit(highlight_surface, (0, 0))
        
        # Add shadow if specified
        if style.shadow:
            shadow_surface = self._add_shadow(text_surface, style)
            return shadow_surface
        
        return text_surface
    
    def _add_shadow(self, surface: any, style: TextStyle) -> any:
        """Add a shadow effect to a surface."""
        import pygame
        
        shadow_offset_x, shadow_offset_y = style.shadow_offset
        shadow_size = (
            surface.get_width() + abs(shadow_offset_x),
            surface.get_height() + abs(shadow_offset_y)
        )
        
        # Create surface large enough for shadow + text
        result = pygame.Surface(shadow_size)
        result.fill((0, 0, 0, 0))  # Transparent background
        
        # Draw shadow
        shadow = pygame.Surface(surface.get_size())
        shadow.fill(style.shadow_color)
        result.blit(shadow, (shadow_offset_x, shadow_offset_y))
        
        # Draw original text on top
        result.blit(surface, (0, 0))
        
        return result
    
    def measure_text(self, text: str, style: TextStyle) -> Tuple[int, int]:
        """
        Measure the dimensions of rendered text.
        
        Args:
            text: The text to measure
            style: The TextStyle configuration
            
        Returns:
            Tuple of (width, height) in pixels
        """
        if not self._pygame_loaded:
            # Fallback estimation
            return (len(text) * style.font_size * 0.6, style.font_size)
        
        import pygame
        
        font = self.get_font(style)
        if font is None:
            return (0, 0)
        
        return font.size(text)
    
    def wrap_text(self, text: str, style: TextStyle, max_width: int) -> List[str]:
        """
        Wrap text to fit within a maximum width.
        
        Args:
            text: The text to wrap
            style: The TextStyle configuration
            max_width: Maximum width in pixels
            
        Returns:
            List of text lines
        """
        if not text:
            return []
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            width, _ = self.measure_text(test_line, style)
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else [text]
    
    def check_contrast_ratio(
        self, 
        foreground: Tuple[int, int, int], 
        background: Tuple[int, int, int]
    ) -> float:
        """
        Calculate the contrast ratio between two colors.
        
        Implements WCAG 2.1 contrast ratio calculation.
        
        Args:
            foreground: RGB tuple for foreground color
            background: RGB tuple for background color
            
        Returns:
            Contrast ratio (1.0 to 21.0)
        """
        def luminance(rgb: Tuple[int, int, int]) -> float:
            """Calculate relative luminance of a color."""
            def adjust(c):
                c = c / 255.0
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            
            r, g, b = rgb
            return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)
        
        l1 = luminance(foreground)
        l2 = luminance(background)
        
        lighter = max(l1, l2)
        darker = min(l1, l2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    def meets_wcag_aa(self, foreground: Tuple[int, int, int], background: Tuple[int, int, int]) -> bool:
        """
        Check if two colors meet WCAG 2.1 AA contrast requirements.
        
        Args:
            foreground: RGB tuple for foreground color
            background: RGB tuple for background color
            
        Returns:
            True if contrast ratio >= 4.5:1 (AA standard for normal text)
        """
        ratio = self.check_contrast_ratio(foreground, background)
        return ratio >= 4.5
    
    # Predefined text styles
    @property
    def style_word_display(self) -> TextStyle:
        """Style for main word display (72pt, white)."""
        return TextStyle(
            font_size=self.FONT_HUGE,
            color=self.WHITE,
            bold=True,
            shadow=True,
            shadow_color=(0, 0, 0),
            shadow_offset=(3, 3)
        )
    
    @property
    def style_starter_letters(self) -> TextStyle:
        """Style for starter hint letters (84pt, yellow highlight)."""
        return TextStyle(
            font_size=self.FONT_MASSIVE,
            color=self.WHITE,
            bold=True,
            highlight_color=self.YELLOW_HIGHLIGHT,
            shadow=True,
            shadow_color=(0, 0, 0),
            shadow_offset=(3, 3)
        )
    
    @property
    def style_definition(self) -> TextStyle:
        """Style for definition text (28pt, light gray)."""
        return TextStyle(
            font_size=self.FONT_MEDIUM - 8,  # 28pt
            color=self.LIGHT_GRAY,
            shadow=False
        )
    
    @property
    def style_context_sentence(self) -> TextStyle:
        """Style for context sentence (24pt, light gray, italic)."""
        return TextStyle(
            font_size=self.FONT_SMALL,
            color=self.LIGHT_GRAY,
            italic=True
        )
    
    @property
    def style_input_letters(self) -> TextStyle:
        """Style for student input letters (60pt, white)."""
        return TextStyle(
            font_size=self.FONT_XLARGE,
            color=self.WHITE,
            bold=True
        )
    
    @property
    def style_button_text(self) -> TextStyle:
        """Style for button text."""
        return TextStyle(
            font_size=self.FONT_MEDIUM,
            color=self.WHITE,
            bold=True,
            background_color=self.ORANGE_ACCENT
        )
    
    @property
    def style_success(self) -> TextStyle:
        """Style for success messages."""
        return TextStyle(
            font_size=self.FONT_LARGE,
            color=self.SUCCESS_GREEN,
            bold=True
        )
    
    @property
    def style_error(self) -> TextStyle:
        """Style for error messages."""
        return TextStyle(
            font_size=self.FONT_LARGE,
            color=self.ERROR_RED,
            bold=True
        )


# Singleton instance for global access
_typography: Optional[Typography] = None
_typography_lock = threading.Lock()


def get_typography(fonts_dir: Optional[str] = None) -> Typography:
    """
    Get or create the global typography instance.
    
    Args:
        fonts_dir: Directory containing custom font files
        
    Returns:
        The Typography singleton instance
    """
    global _typography
    if _typography is None:
        with _typography_lock:
            if _typography is None:
                _typography = Typography(fonts_dir)
    return _typography


def reset_typography():
    """Reset the global typography instance (useful for testing)."""
    global _typography
    with _typography_lock:
        _typography = None

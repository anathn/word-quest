"""
Caption Display Component (STORY-006-03)

Renders captions on screen with customizable styling.
Provides text backup for audio content with proper positioning and visual design.
"""

import pygame
import logging
from typing import Optional, Tuple
from src.components.caption_manager import Caption
from src.components.caption_settings import CaptionSettings


logger = logging.getLogger(__name__)


class CaptionDisplay:
    """
    Renders captions on screen with customizable styling.
    
    Features:
    - Semi-transparent background for readability
    - Speaker name display in gold
    - Configurable font size and position
    - High contrast mode support
    - Text wrapping for long captions
    - Smooth fade animations (optional)
    
    Usage:
        display = CaptionDisplay(screen, settings)
        display.show_caption(caption)
        display.render()  # Call every frame while caption is visible
    """
    
    # Padding around caption text
    PADDING = 20
    
    # Maximum characters per line before wrapping
    MAX_CHAR_PER_LINE = 50
    
    def __init__(self, screen: 'pygame.Surface', settings: CaptionSettings):
        """
        Initialize caption display.
        
        Args:
            screen: Pygame surface to render on
            settings: CaptionSettings instance for appearance
        """
        self.screen = screen
        self.settings = settings
        self.current_caption: Optional[Caption] = None
        
        # Initialize fonts
        self._update_fonts()
        
        # Colors from settings
        self.background_color = settings.background_color
        self.text_color = settings.text_color
        self.speaker_color = settings.speaker_color
        
        # Position calculation
        self.caption_x = screen.get_width() // 2
        self.caption_y = self._calculate_y_position()
        
        logger.debug(f"CaptionDisplay initialized at ({self.caption_x}, {self.caption_y})")
    
    def _update_fonts(self) -> None:
        """Update fonts based on current settings."""
        try:
            self.font = pygame.font.Font(None, self.settings.font_size)
            self.speaker_font = pygame.font.Font(None, 
                                               max(18, self.settings.font_size - 8))
        except Exception as e:
            logger.error(f"Error loading fonts: {e}")
            # Fallback to default fonts
            self.font = pygame.font.Font(None, self.settings.font_size)
            self.speaker_font = pygame.font.Font(None, 20)
    
    def _calculate_y_position(self) -> int:
        """Calculate caption position based on settings."""
        if self.settings.position == "middle":
            return self.screen.get_height() // 2 + 100
        else:  # "bottom"
            return self.screen.get_height() - 100
    
    def show_caption(self, caption: Caption) -> None:
        """
        Store caption for rendering.
        
        Args:
            caption: Caption object to display
        """
        self.current_caption = caption
        self._update_colors_from_settings()
        logger.debug(f"Caption displayed: {caption.speaker}: {caption.text[:50]}...")
    
    def hide_caption(self) -> None:
        """Hide current caption."""
        self.current_caption = None
        logger.debug("Caption hidden")
    
    def update_settings(self, settings: CaptionSettings) -> None:
        """
        Update display settings.
        
        Args:
            settings: New CaptionSettings instance
        """
        self.settings = settings
        self._update_fonts()
        self._update_colors_from_settings()
        self.caption_y = self._calculate_y_position()
        logger.info("Caption display settings updated")
    
    def _update_colors_from_settings(self) -> None:
        """Update colors from current settings."""
        self.background_color = self.settings.background_color
        self.text_color = self.settings.text_color
        self.speaker_color = self.settings.speaker_color
    
    def _wrap_text(self, text: str, max_width: int) -> list:
        """
        Wrap text to fit within given width.
        
        Args:
            text: Text to wrap
            max_width: Maximum width in pixels
            
        Returns:
            List of text lines
        """
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = f"{current_line} {word}".strip() if current_line else word
            test_width = self.font.size(test_line)[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text]
    
    def render(self) -> None:
        """Draw caption on screen."""
        if not self.current_caption:
            return
        
        try:
            # Render speaker name if present
            speaker_rect = None
            text_offset_y = 0
            
            if self.current_caption.speaker:
                speaker_text = f"{self.current_caption.speaker}:"
                speaker_surface = self.speaker_font.render(
                    speaker_text, True, self.speaker_color)
                speaker_rect = speaker_surface.get_rect()
                speaker_width = speaker_rect.width
            
            # Handle text wrapping
            caption_text = self.current_caption.text
            available_width = self.screen.get_width() - (self.PADDING * 3)
            text_lines = self._wrap_text(caption_text, available_width)
            
            # Calculate total height needed
            line_heights = [self.font.size(line)[1] for line in text_lines]
            total_text_height = sum(line_heights)
            
            # Add speaker height if present
            speaker_height = speaker_rect.height if speaker_rect else 0
            if speaker_rect and text_lines:
                text_offset_y = speaker_height + 5  # Small gap
            
            # Calculate background dimensions
            max_line_width = max(
                [speaker_rect.width if speaker_rect else 0] + 
                [self.font.size(line)[0] for line in text_lines]
            )
            
            bg_width = max_line_width + (self.PADDING * 2)
            bg_height = speaker_height + total_text_height + (self.PADDING * 2)
            
            # Create background surface with transparency
            bg_surface = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
            bg_surface.fill(self.background_color)
            
            # Center background on screen
            bg_rect = bg_surface.get_rect(center=(self.caption_x, self.caption_y))
            self.screen.blit(bg_surface, bg_rect)
            
            # Draw speaker name if present
            if speaker_rect:
                speaker_rect.left = bg_rect.left + self.PADDING
                speaker_rect.top = bg_rect.top + 5
                self.screen.blit(speaker_surface, speaker_rect)
            
            # Draw text lines
            current_y = bg_rect.top + text_offset_y + (self.PADDING // 2)
            for line in text_lines:
                text_surface = self.font.render(line, True, self.text_color)
                text_rect = text_surface.get_rect(
                    left=bg_rect.left + self.PADDING,
                    top=current_y
                )
                self.screen.blit(text_surface, text_rect)
                current_y += line_heights[text_lines.index(line)]
            
        except Exception as e:
            logger.error(f"Error rendering caption: {e}")
    
    def update_screen_size(self, screen: 'pygame.Surface') -> None:
        """
        Update screen reference (call on window resize).
        
        Args:
            screen: New screen surface
        """
        self.screen = screen
        self.caption_x = screen.get_width() // 2
        self.caption_y = self._calculate_y_position()
        logger.debug(f"Screen size updated: {screen.get_width()}x{screen.get_height()}")
    
    def get_caption_rect(self) -> Optional[pygame.Rect]:
        """
        Get bounding rectangle of current caption.
        
        Returns:
            pygame.Rect of caption bounds or None
        """
        if not self.current_caption:
            return None
        
        # Calculate approximate rect (for accessibility focus)
        width = self.screen.get_width() - (self.PADDING * 2)
        height = self.settings.font_size * 3  # Approximate
        
        return pygame.Rect(
            self.PADDING,
            self.caption_y - height // 2,
            width,
            height
        )
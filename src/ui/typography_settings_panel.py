"""
Typography settings UI panel for Word Quest.

Provides UI controls for font selection and typography settings
in the parent dashboard, including OpenDyslexic font toggle.

STORY-006-05: OpenDyslexic Font Implementation
"""

import pygame
from typing import Optional, Callable, List
import logging

from .font_manager import get_font_manager
from ..components.typography_settings import TypographySettings, get_typography_settings

logger = logging.getLogger(__name__)


class TypographySettingsPanel:
    """
    UI panel for typography settings in the parent dashboard.
    
    Allows parents to:
    - Toggle between default and OpenDyslexic fonts
    - View side-by-side font comparison
    - See description of font accessibility benefits
    
    Attributes:
        rect: Panel rectangle for positioning and sizing
        font_manager: FontManager instance for font operations
        settings: TypographySettings instance for persistence
        on_font_changed: Optional callback when font settings change
    """
    
    # Panel dimensions
    PANEL_WIDTH = 600
    PANEL_HEIGHT = 350
    
    # Layout constants
    MARGIN = 20
    SPACING = 15
    HEADER_HEIGHT = 50
    LABEL_HEIGHT = 30
    SAMPLE_HEIGHT = 60
    
    # Vertical positions for centered layout
    # Panel height is 350px, center is at 175px
    # Layout distributed to center buttons: header(15) + desc(65) + spacing + buttons(155) + spacing + comparison(210)
    HEADER_TOP_OFFSET = 15
    DESCRIPTION_TOP_OFFSET = 65
    BUTTONS_TOP_OFFSET = 155  # Centered vertically in panel
    COMPARISON_TOP_OFFSET = 210
    
    # Colors
    PANEL_BG = (42, 42, 80)  # UI_BG_LIGHT
    PANEL_BORDER = (100, 100, 150)  # UI_BORDER
    TEXT_PRIMARY = (255, 255, 255)
    TEXT_SECONDARY = (189, 189, 189)
    SAMPLE_BG = (30, 30, 70)
    BUTTON_DEFAULT = (33, 150, 243)  # Blue
    BUTTON_HOVER = (25, 118, 210)
    BUTTON_DISABLED = (100, 100, 120)
    
    def __init__(self, x: int, y: int, 
                 on_font_changed: Optional[Callable[[str], None]] = None):
        """
        Initialize typography settings panel.
        
        Args:
            x: X coordinate for panel position
            y: Y coordinate for panel position
            on_font_changed: Callback function called when font changes
                            (receives new font family name)
        """
        self.rect = pygame.Rect(x, y, self.PANEL_WIDTH, self.PANEL_HEIGHT)
        self.on_font_changed = on_font_changed
        
        # Get instances
        self.font_manager = get_font_manager()
        self.settings = get_typography_settings()
        
        # Current font selection
        self.selected_font = self.settings.font_family
        
        # UI elements
        self.header_font = None
        self.body_font = None
        self.small_font = None
        self.description_font = None
        
        # Set fonts based on current settings
        self._update_fonts()
        
        # UI state
        self._hovered_button: Optional[str] = None
        # Note: button positions are calculated in _get_button_rects() to handle panel repositioning
        
        logger.info(f"TypographySettingsPanel initialized at ({x}, {y})")
    
    def _update_fonts(self) -> None:
        """Update fonts based on current typography settings."""
        self.header_font = self.font_manager.get_font(size=32, bold=True)
        self.body_font = self.font_manager.get_font(size=20)
        self.small_font = self.font_manager.get_font(size=16)
        self.description_font = self.font_manager.get_font(size=14)
    
    def _get_button_rects(self) -> dict:
        """Calculate button rectangles based on current panel position."""
        button_start_y = self.rect.y + self.BUTTONS_TOP_OFFSET
        
        return {
            'default': pygame.Rect(
                self.rect.x + self.MARGIN,
                button_start_y,
                (self.PANEL_WIDTH - self.MARGIN * 2) // 2 - self.SPACING // 2,
                40
            ),
            'opendyslexic': pygame.Rect(
                self.rect.x + self.MARGIN + (self.PANEL_WIDTH - self.MARGIN * 2) // 2 + self.SPACING // 2,
                button_start_y,
                (self.PANEL_WIDTH - self.MARGIN * 2) // 2 - self.SPACING // 2,
                40
            )
        }
    
    def handle_event(self, event) -> bool:
        """
        Handle pygame events for the panel.
        
        Args:
            event: Pygame event to handle
            
        Returns:
            True if event was handled by this panel
        """
        if event.type == pygame.MOUSEMOTION:
            # Track hover state
            mouse_pos = event.pos
            button_rects = self._get_button_rects()
            for name, rect in button_rects.items():
                if rect.collidepoint(mouse_pos):
                    self._hovered_button = name
                    break
            else:
                self._hovered_button = None
            return False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                button_rects = self._get_button_rects()
                for name, rect in button_rects.items():
                    if rect.collidepoint(mouse_pos):
                        self._select_font(name)
                        return True
            return False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                # Keyboard navigation (simplified)
                if self._hovered_button:
                    self._select_font(self._hovered_button)
                return True
        
        return False
    
    def _select_font(self, font_family: str) -> None:
        """
        Select a font family.
        
        Args:
            font_family: Font family to select ("default" or "opendyslexic")
        """
        if font_family not in ['default', 'opendyslexic']:
            logger.warning(f"Invalid font family: {font_family}")
            return
        
        self.selected_font = font_family
        self._update_fonts()
        
        # Update typography settings
        if font_family == 'opendyslexic' and not self.font_manager.is_opendyslexic_available():
            logger.warning("OpenDyslexic font not available, using default")
            self.selected_font = 'default'
            return
        
        # Save settings
        self.settings.set_font_family(font_family)
        self.settings.save()
        
        # Callback
        if self.on_font_changed:
            self.on_font_changed(font_family)
        
        logger.info(f"Font selection changed to: {font_family}")
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render the panel to the screen.
        
        Args:
            screen: Pygame surface to render to
        """
        # Draw panel background
        pygame.draw.rect(screen, self.PANEL_BG, self.rect)
        pygame.draw.rect(screen, self.PANEL_BORDER, self.rect, 2)
        
        # Draw header
        header_text = "Dyslexia-Friendly Font"
        header_surf = self.header_font.render(header_text, True, self.TEXT_PRIMARY)
        header_rect = header_surf.get_rect(
            centerx=self.rect.centerx,
            top=self.rect.top + self.HEADER_TOP_OFFSET
        )
        screen.blit(header_surf, header_rect)
        
        # Draw description
        description_line1 = "OpenDyslexic font can help students with dyslexia"
        description_line2 = "read more easily. It features weighted bottoms,"
        desc_surf1 = self.description_font.render(description_line1, True, self.TEXT_SECONDARY)
        desc_rect1 = desc_surf1.get_rect(
            centerx=self.rect.centerx,
            top=self.rect.top + self.DESCRIPTION_TOP_OFFSET
        )
        screen.blit(desc_surf1, desc_rect1)
        
        desc_surf2 = self.description_font.render(description_line2, True, self.TEXT_SECONDARY)
        desc_rect2 = desc_surf2.get_rect(
            centerx=self.rect.centerx,
            top=desc_rect1.bottom + 5
        )
        screen.blit(desc_surf2, desc_rect2)
        
        # Draw font selection buttons
        self._render_buttons(screen)
        
        # Draw font comparison
        self._render_font_comparison(screen)
        
        # Draw availability note
        if not self.font_manager.is_opendyslexic_available():
            note = "Note: OpenDyslexic font files not found. Using default font."
            note_surf = self.small_font.render(note, True, (255, 200, 100))
            note_rect = note_surf.get_rect(
                centerx=self.rect.centerx,
                bottom=self.rect.bottom - 10
            )
            screen.blit(note_surf, note_rect)
    
    def _render_buttons(self, screen: pygame.Surface) -> None:
        """
        Render font selection buttons.
        
        Args:
            screen: Pygame surface to render to
        """
        button_rects = self._get_button_rects()
        
        # Font options
        buttons = [
            ('default', 'Default Font', "Standard clear font"),
            ('opendyslexic', 'Dyslexia-Friendly (OpenDyslexic)', "OpenDyslexic font")
        ]
        
        for name, label, subtitle in buttons:
            rect = button_rects[name]
            
            # Determine button state
            is_selected = (name == 'opendyslexic' and self.font_manager.is_opendyslexic_available()) or \
                         (name == 'default' and self.selected_font == 'default')
            is_hover = (self._hovered_button == name)
            
            # Disable OpenDyslexic button if font not available
            if name == 'opendyslexic' and not self.font_manager.is_opendyslexic_available():
                is_hover = False
            
            # Button color
            if name == 'opendyslexic' and not self.font_manager.is_opendyslexic_available():
                color = self.BUTTON_DISABLED
            elif is_selected:
                color = (76, 175, 80)  # Green for selected
            elif is_hover:
                color = self.BUTTON_HOVER
            else:
                color = self.BUTTON_DEFAULT
            
            # Draw button background
            pygame.draw.rect(screen, color, rect, border_radius=5)
            
            # Draw button border (highlight if hovered)
            border_color = (255, 255, 255) if is_hover else self.PANEL_BORDER
            pygame.draw.rect(screen, border_color, rect, 2, border_radius=5)
            
            # Draw label
            label_surf = self.body_font.render(label, True, self.TEXT_PRIMARY)
            label_rect = label_surf.get_rect(center=rect.center)
            screen.blit(label_surf, label_rect)
            
            # Draw selected indicator
            if is_selected:
                # Draw checkmark
                checkmark = self.body_font.render("✓", True, (255, 255, 255))
                checkmark_rect = checkmark.get_rect(
                    right=rect.right - 10,
                    centery=rect.centery
                )
                screen.blit(checkmark, checkmark_rect)
    
    def _render_font_comparison(self, screen: pygame.Surface) -> None:
        """
        Render side-by-side font comparison.
        
        Args:
            screen: Pygame surface to render to
        """
        # Sample text and display area setup
        sample_text = "The quick brown fox jumps over the lazy dog"
        
        # Section title
        section_title = "Font Comparison"
        title_surf = self.body_font.render(section_title, True, self.TEXT_PRIMARY)
        title_rect = title_surf.get_rect(
            left=self.rect.left + self.MARGIN,
            top=self.rect.top + self.COMPARISON_TOP_OFFSET
        )
        screen.blit(title_surf, title_rect)
        
        # Sample display area
        sample_rect = pygame.Rect(
            self.rect.left + self.MARGIN,
            title_rect.bottom + self.SPACING,
            self.PANEL_WIDTH - self.MARGIN * 2,
            100
        )
        pygame.draw.rect(screen, self.SAMPLE_BG, sample_rect, border_radius=5)
        
        # Draw font samples using helper method
        self._draw_simple_samples(screen, sample_text, sample_rect)
    
    def _draw_simple_samples(self, screen: pygame.Surface, text: str, area_rect: pygame.Rect) -> None:
        """Draw font samples using simpler approach."""
        y_offset = area_rect.top + 10
        
        # Draw default font sample
        default_font = self.font_manager.get_font(family='default', size=24)
        default_surf = default_font.render(text, True, self.TEXT_PRIMARY)
        default_rect = default_surf.get_rect(centerx=area_rect.centerx, top=y_offset)
        screen.blit(default_surf, default_rect)
        
        # Draw default label
        default_label = "Default Font:"
        label_surf = self.small_font.render(default_label, True, self.TEXT_SECONDARY)
        label_rect = label_surf.get_rect(
            left=area_rect.left,
            bottom=default_rect.top - 2
        )
        screen.blit(label_surf, label_rect)
        
        y_offset = default_rect.bottom + 15
        
        # Draw OpenDyslexic sample if available
        if self.font_manager.is_opendyslexic_available():
            odl_font = self.font_manager.get_font(family='opendyslexic', size=24)
            if odl_font is not None:
                try:
                    odl_surf = odl_font.render(text, True, self.TEXT_PRIMARY)
                    odl_rect = odl_surf.get_rect(centerx=area_rect.centerx, top=y_offset)
                    screen.blit(odl_surf, odl_rect)
                    
                    # Draw OpenDyslexic label
                    odl_label = "OpenDyslexic:"
                    label_surf = self.small_font.render(odl_label, True, self.TEXT_SECONDARY)
                    label_rect = label_surf.get_rect(
                        left=area_rect.left,
                        bottom=odl_rect.top - 2
                    )
                    screen.blit(label_surf, label_rect)
                except pygame.error as e:
                    logger.warning(f"Failed to render OpenDyslexic font sample: {e}")
                    # Skip rendering this sample if font is not usable
    
    def get_current_font_family(self) -> str:
        """
        Get the currently selected font family.
        
        Returns:
            Current font family name
        """
        return self.selected_font
    
    def apply_selected_font(self) -> bool:
        """
        Apply the selected font to the global font manager.
        
        Returns:
            True if font was applied successfully
        """
        success = self.font_manager.set_current_family(self.selected_font)
        if success:
            self._update_fonts()
        return success


# Convenience function to create panel
def create_typography_settings_panel(
    x: int, y: int,
    on_font_changed: Optional[Callable[[str], None]] = None
) -> TypographySettingsPanel:
    """
    Create a typography settings panel.
    
    Args:
        x: X coordinate
        y: Y coordinate
        on_font_changed: Callback for font changes
        
    Returns:
        TypographySettingsPanel instance
    """
    return TypographySettingsPanel(x, y, on_font_changed)
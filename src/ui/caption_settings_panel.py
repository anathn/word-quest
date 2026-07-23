"""
Caption Settings Panel

UI component for configuring closed captions settings.
Implements STORY-006-03: Closed Captions - Settings UI Integration

Features:
- Enable/disable toggle
- Font size slider (18-48pt)
- Caption duration control (2-10s)
- Position selection (bottom/middle)
- SFX descriptions toggle
- High contrast toggle
- Test caption button
- Integration with CaptionManager for live updates

Example:
    caption_manager = CaptionManager(caption_display)
    caption_settings_mgr = CaptionSettingsManager()
    panel = CaptionSettingsPanel(caption_manager, caption_settings_mgr)
    panel.render(screen)
    panel.handle_event(event)
"""

import pygame
from typing import Optional, Callable, Dict, Any
from src.components.caption_manager import CaptionManager, CaptionIntensity
from src.components.caption_settings import CaptionSettingsManager, CaptionSettings


class CaptionSettingsPanel:
    """
    UI panel for caption settings configuration.
    
    Features:
    - Enable/disable toggle
    - Font size slider (18-48pt)
    - Duration slider (2-10s)
    - Position toggle (bottom/middle)
    - SFX descriptions checkbox
    - High contrast checkbox
    - Test caption button
    - Visual feedback for settings
    
    Example:
        caption_manager = CaptionManager(caption_display)
        settings_mgr = CaptionSettingsManager()
        panel = CaptionSettingsPanel(caption_manager, settings_mgr)
        
        # In game loop
        panel.handle_event(event)
        panel.render(screen)
    """
    
    # Colors
    COLOR_BG = (250, 250, 255)
    COLOR_CARD = (255, 255, 255)
    COLOR_TEXT = (50, 50, 70)
    COLOR_TEXT_LIGHT = (100, 100, 120)
    COLOR_BORDER = (200, 200, 220)
    COLOR_ACCENT = (76, 175, 80)  # Green for enabled
    COLOR_ACCENT_DISABLED = (189, 189, 189)  # Gray for disabled
    COLOR_HIGH_CONTRAST_BG = (255, 255, 255, 230)
    COLOR_HIGH_CONTRAST_TEXT = (0, 0, 0)
    
    # Layout constants
    PADDING = 20
    SECTION_SPACING = 20
    SLIDER_HEIGHT = 20
    BUTTON_HEIGHT = 40
    ROW_HEIGHT = 50
    
    def __init__(
        self,
        caption_manager: CaptionManager,
        settings_manager: CaptionSettingsManager,
        width: int = 600,
        height: int = 500,
        on_settings_change: Optional[Callable[[], None]] = None
    ):
        """
        Initialize caption settings panel.
        
        Args:
            caption_manager: CaptionManager instance for caption control
            settings_manager: CaptionSettingsManager instance for persistence
            width: Panel width in pixels
            height: Panel height in pixels
            on_settings_change: Callback when settings change
        """
        self.caption_manager = caption_manager
        self.settings_mgr = settings_manager
        self.settings = settings_manager.get_settings()
        self.width = width
        self.height = height
        self.on_settings_change = on_settings_change
        
        # UI state
        self._enabled = self.settings.enabled
        self._font_size = self.settings.font_size
        self._duration = self.settings.duration
        self._position = self.settings.position
        self._show_sfx = self.settings.show_sfx
        self._high_contrast = self.settings.high_contrast
        self._intensity_mode = self.settings.intensity_mode
        self._is_hovering_test_button = False
        self._slider_dragging = False
        self._volume_dragging = False
        
        # Calculate dimensions
        self.rect = pygame.Rect(0, 0, width, height)
        
        # Component rectangles (set in _calculate_layout)
        self._toggle_rect = pygame.Rect(0, 0, 0, 0)
        self._font_size_slider_rect = pygame.Rect(0, 0, 0, 0)
        self._duration_slider_rect = pygame.Rect(0, 0, 0, 0)
        self._position_toggle_rect = pygame.Rect(0, 0, 0, 0)
        self._test_button_rect = pygame.Rect(0, 0, 0, 0)
        self._sfx_checkbox_rect = pygame.Rect(0, 0, 0, 0)
        self._high_contrast_checkbox_rect = pygame.Rect(0, 0, 0, 0)
        
        self._calculate_layout()
        
        # Load current settings
        self._update_from_settings()
    
    def _calculate_layout(self) -> None:
        """Calculate positions for all UI components"""
        x_start = self.PADDING
        y_start = self.PADDING
        content_width = self.width - 2 * self.PADDING
        
        # Toggle row
        toggle_width = 80
        self._toggle_rect = pygame.Rect(
            x_start, y_start, toggle_width, self.BUTTON_HEIGHT
        )
        
        # Font size slider
        font_size_y = y_start + self.ROW_HEIGHT + self.SECTION_SPACING
        slider_x = x_start + 140
        slider_width = content_width - 140
        
        self._font_size_slider_rect = pygame.Rect(
            slider_x, font_size_y, slider_width, self.SLIDER_HEIGHT
        )
        
        # Duration slider
        duration_y = font_size_y + self.ROW_HEIGHT + 10
        self._duration_slider_rect = pygame.Rect(
            slider_x, duration_y, slider_width, self.SLIDER_HEIGHT
        )
        
        # Position toggle
        position_y = duration_y + self.ROW_HEIGHT + self.SECTION_SPACING
        self._position_toggle_rect = pygame.Rect(
            x_start, position_y, toggle_width, self.BUTTON_HEIGHT
        )
        
        # SFX checkbox
        sfx_y = position_y + self.ROW_HEIGHT + 10
        self._sfx_checkbox_rect = pygame.Rect(
            x_start, sfx_y, 30, 30
        )
        
        # High contrast checkbox
        hc_y = sfx_y + self.ROW_HEIGHT + 10
        self._high_contrast_checkbox_rect = pygame.Rect(
            x_start, hc_y, 30, 30
        )
        
        # Test button
        test_y = hc_y + self.ROW_HEIGHT + self.SECTION_SPACING
        self._test_button_rect = pygame.Rect(
            x_start + content_width - 140, test_y,
            140, self.BUTTON_HEIGHT
        )
    
    def _update_from_settings(self) -> None:
        """Update local state from settings"""
        self._enabled = self.settings.enabled
        self._font_size = self.settings.font_size
        self._duration = self.settings.duration
        self._position = self.settings.position
        self._show_sfx = self.settings.show_sfx
        self._high_contrast = self.settings.high_contrast
        self._intensity_mode = self.settings.intensity_mode
        
        # Update caption manager if available
        if self.caption_manager:
            self.caption_manager.set_enabled(self._enabled)
            if self._high_contrast:
                self.caption_manager.set_intensity_mode(CaptionIntensity.FULL)
            else:
                self.caption_manager.set_intensity_mode(
                    CaptionIntensity.FULL if self._show_sfx else CaptionIntensity.REDUCED
                )
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events.
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled
        """
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            self._is_hovering_test_button = self._test_button_rect.collidepoint(mouse_pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            
            # Toggle enable/disable
            if self._toggle_rect.collidepoint(mouse_pos):
                self._enabled = not self._enabled
                self._apply_settings()
                return True
            
            # Position toggle
            if self._position_toggle_rect.collidepoint(mouse_pos):
                self._position = "middle" if self._position == "bottom" else "bottom"
                self._apply_settings()
                return True
            
            # SFX checkbox
            if self._sfx_checkbox_rect.collidepoint(mouse_pos):
                self._show_sfx = not self._show_sfx
                self._apply_settings()
                return True
            
            # High contrast checkbox
            if self._high_contrast_checkbox_rect.collidepoint(mouse_pos):
                self._high_contrast = not self._high_contrast
                self._apply_settings()
                return True
            
            # Test button
            if self._test_button_rect.collidepoint(mouse_pos):
                self._test_caption()
                return True
            
            # Font size slider
            if self._font_size_slider_rect.collidepoint(mouse_pos):
                self._slider_dragging = True
                self._update_font_size_from_mouse(mouse_pos[0])
                return True
            
            # Duration slider
            if self._duration_slider_rect.collidepoint(mouse_pos):
                self._volume_dragging = True
                self._update_duration_from_mouse(mouse_pos[0])
                return True
            
        elif event.type == pygame.MOUSEBUTTONUP:
            self._slider_dragging = False
            self._volume_dragging = False
        
        elif event.type == pygame.MOUSEMOTION and self._slider_dragging:
            self._update_font_size_from_mouse(event.pos[0])
            return True
            
        elif event.type == pygame.MOUSEMOTION and self._volume_dragging:
            self._update_duration_from_mouse(event.pos[0])
            return True
        
        return False
    
    def _update_font_size_from_mouse(self, x: int) -> None:
        """Update font size from mouse position on slider"""
        slider_x = self._font_size_slider_rect.x
        slider_width = self._font_size_slider_rect.width
        
        # Clamp x to slider bounds
        x = max(slider_x, min(x, slider_x + slider_width))
        
        # Calculate font size (18-48)
        progress = (x - slider_x) / slider_width
        self._font_size = int(18 + progress * 30)
        
        self._apply_settings()
    
    def _update_duration_from_mouse(self, x: int) -> None:
        """Update duration from mouse position on slider"""
        slider_x = self._duration_slider_rect.x
        slider_width = self._duration_slider_rect.width
        
        # Clamp x to slider bounds
        x = max(slider_x, min(x, slider_x + slider_width))
        
        # Calculate duration (2-10s)
        progress = (x - slider_x) / slider_width
        self._duration = 2.0 + progress * 8.0
        
        self._apply_settings()
    
    def _test_caption(self) -> None:
        """Show test caption"""
        if self.caption_manager and self._enabled:
            test_messages = [
                "This is a test caption",
                "Captions are working correctly!",
                "Try spelling this word: CAPTION"
            ]
            import random
            test_text = random.choice(test_messages)
            
            self.caption_manager.show_caption(
                text=test_text,
                speaker="Test",
                duration=self._duration
            )
    
    def _apply_settings(self) -> None:
        """Apply current settings to managers"""
        # Update settings manager
        self.settings_mgr.set_enabled(self._enabled)
        self.settings_mgr.set_font_size(self._font_size)
        self.settings_mgr.set_position(self._position)
        self.settings_mgr.set_duration(self._duration)
        self.settings_mgr.set_sfx_display(self._show_sfx)
        self.settings_mgr.set_high_contrast(self._high_contrast)
        
        # Update caption manager
        if self.caption_manager:
            self.caption_manager.set_enabled(self._enabled)
            if self._high_contrast:
                self.caption_manager.set_intensity_mode(CaptionIntensity.FULL)
            else:
                self.caption_manager.set_intensity_mode(
                    CaptionIntensity.FULL if self._show_sfx else CaptionIntensity.REDUCED
                )
        
        # Update settings object
        self.settings = self.settings_mgr.get_settings()
        
        # Callback
        if self.on_settings_change:
            self.on_settings_change()
    
    def render(self, surface: pygame.Surface) -> None:
        """
        Render the panel.
        
        Args:
            surface: Pygame surface to render to
        """
        # Draw background
        bg_surface = pygame.Surface((self.width, self.height))
        bg_surface.fill(self.COLOR_BG)
        surface.blit(bg_surface, self.rect.topleft)
        
        # Draw card background
        card_rect = pygame.Rect(
            self.PADDING, self.PADDING,
            self.width - 2 * self.PADDING, self.height - 2 * self.PADDING
        )
        pygame.draw.rect(surface, self.COLOR_CARD, card_rect, border_radius=10)
        pygame.draw.rect(
            surface, self.COLOR_BORDER, card_rect, 2, border_radius=10
        )
        
        # Draw title
        font = pygame.font.Font(None, 32)
        title_surf = font.render("Caption Settings", True, self.COLOR_TEXT)
        surface.blit(title_surf, (self.PADDING + 20, self.PADDING + 5))
        
        # Draw enable/disable toggle
        self._render_toggle(surface)
        
        # Draw font size control
        self._render_font_size_control(surface)
        
        # Draw duration control
        self._render_duration_control(surface)
        
        # Draw position toggle
        self._render_position_toggle(surface)
        
        # Draw checkboxes
        self._render_checkboxes(surface)
        
        # Draw test button
        self._render_test_button(surface)
    
    def _render_toggle(self, surface: pygame.Surface) -> None:
        """Render the enable/disable toggle"""
        y_pos = self._toggle_rect.y
        x_label = self.PADDING + 120
        
        # Label
        font = pygame.font.Font(None, 28)
        label = "Enable Captions" if self._enabled else "Disable Captions"
        label_surf = font.render(label, True, self.COLOR_TEXT)
        surface.blit(label_surf, (x_label, y_pos + 8))
        
        # Toggle button
        toggle_color = self.COLOR_ACCENT if self._enabled else self.COLOR_ACCENT_DISABLED
        
        if self._toggle_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(
                surface, toggle_color, self._toggle_rect, 3, border_radius=8
            )
        else:
            pygame.draw.rect(
                surface, toggle_color, self._toggle_rect, 2, border_radius=8
            )
        
        pygame.draw.rect(
            surface, toggle_color,
            pygame.Rect(
                self._toggle_rect.x + 3, self._toggle_rect.y + 3,
                self._toggle_rect.width - 6, self._toggle_rect.height - 6
            ), border_radius=6
        )
    
    def _render_font_size_control(self, surface: pygame.Surface) -> None:
        """Render font size slider"""
        y_pos = self._font_size_slider_rect.y
        
        # Label
        font = pygame.font.Font(None, 28)
        label = f"Font Size: {self._font_size}pt"
        label_surf = font.render(label, True, self.COLOR_TEXT)
        surface.blit(label_surf, (self.PADDING + 20, y_pos - 5))
        
        # Slider background
        slider_bg = pygame.Rect(
            self._font_size_slider_rect.x, self._font_size_slider_rect.y,
            self._font_size_slider_rect.width, self._font_size_slider_rect.height
        )
        pygame.draw.rect(surface, (230, 230, 230), slider_bg, border_radius=10)
        
        # Slider fill
        fill_width = int(self._font_size_slider_rect.width * ((self._font_size - 18) / 30))
        fill_rect = pygame.Rect(
            self._font_size_slider_rect.x, self._font_size_slider_rect.y,
            fill_width, self._font_size_slider_rect.height
        )
        pygame.draw.rect(surface, self.COLOR_ACCENT, fill_rect, border_radius=10)
        
        # Slider handle
        handle_x = self._font_size_slider_rect.x + fill_width
        handle_rect = pygame.Rect(
            handle_x - 10, self._font_size_slider_rect.y - 3,
            20, self._font_size_slider_rect.height + 6
        )
        pygame.draw.ellipse(surface, self.COLOR_ACCENT, handle_rect)
    
    def _render_duration_control(self, surface: pygame.Surface) -> None:
        """Render duration slider"""
        y_pos = self._duration_slider_rect.y
        
        # Label
        font = pygame.font.Font(None, 28)
        label = f"Duration: {self._duration:.1f}s"
        label_surf = font.render(label, True, self.COLOR_TEXT)
        surface.blit(label_surf, (self.PADDING + 20, y_pos - 5))
        
        # Slider background
        slider_bg = pygame.Rect(
            self._duration_slider_rect.x, self._duration_slider_rect.y,
            self._duration_slider_rect.width, self._duration_slider_rect.height
        )
        pygame.draw.rect(surface, (230, 230, 230), slider_bg, border_radius=10)
        
        # Slider fill
        fill_width = int(self._duration_slider_rect.width * ((self._duration - 2.0) / 8.0))
        fill_rect = pygame.Rect(
            self._duration_slider_rect.x, self._duration_slider_rect.y,
            fill_width, self._duration_slider_rect.height
        )
        pygame.draw.rect(surface, (33, 150, 243), fill_rect, border_radius=10)
        
        # Slider handle
        handle_x = self._duration_slider_rect.x + fill_width
        handle_rect = pygame.Rect(
            handle_x - 10, self._duration_slider_rect.y - 3,
            20, self._duration_slider_rect.height + 6
        )
        pygame.draw.ellipse(surface, (33, 150, 243), handle_rect)
    
    def _render_position_toggle(self, surface: pygame.Surface) -> None:
        """Render position toggle"""
        y_pos = self._position_toggle_rect.y
        x_label = self.PADDING + 120
        
        # Label
        font = pygame.font.Font(None, 28)
        position_label = self._position.capitalize()
        label_surf = font.render(position_label, True, self.COLOR_TEXT)
        surface.blit(label_surf, (x_label, y_pos + 8))
        
        # Toggle button
        toggle_color = self.COLOR_ACCENT
        
        if self._position_toggle_rect.collidepoint(pygame.mouse.get_pos()):
            pygame.draw.rect(
                surface, toggle_color, self._position_toggle_rect, 3, border_radius=8
            )
        else:
            pygame.draw.rect(
                surface, toggle_color, self._position_toggle_rect, 2, border_radius=8
            )
        
        # Position icon
        icon_font = pygame.font.Font(None, 24)
        icon = "⬇" if self._position == "bottom" else "●"
        icon_surf = icon_font.render(icon, True, self.COLOR_TEXT)
        surface.blit(icon_surf, (x_label + 100, y_pos + 8))
    
    def _render_checkboxes(self, surface: pygame.Surface) -> None:
        """Render SFX and high contrast checkboxes"""
        font = pygame.font.Font(None, 28)
        
        # SFX checkbox
        sfx_y = self._sfx_checkbox_rect.y
        sfx_label = "Show SFX Descriptions"
        sfx_label_surf = font.render(sfx_label, True, self.COLOR_TEXT)
        surface.blit(sfx_label_surf, (self._sfx_checkbox_rect.x + 40, sfx_y + 5))
        
        self._render_checkbox(
            surface, self._sfx_checkbox_rect, self._show_sfx,
            self.COLOR_ACCENT
        )
        
        # High contrast checkbox
        hc_y = self._high_contrast_checkbox_rect.y
        hc_label = "High Contrast"
        hc_label_surf = font.render(hc_label, True, self.COLOR_TEXT)
        surface.blit(hc_label_surf, (self._high_contrast_checkbox_rect.x + 40, hc_y + 5))
        
        self._render_checkbox(
            surface, self._high_contrast_checkbox_rect, self._high_contrast,
            (255, 152, 0)
        )
    
    def _render_checkbox(
        self, surface: pygame.Surface, rect: pygame.Rect, 
        checked: bool, check_color: tuple
    ) -> None:
        """Render a checkbox"""
        if checked:
            pygame.draw.rect(surface, check_color, rect, 0, border_radius=4)
            # Draw checkmark
            pygame.draw.line(
                surface, (255, 255, 255),
                (rect.x + 7, rect.y + 15), (rect.x + 13, rect.y + 22), 3
            )
            pygame.draw.line(
                surface, (255, 255, 255),
                (rect.x + 13, rect.y + 22), (rect.x + 23, rect.y + 8), 3
            )
        else:
            pygame.draw.rect(surface, self.COLOR_BORDER, rect, 2, border_radius=4)
    
    def _render_test_button(self, surface: pygame.Surface) -> None:
        """Render test caption button"""
        color = self.COLOR_ACCENT if self._enabled else self.COLOR_ACCENT_DISABLED
        
        # Draw button
        if self._is_hovering_test_button:
            pygame.draw.rect(surface, color, self._test_button_rect, 3, border_radius=8)
        else:
            pygame.draw.rect(surface, color, self._test_button_rect, 2, border_radius=8)
        
        # Button text
        font = pygame.font.Font(None, 26)
        text_surf = font.render("Test Caption", True, self.COLOR_TEXT)
        text_rect = text_surf.get_rect(center=self._test_button_rect.center)
        surface.blit(text_surf, text_rect)
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get current settings as dictionary.
        
        Returns:
            Dictionary with current settings
        """
        return {
            'enabled': self._enabled,
            'font_size': self._font_size,
            'duration': self._duration,
            'position': self._position,
            'show_sfx': self._show_sfx,
            'high_contrast': self._high_contrast,
            'intensity_mode': self._intensity_mode
        }
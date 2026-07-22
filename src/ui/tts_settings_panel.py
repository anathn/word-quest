"""
TTS Settings Panel

UI component for configuring Text-to-Speech settings.
Implements STORY-006-02: Text-to-Speech Engine - Settings Integration

Features:
- TTS enable/disable toggle
- Speech speed slider (50% to 200%)
- Speech volume slider (0% to 100%)
- Voice selection dropdown
- Test pronunciation button
- Integration with TTSManager for live updates

Example:
    tts_manager = TTSManager()
    panel = TTSSettingsPanel(tts_manager)
    panel.render(screen)
    panel.handle_event(event)
"""

import pygame
from typing import Optional, Callable, List, Dict, Any
import importlib.util

# Check if TTS modules are available
TTS_AVAILABLE = importlib.util.find_spec("src.components.tts_manager") is not None


class TTSSettingsPanel:
    """
    UI panel for TTS configuration.
    
    Features:
    - Enable/disable toggle
    - Speed slider (0.5x to 2.0x)
    - Volume slider (0.0 to 1.0)
    - Voice selection
    - Test pronunciation button
    - Visual feedback for settings
    
    Example:
        tts_manager = TTSManager()
        panel = TTSSettingsPanel(tts_manager)
        
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
    COLOR_ERROR = (244, 67, 54)
    COLOR_SPEAKER = (33, 150, 243)  # Blue for TTS indicator
    COLOR_VOLUME_BG = (230, 230, 230)  # Light gray for slider background
    
    # Layout constants
    PADDING = 20
    SECTION_SPACING = 20
    SLIDER_HEIGHT = 20
    BUTTON_HEIGHT = 40
    BUTTON_WIDTH = 140
    ROW_HEIGHT = 50
    
    # Speed presets
    SPEED_PRESETS = {
        'Slow': 0.5,
        'Normal': 1.0,
        'Fast': 1.5,
        'Very Fast': 2.0
    }
    
    def __init__(
        self,
        tts_manager,
        width: int = 600,
        height: int = 300,
        on_settings_change: Optional[Callable[[], None]] = None,
        test_word: str = "Example"
    ):
        """
        Initialize TTS settings panel.
        
        Args:
            tts_manager: TTSManager instance for TTS control
            width: Panel width in pixels
            height: Panel height in pixels
            on_settings_change: Callback when settings change
            test_word: Word to use for testing pronunciation
            
        Raises:
            TypeError: If on_settings_change is provided but not callable
        """
        # Validate callback
        if on_settings_change is not None and not callable(on_settings_change):
            raise TypeError("on_settings_change must be callable")
        
        self.tts_manager = tts_manager
        self.width = width
        self.height = height
        self.on_settings_change = on_settings_change
        self.test_word = test_word
        
        # UI state
        self._enabled = True
        self._speed = 1.0
        self._volume = 1.0
        self._selected_preset = "Normal"
        self._is_hovering_test_button = False
        self._test_button_active = False
        
        # Calculate dimensions
        self.rect = pygame.Rect(0, 0, width, height)
        
        # Component rectangles (set in _calculate_layout)
        self._toggle_rect = pygame.Rect(0, 0, 0, 0)
        self._speed_slider_rect = pygame.Rect(0, 0, 0, 0)
        self._volume_slider_rect = pygame.Rect(0, 0, 0, 0)
        self._test_button_rect = pygame.Rect(0, 0, 0, 0)
        self._preset_buttons: Dict[str, pygame.Rect] = {}
        
        self._calculate_layout()
        
        # Load current settings
        self._update_from_manager()
        
        # Check TTS availability
        self._tts_available = TTS_AVAILABLE and tts_manager.is_initialized
        
        if not self._tts_available:
            self._enabled = False
    
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
        
        # Speed controls
        speed_y = y_start + self.ROW_HEIGHT + self.SECTION_SPACING
        preset_width = 100
        slider_x = x_start + 140
        slider_width = content_width - 140
        
        self._speed_slider_rect = pygame.Rect(
            slider_x, speed_y, slider_width, self.SLIDER_HEIGHT
        )
        
        # Preset buttons row
        preset_y = speed_y + self.SLIDER_HEIGHT + 10
        button_spacing = 10
        total_button_width = (
            len(self.SPEED_PRESETS) * (preset_width + button_spacing) - button_spacing
        )
        preset_start_x = x_start + (content_width - total_button_width) // 2
        
        offset = 0
        for label in self.SPEED_PRESETS:
            self._preset_buttons[label] = pygame.Rect(
                preset_start_x + offset, preset_y, preset_width, self.BUTTON_HEIGHT - 10
            )
            offset += preset_width + button_spacing
        
        # Volume controls
        volume_y = preset_y + self.BUTTON_HEIGHT + self.SECTION_SPACING
        self._volume_slider_rect = pygame.Rect(
            slider_x, volume_y, slider_width, self.SLIDER_HEIGHT
        )
        
        # Test button
        test_y = volume_y + self.SLIDER_HEIGHT + self.SECTION_SPACING
        self._test_button_rect = pygame.Rect(
            x_start + content_width - self.BUTTON_WIDTH, test_y,
            self.BUTTON_WIDTH, self.BUTTON_HEIGHT
        )
    
    def _update_from_manager(self) -> None:
        """Update local state from TTS manager settings"""
        if self.tts_manager:
            settings = self.tts_manager.get_settings()
            self._enabled = settings.enabled
            self._speed = settings.speed
            self._volume = settings.volume
            
            # Find closest preset
            for preset, value in self.SPEED_PRESETS.items():
                if abs(settings.speed - value) < 0.05:
                    self._selected_preset = preset
                    break
    
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
                if self.tts_manager:
                    self.tts_manager.set_enabled(self._enabled)
                if self.on_settings_change:
                    self.on_settings_change()
                return True
            
            # Test button
            if self._test_button_rect.collidepoint(mouse_pos) and self._tts_available:
                self._test_pronunciation()
                return True
            
            # Preset buttons
            for preset, rect in self._preset_buttons.items():
                if rect.collidepoint(mouse_pos):
                    self._selected_preset = preset
                    new_speed = self.SPEED_PRESETS[preset]
                    self._speed = new_speed
                    if self.tts_manager:
                        self.tts_manager.set_speed(new_speed)
                    if self.on_settings_change:
                        self.on_settings_change()
                    return True
            
            # Speed slider
            if self._speed_slider_rect.collidepoint(mouse_pos):
                self._slider_dragging = True
                self._update_speed_from_mouse(mouse_pos[0])
                return True
            
            # Volume slider
            if self._volume_slider_rect.collidepoint(mouse_pos):
                self._volume_dragging = True
                self._update_volume_from_mouse(mouse_pos[0])
                return True
            
        elif event.type == pygame.MOUSEBUTTONUP:
            self._slider_dragging = False
            self._volume_dragging = False
        
        elif event.type == pygame.MOUSEMOTION and self._slider_dragging:
            self._update_speed_from_mouse(event.pos[0])
            return True
            
        elif event.type == pygame.MOUSEMOTION and self._volume_dragging:
            self._update_volume_from_mouse(event.pos[0])
            return True
        
        return False
    
    def _update_speed_from_mouse(self, x: int) -> None:
        """Update speed from mouse position on slider"""
        slider_x = self._speed_slider_rect.x
        slider_width = self._speed_slider_rect.width
        
        # Clamp x to slider bounds
        x = max(slider_x, min(x, slider_x + slider_width))
        
        # Calculate speed (0.5 to 2.0)
        progress = (x - slider_x) / slider_width
        self._speed = 0.5 + progress * 1.5
        
        if self.tts_manager:
            self.tts_manager.set_speed(self._speed)
        
        # Update preset selection
        for preset, value in self.SPEED_PRESETS.items():
            if abs(self._speed - value) < 0.1:
                self._selected_preset = preset
                break
        
        if self.on_settings_change:
            self.on_settings_change()
    
    def _update_volume_from_mouse(self, x: int) -> None:
        """Update volume from mouse position on slider"""
        slider_x = self._volume_slider_rect.x
        slider_width = self._volume_slider_rect.width
        
        # Clamp x to slider bounds
        x = max(slider_x, min(x, slider_x + slider_width))
        
        # Calculate volume (0.0 to 1.0)
        progress = (x - slider_x) / slider_width
        self._volume = progress
        
        if self.tts_manager:
            self.tts_manager.set_volume(self._volume)
        
        if self.on_settings_change:
            self.on_settings_change()
    
    def _test_pronunciation(self) -> None:
        """Play test pronunciation"""
        if self.tts_manager and self._enabled and self._tts_available:
            self._test_button_active = True
            self.tts_manager.speak_word(self.test_word)
            
            # Reset button state after short delay
            pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
    
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
        title_surf = font.render("Text-to-Speech Settings", True, self.COLOR_TEXT)
        surface.blit(title_surf, (self.PADDING + 20, self.PADDING + 5))
        
        # Draw enable/disable toggle
        self._render_toggle(surface)
        
        # Draw speed controls
        self._render_speed_controls(surface)
        
        # Draw volume controls
        self._render_volume_controls(surface)
        
        # Draw test button
        self._render_test_button(surface)
        
        # Draw TTS availability indicator
        self._render_availability_indicator(surface)
    
    def _render_toggle(self, surface: pygame.Surface) -> None:
        """Render the enable/disable toggle"""
        y_pos = self._toggle_rect.y
        x_label = self.PADDING + 120
        
        # Label
        font = pygame.font.Font(None, 28)
        label = "Enable TTS" if self._enabled else "Disable TTS"
        label_surf = font.render(label, True, self.COLOR_TEXT)
        surface.blit(label_surf, (x_label, y_pos + 8))
        
        # Toggle button
        toggle_color = self.COLOR_ACCENT if self._enabled else self.COLOR_ACCENT_DISABLED
        
        if self._toggle_rect.collidepoint(pygame.mouse.get_pos()):
            # Draw thicker border on hover
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
    
    def _render_speed_controls(self, surface: pygame.Surface) -> None:
        """Render speed controls"""
        # Label
        font = pygame.font.Font(None, 28)
        label = f"Speech Speed: {self._speed:.1f}x"
        label_surf = font.render(label, True, self.COLOR_TEXT)
        surface.blit(label_surf, (self.PADDING + 20, self._speed_slider_rect.y - 5))
        
        # Slider background
        slider_bg = pygame.Rect(
            self._speed_slider_rect.x, self._speed_slider_rect.y,
            self._speed_slider_rect.width, self._speed_slider_rect.height
        )
        pygame.draw.rect(surface, self.COLOR_VOLUME_BG, slider_bg, border_radius=10)
        
        # Slider fill
        fill_width = int(self._speed_slider_rect.width * ((self._speed - 0.5) / 1.5))
        fill_rect = pygame.Rect(
            self._speed_slider_rect.x, self._speed_slider_rect.y,
            fill_width, self._speed_slider_rect.height
        )
        pygame.draw.rect(surface, self.COLOR_ACCENT, fill_rect, border_radius=10)
        
        # Slider handle
        handle_x = self._speed_slider_rect.x + fill_width
        handle_rect = pygame.Rect(
            handle_x - 10, self._speed_slider_rect.y - 3,
            20, self._speed_slider_rect.height + 6
        )
        pygame.draw.ellipse(surface, self.COLOR_ACCENT, handle_rect)
        
        # Preset buttons
        for preset, rect in self._preset_buttons.items():
            color = (
                self.COLOR_ACCENT if preset == self._selected_preset 
                else self.COLOR_BORDER
            )
            
            is_hovered = rect.collidepoint(pygame.mouse.get_pos())
            
            pygame.draw.rect(surface, color, rect, 2, border_radius=8)
            
            # Text
            preset_font = pygame.font.Font(None, 24)
            preset_surf = preset_font.render(preset, True, self.COLOR_TEXT)
            text_rect = preset_surf.get_rect(center=rect.center)
            surface.blit(preset_surf, text_rect)
    
    def _render_volume_controls(self, surface: pygame.Surface) -> None:
        """Render volume controls"""
        # Label
        font = pygame.font.Font(None, 28)
        volume_percent = int(self._volume * 100)
        label = f"Volume: {volume_percent}%"
        label_surf = font.render(label, True, self.COLOR_TEXT)
        surface.blit(label_surf, (self.PADDING + 20, self._volume_slider_rect.y - 5))
        
        # Slider background
        slider_bg = pygame.Rect(
            self._volume_slider_rect.x, self._volume_slider_rect.y,
            self._volume_slider_rect.width, self._volume_slider_rect.height
        )
        pygame.draw.rect(surface, self.COLOR_VOLUME_BG, slider_bg, border_radius=10)
        
        # Slider fill
        fill_width = int(self._volume_slider_rect.width * self._volume)
        fill_rect = pygame.Rect(
            self._volume_slider_rect.x, self._volume_slider_rect.y,
            fill_width, self._volume_slider_rect.height
        )
        pygame.draw.rect(surface, self.COLOR_SPEAKER, fill_rect, border_radius=10)
        
        # Slider handle
        handle_x = self._volume_slider_rect.x + fill_width
        handle_rect = pygame.Rect(
            handle_x - 10, self._volume_slider_rect.y - 3,
            20, self._volume_slider_rect.height + 6
        )
        pygame.draw.ellipse(surface, self.COLOR_SPEAKER, handle_rect)
        
        # Volume icon
        icon_font = pygame.font.Font(None, 24)
        icon = "🔊" if self._volume > 0.5 else "🔉" if self._volume > 0 else "🔇"
        icon_surf = icon_font.render(icon, True, self.COLOR_TEXT)
        surface.blit(icon_surf, (self.PADDING + 20, self._volume_slider_rect.y + 2))
    
    def _render_test_button(self, surface: pygame.Surface) -> None:
        """Render test pronunciation button"""
        color = self.COLOR_ACCENT if self._enabled and self._tts_available else self.COLOR_ACCENT_DISABLED
        
        # Draw button
        if self._is_hovering_test_button or self._test_button_active:
            pygame.draw.rect(surface, color, self._test_button_rect, 3, border_radius=8)
        else:
            pygame.draw.rect(surface, color, self._test_button_rect, 2, border_radius=8)
        
        # Button text
        font = pygame.font.Font(None, 26)
        if self._test_button_active:
            text = "Playing..."
        else:
            text = "Test Pronunciation"
        text_surf = font.render(text, True, self.COLOR_TEXT)
        text_rect = text_surf.get_rect(center=self._test_button_rect.center)
        surface.blit(text_surf, text_rect)
        
        # Speaker icon
        icon_font = pygame.font.Font(None, 24)
        icon_surf = icon_font.render("🔊", True, self.COLOR_TEXT)
        surface.blit(icon_surf, (self._test_button_rect.x + 10, self._test_button_rect.y + 8))
    
    def _render_availability_indicator(self, surface: pygame.Surface) -> None:
        """Render TTS availability status"""
        if self._tts_available:
            # Available indicator
            color = self.COLOR_ACCENT
            icon = "✓"
            text = "TTS Ready"
        else:
            # Not available indicator
            color = (255, 152, 0)  # Orange for warning
            icon = "!"
            text = "TTS Unavailable"
        
        # Small indicator at bottom
        font = pygame.font.Font(None, 22)
        indicator = f"{icon} {text}"
        indicator_surf = font.render(indicator, True, color)
        surface.blit(indicator_surf, (self.PADDING + 20, self.height - 30))
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get current settings as dictionary.
        
        Returns:
            Dictionary with 'enabled', 'speed', and 'volume' keys
        """
        return {
            'enabled': self._enabled,
            'speed': self._speed,
            'volume': self._volume,
            'preset': self._selected_preset
        }
    
    def set_enabled(self, enabled: bool) -> None:
        """Set TTS enabled state"""
        self._enabled = enabled
        if self.tts_manager:
            self.tts_manager.set_enabled(enabled)
    
    def set_speed(self, speed: float) -> None:
        """Set speech speed"""
        speed = max(0.5, min(2.0, speed))
        self._speed = speed
        if self.tts_manager:
            self.tts_manager.set_speed(speed)


def create_tts_settings_panel(tts_manager, width: int = 600, height: int = 300):
    """
    Factory function to create a TTS settings panel.
    
    Args:
        tts_manager: TTSManager instance
        width: Panel width
        height: Panel height
        
    Returns:
        TTSSettingsPanel instance
    """
    return TTSSettingsPanel(tts_manager, width, height)
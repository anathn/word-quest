"""
Music Settings Panel

UI component for configuring background music settings.
Implements STORY-005-04: Background Music - Settings Integration

Features:
- Music volume slider (0-100%)
- Mute/unmute toggle
- Music preview functionality
- Integration with PlayerPreferencesManager for persistence

Example:
    panel = MusicSettingsPanel(music_manager, preferences_manager)
    panel.render(screen)
    panel.handle_event(event)
"""

import pygame
from typing import Optional, Callable
import importlib.util

# Check if music_manager module can be imported
MUSIC_AVAILABLE = importlib.util.find_spec("src.audio.music_manager") is not None
PREFERENCES_AVAILABLE = importlib.util.find_spec("src.settings.player_preferences") is not None


class MusicSettingsPanel:
    """
    UI panel for music configuration.
    
    Features:
    - Volume slider (0-100%)
    - Mute/unmute toggle button
    - Display current volume percentage
    - Integration with MusicManager and PlayerPreferencesManager
    
    Example:
        music_manager = get_music_manager()
        pref_manager = get_preferences_manager()
        panel = MusicSettingsPanel(music_manager, pref_manager)
        
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
    COLOR_ACCENT = (76, 175, 80)
    COLOR_ACCENT_LIGHT = (100, 189, 100)
    COLOR_ERROR = (244, 67, 54)
    COLOR_VOLUME_BG = (200, 200, 200)
    COLOR_VOLUME_FILL = (76, 175, 80)
    COLOR_PLAYING = (33, 150, 243)  # Blue for preview indicator
    
    # Layout constants
    PADDING = 20
    SECTION_SPACING = 25
    SLIDER_HEIGHT_THICK = 30
    BUTTON_HEIGHT = 35
    BUTTON_WIDTH = 120
    
    def __init__(
        self,
        music_manager,
        preferences_manager,
        width: int = 600,
        height: int = 200,
        on_volume_change: Optional[Callable[[float], None]] = None,
        on_mute_change: Optional[Callable[[bool], None]] = None
    ):
        """
        Initialize music settings panel.
        
        Args:
            music_manager: MusicManager instance for music control
            preferences_manager: PlayerPreferencesManager for persistence
            width: Panel width in pixels
            height: Panel height in pixels
            on_volume_change: Callback when volume changes
            on_mute_change: Callback when mute state changes
        """
        self.music_manager = music_manager
        self.preferences_manager = preferences_manager
        self.width = width
        self.height = height
        self.on_volume_change = on_volume_change
        self.on_mute_change = on_mute_change
        
        # Local state mirrors music manager
        self._music_volume = music_manager.get_volume() if music_manager else 0.3
        self._is_muted = music_manager.is_muted() if music_manager else False
        
        # UI state
        self._slider_dragging = False
        self._slider_drag_start_x = 0
        self._slider_start_volume = 0.0
        
        # Fonts (initialized on first render)
        self._title_font: Optional[pygame.font.Font] = None
        self._header_font: Optional[pygame.font.Font] = None
        self._body_font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None
        
        # UI element rects (calculated on render)
        self._volume_slider_rect: Optional[pygame.Rect] = None
        self._mute_button_rect: Optional[pygame.Rect] = None
        self._preview_button_rect: Optional[pygame.Rect] = None
        
        # Preview state
        self._preview_playing = False
        self._preview_timer = 0.0
    
    def _init_fonts(self):
        """Initialize Pygame fonts."""
        if self._title_font is None:
            try:
                self._title_font = pygame.font.SysFont('arial', 18, bold=True)
                self._header_font = pygame.font.SysFont('arial', 14, bold=True)
                self._body_font = pygame.font.SysFont('arial', 13)
                self._small_font = pygame.font.SysFont('arial', 11)
            except Exception:
                self._title_font = pygame.font.Font(None, 18)
                self._header_font = pygame.font.Font(None, 14)
                self._body_font = pygame.font.Font(None, 13)
                self._small_font = pygame.font.Font(None, 11)
    
    def render(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0):
        """
        Render the music settings panel.
        
        Args:
            surface: Pygame surface to render to
            offset_x: Horizontal offset for panel position
            offset_y: Vertical offset for panel position
        """
        self._init_fonts()
        
        x_offset = offset_x
        y_offset = offset_y
        
        # Draw title
        self._draw_title(surface, x_offset, y_offset)
        
        current_y = y_offset + 50
        
        # Check if music system is available
        if not self.music_manager or not self.music_manager.is_audio_available():
            self._draw_music_unavailable(surface, x_offset, current_y)
            return
        
        # Draw volume controls
        current_y = self._draw_volume_section(surface, x_offset, current_y)
        
        # Draw mute toggle
        self._draw_mute_section(surface, x_offset, current_y)
    
    def _draw_title(self, surface: pygame.Surface, x_offset: int, y_offset: int):
        """Draw panel title."""
        if not self._title_font:
            return
        
        title = "Music Settings"
        title_surf = self._title_font.render(title, True, self.COLOR_TEXT)
        title_rect = title_surf.get_rect(left=x_offset + self.PADDING, top=y_offset)
        surface.blit(title_surf, title_rect)
        
        # Subtitle
        if self._small_font:
            subtitle = "Adjust music volume and mute settings"
            subtitle_surf = self._small_font.render(subtitle, True, self.COLOR_TEXT_LIGHT)
            subtitle_rect = subtitle_surf.get_rect(
                left=x_offset + self.PADDING, 
                top=y_offset + 28
            )
            surface.blit(subtitle_surf, subtitle_rect)
    
    def _draw_music_unavailable(self, surface: pygame.Surface, x_offset: int, y_offset: int):
        """Draw message when music is unavailable."""
        if not self._body_font:
            return
        
        # Warning box
        warning_rect = pygame.Rect(
            x_offset + self.PADDING,
            y_offset,
            self.width - 2 * self.PADDING,
            80
        )
        
        # Yellow background
        pygame.draw.rect(surface, (255, 245, 200), warning_rect, border_radius=8)
        pygame.draw.rect(surface, (255, 200, 0), warning_rect, 2, border_radius=8)
        
        # Warning icon and message
        if self._header_font:
            warning_text = "Audio Unavailable"
            warning_surf = self._header_font.render(warning_text, True, (150, 100, 0))
            warning_surf_rect = warning_surf.get_rect(
                left=warning_rect.x + 15, top=warning_rect.y + 15
            )
            surface.blit(warning_surf, warning_surf_rect)
            
            # Instructions
            info_text = "Music could not be initialized. Please check your audio settings."
            info_surf = self._body_font.render(info_text, True, (150, 100, 0))
            info_rect = info_surf.get_rect(
                left=warning_rect.x + 15, top=warning_rect.y + 45
            )
            surface.blit(info_surf, info_rect)
    
    def _draw_volume_section(self, surface: pygame.Surface, x_offset: int, y_offset: int) -> int:
        """Draw volume control section."""
        if not self._header_font:
            return y_offset
        
        # Section header
        header_surf = self._header_font.render("Music Volume", True, self.COLOR_TEXT)
        surface.blit(header_surf, (x_offset + self.PADDING, y_offset))
        
        current_y = y_offset + 35
        
        # Volume slider background
        slider_x = x_offset + self.PADDING + 100
        slider_y = current_y
        slider_width = self.width - 2 * self.PADDING - 110
        
        self._volume_slider_rect = pygame.Rect(
            slider_x, slider_y, slider_width, self.SLIDER_HEIGHT_THICK
        )
        
        # Slider background
        pygame.draw.rect(
            surface, self.COLOR_VOLUME_BG, 
            self._volume_slider_rect, border_radius=self.SLIDER_HEIGHT_THICK // 2
        )
        
        # Fill based on current volume (not muted)
        effective_volume = 0.0 if self._is_muted else self._music_volume
        fill_width = int(slider_width * effective_volume)
        
        if fill_width > 0:
            fill_rect = pygame.Rect(
                slider_x, slider_y, fill_width, self.SLIDER_HEIGHT_THICK
            )
            pygame.draw.rect(
                surface, self.COLOR_VOLUME_FILL, 
                fill_rect, border_radius=self.SLIDER_HEIGHT_THICK // 2
            )
        
        # Slider thumb
        thumb_x = slider_x + int(slider_width * effective_volume) - self.SLIDER_HEIGHT_THICK // 2
        thumb_y = slider_y
        
        # Clamp thumb position
        thumb_x = max(slider_x, min(thumb_x, slider_x + slider_width - self.SLIDER_HEIGHT_THICK))
        
        thumb_rect = pygame.Rect(thumb_x, thumb_y, self.SLIDER_HEIGHT_THICK, self.SLIDER_HEIGHT_THICK)
        
        # Hover effect
        if self._slider_dragging or thumb_rect.collidepoint(pygame.mouse.get_pos()):
            thumb_color = self.COLOR_ACCENT_LIGHT
        else:
            thumb_color = self.COLOR_ACCENT
        
        pygame.draw.circle(surface, thumb_color, thumb_rect.center, self.SLIDER_HEIGHT_THICK // 2)
        pygame.draw.circle(surface, self.COLOR_BORDER, thumb_rect.center, self.SLIDER_HEIGHT_THICK // 2, 2)
        
        # Volume percentage display
        volume_percent = int(effective_volume * 100)
        if self._body_font:
            percent_surf = self._body_font.render(f"{volume_percent}%", True, self.COLOR_TEXT)
            percent_rect = percent_surf.get_rect(
                left=x_offset + self.PADDING, 
                bottom=current_y + self.SLIDER_HEIGHT_THICK + 5
            )
            surface.blit(percent_surf, percent_rect)
        
        return current_y + self.SLIDER_HEIGHT_THICK + 40
    
    def _draw_mute_section(self, surface: pygame.Surface, x_offset: int, y_offset: int):
        """Draw mute toggle button."""
        if not self._body_font:
            return
        
        # Mute toggle button
        mute_text = "🔇 Muted" if self._is_muted else "🔊 Unmute"
        
        self._mute_button_rect = pygame.Rect(
            x_offset + self.PADDING,
            y_offset,
            self.BUTTON_WIDTH,
            self.BUTTON_HEIGHT
        )
        
        is_mute_hovered = self._mute_button_rect.collidepoint(pygame.mouse.get_pos())
        mute_color = self.COLOR_ACCENT_LIGHT if is_mute_hovered else self.COLOR_ACCENT
        
        pygame.draw.rect(surface, mute_color, self._mute_button_rect, border_radius=4)
        pygame.draw.rect(surface, self.COLOR_BORDER, self._mute_button_rect, 2, border_radius=4)
        
        mute_surf = self._small_font.render(mute_text, True, (255, 255, 255))
        mute_rect = mute_surf.get_rect(center=self._mute_button_rect.center)
        surface.blit(mute_surf, mute_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events.
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_mouse_click(event.pos)
        
        if event.type == pygame.MOUSEBUTTONUP:
            return self._handle_mouse_up(event.pos)
        
        if event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)
            return True
        
        return False
    
    def _handle_mouse_click(self, pos: tuple) -> bool:
        """Handle mouse click events."""
        # Mute toggle
        if self._mute_button_rect and self._mute_button_rect.collidepoint(pos):
            self._toggle_mute()
            return True
        
        # Volume slider click
        if self._volume_slider_rect and self._volume_slider_rect.collidepoint(pos):
            self._slider_dragging = True
            self._slider_drag_start_x = pos[0]
            self._slider_start_volume = self._music_volume if not self._is_muted else 0.0
            self._update_volume_from_slider(pos[0])
            return True
        
        return False
    
    def _handle_mouse_up(self, pos: tuple) -> bool:
        """Handle mouse up events."""
        if self._slider_dragging:
            self._slider_dragging = False
            # Save to preferences when done dragging
            if self.preferences_manager:
                self.preferences_manager.set_music_volume(self._music_volume)
                self.preferences_manager.set_music_muted(self._is_muted)
            return True
        return False
    
    def _handle_mouse_motion(self, pos: tuple):
        """Handle mouse motion for hover effects."""
        # Hover effects are handled in render
        pass
    
    def _toggle_mute(self):
        """Toggle mute state."""
        if not self.music_manager:
            return
        
        self._is_muted = not self._is_muted
        self.music_manager.mute() if self._is_muted else self.music_manager.unmute()
        
        # Notify callback
        if self.on_mute_change:
            self.on_mute_change(self._is_muted)
    
    def _update_volume_from_slider(self, x_position: int):
        """Update volume based on slider position."""
        if not self._volume_slider_rect or not self.music_manager:
            return
        
        slider_x = self._volume_slider_rect.x
        slider_width = self._volume_slider_rect.width
        
        # Calculate position within slider (0.0 to 1.0)
        position = (x_position - slider_x) / slider_width
        position = max(0.0, min(1.0, position))
        
        # Update volume
        self._music_volume = position
        
        # Unmute if volume is above 0
        if position > 0 and self._is_muted:
            self._is_muted = False
        
        self.music_manager.set_volume(position)
        
        # Notify callback
        if self.on_volume_change:
            self.on_volume_change(position)
    
    def update(self, delta_time: float):
        """
        Update panel state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        # Update preview timer
        if self._preview_playing:
            self._preview_timer += delta_time
            if self._preview_timer > 2.0:  # Reset after 2 seconds
                self._preview_playing = False
                self._preview_timer = 0.0
    
    def set_volume(self, volume: float):
        """
        Set volume from external source.
        
        Args:
            volume: Volume level 0.0 to 1.0
        """
        self._music_volume = volume
        if self.music_manager:
            self.music_manager.set_volume(volume)
    
    def get_volume(self) -> float:
        """
        Get current volume level.
        
        Returns:
            Volume level 0.0 to 1.0
        """
        return self._music_volume
    
    def is_muted(self) -> bool:
        """
        Get mute state.
        
        Returns:
            True if muted, False otherwise
        """
        return self._is_muted


def create_music_settings_panel(
    music_manager=None,
    preferences_manager=None,
    width: int = 600,
    height: int = 200,
    on_volume_change: Optional[Callable[[float], None]] = None,
    on_mute_change: Optional[Callable[[bool], None]] = None
) -> MusicSettingsPanel:
    """
    Factory function to create a MusicSettingsPanel.
    
    Args:
        music_manager: MusicManager instance (will use singleton if None)
        preferences_manager: PlayerPreferencesManager instance
        width: Panel width
        height: Panel height
        on_volume_change: Callback when volume changes
        on_mute_change: Callback when mute state changes
        
    Returns:
        Configured MusicSettingsPanel
    """
    # Auto-import modules if needed
    if music_manager is None and MUSIC_AVAILABLE:
        from src.audio.music_manager import get_music_manager
        music_manager = get_music_manager()
    
    if preferences_manager is None and PREFERENCES_AVAILABLE:
        from src.settings.player_preferences import get_preferences_manager
        preferences_manager = get_preferences_manager()
    
    return MusicSettingsPanel(
        music_manager,
        preferences_manager,
        width,
        height,
        on_volume_change,
        on_mute_change
    )
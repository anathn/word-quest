"""
Sound Settings Panel

UI component for configuring and previewing sound effects.
Implements STORY-005-03: Sound Preview Feature (Low Priority Suggestion)

Features:
- Preview individual sound effects
- Global SFX volume control
- Mute/unmute toggle
- Visual feedback when sounds play
- Volume testing with per-sound preview

Example:
    panel = SoundSettingsPanel(sound_manager)
    panel.render(screen)
    panel.handle_event(event)
"""

import pygame
from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass

from src.audio.sfx_config import SoundEvent, SFX_LIBRARY, DEFAULT_SFX_VOLUME, MIN_VOLUME, MAX_VOLUME
from src.audio.sound_manager import SoundManager, get_sound_manager


@dataclass
class SoundPreviewButton:
    """Represents a sound preview button."""
    event: SoundEvent
    label: str
    description: str
    rect: pygame.Rect
    preview_color: tuple = (76, 175, 80)
    hover_color: tuple = (100, 189, 100)
    playing: bool = False


class SoundSettingsPanel:
    """
    UI panel for sound effect configuration and preview.
    
    Features:
    - Preview all sound effects individually
    - Global SFX volume slider (0-100%)
    - Mute/unmute toggle
    - Visual feedback when sounds play
    - Default restore button
    
    Example:
        sound_manager = get_sound_manager()
        sound_manager.initialize()
        panel = SoundSettingsPanel(sound_manager)
        
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
    COLOR_PLAYING = (33, 150, 243)  # Blue for playing indicator
    COLOR_VOLUME_BG = (200, 200, 200)
    COLOR_VOLUME_FILL = (76, 175, 80)
    
    # Layout constants
    PADDING = 20
    SECTION_SPACING = 25
    BUTTON_HEIGHT = 45
    BUTTON_WIDTH = 140
    SLIDER_HEIGHT = 20
    SLIDER_HEIGHT_THICK = 30
    CHEVRON_SIZE = 40
    
    # Sound button layout (grid)
    BUTTONS_PER_ROW = 3
    BUTTON_SPACING_X = 15
    BUTTON_SPACING_Y = 15
    BUTTON_PADDING_X = 15
    
    def __init__(
        self,
        sound_manager: SoundManager,
        width: int = 600,
        on_volume_change: Optional[Callable[[float], None]] = None
    ):
        """
        Initialize sound settings panel.
        
        Args:
            sound_manager: SoundManager instance for playback
            width: Panel width in pixels
            on_volume_change: Callback when volume changes
        """
        self.sound_manager = sound_manager
        self.width = width
        self.height = 500
        self.on_volume_change = on_volume_change
        
        # Local volume state (mirrors sound_manager)
        self._global_volume = sound_manager.get_volume() if sound_manager else DEFAULT_SFX_VOLUME
        self._is_muted = sound_manager.is_muted() if sound_manager else False
        
        # UI state
        self._hovered_button: Optional[SoundPreviewButton] = None
        self._slider_dragging = False
        self._slider_drag_start_x = 0
        self._slider_start_volume = 0.0
        
        # Fonts (initialized on first render)
        self._title_font: Optional[pygame.font.Font] = None
        self._header_font: Optional[pygame.font.Font] = None
        self._body_font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None
        
        # UI element rects (calculated on render)
        self._sound_buttons: List[SoundPreviewButton] = []
        self._volume_slider_rect: Optional[pygame.Rect] = None
        self._mute_button_rect: Optional[pygame.Rect] = None
        self._restore_button_rect: Optional[pygame.Rect] = None
        
        # Sound descriptions for display
        self._sound_descriptions = {
            SoundEvent.CORRECT_ANSWER: "Major chord chime",
            SoundEvent.INCORRECT_ANSWER: "Gentle descending tone",
            SoundEvent.STREAK_3: "3-word streak celebration",
            SoundEvent.STREAK_5: "5-word streak fanfare",
            SoundEvent.PLANET_COMPLETE: "Planet completion victory",
            SoundEvent.BUTTON_CLICK: "UI button click",
            SoundEvent.PLANET_APPROACH: "Planet approach sound",
            SoundEvent.ROCKET_BONUS: "Rocket bonus sound",
        }
        
        # Playback tracking
        self._current_playing: Optional[SoundEvent] = None
        self._playing_timer: float = 0.0
    
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
        Render the sound settings panel.
        
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
        
        current_y = y_offset + 60
        
        # Check if audio is available
        if not self.sound_manager or not self.sound_manager.is_audio_available():
            self._draw_audio_unavailable(surface, x_offset, current_y)
            return
        
        # Draw volume controls
        current_y = self._draw_volume_section(surface, x_offset, current_y)
        
        # Draw preview section
        current_y = self._draw_preview_section(surface, x_offset, current_y)
        
        # Draw action buttons
        self._draw_action_buttons(surface, x_offset, current_y)
        
        # Render playing indicator
        self._render_playing_indicator(surface, x_offset, y_offset)
    
    def _draw_title(self, surface: pygame.Surface, x_offset: int, y_offset: int):
        """Draw panel title."""
        if not self._title_font:
            return
        
        title = "Sound Effects Settings"
        title_surf = self._title_font.render(title, True, self.COLOR_TEXT)
        title_rect = title_surf.get_rect(left=x_offset + self.PADDING, top=y_offset)
        surface.blit(title_surf, title_rect)
        
        # Subtitle
        if self._small_font:
            subtitle = "Preview and adjust sound effect volume"
            subtitle_surf = self._small_font.render(subtitle, True, self.COLOR_TEXT_LIGHT)
            subtitle_rect = subtitle_surf.get_rect(
                left=x_offset + self.PADDING, 
                top=y_offset + 28
            )
            surface.blit(subtitle_surf, subtitle_rect)
    
    def _draw_audio_unavailable(self, surface: pygame.Surface, x_offset: int, y_offset: int):
        """Draw message when audio is unavailable."""
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
            warning_text = "⚠️ Audio Unavailable"
            warning_surf = self._header_font.render(warning_text, True, (150, 100, 0))
            warning_surf_rect = warning_surf.get_rect(
                left=warning_rect.x + 15, top=warning_rect.y + 15
            )
            surface.blit(warning_surf, warning_surf_rect)
            
            # Instructions
            info_text = "Sound effects could not be initialized. Please check your audio settings."
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
        header_surf = self._header_font.render("Master Volume", True, self.COLOR_TEXT)
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
        effective_volume = 0.0 if self._is_muted else self._global_volume
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
        
        # Mute toggle button
        mute_text = "🔇 Muted" if self._is_muted else "🔊 Unmute"
        mute_button_width = 120
        mute_button_height = 35
        
        self._mute_button_rect = pygame.Rect(
            slider_x + slider_width - mute_button_width - 10,
            current_y,
            mute_button_width,
            mute_button_height
        )
        
        is_mute_hovered = self._mute_button_rect.collidepoint(pygame.mouse.get_pos())
        mute_color = (200, 200, 200) if is_mute_hovered else (180, 180, 180)
        
        pygame.draw.rect(surface, mute_color, self._mute_button_rect, border_radius=4)
        pygame.draw.rect(surface, self.COLOR_BORDER, self._mute_button_rect, 2, border_radius=4)
        
        if self._small_font:
            mute_surf = self._small_font.render(mute_text, True, self.COLOR_TEXT)
            mute_rect = mute_surf.get_rect(center=self._mute_button_rect.center)
            surface.blit(mute_surf, mute_rect)
        
        return current_y + self.SLIDER_HEIGHT_THICK + 35
    
    def _draw_preview_section(self, surface: pygame.Surface, x_offset: int, y_offset: int) -> int:
        """Draw sound preview buttons."""
        if not self._header_font:
            return y_offset
        
        # Section header
        header_surf = self._header_font.render("Preview Sounds", True, self.COLOR_TEXT)
        surface.blit(header_surf, (x_offset + self.PADDING, y_offset))
        
        current_y = y_offset + 35
        
        # Create sound button grid
        self._sound_buttons = []
        margin = 10
        
        # Calculate button sizes based on grid
        available_width = self.width - 2 * self.PADDING - 2 * margin
        total_button_spacing = (self.BUTTONS_PER_ROW - 1) * self.BUTTON_SPACING_X
        button_width = (available_width - total_button_spacing) // self.BUTTONS_PER_ROW
        button_height = 50
        
        for idx, (event, config) in enumerate(SFX_LIBRARY.items()):
            row = idx // self.BUTTONS_PER_ROW
            col = idx % self.BUTTONS_PER_ROW
            
            button_x = x_offset + self.PADDING + margin + col * (button_width + self.BUTTON_SPACING_X)
            button_y = current_y + row * (button_height + self.BUTTON_SPACING_Y)
            
            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            
            # Check if currently playing
            is_playing = self._current_playing == event
            
            button = SoundPreviewButton(
                event=event,
                label=self._get_button_label(event),
                description=self._sound_descriptions.get(event, ""),
                rect=button_rect,
                hover_color=self.COLOR_ACCENT_LIGHT,
                playing=is_playing
            )
            
            self._sound_buttons.append(button)
            
            # Draw button
            is_hovered = button_rect.collidepoint(pygame.mouse.get_pos())
            
            if is_playing:
                # Playing state - blue highlight
                button_color = self.COLOR_PLAYING
            elif is_hovered:
                button_color = button.hover_color
            else:
                button_color = button.preview_color
            
            # Button background
            pygame.draw.rect(surface, button_color, button_rect, border_radius=6)
            
            # Button border
            border_color = (255, 255, 255) if is_hovered or is_playing else self.COLOR_BORDER
            pygame.draw.rect(surface, border_color, button_rect, 2, border_radius=6)
            
            # Button label
            if self._body_font:
                label_surf = self._body_font.render(button.label, True, (255, 255, 255))
                label_rect = label_surf.get_rect(center=button_rect.center)
                surface.blit(label_surf, label_rect)
            
            # Playing indicator
            if is_playing and self._small_font:
                indicator_surf = self._small_font.render("▶ Playing", True, (255, 255, 255))
                indicator_rect = indicator_surf.get_rect(center=button_rect.center)
                indicator_rect.centery = button_rect.bottom + 18
                surface.blit(indicator_surf, indicator_rect)
        
        # Calculate total height needed
        num_buttons = len(self._sound_buttons)
        num_rows = (num_buttons + self.BUTTONS_PER_ROW - 1) // self.BUTTONS_PER_ROW
        
        return current_y + num_rows * (button_height + self.BUTTON_SPACING_Y) + 20
    
    def _draw_action_buttons(self, surface: pygame.Surface, x_offset: int, y_offset: int):
        """Draw restore default button."""
        if not self._body_font:
            return
        
        # Restore default volume button
        restore_button_width = 160
        restore_button_height = 35
        
        self._restore_button_rect = pygame.Rect(
            x_offset + self.PADDING,
            y_offset,
            restore_button_width,
            restore_button_height
        )
        
        is_restore_hovered = self._restore_button_rect.collidepoint(pygame.mouse.get_pos())
        restore_color = self.COLOR_ACCENT_LIGHT if is_restore_hovered else self.COLOR_ACCENT
        
        pygame.draw.rect(surface, restore_color, self._restore_button_rect, border_radius=4)
        pygame.draw.rect(surface, self.COLOR_BORDER, self._restore_button_rect, 2, border_radius=4)
        
        restore_text = "↺ Reset to Default (50%)"
        restore_surf = self._small_font.render(restore_text, True, (255, 255, 255))
        restore_rect = restore_surf.get_rect(center=self._restore_button_rect.center)
        surface.blit(restore_surf, restore_rect)
    
    def _render_playing_indicator(self, surface: pygame.Surface, x_offset: int, y_offset: int):
        """Timer for playing state reset."""
        pass  # Playing state is already rendered in preview section
    
    def update(self, delta_time: float):
        """
        Update panel state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        # Update playing timer
        if self._current_playing is not None:
            self._playing_timer += delta_time
            if self._playing_timer > 0.5:  # Reset after 500ms
                self._current_playing = None
                self._playing_timer = 0.0
    
    def _get_button_label(self, event: SoundEvent) -> str:
        """Get display label for sound event."""
        labels = {
            SoundEvent.CORRECT_ANSWER: "✓ Correct",
            SoundEvent.INCORRECT_ANSWER: "✗ Incorrect",
            SoundEvent.STREAK_3: "🔥 Streak 3",
            SoundEvent.STREAK_5: "⭐ Streak 5",
            SoundEvent.PLANET_COMPLETE: "🪐 Planet Done",
            SoundEvent.BUTTON_CLICK: "🖱️ Click",
            SoundEvent.PLANET_APPROACH: "🚀 Approach",
            SoundEvent.ROCKET_BONUS: "🎉 Bonus",
        }
        return labels.get(event, event.value)
    
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
            return True  # Always handle motion for hover effects
        
        return False
    
    def _handle_mouse_click(self, pos: tuple) -> bool:
        """Handle mouse click events."""
        # Sound preview buttons
        for button in self._sound_buttons:
            if button.rect.collidepoint(pos):
                self._play_sound_preview(button.event)
                return True
        
        # Mute toggle
        if self._mute_button_rect and self._mute_button_rect.collidepoint(pos):
            self._toggle_mute()
            return True
        
        # Restore default button
        if self._restore_button_rect and self._restore_button_rect.collidepoint(pos):
            self._restore_default()
            return True
        
        # Volume slider click
        if self._volume_slider_rect and self._volume_slider_rect.collidepoint(pos):
            self._slider_dragging = True
            self._slider_drag_start_x = pos[0]
            self._slider_start_volume = self._global_volume if not self._is_muted else 0.0
            self._update_volume_from_slider(pos[0])
            return True
        
        return False
    
    def _handle_mouse_up(self, pos: tuple) -> bool:
        """Handle mouse up events."""
        if self._slider_dragging:
            self._slider_dragging = False
            return True
        return False
    
    def _handle_mouse_motion(self, pos: tuple):
        """Handle mouse motion for hover effects."""
        # Check sound button hovers
        for button in self._sound_buttons:
            if button.rect.collidepoint(pos):
                self._hovered_button = button
                break
        else:
            self._hovered_button = None
    
    def _play_sound_preview(self, event: SoundEvent):
        """Play a sound for preview."""
        if not self.sound_manager:
            return
        
        if self._is_muted:
            return
        
        # Set current playing for visual feedback
        self._current_playing = event
        self._playing_timer = 0.0
        
        # Play sound
        if not self.sound_manager.is_initialized():
            self.sound_manager.initialize()
        
        if self.sound_manager.is_audio_available():
            # Use full volume for preview for clear feedback
            self.sound_manager.play(event, volume_override=0.8)
    
    def _toggle_mute(self):
        """Toggle mute state."""
        if not self.sound_manager:
            return
        
        self._is_muted = not self._is_muted
        self.sound_manager.mute() if self._is_muted else self.sound_manager.unmute()
    
    def _restore_default(self):
        """Restore volume to default."""
        if not self.sound_manager:
            return
        
        self._global_volume = DEFAULT_SFX_VOLUME
        self._is_muted = False
        self.sound_manager.set_volume(DEFAULT_SFX_VOLUME)
        self.sound_manager.unmute()
        
        # Callback
        if self.on_volume_change:
            self.on_volume_change(DEFAULT_SFX_VOLUME)
    
    def _update_volume_from_slider(self, x_position: int):
        """Update volume based on slider position."""
        if not self._volume_slider_rect or not self.sound_manager:
            return
        
        slider_x = self._volume_slider_rect.x
        slider_width = self._volume_slider_rect.width
        
        # Calculate position within slider (0.0 to 1.0)
        position = (x_position - slider_x) / slider_width
        position = max(0.0, min(1.0, position))
        
        # Update volume
        self._global_volume = position
        
        if not self._is_muted:
            self.sound_manager.set_volume(position)
        
        # Callback
        if self.on_volume_change:
            self.on_volume_change(position)
    
    def get_rect(self) -> pygame.Rect:
        """
        Get panel bounding rectangle.
        
        Returns:
            Rect covering the panel
        """
        return pygame.Rect(0, 0, self.width, self.height)
    
    def set_volume(self, volume: float):
        """
        Set volume from external source.
        
        Args:
            volume: Volume level 0.0 to 1.0
        """
        self._global_volume = volume
        if self.sound_manager:
            self.sound_manager.set_volume(volume)
    
    def get_volume(self) -> float:
        """
        Get current volume level.
        
        Returns:
            Volume level 0.0 to 1.0
        """
        return self._global_volume


def create_sound_settings_panel(
    sound_manager: Optional[SoundManager] = None,
    width: int = 600,
    on_volume_change: Optional[Callable[[float], None]] = None
) -> SoundSettingsPanel:
    """
    Factory function to create a SoundSettingsPanel.
    
    Args:
        sound_manager: SoundManager instance (auto-created if None)
        width: Panel width
        on_volume_change: Callback when volume changes
        
    Returns:
        Configured SoundSettingsPanel
    """
    if sound_manager is None:
        sound_manager = get_sound_manager()
    
    return SoundSettingsPanel(sound_manager, width, on_volume_change)
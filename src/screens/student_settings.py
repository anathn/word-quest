"""
Student Settings Screen (STORY-004-05)

Settings screen for student profile customization including rocket color selection.
Provides UI for personalization options.
"""

import pygame
from typing import Optional, List
import sys

from src.models.rocket_colors import DEFAULT_ROCKET_COLOR, ROCKET_COLOR_PRESETS
from src.ui.color_picker import ColorPicker
from src.ui.typography import Typography
from src.profiles.profile_manager import ProfileManager


class StudentSettingsScreen:
    """
    Settings screen for student customization.
    
    Features:
    - Rocket color picker with 8 preset options
    - Real-time rocket preview
    - Save/Cancel buttons
    - Integration with student profile system
    
    Args:
        screen: Pygame surface for rendering
        profile_manager: ProfileManager instance for saving changes
        profile_id: ID of the profile being edited
    """
    
    # UI Layout constants
    HEADER_HEIGHT = 60
    COLOR_PICKER_Y = 80
    ROCKET_PREVIEW_Y = 260
    BUTTON_Y = 380
    BUTTON_HEIGHT = 40
    MARGIN_X = 50
    
    # Colors
    BACKGROUND_COLOR = (26, 26, 62)  # Deep space blue #1a1a3e
    PANEL_COLOR = (40, 40, 80)       # Slightly lighter panel
    TEXT_COLOR = (255, 255, 255)
    BUTTON_COLOR = (68, 136, 255)    # Blue #4488FF
    BUTTON_HOVER_COLOR = (88, 156, 255)
    BUTTON_TEXT_COLOR = (255, 255, 255)
    CANCEL_BUTTON_COLOR = (176, 176, 176)  # Grey
    
    def __init__(self, screen: pygame.Surface, profile_manager: ProfileManager, profile_id: str):
        """
        Initialize the settings screen.
        
        Args:
            screen: Pygame surface for rendering
            profile_manager: ProfileManager instance
            profile_id: ID of profile to edit
        """
        self.screen = screen
        self.profile_manager = profile_manager
        self.profile_id = profile_id
        self.running = True
        
        # Load current profile data
        profile = profile_manager.get_profile(profile_id)
        if profile:
            self.current_rocket_color = profile.rocket_color
        else:
            self.current_rocket_color = DEFAULT_ROCKET_COLOR
        
        # Get screen dimensions
        self.screen_width, self.screen_height = screen.get_size()
        
        # Calculate color picker position (centered)
        picker_width = 4 * (ColorPicker.SWATCH_SIZE[0] + ColorPicker.SPACING) - ColorPicker.SPACING
        picker_x = (self.screen_width - picker_width) // 2
        
        # Initialize color picker
        self.color_picker = ColorPicker(self.screen, picker_x, self.COLOR_PICKER_Y)
        self.color_picker.selected_color = self.current_rocket_color
        
        # Set up callback for color selection
        def on_color_change(hex_color: str):
            self.current_rocket_color = hex_color
        self.color_picker.on_color_selected = on_color_change
        
        # Initialize rocket preview
        self.rocket_preview_rect = pygame.Rect(0, 0, 80, 120)
        self.rocket_preview_rect.centerx = self.screen_width // 2
        self.rocket_preview_rect.top = self.ROCKET_PREVIEW_Y
        
        # Button definitions
        self.save_button = pygame.Rect(
            self.screen_width // 2 - 160,
            self.BUTTON_Y,
            120,
            self.BUTTON_HEIGHT
        )
        self.cancel_button = pygame.Rect(
            self.screen_width // 2 + 40,
            self.BUTTON_Y,
            120,
            self.BUTTON_HEIGHT
        )
        
        # Hover states
        self._save_hover = False
        self._cancel_hover = False
        
        # Font for header
        self._header_font = Typography.get_font("heading", 32)
        self._label_font = Typography.get_font("body", 24)
        
        # Simple rocket preview surface
        self._rocket_preview_surf = self._create_rocket_preview()
    
    def _create_rocket_preview(self) -> pygame.Surface:
        """
        Create a simple rocket preview sprite.
        
        Returns:
            pygame.Surface with rocket graphic
        """
        surf = pygame.Surface((80, 120), pygame.SRCALPHA)
        
        # Rocket body
        body_points = [
            (40, 10),   # Top tip
            (60, 50),   # Right shoulder
            (55, 90),   # Right bottom
            (25, 90),   # Left bottom
            (20, 50),   # Left shoulder
        ]
        pygame.draw.polygon(surf, (240, 240, 240), body_points)
        
        # Window
        pygame.draw.circle(surf, (135, 206, 235), (40, 35), 12)
        pygame.draw.circle(surf, (100, 150, 180), (40, 35), 12, 2)
        
        # Fins
        fin_left = [(20, 60), (5, 95), (25, 88)]
        fin_right = [(60, 60), (75, 95), (55, 88)]
        pygame.draw.polygon(surf, (200, 200, 200), fin_left)
        pygame.draw.polygon(surf, (200, 200, 200), fin_right)
        
        return surf
    
    def _apply_color_to_preview(self, surface: pygame.Surface) -> pygame.Surface:
        """
        Apply the current rocket color to the preview sprite.
        
        Args:
            surface: Base rocket surface
            
        Returns:
            Tinted copy of the surface
        """
        # Parse hex to RGB
        hex_color = self.current_rocket_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Create tinted copy
        tinted = surface.copy()
        tint_r, tint_g, tint_b = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
        
        for x in range(tinted.get_width()):
            for y in range(tinted.get_height()):
                pixel = tinted.get_at((x, y))
                if pixel.a > 0:
                    r = min(255, int(pixel.r * tint_r))
                    g = min(255, int(pixel.g * tint_g))
                    b = min(255, int(pixel.b * tint_b))
                    tinted.set_at((x, y), pygame.Color(r, g, b, pixel.a))
        
        return tinted
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events.
        
        Args:
            event: Pygame event to process
            
        Returns:
            True if event was handled
        """
        # Update hover states for buttons
        mouse_pos = pygame.mouse.get_pos()
        self._save_hover = self.save_button.collidepoint(mouse_pos)
        self._cancel_hover = self.cancel_button.collidepoint(mouse_pos)
        
        # Handle color picker events
        if self.color_picker.handle_event(event):
            return True
        
        # Handle button clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.save_button.collidepoint(event.pos):
                    self._save_changes()
                    return True
                elif self.cancel_button.collidepoint(event.pos):
                    self.running = False
                    return True
        
        return False
    
    def _save_changes(self):
        """Save the rocket color change to the profile."""
        try:
            self.profile_manager.update_profile(
                profile_id=self.profile_id,
                rocket_color=self.current_rocket_color
            )
            # Exit screen after saving
            self.running = False
        except ValueError as e:
            # In a real implementation, show error message
            print(f"Error saving profile: {e}")
            import traceback
            traceback.print_exc()
    
    def render(self):
        """Render the settings screen."""
        # Fill background
        self.screen.fill(self.BACKGROUND_COLOR)
        
        # Draw header
        header_text = Typography.render(self._header_font, "Rocket Customization", self.TEXT_COLOR)
        header_rect = header_text.get_rect(centerx=self.screen_width // 2, top=20)
        self.screen.blit(header_text, header_rect)
        
        # Draw "Choose your rocket color" label
        label_text = Typography.render(self._label_font, "Choose your rocket color:", self.TEXT_COLOR)
        label_rect = label_text.get_rect(centerx=self.screen_width // 2, top=self.COLOR_PICKER_Y - 35)
        self.screen.blit(label_text, label_rect)
        
        # Render color picker
        self.color_picker.render()
        
        # Draw rocket preview section
        preview_label = Typography.render(self._label_font, "Preview:", self.TEXT_COLOR)
        preview_label_rect = preview_label.get_rect(centerx=self.screen_width // 2, top=self.ROCKET_PREVIEW_Y - 30)
        self.screen.blit(preview_label, preview_label_rect)
        
        # Render rocket preview with current color
        preview_surf = self._apply_color_to_preview(self._rocket_preview_surf)
        self.screen.blit(preview_surf, self.rocket_preview_rect.topleft)
        
        # Draw current color name
        color_name = self._get_color_name(self.current_rocket_color)
        color_text = Typography.render(self._label_font, f"Current: {color_name}", self.TEXT_COLOR)
        color_rect = color_text.get_rect(centerx=self.screen_width // 2, top=self.ROCKET_PREVIEW_Y + 100)
        self.screen.blit(color_text, color_rect)
        
        # Draw buttons
        self._draw_button(self.save_button, "Save", self.BUTTON_COLOR, self._save_hover)
        self._draw_button(self.cancel_button, "Cancel", self.CANCEL_BUTTON_COLOR, self._cancel_hover)
    
    def _get_color_name(self, hex_color: str) -> str:
        """
        Get the display name for a color.
        
        Args:
            hex_color: Hex color string
            
        Returns:
            Color name string
        """
        for color_data in ROCKET_COLOR_PRESETS:
            if color_data["hex"].upper() == hex_color.upper():
                return color_data["name"]
        return hex_color
    
    def _draw_button(self, rect: pygame.Rect, text: str, color: tuple, hover: bool):
        """
        Draw a button.
        
        Args:
            rect: Button rectangle
            text: Button label
            color: Button background color
            hover: Whether mouse is hovering
        """
        # Button background
        bg_color = self.BUTTON_HOVER_COLOR if hover else color
        button_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(button_surf, bg_color, (0, 0, rect.width, rect.height), border_radius=8)
        
        # Button border
        border_color = (255, 255, 255) if hover else (200, 200, 200)
        pygame.draw.rect(button_surf, border_color, (0, 0, rect.width, rect.height), 2, border_radius=8)
        
        self.screen.blit(button_surf, rect.topleft)
        
        # Button text
        button_font = Typography.get_font("heading", 20)
        text_surface = Typography.render(button_font, text, self.BUTTON_TEXT_COLOR)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
    
    def is_running(self) -> bool:
        """
        Check if the screen is still running.
        
        Returns:
            True if screen should continue running
        """
        return self.running


def create_student_settings_screen(
    screen: pygame.Surface,
    profile_manager: ProfileManager,
    profile_id: str
) -> StudentSettingsScreen:
    """
    Factory function to create a StudentSettingsScreen instance.
    
    Args:
        screen: Pygame surface for rendering
        profile_manager: ProfileManager instance
        profile_id: ID of profile to edit
        
    Returns:
        Configured StudentSettingsScreen instance
    """
    return StudentSettingsScreen(screen, profile_manager, profile_id)
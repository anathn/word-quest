"""
Color Picker Component (STORY-004-05)

UI component for selecting rocket colors with preset options.
Provides a grid of color swatches with accessibility features.

This module re-exports color constants from src.models.rocket_colors
to maintain backwards compatibility.
"""

import pygame
from typing import Optional, Callable

# Re-export from shared module to avoid circular imports
from src.models.rocket_colors import (
    ROCKET_COLOR_PRESETS,
    DEFAULT_ROCKET_COLOR,
    hex_to_rgb,
    rgb_to_hex
)


class ColorPicker:
    """
    Color selection UI component with preset swatches.
    
    Displays a grid of color options with names and selection indicators.
    Supports mouse clicks and visual feedback for hover/selection states.
    
    Attributes:
        screen: Pygame surface to render on
        position: Top-left corner (x, y)
        selected_color: Currently selected color hex string
        colors: List of color preset dictionaries
        swatch_size: Dimensions of each color swatch (width, height)
        spacing: Gap between swatches in pixels
    """
    
    # Visual constants
    SWATCH_SIZE = (60, 60)
    SPACING = 10
    GRID_COLS = 4
    BORDER_WIDTH = 3
    BORDER_SELECTED = (255, 255, 255)  # White border for selected
    BORDER_HOVER = (200, 200, 200)  # Grey border for hover
    
    def __init__(self, screen: pygame.Surface, x: int, y: int):
        """
        Initialize the color picker.
        
        Args:
            screen: Pygame surface to render on
            x: X position (top-left corner)
            y: Y position (top-left corner)
        """
        self.screen = screen
        self.position = (x, y)
        self.selected_color = DEFAULT_ROCKET_COLOR
        self.colors = ROCKET_COLOR_PRESETS
        self._hover_index: Optional[int] = None
        
        # Callback for color selection events
        self.on_color_selected: Optional[Callable[[str], None]] = None
        
        # Font for color names
        self._font = pygame.font.Font(None, 24)
    
    def _get_swatch_rect(self, index: int) -> pygame.Rect:
        """
        Get the rectangular bounds of a color swatch.
        
        Args:
            index: Index into the colors list
            
        Returns:
            pygame.Rect representing the swatch area
        """
        row = index // self.GRID_COLS
        col = index % self.GRID_COLS
        
        x = self.position[0] + col * (self.SWATCH_SIZE[0] + self.SPACING)
        y = self.position[1] + row * (self.SWATCH_SIZE[1] + self.SPACING)
        
        return pygame.Rect(x, y, *self.SWATCH_SIZE)
    
    def render(self):
        """
        Draw the color picker grid.
        
        Renders all color swatches with:
        - Colored rectangle for the swatch
        - White border if selected
        - Grey border if hovered
        - Color name text below each swatch
        """
        for i, color_data in enumerate(self.colors):
            rect = self._get_swatch_rect(i)
            
            # Draw swatch background
            pygame.draw.rect(self.screen, color_data["rgb"], rect)
            
            # Draw border
            if color_data["hex"] == self.selected_color:
                # Selected: white border
                border_rect = rect.inflate(self.BORDER_WIDTH * 2, self.BORDER_WIDTH * 2)
                pygame.draw.rect(self.screen, self.BORDER_SELECTED, border_rect, self.BORDER_WIDTH)
            elif i == self._hover_index:
                # Hovered: grey border
                border_rect = rect.inflate(self.BORDER_WIDTH, self.BORDER_WIDTH)
                pygame.draw.rect(self.screen, self.BORDER_HOVER, border_rect, self.BORDER_WIDTH)
            
            # Draw color name below swatch
            color_name = color_data["name"]
            text_surface = self._font.render(color_name, True, (255, 255, 255))
            text_rect = text_surface.get_rect(
                centerx=rect.centerx,
                top=rect.bottom + 4
            )
            self.screen.blit(text_surface, text_rect)
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events for color selection.
        
        Processes mouse clicks and hover events.
        
        Args:
            event: Pygame event to process
            
        Returns:
            True if event was handled, False otherwise
        """
        if event.type == pygame.MOUSEMOTION:
            # Update hover state
            self._hover_index = self._get_hover_index(event.pos)
            return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                clicked_index = self._get_hover_index(event.pos)
                if clicked_index is not None:
                    self.select_color(self.colors[clicked_index]["hex"])
                    return True
        
        return False
    
    def _get_hover_index(self, pos: tuple) -> Optional[int]:
        """
        Determine which swatch is under the cursor.
        
        Args:
            pos: Mouse position (x, y)
            
        Returns:
            Index of swatch under cursor, or None if outside grid
        """
        for i, _ in enumerate(self.colors):
            rect = self._get_swatch_rect(i)
            if rect.collidepoint(pos):
                return i
        return None
    
    def select_color(self, hex_color: str):
        """
        Change the selected color.
        
        Args:
            hex_color: Hex color string (e.g., "#FF4444")
        """
        self.selected_color = hex_color
        
        # Trigger callback if set
        if self.on_color_selected:
            self.on_color_selected(hex_color)
    
    def get_selected_color(self) -> str:
        """
        Get the currently selected color.
        
        Returns:
            Hex color string
        """
        return self.selected_color
    
    def get_bounds(self) -> pygame.Rect:
        """
        Get the bounding rectangle of the entire color picker.
        
        Returns:
            pygame.Rect covering all swatches
        """
        total_width = self.GRID_COLS * self.SWATCH_SIZE[0] + (self.GRID_COLS - 1) * self.SPACING
        total_height = 2 * self.SWATCH_SIZE[1] + self.SPACING  # 2 rows for 8 colors
        
        return pygame.Rect(
            self.position[0],
            self.position[1],
            total_width,
            total_height
        )


def create_color_picker(screen: pygame.Surface, x: int, y: int) -> ColorPicker:
    """
    Factory function to create a ColorPicker instance.
    
    Args:
        screen: Pygame surface to render on
        x: X position
        y: Y position
        
    Returns:
        Configured ColorPicker instance
    """
    return ColorPicker(screen, x, y)
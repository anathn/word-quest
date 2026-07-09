"""
Accuracy Display Component

Renders accuracy rates with trend indicators for both parent and student views.

This component implements the UI portion of STORY-002-04: Accuracy Rate Calculation.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class AccuracyDisplayConfig:
    """Configuration for accuracy display styling."""
    # Colors
    improving_color: str = "#4CAF50"  # Green
    stable_color: str = "#2196F3"     # Blue
    declining_color: str = "#FF9800"  # Orange
    new_color: str = "#9E9E9E"        # Grey
    
    # Text sizes (for pygame fonts)
    percentage_size: int = 48
    label_size: int = 24
    trend_size: int = 28
    
    # Layout
    show_text_label: bool = True  # Show "Improving" in addition to arrow
    show_percentage: bool = True  # Show percentage value


class AccuracyDisplay:
    """
    Renders accuracy information with trend indicators.
    
    Provides both detailed parent view and simplified student view.
    """
    
    def __init__(
        self,
        progress_tracker,
        config: Optional[AccuracyDisplayConfig] = None
    ):
        """
        Initialize the accuracy display.
        
        Args:
            progress_tracker: ProgressTracker instance for data
            config: Optional display configuration
        """
        self.progress_tracker = progress_tracker
        self.config = config or AccuracyDisplayConfig()
        
        # Font cache (initialized on first render)
        self._fonts = {}
        self._pygame_imported = False
    
    def _ensure_pygame_imported(self):
        """Conditionally import pygame fonts."""
        if not self._pygame_imported:
            try:
                import pygame
                if 'pygame' not in globals():
                    globals()['pygame'] = pygame
                self._pygame_imported = True
            except ImportError:
                # pygame not available, use mock implementation
                self._pygame_imported = False
    
    def _get_font(self, size: int, bold: bool = False) -> Optional['pygame.font.Font']:
        """
        Get a pygame font object.
        
        Args:
            size: Font size in points
            bold: Whether to use bold font
            
        Returns:
            Font object or None if pygame not available
        """
        self._ensure_pygame_imported()
        
        if not self._pygame_imported:
            return None
        
        import pygame
        font_key = (size, bold)
        
        if font_key not in self._fonts:
            try:
                if bold:
                    self._fonts[font_key] = pygame.font.SysFont('Arial', size, bold=True)
                else:
                    self._fonts[font_key] = pygame.font.SysFont('Arial', size)
            except Exception:
                # Font creation failed
                return None
        
        return self._fonts[font_key]
    
    def get_color_for_trend(self, trend: str) -> str:
        """
        Get the appropriate color for a trend value.
        
        Args:
            trend: Trend value ("improving", "stable", "declining", "new")
            
        Returns:
            Color hex string
        """
        color_map = {
            "improving": self.config.improving_color,
            "stable": self.config.stable_color,
            "declining": self.config.declining_color,
            "new": self.config.new_color
        }
        return color_map.get(trend, self.config.new_color)
    
    def get_display_data(self) -> Dict:
        """
        Get all data needed for display.
        
        Returns:
            Dictionary containing:
            - percentage: Accuracy percentage
            - trend_symbol: Arrow symbol
            - trend_label: Text description
            - trend: Raw trend value
            - color: Appropriate color hex for current trend
        """
        display_data = self.progress_tracker.get_accuracy_display()
        display_data['color'] = self.get_color_for_trend(display_data['trend'])
        return display_data
    
    def render_student_view(self, surface, x: int, y: int):
        """
        Render simplified accuracy display for students.
        
        Student view shows encouraging message instead of raw numbers.
        
        Args:
            surface: Pygame surface to render on
            x: X coordinate
            y: Y coordinate
        """
        # Import pygame for rendering
        try:
            import pygame
        except ImportError:
            # Mock for testing without pygame
            return
        
        display_data = self.get_display_data()
        trend = display_data['trend']
        
        # Choose encouraging message based on trend
        if trend == "improving":
            message = "Great Progress!"
        elif trend == "stable":
            message = "Keep it Up!"
        elif trend == "declining":
            message = "Let's Practice More!"
        else:
            message = "New!"
        
        # Render message
        font = self._get_font(self.config.label_size)
        if font:
            text_surface = font.render(message, True, (255, 255, 255))
            surface.blit(text_surface, (x, y))
    
    def render_parent_view(
        self,
        surface,
        x: int,
        y: int,
        include_trend: bool = True,
        include_comparison: bool = True
    ):
        """
        Render detailed accuracy display for parents.
        
        Parent view shows percentage, trend arrow, and text label.
        
        Args:
            surface: Pygame surface to render on
            x: X coordinate
            y: Y coordinate
            include_trend: Whether to show trend indicator
            include_comparison: Whether to show comparison details
        """
        # Import pygame for rendering
        try:
            import pygame
        except ImportError:
            # Mock for testing without pygame
            return
        
        display_data = self.get_display_data()
        percentage = display_data['percentage']
        trend = display_data['trend']
        trend_symbol = display_data['trend_symbol']
        trend_label = display_data['trend_label']
        color = display_data['color']
        
        # Parse color for pygame
        color_tuple = self._parse_color(color)
        
        # Render percentage
        if self.config.show_percentage:
            percentage_text = f"{percentage}%"
            font = self._get_font(self.config.percentage_size, bold=True)
            if font:
                text_surface = font.render(percentage_text, True, (255, 255, 255))
                surface.blit(text_surface, (x, y))
        
        # Render trend indicator
        if include_trend:
            trend_x = x + (100 if self.config.show_percentage else 0)
            
            if self.config.show_text_label:
                # Show both arrow and text
                trend_text = f"{trend_symbol} {trend_label}"
            else:
                trend_text = trend_symbol
            
            font = self._get_font(self.config.trend_size)
            if font:
                text_surface = font.render(trend_text, True, color_tuple)
                # Show trend below percentage
                surface.blit(text_surface, (trend_x, y + 60))
        
        # Render comparison details
        if include_comparison:
            comparison = self.progress_tracker.get_accuracy_comparison()
            comparison_y = y + 120
            
            prev_label = f"Prev Session: {comparison['previous_session_accuracy']}%"
            font = self._get_font(self.config.label_size)
            if font:
                text_surface = font.render(prev_label, True, (200, 200, 200))
                surface.blit(text_surface, (x, comparison_y))
            
            weekly_label = f"Weekly Avg: {comparison['weekly_average_accuracy']}%"
            if font:
                text_surface = font.render(weekly_label, True, (200, 200, 200))
                surface.blit(text_surface, (x, comparison_y + 30))
    
    def _parse_color(self, color_hex: str) -> tuple:
        """
        Parse a hex color string to RGB tuple.
        
        Args:
            color_hex: Hex color string (e.g., "#4CAF50")
            
        Returns:
            RGB tuple (r, g, b)
        """
        color_hex = color_hex.lstrip('#')
        return tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    
    def get_widget_data(self) -> Dict:
        """
        Get widget data for non- pygame rendering (e.g., web, text).
        
        Returns:
            Dictionary with all display data formatted for widget rendering
        """
        display_data = self.get_display_data()
        comparison = self.progress_tracker.get_accuracy_comparison()
        
        return {
            **display_data,
            **comparison,
            'color_name': {
                "improving": "green",
                "stable": "blue", 
                "declining": "orange",
                "new": "grey"
            }.get(display_data['trend'], "grey")
        }


def create_accuracy_display(
    progress_tracker,
    config: Optional[AccuracyDisplayConfig] = None
) -> AccuracyDisplay:
    """
    Factory function to create an AccuracyDisplay instance.
    
    Args:
        progress_tracker: ProgressTracker instance
        config: Optional display configuration
        
    Returns:
        Configured AccuracyDisplay instance
    """
    return AccuracyDisplay(progress_tracker, config)
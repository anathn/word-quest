"""
Trend Graph Component

Renders line graphs for weekly trend visualization.
Implements STORY-003-05: Weekly Summary View
"""

import pygame
from typing import List, Optional, Tuple
from datetime import date

from src.models.summary_data import WeeklySummary


class TrendGraph:
    """
    Pygame line graph component for displaying trend data.
    
    Renders weekly metrics as a line graph with axes, labels, and data points.
    """
    
    # Colors
    COLOR_LINE = (64, 128, 255)
    COLOR_FILL = (64, 128, 255, 64)
    COLOR_GRID = (220, 220, 230)
    COLOR_AXIS = (100, 100, 120)
    COLOR_TEXT = (50, 50, 70)
    COLOR_POINT = (76, 175, 80)
    
    def __init__(self, width: int = 400, height: int = 200):
        """
        Initialize the trend graph.
        
        Args:
            width: Graph width in pixels
            height: Graph height in pixels
        """
        self.width = width
        self.height = height
        self.padding = 40
        self.graph_width = width - (2 * self.padding)
        self.graph_height = height - (2 * self.padding)
        
        # Fonts (initialized on first render)
        self._title_font: Optional[pygame.font.Font] = None
        self._label_font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None
    
    def _init_fonts(self):
        """Initialize Pygame fonts."""
        if self._title_font is None:
            try:
                self._title_font = pygame.font.SysFont('arial', 16, bold=True)
                self._label_font = pygame.font.SysFont('arial', 13)
                self._small_font = pygame.font.SysFont('arial', 11)
            except Exception:
                self._title_font = pygame.font.Font(None, 16)
                self._label_font = pygame.font.Font(None, 13)
                self._small_font = pygame.font.Font(None, 11)
    
    def draw(self, surface: pygame.Surface, summaries: List[WeeklySummary], 
             metric: str = "accuracy_rate", title: str = "Progress Trend"):
        """
        Draw trend line graph for a metric.
        
        Args:
            surface: Pygame surface to draw on
            summaries: List of WeeklySummary objects (4 weeks)
            metric: Metric to graph ("accuracy_rate" or "words_mastered")
            title: Graph title
        """
        self._init_fonts()
        
        # Clear the surface
        surface.fill((255, 255, 255))
        
        if not summaries or not any(s.has_data() for s in summaries):
            self._draw_empty_message(surface)
            return
        
        # Calculate data points
        data_points: List[Tuple[int, float]] = []
        labels: List[str] = []
        
        for i, summary in enumerate(summaries):
            if metric == "accuracy_rate":
                value = summary.accuracy_rate * 100  # Convert to percentage
            elif metric == "words_mastered":
                value = float(summary.words_mastered)
            else:
                value = 0.0
            
            data_points.append((i, value))
            labels.append(self._format_week_label(summary.week_start))
        
        # Determine Y-axis range
        values = [dp[1] for dp in data_points]
        max_value = max(values) if values else 100
        min_value = min(values) if values else 0
        
        # Add padding to Y-axis
        value_range = max_value - min_value if max_value != min_value else 100
        y_min = max(0, min_value - value_range * 0.1)
        y_max = max_value + value_range * 0.1
        
        # Draw components
        self._draw_title(surface, title)
        self._draw_axes(surface)
        self._draw_grid(surface, y_min, y_max)
        self._draw_line(surface, data_points, y_min, y_max)
        self._draw_labels(surface, labels, y_min, y_max)
        self._draw_points(surface, data_points, y_min, y_max)
    
    def _format_week_label(self, week_start: date) -> str:
        """Format week start date as label."""
        # Show week number and month
        week_num = week_start.isocalendar()[1]
        month = week_start.strftime("%b")
        return f"W{week_num:02d}"
    
    def _draw_title(self, surface: pygame.Surface, title: str):
        """Draw graph title."""
        if self._title_font:
            title_surf = self._title_font.render(title, True, self.COLOR_TEXT)
            title_rect = title_surf.get_rect(centerx=self.width // 2, top=5)
            surface.blit(title_surf, title_rect)
    
    def _draw_axes(self, surface: pygame.Surface):
        """Draw X and Y axes."""
        # Y-axis
        y_axis_x = self.padding
        pygame.draw.line(surface, self.COLOR_AXIS,
                        (y_axis_x, self.padding),
                        (y_axis_x, self.height - self.padding),
                        2)
        
        # X-axis
        x_axis_y = self.height - self.padding
        pygame.draw.line(surface, self.COLOR_AXIS,
                        (self.padding, x_axis_y),
                        (self.width - self.padding, x_axis_y),
                        2)
    
    def _draw_grid(self, surface: pygame.Surface, y_min: float, y_max: float):
        """Draw grid lines."""
        # Horizontal grid lines (5 lines including 0 and max)
        num_grid_lines = 5
        for i in range(num_grid_lines):
            y_value = y_min + (y_max - y_min) * i / (num_grid_lines - 1)
            y_pixel = self.height - self.padding - int(
                (y_value - y_min) / (y_max - y_min) * self.graph_height
            ) if y_max != y_min else self.height - self.padding
            
            # Grid line
            pygame.draw.line(surface, self.COLOR_GRID,
                           (self.padding, y_pixel),
                           (self.width - self.padding, y_pixel),
                           1)
            
            # Y-axis label
            if self._small_font:
                label = f"{y_value:.0f}"
                label_surf = self._small_font.render(label, True, self.COLOR_AXIS)
                label_rect = label_surf.get_rect(right=self.padding - 5, centery=y_pixel)
                surface.blit(label_surf, label_rect)
    
    def _draw_line(self, surface: pygame.Surface, data_points: List[Tuple[int, float]],
                   y_min: float, y_max: float):
        """Draw the trend line connecting data points."""
        if len(data_points) < 2:
            return
        
        # Calculate pixel positions
        point_pixels: List[Tuple[int, int]] = []
        for i, (_, value) in enumerate(data_points):
            x_pixel = self.padding + (i / (len(data_points) - 1)) * self.graph_width if len(data_points) > 1 else self.padding
            y_pixel = self.height - self.padding - int(
                (value - y_min) / (y_max - y_min) * self.graph_height
            ) if y_max != y_min else self.height - self.padding
            point_pixels.append((x_pixel, y_pixel))
        
        # Draw line segments
        if len(point_pixels) >= 2:
            for i in range(len(point_pixels) - 1):
                pygame.draw.line(surface, self.COLOR_LINE,
                               point_pixels[i],
                               point_pixels[i + 1],
                               3)
    
    def _draw_points(self, surface: pygame.Surface, data_points: List[Tuple[int, float]],
                     y_min: float, y_max: float):
        """Draw data points on the line."""
        for i, (_, value) in enumerate(data_points):
            x_pixel = self.padding + (i / (len(data_points) - 1)) * self.graph_width if len(data_points) > 1 else self.padding
            y_pixel = self.height - self.padding - int(
                (value - y_min) / (y_max - y_min) * self.graph_height
            ) if y_max != y_min else self.height - self.padding
            
            # Draw point circle
            pygame.draw.circle(surface, self.COLOR_POINT, (int(x_pixel), int(y_pixel)), 6)
            pygame.draw.circle(surface, (255, 255, 255), (int(x_pixel), int(y_pixel)), 3)
            
            # Draw value label above point
            if self._small_font:
                value_label = f"{value:.1f}"
                value_surf = self._small_font.render(value_label, True, self.COLOR_TEXT)
                value_rect = value_surf.get_rect(centerx=int(x_pixel), bottom=int(y_pixel) - 8)
                surface.blit(value_surf, value_rect)
    
    def _draw_labels(self, surface: pygame.Surface, labels: List[str],
                     y_min: float, y_max: float):
        """Draw X-axis labels."""
        if not self._small_font:
            return
        
        # X-axis labels
        for i, label in enumerate(labels):
            x_pixel = self.padding + (i / (len(labels) - 1)) * self.graph_width if len(labels) > 1 else self.padding
            
            label_surf = self._small_font.render(label, True, self.COLOR_TEXT)
            label_rect = label_surf.get_rect(centerx=int(x_pixel), top=self.height - self.padding + 5)
            surface.blit(label_surf, label_rect)
    
    def _draw_empty_message(self, surface: pygame.Surface):
        """Draw 'No data available' message."""
        if self._label_font:
            message = "No practice data for this period"
            message_surf = self._label_font.render(message, True, self.COLOR_AXIS)
            message_rect = message_surf.get_rect(center=(self.width // 2, self.height // 2))
            surface.blit(message_surf, message_rect)
            
            if self._small_font:
                hint = "Complete some practice sessions to see trends"
                hint_surf = self._small_font.render(hint, True, self.COLOR_GRID)
                hint_rect = hint_surf.get_rect(center=(self.width // 2, self.height // 2 + 20))
                surface.blit(hint_surf, hint_rect)


def create_trend_graph(width: int = 400, height: int = 200) -> TrendGraph:
    """
    Factory function to create a TrendGraph instance.
    
    Args:
        width: Graph width in pixels
        height: Graph height in pixels
        
    Returns:
        Configured TrendGraph instance
    """
    return TrendGraph(width=width, height=height)
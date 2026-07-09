"""
Graph Renderer Component

Renders line graphs for progress visualization.
Implements STORY-002-06: Progress Graph (Fluency Trend)

This component provides Pygame-based rendering for fluency trend graphs.
"""

import pygame
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from src.components.analytics import DataPoint


@dataclass
class GraphConfig:
    """Configuration for graph rendering."""
    width: int = 600
    height: int = 300
    margin: Dict[str, int] = None
    
    def __post_init__(self):
        if self.margin is None:
            self.margin = {'top': 40, 'right': 40, 'bottom': 60, 'left': 60}


class GraphRenderer:
    """
    Renders line graphs using Pygame.
    
    Features:
    - Line graph with data points
    - Grid lines and axes
    - Hover tooltips
    - Export to image (PNG)
    """
    
    # Colors
    COLOR_BG = (245, 245, 245)  # Light gray background
    COLOR_AXIS = (50, 50, 70)   # Dark blue-gray for axes
    COLOR_GRID = (200, 200, 220)  # Light grid lines
    COLOR_LINE = (76, 175, 80)    # Green for trend line
    COLOR_POINT = (76, 175, 80)   # Green for data points
    COLOR_POINT_FILL = (255, 255, 255)  # White fill for points
    COLOR_TEXT = (50, 50, 70)   # Text color
    COLOR_TOOLTIP = (255, 255, 255)  # Tooltip background
    
    def __init__(self, config: Optional[GraphConfig] = None):
        """
        Initialize the graph renderer.
        
        Args:
            config: Optional graph configuration
        """
        self.config = config or GraphConfig()
        self._hover_point: Optional[Tuple[int, DataPoint, Tuple[int, int]]] = None
        self._font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None
    
    def _init_fonts(self):
        """Initialize Pygame fonts (lazy initialization)."""
        if self._font is None:
            try:
                self._font = pygame.font.SysFont('arial', 14)
                self._small_font = pygame.font.SysFont('arial', 11)
            except:
                self._font = pygame.font.Font(None, 14)
                self._small_font = pygame.font.Font(None, 11)
    
    def render(
        self, 
        screen: pygame.Surface, 
        data: List[DataPoint], 
        title: str = "Fluency Progress",
        x_label: str = "Week",
        y_label: str = "Avg Attempts"
    ):
        """
        Render the graph to a Pygame surface.
        
        Args:
            screen: Pygame surface to render to
            data: List of DataPoint objects
            title: Graph title
            x_label: X-axis label
            y_label: Y-axis label
        """
        self._init_fonts()
        
        # Calculate plot area
        w = self.config.width
        h = self.config.height
        m = self.config.margin
        
        plot_left = m['left']
        plot_right = w - m['right']
        plot_top = m['top']
        plot_bottom = h - m['bottom']
        plot_width = plot_right - plot_left
        plot_height = plot_bottom - plot_top
        
        # Clear background
        screen.fill(self.COLOR_BG)
        
        # Draw title
        if self._font:
            title_surf = self._font.render(title, True, self.COLOR_AXIS)
            title_rect = title_surf.get_rect(center=(w // 2, 20))
            screen.blit(title_surf, title_rect)
        
        # Draw axes
        self._draw_axes(screen, plot_left, plot_right, plot_top, plot_bottom)
        
        # Draw grid
        self._draw_grid(screen, data, plot_left, plot_right, plot_top, plot_bottom)
        
        # Draw trend line
        if len(data) >= 2:
            self._draw_trend_line(screen, data, plot_left, plot_right, plot_top, plot_bottom)
        
        # Draw data points
        self._draw_data_points(screen, data, plot_left, plot_right, plot_top, plot_bottom)
        
        # Draw labels
        self._draw_labels(screen, data, plot_left, plot_right, plot_top, plot_bottom)
        
        # Draw interpretation help
        help_text = "Lower is better! Fewer attempts = faster spelling"
        help_surf = self._small_font.render(help_text, True, (100, 100, 120))
        help_rect = help_surf.get_rect(center=(w // 2, h - 15))
        screen.blit(help_surf, help_rect)
        
        # Draw tooltip if hovering
        if self._hover_point:
            self._draw_tooltip(screen, self._hover_point)
    
    def _draw_axes(
        self, 
        screen: pygame.Surface, 
        left: int, 
        right: int, 
        top: int, 
        bottom: int
    ):
        """Draw X and Y axes."""
        # X-axis
        pygame.draw.line(screen, self.COLOR_AXIS, (left, bottom), (right, bottom), 2)
        # Y-axis
        pygame.draw.line(screen, self.COLOR_AXIS, (left, top), (left, bottom), 2)
    
    def _draw_grid(
        self, 
        screen: pygame.Surface, 
        data: List[DataPoint], 
        left: int, 
        right: int, 
        top: int, 
        bottom: int
    ):
        """Draw grid lines."""
        plot_width = right - left
        plot_height = bottom - top
        
        if not data:
            return
        
        # Find max average for Y-axis scale
        max_avg = max((d.average for d in data), default=3.0)
        max_avg = max(max_avg, 1.0)  # At least 1.0 scale
        
        # Horizontal grid lines (Y-axis)
        grid_lines = 5
        for i in range(grid_lines + 1):
            y = top + (i / grid_lines) * plot_height
            pygame.draw.line(screen, self.COLOR_GRID, (left, y), (right, y), 1)
        
        # Vertical grid lines (X-axis)
        num_weeks = len(data)
        for i in range(num_weeks):
            x = left + (i / max(num_weeks - 1, 1)) * plot_width
            pygame.draw.line(screen, self.COLOR_GRID, (x, top), (x, bottom), 1)
    
    def _draw_trend_line(
        self, 
        screen: pygame.Surface, 
        data: List[DataPoint], 
        left: int, 
        right: int, 
        top: int, 
        bottom: int
    ):
        """Draw the trend line connecting data points."""
        if len(data) < 2:
            return
        
        plot_width = right - left
        plot_height = bottom - top
        
        # Find max average for Y-axis scale
        max_avg = max((d.average for d in data if d.word_count > 0), default=3.0)
        max_avg = max(max_avg, 1.0)
        
        # Calculate points
        points = []
        valid_count = sum(1 for d in data if d.word_count > 0)
        
        for i, point in enumerate(data):
            if point.word_count == 0:
                continue
                
            x = left + (i / (len(data) - 1)) * plot_width if len(data) > 1 else left
            y = bottom - (point.average / max_avg) * plot_height
            points.append((x, y))
        
        if len(points) >= 2:
            pygame.draw.lines(screen, self.COLOR_LINE, False, points, 3)
    
    def _draw_data_points(
        self, 
        screen: pygame.Surface, 
        data: List[DataPoint], 
        left: int, 
        right: int, 
        top: int, 
        bottom: int
    ):
        """Draw individual data points."""
        plot_width = right - left
        plot_height = bottom - top
        
        if not data:
            return
        
        # Find max average for Y-axis scale
        max_avg = max((d.average for d in data if d.word_count > 0), default=3.0)
        max_avg = max(max_avg, 1.0)
        
        point_radius = 6
        
        for i, point in enumerate(data):
            if point.word_count == 0:
                continue
            
            x = left + (i / (len(data) - 1)) * plot_width if len(data) > 1 else left
            y = bottom - (point.average / max_avg) * plot_height
            
            # Draw point as circle with white fill
            pygame.draw.circle(screen, self.COLOR_POINT_FILL, (int(x), int(y)), point_radius)
            pygame.draw.circle(screen, self.COLOR_POINT, (int(x), int(y)), point_radius, 2)
    
    def _draw_labels(
        self, 
        screen: pygame.Surface, 
        data: List[DataPoint], 
        left: int, 
        right: int, 
        top: int, 
        bottom: int
    ):
        """Draw axis labels and values."""
        if not data:
            return
        
        plot_height = bottom - top
        
        # Find max average for Y-axis scale
        max_avg = max((d.average for d in data if d.word_count > 0), default=3.0)
        max_avg = max(max_avg, 1.0)
        
        # Y-axis labels (left side)
        grid_lines = 5
        if self._font:
            for i in range(grid_lines + 1):
                # Calculate scale value
                scale_value = 1.0 + (i / grid_lines) * (max_avg - 1.0)
                label = f"{scale_value:.1f}"
                text_surf = self._small_font.render(label, True, self.COLOR_TEXT)
                y = bottom - (i / grid_lines) * plot_height
                text_rect = text_surf.get_rect(right=left - 5, centery=y)
                screen.blit(text_surf, text_rect)
            
            # X-axis labels (bottom)
            num_labels = min(len(data), 8)  # Limit labels to avoid crowding
            step = max(1, len(data) // num_labels)
            
            for i in range(0, len(data), step):
                point = data[i]
                # Simplify week label (just show week number)
                week_num = point.week.split('-W')[1] if '-W' in point.week else point.week
                label = f"W{week_num}"
                text_surf = self._small_font.render(label, True, self.COLOR_TEXT)
                x = left + (i / (len(data) - 1)) * (right - left) if len(data) > 1 else left
                text_rect = text_surf.get_rect(centerx=x, top=bottom + 5)
                screen.blit(text_surf, text_rect)
    
    def _draw_tooltip(
        self, 
        screen: pygame.Surface, 
        hover_data: Tuple[int, DataPoint, Tuple[int, int]]
    ):
        """Draw tooltip for hovered data point."""
        point_idx, data_point, pos = hover_data
        
        if self._font is None:
            return
        
        # Tooltip content
        week_num = data_point.week.split('-W')[1] if '-W' in data_point.week else data_point.week
        lines = [
            f"Week {week_num}",
            f"Avg Attempts: {data_point.average:.2f}",
            f"Words: {data_point.word_count}"
        ]
        
        # Calculate tooltip dimensions
        max_width = 120
        tooltip_height = 20 + len(lines) * 16
        
        x, y = pos
        tooltip_x = x + 10
        tooltip_y = y - tooltip_height // 2
        
        # Ensure tooltip stays on screen
        screen_width, screen_height = screen.get_size()
        if tooltip_x + max_width > screen_width:
            tooltip_x = x - max_width - 10
        
        # Draw tooltip background
        pygame.draw.rect(screen, self.COLOR_TOOLTIP, (tooltip_x, tooltip_y, max_width, tooltip_height))
        pygame.draw.rect(screen, self.COLOR_AXIS, (tooltip_x, tooltip_y, max_width, tooltip_height), 1)
        
        # Draw text
        for i, line in enumerate(lines):
            text_surf = self._small_font.render(line, True, self.COLOR_TEXT)
            text_rect = text_surf.get_rect(topleft=(tooltip_x + 5, tooltip_y + 5 + i * 16))
            screen.blit(text_surf, text_rect)
    
    def handle_mouse_motion(self, pos: Tuple[int, int], data: List[DataPoint], screen_rect: pygame.Rect):
        """
        Handle mouse movement for hover effects.
        
        Args:
            pos: Mouse position (x, y)
            data: List of DataPoint objects
            screen_rect: Rect defining the graph area
        """
        # Check if mouse is over a data point
        self._hover_point = None
        
        if len(data) < 2:
            return
        
        m = self.config.margin
        left = m['left']
        right = screen_rect.width - m['right']
        top = m['top']
        bottom = screen_rect.height - m['bottom']
        plot_width = right - left
        plot_height = bottom - top
        
        # Find max average for Y-axis scale
        max_avg = max((d.average for d in data if d.word_count > 0), default=3.0)
        max_avg = max(max_avg, 1.0)
        
        point_radius = 8  # Slightly larger for hover detection
        
        for i, point in enumerate(data):
            if point.word_count == 0:
                continue
            
            x = left + (i / (len(data) - 1)) * plot_width if len(data) > 1 else left
            y = bottom - (point.average / max_avg) * plot_height
            
            # Check if mouse is near this point
            dx = pos[0] - x
            dy = pos[1] - y
            if dx*dx + dy*dy <= point_radius * point_radius:
                self._hover_point = (i, point, (int(x), int(y)))
                break
    
    def export_to_surface(self, data: List[DataPoint], title: str = "Fluency Progress") -> pygame.Surface:
        """
        Export graph to a standalone Pygame surface.
        
        Args:
            data: List of DataPoint objects
            title: Graph title
            
        Returns:
            Pygame surface containing the graph
        """
        surface = pygame.Surface((self.config.width, self.config.height))
        self.render(surface, data, title)
        return surface
    
    def export_to_png(self, filepath: str, data: List[DataPoint], title: str = "Fluency Progress"):
        """
        Export graph to PNG file.
        
        Args:
            filepath: Path to save the PNG file
            data: List of DataPoint objects
            title: Graph title
        """
        surface = self.export_to_surface(data, title)
        pygame.image.save(surface, filepath)
    
    def clear_hover(self):
        """Clear the current hover state."""
        self._hover_point = None


def create_graph_renderer(config: Optional[GraphConfig] = None) -> GraphRenderer:
    """
    Factory function to create a GraphRenderer instance.
    
    Args:
        config: Optional graph configuration
        
    Returns:
        Configured GraphRenderer instance
    """
    return GraphRenderer(config=config)
"""
Parent Dashboard Screen

Displays progress visualization and analytics for parents.
Implements STORY-002-06: Progress Graph (Fluency Trend)

This screen shows fluency trends, accuracy metrics, and progress summary.
"""

import pygame
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

from src.components.analytics import AnalyticsEngine, DataPoint
from src.ui.graph_renderer import GraphRenderer, GraphConfig


@dataclass
class DashboardButton:
    """Represents an interactive button on the dashboard."""
    text: str
    rect: pygame.Rect
    callback: Optional[Callable] = None
    color: tuple = (76, 175, 80)
    hover_color: tuple = (100, 189, 100)


class ParentDashboardScreen:
    """
    Parent dashboard for viewing student progress.
    
    Features:
    - Fluency trend graph (8 weeks)
    - Summary statistics
    - Export functionality
    """
    
    # Colors
    COLOR_BG = (250, 250, 255)
    COLOR_CARD = (255, 255, 255)
    COLOR_TEXT = (50, 50, 70)
    COLOR_TEXT_LIGHT = (100, 100, 120)
    COLOR_BORDER = (200, 200, 220)
    COLOR_ACCENT = (76, 175, 80)
    
    def __init__(self, analytics_engine: AnalyticsEngine, screen_width: int = 800, screen_height: int = 600):
        """
        Initialize the parent dashboard.
        
        Args:
            analytics_engine: AnalyticsEngine instance for data
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.analytics = analytics_engine
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Graph renderer
        graph_config = GraphConfig(width=600, height=300)
        self.graph_renderer = GraphRenderer(config=graph_config)
        
        # UI elements
        self._buttons: List[DashboardButton] = []
        self._hovered_button: Optional[DashboardButton] = None
        self._insufficient_data: bool = False
        
        # Fonts
        self._title_font: Optional[pygame.font.Font] = None
        self._body_font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None
        
        # Data
        self._weekly_data: List[DataPoint] = []
        self._load_data()
    
    def _init_fonts(self):
        """Initialize Pygame fonts."""
        if self._title_font is None:
            try:
                self._title_font = pygame.font.SysFont('arial', 24)
                self._body_font = pygame.font.SysFont('arial', 16)
                self._small_font = pygame.font.SysFont('arial', 13)
            except:
                self._title_font = pygame.font.Font(None, 24)
                self._body_font = pygame.font.Font(None, 16)
                self._small_font = pygame.font.Font(None, 13)
    
    def _load_data(self):
        """Load and process data for dashboard."""
        self._weekly_data = self.analytics.get_weekly_averages(weeks=8)
        
        # Check if we have sufficient data
        valid_data = [d for d in self._weekly_data if d.word_count > 0]
        self._insufficient_data = len(valid_data) < 2
    
    def render(self, screen: pygame.Surface):
        """
        Render the dashboard to the screen.
        
        Args:
            screen: Pygame surface to render to
        """
        self._init_fonts()
        
        # Clear background
        screen.fill(self.COLOR_BG)
        
        # Draw header
        self._draw_header(screen)
        
        # Draw content area
        card_rect = pygame.Rect(50, 80, self.screen_width - 100, self.screen_height - 130)
        self._draw_card(screen, card_rect)
        
        # Draw graph or insufficient data message
        if self._insufficient_data:
            self._draw_insufficient_data(screen, card_rect)
        else:
            self._draw_graph(screen, card_rect)
        
        # Draw summary stats
        self._draw_summary_stats(screen, card_rect)
    
    def _draw_header(self, screen: pygame.Surface):
        """Draw the header/title area."""
        if self._title_font:
            title = "Parent Dashboard - Progress Overview"
            title_surf = self._title_font.render(title, True, self.COLOR_TEXT)
            title_rect = title_surf.get_rect(centerx=self.screen_width // 2, top=20)
            screen.blit(title_surf, title_rect)
    
    def _draw_card(self, screen: pygame.Surface, rect: pygame.Rect):
        """Draw a card container."""
        # Card background
        pygame.draw.rect(screen, self.COLOR_CARD, rect, border_radius=8)
        
        # Card border
        pygame.draw.rect(screen, self.COLOR_BORDER, rect, 2, border_radius=8)
    
    def _draw_graph(self, screen: pygame.Surface, card_rect: pygame.Rect):
        """Draw the fluency trend graph."""
        # Define graph area within the card
        graph_rect = pygame.Rect(
            card_rect.x + 50,
            card_rect.y + 30,
            600, 300
        )
        
        # Create a surface for the graph
        graph_surface = pygame.Surface((600, 300))
        
        # Render graph
        self.graph_renderer.render(
            graph_surface,
            self._weekly_data,
            title="Fluency Progress - Average Attempts per Word",
            x_label="Week",
            y_label="Avg Attempts"
        )
        
        # Draw graph on screen
        screen.blit(graph_surface, (graph_rect.x, graph_rect.y))
        
        # Draw export button
        self._create_export_button(graph_rect)
    
    def _draw_insufficient_data(self, screen: pygame.Surface, card_rect: pygame.Rect):
        """Draw message when there's insufficient data."""
        message = self.analytics.get_insufficient_data_message()
        
        if self._body_font:
            # Centered message
            text_surf = self._body_font.render(message, True, self.COLOR_TEXT_LIGHT)
            text_rect = text_surf.get_rect(center=card_rect.center, y=card_rect.y + 50)
            screen.blit(text_surf, text_rect)
    
    def _draw_summary_stats(self, screen: pygame.Surface, card_rect: pygame.Rect):
        """Draw summary statistics below the graph."""
        if self._insufficient_data:
            return
        
        # Calculate trend
        trend = self.analytics.get_trend_direction(self._weekly_data)
        fluency_score = self.analytics.calculate_fluency_score(self._weekly_data)
        
        y_offset = card_rect.y + 360
        
        if self._body_font:
            # Trend indicator
            if trend == "improving":
                trend_text = "Trend: Improving (fewer attempts over time)"
                trend_color = (76, 175, 80)
            elif trend == "declining":
                trend_text = "Trend: Needs Practice (more attempts over time)"
                trend_color = (255, 152, 0)
            else:
                trend_text = "Trend: Stable"
                trend_color = self.COLOR_TEXT
            
            text_surf = self._body_font.render(trend_text, True, trend_color)
            screen.blit(text_surf, (card_rect.x + 50, y_offset))
            
            # Fluency score
            score_text = f"Current Fluency Score: {fluency_score:.2f} (lower is better)"
            text_surf = self._body_font.render(score_text, True, self.COLOR_TEXT)
            screen.blit(text_surf, (card_rect.x + 50, y_offset + 30))
            
            # Story note
            note_text = "Note: Lower average attempts indicate improved spelling fluency."
            text_surf = self._small_font.render(note_text, True, self.COLOR_TEXT_LIGHT)
            screen.blit(text_surf, (card_rect.x + 50, y_offset + 60))
    
    def _create_export_button(self, graph_rect: pygame.Rect):
        """Create export button."""
        button_rect = pygame.Rect(
            graph_rect.x + 300,
            graph_rect.y + graph_rect.height - 40,
            120, 30
        )
        
        # Only create button if not already created with different position
        existing = [b for b in self._buttons if b.text == "Export Graph"]
        if not existing or existing[0].rect != button_rect:
            self._buttons = [b for b in self._buttons if b.text != "Export Graph"]
            self._buttons.append(DashboardButton(
                text="Export Graph",
                rect=button_rect,
                callback=self._export_graph,
                color=self.COLOR_ACCENT
            ))
    
    def _export_graph(self):
        """Export the current graph to PNG."""
        try:
            filepath = "data/fluency_progress.png"
            self.graph_renderer.export_to_png(
                filepath,
                self._weekly_data,
                "Fluency Progress - Last 8 Weeks"
            )
            print(f"Graph exported to {filepath}")
        except Exception as e:
            print(f"Failed to export graph: {e}")
    
    def handle_mouse_motion(self, pos: tuple):
        """
        Handle mouse movement for hover effects.
        
        Args:
            pos: Mouse position (x, y)
        """
        self._hovered_button = None
        
        # Check buttons
        for button in self._buttons:
            if button.rect.collidepoint(pos):
                self._hovered_button = button
                break
    
    def handle_mouse_click(self, pos: tuple):
        """
        Handle mouse click.
        
        Args:
            pos: Mouse position (x, y)
        """
        for button in self._buttons:
            if button.rect.collidepoint(pos) and button.callback:
                button.callback()
                return
    
    def handle_event(self, event: pygame.event.Event):
        """
        Handle pygame events.
        
        Args:
            event: Pygame event
        """
        if event.type == pygame.MOUSEMOTION:
            self.handle_mouse_motion(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.handle_mouse_click(event.pos)
    
    def draw(self, screen: pygame.Surface):
        """
        Render all UI elements including buttons.
        
        Args:
            screen: Pygame surface to render to
        """
        self.render(screen)
        
        # Draw buttons
        for button in self._buttons:
            color = button.hover_color if button == self._hovered_button else button.color
            
            # Button background
            pygame.draw.rect(screen, color, button.rect, border_radius=4)
            
            # Button border
            pygame.draw.rect(screen, self.COLOR_BORDER, button.rect, 2, border_radius=4)
            
            # Button text
            if self._small_font:
                text_surf = self._small_font.render(button.text, True, (255, 255, 255))
                text_rect = text_surf.get_rect(center=button.rect.center)
                screen.blit(text_surf, text_rect)


def create_parent_dashboard(
    sessions: List[Dict],
    screen_width: int = 800,
    screen_height: int = 600
) -> ParentDashboardScreen:
    """
    Factory function to create a ParentDashboardScreen.
    
    Args:
        sessions: List of session data dictionaries
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        
    Returns:
        Configured ParentDashboardScreen instance
    """
    analytics = AnalyticsEngine(sessions=sessions)
    return ParentDashboardScreen(
        analytics_engine=analytics,
        screen_width=screen_width,
        screen_height=screen_height
    )
"""
Parent Dashboard Screen with Authentication

Displays progress visualization and analytics for parents.
Implements STORY-003-01: Parent Authentication
Implements STORY-002-06: Progress Graph (Fluency Trend)

This screen shows fluency trends, accuracy metrics, and progress summary.
Access is protected by password authentication.
"""

import pygame
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import logging

from src.components.analytics import AnalyticsEngine, DataPoint
from src.components.tts_manager import TTSManager
from src.components.tts_settings import TTSConfigManager, TTSSettings
from src.ui.graph_renderer import GraphRenderer, GraphConfig
from src.ui.tts_settings_panel import TTSSettingsPanel
from src.ui.caption_settings_panel import CaptionSettingsPanel
from src.ui.typography_settings_panel import TypographySettingsPanel
from src.components.caption_settings import CaptionSettingsManager
from src.components.typography_settings import get_typography_settings
from src.auth.session_manager import SessionManager
from src.auth.password_manager import PasswordManager
from src.ui.password_prompt import PasswordPrompt
from src.ui.star_field import StarField
from src.ui.theme import get_theme
from src.audio.music_manager import get_music_manager, MusicState

logger = logging.getLogger(__name__)


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
    
    # Theme manager (STORY-005-01)
    theme = None
    star_field = None
    
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
        
        # Space theme initialization (STORY-005-01)
        self.theme = get_theme()
        self.star_field = StarField(screen_width, screen_height)
        
        # Graph renderer
        graph_config = GraphConfig(width=600, height=300)
        self.graph_renderer = GraphRenderer(config=graph_config)
        
        # TTS components (STORY-006-02) - Declare attributes first
        self.tts_manager: Optional[TTSManager] = None
        self.tts_settings_panel: Optional[TTSSettingsPanel] = None
        self.show_tts_settings: bool = False
        
        # Caption components (STORY-006-03)
        self.caption_settings_mgr: Optional[CaptionSettingsManager] = None
        self.caption_panel: Optional[CaptionSettingsPanel] = None
        self.show_caption_settings: bool = False
        self._caption_manager: Optional[Any] = None  # Store for later init
        
        # Typography components (STORY-006-05)
        self.typography_settings = get_typography_settings()
        self.typography_panel: Optional[TypographySettingsPanel] = None
        self.show_typography_settings: bool = False
        
        # UI elements
        self._buttons: List[DashboardButton] = []
        self._hovered_button: Optional[DashboardButton] = None
        
        # Music manager (STORY-005-04)
        self.music_manager = get_music_manager()
        
        # Initialize TTS manager after all attributes are declared
        self.tts_manager = TTSManager()
        self.tts_settings_panel = TTSSettingsPanel(
            tts_manager=self.tts_manager,
            width=600,
            height=350,
            on_settings_changed=self._on_tts_settings_changed
        )
        
        # Initialize caption settings manager
        self.caption_settings_mgr = CaptionSettingsManager()
        # Caption panel will be initialized when caption_manager is available
        # via init_caption_panel() method
        
        # Initialize typography settings panel (STORY-006-05)
        self.typography_panel = TypographySettingsPanel(
            x=0, y=0,  # Will be centered when rendered
            on_font_changed=self._on_font_changed
        )
    
    def on_enter(self):
        """Called when screen becomes active - play dashboard music."""
        try:
            self.music_manager.initialize()
            self.music_manager.play(MusicState.PARENT_DASHBOARD)
        except Exception as e:
            # Music initialization failed - continue without music
            print(f"Warning: Could not initialize music in parent dashboard: {e}")
        self._insufficient_data: bool = False
        
        # Fonts
        self._title_font: Optional[pygame.font.Font] = None
        self._body_font: Optional[pygame.font.Font] = None
        self._small_font: Optional[pygame.font.Font] = None
        
        # Data
        self._weekly_data: List[DataPoint] = []
        self._load_data()
        
        # Create dashboard buttons
        self._create_dashboard_buttons()
    
    def init_caption_panel(self, caption_manager: Any) -> None:
        """Initialize caption settings panel with caption manager.
        
        Args:
            caption_manager: CaptionManager instance from Game class
        """
        self._caption_manager = caption_manager
        self.caption_panel = CaptionSettingsPanel(
            caption_manager=caption_manager,
            settings_manager=self.caption_settings_mgr,
            width=600,
            height=500,
            on_settings_changed=self._on_caption_settings_changed
        )
    
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
        
        # Render space theme background (STORY-005-01)
        # Fill with deep space blue
        screen.fill(self.theme.get_color("space_blue"))
        
        # Render star field (twinkling animation)
        self.star_field.render(screen)
        
        # Draw header
        self._draw_header(screen)
        
        # Draw content area (with lighter background for readability)
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
    
    def _create_dashboard_buttons(self) -> None:
        """Create the main dashboard buttons."""
        # Create buttons in a row near the bottom of the card
        button_y = self.screen_height - 120
        button_width = 150
        button_height = 40
        spacing = 20
        
        # TTS Settings button
        tts_button_rect = pygame.Rect(
            self.screen_width // 2 - button_width * 3 // 2 - spacing,
            button_y,
            button_width, button_height
        )
        self._buttons.append(DashboardButton(
            text="TTS Settings",
            rect=tts_button_rect,
            callback=self._toggle_tts_settings,
            color=(33, 150, 243)  # Blue
        ))
        
        # Font Settings button (STORY-006-05)
        font_button_rect = pygame.Rect(
            self.screen_width // 2 - button_width // 2,
            button_y,
            button_width, button_height
        )
        self._buttons.append(DashboardButton(
            text="Font Settings",
            rect=font_button_rect,
            callback=self._toggle_font_settings,
            color=(255, 152, 0)  # Orange
        ))
        
        # Caption Settings button
        caption_button_rect = pygame.Rect(
            self.screen_width // 2 + button_width // 2 + spacing,
            button_y,
            button_width, button_height
        )
        self._buttons.append(DashboardButton(
            text="Caption Settings",
            rect=caption_button_rect,
            callback=self._toggle_caption_settings,
            color=(156, 39, 176)  # Purple
        ))
    
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
    
    def update(self, delta_time: float):
        """
        Update dashboard state (call each frame).
        
        Args:
            delta_time: Time since last update in seconds
        """
        # Update star field twinkling animation (STORY-005-01)
        if self.star_field:
            self.star_field.update(delta_time)
    
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
        
        # Pass events to settings panels if visible
        if self.show_tts_settings:
            self.tts_settings_panel.handle_event(event)
        
        if self.show_typography_settings and self.typography_panel:
            self.typography_panel.handle_event(event)
        
        if self.show_caption_settings and self.caption_panel:
            # Check for close button click first
            close_rect = pygame.Rect(self.caption_panel.width - 40, 20, 25, 25)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if close_rect.collidepoint(event.pos):
                    self.show_caption_settings = False
                    return
            
            self.caption_panel.handle_event(event)
    
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
        
        # Draw caption settings panel if visible
        if self.show_caption_settings and self.caption_panel:
            # Center the panel on screen
            panel_x = (self.screen_width - self.caption_panel.width) // 2
            panel_y = (self.screen_height - self.caption_panel.height) // 2
            self.caption_panel.rect.topleft = (panel_x, panel_y)
            
            # Render panel at centered position
            self.caption_panel.render(screen)
            
            # Panel close button
            close_rect = pygame.Rect(panel_x + self.caption_panel.width - 40, panel_y + 20, 25, 25)
            pygame.draw.rect(screen, (255, 82, 82), close_rect, border_radius=4)
            if close_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, (255, 52, 52), close_rect, border_radius=4)
            
            # Draw X
            if self._small_font:
                x_surf = self._small_font.render("X", True, (255, 255, 255))
                x_rect = x_surf.get_rect(center=close_rect.center)
                screen.blit(x_surf, x_rect)
        
        # Draw TTS settings panel if visible
        if self.show_tts_settings:
            # Center the panel on screen
            panel_x = (self.screen_width - self.tts_settings_panel.width) // 2
            panel_y = (self.screen_height - self.tts_settings_panel.height) // 2
            self.tts_settings_panel.rect.topleft = (panel_x, panel_y)
            self.tts_settings_panel.render(screen)
            
            # Panel close button
            close_rect = pygame.Rect(panel_x + self.tts_settings_panel.width - 40, panel_y + 20, 25, 25)
            pygame.draw.rect(screen, (255, 82, 82), close_rect, border_radius=4)
        
        # Draw font settings panel if visible (STORY-006-05)
        if self.show_typography_settings and self.typography_panel:
            # Center the panel on screen
            panel_x = (self.screen_width - self.typography_panel.rect.width) // 2
            panel_y = (self.screen_height - self.typography_panel.rect.height) // 2
            self.typography_panel.rect.topleft = (panel_x, panel_y)
            self.typography_panel.render(screen)
            
            # Panel close button
            close_rect = pygame.Rect(panel_x + self.typography_panel.rect.width - 40, panel_y + 20, 25, 25)
            pygame.draw.rect(screen, (255, 82, 82), close_rect, border_radius=4)
            if close_rect.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(screen, (255, 52, 52), close_rect, border_radius=4)
            
            # Draw X
            if self._small_font:
                x_surf = self._small_font.render("X", True, (255, 255, 255))
                x_rect = x_surf.get_rect(center=close_rect.center)
                screen.blit(x_surf, x_rect)
    
    def _toggle_tts_settings(self) -> None:
        """Toggle TTS settings panel visibility."""
        self.show_tts_settings = not self.show_tts_settings
        if self.show_tts_settings:
            self.show_caption_settings = False
            self.show_typography_settings = False  # Close other panels
    
    def _toggle_font_settings(self) -> None:
        """Toggle font settings panel visibility (STORY-006-05)."""
        self.show_typography_settings = not self.show_typography_settings
        if self.show_typography_settings:
            self.show_tts_settings = False
            self.show_caption_settings = False  # Close other panels
        # Apply font selection immediately
        if self.typography_panel:
            self.typography_panel.apply_selected_font()
    
    def _toggle_caption_settings(self) -> None:
        """Toggle caption settings panel visibility."""
        if self.caption_panel is None:
            logger.warning("Caption panel not initialized")
            return
        self.show_caption_settings = not self.show_caption_settings
        if self.show_caption_settings:
            self.show_tts_settings = False  # Close other panel
    
    def _on_tts_settings_changed(self):
        """Callback when TTS settings change."""
        # Reinitialize TTS if enabled state changed
        if self.tts_manager and not self.tts_manager.is_enabled:
            self.tts_manager.stop()
        logger.info("TTS settings changed")
    
    def _on_font_changed(self, new_font_family: str) -> None:
        """Callback when font settings change (STORY-006-05)."""
        logger.info(f"Font changed to: {new_font_family}")
        # The font will be applied on next render via theme.get_font()
        # No additional action needed here as TypographySettingsPanel handles persistence
    
    def _on_caption_settings_changed(self) -> None:
        """Callback when caption settings change."""
        logger.info("Caption settings changed")


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
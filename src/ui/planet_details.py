"""
Planet Details Panel

Displays detailed information about a selected planet in the space map.
Shows words mastered, accuracy, attempts, and other progress metrics.
"""

from typing import Optional, Callable
import pygame

from src.models.map_state import PlanetNode, PlanetState
from src.ui.typography import Typography
from src.components.audio_system import AudioSystem


class PlanetDetailsPanel:
    """
    Panel showing planet details when a planet is selected.
    
    Displays:
    - Planet name and number
    - Completion status
    - Words mastered
    - Accuracy rate
    - Total attempts
    - Close button to return to map
    """
    
    # Panel dimensions
    PANEL_WIDTH = 400
    PANEL_HEIGHT = 320
    PADDING = 20
    BORDER_RADIUS = 15
    
    # Colors
    COLORS = {
        'background': (30, 30, 60),
        'border': (100, 149, 237),
        'title': (255, 255, 255),
        'label': (200, 200, 220),
        'value': (100, 255, 218),
        'success': (76, 175, 80),
        'warning': (255, 193, 7),
        'locked': (128, 128, 140)
    }
    
    def __init__(
        self,
        screen: pygame.Surface,
        typography: Typography,
        audio_system: Optional[AudioSystem] = None
    ):
        """
        Initialize planet details panel.
        
        Args:
            screen: Pygame surface to render to
            typography: Typography for text rendering
            audio_system: Optional AudioSystem for feedback
        """
        self.screen = screen
        self.typography = typography
        self.audio_system = audio_system
        
        # Panel state
        self.planet: Optional[PlanetNode] = None
        self.visible = False
        
        # Close button
        self.close_button_rect: Optional[pygame.Rect] = None
        
        # Cached surfaces
        self._title_surface: Optional[pygame.Surface] = None
        self._surfaces: dict[str, pygame.Surface] = {}
        
        # UI callbacks
        self.on_close: Optional[Callable[[], None]] = None
        
        # Animation
        self._fade_alpha = 0
        self._target_alpha = 255
        self._slide_offset = 0  # For slide-in animation
    
    def set_planet(self, planet: PlanetNode):
        """
        Set the planet to display details for.
        
        Args:
            planet: PlanetNode with planet data
        """
        self.planet = planet
        self.visible = True
        self._fade_alpha = 0
        self._target_alpha = 255
        self._update_surfaces()
        
        # Audio feedback
        if self.audio_system:
            self.audio_system.play_sfx('focus_change')
    
    def _update_surfaces(self):
        """Regenerate all text surfaces."""
        if not self.planet:
            return
        
        # Clear cache
        self._surfaces.clear()
        
        # Title: Planet name with number
        try:
            title_font = self.typography.title
            self._title_surface = title_font.render(
                f"{self.planet.planet_name}",
                True, self.COLORS['title']
            )
            
            # Status line
            status_font = self.typography.body
            status_text = self._get_status_text()
            self._surfaces['status'] = status_font.render(
                status_text,
                True, self.COLORS.get(self.planet.state, self.COLORS['value'])
            )
            
            # Stats
            self._surfaces['words_mastered'] = status_font.render(
                f"Words Mastered: {self.planet.words_mastered}",
                True, self.COLORS['label']
            )
            self._surfaces['accuracy'] = status_font.render(
                f"Accuracy: {self.planet.accuracy:.0f}%",
                True, self.COLORS['label']
            )
            self._surfaces['attempts'] = status_font.render(
                f"Total Attempts: {self.planet.total_attempts}",
                True, self.COLORS['label']
            )
            
            # Additional info
            body_font = self.typography.body_small
            if self.planet.state == PlanetState.LOCKED:
                self._surfaces['locked_msg'] = body_font.render(
                    "Complete previous planets to unlock",
                    True, self.COLORS['locked']
                )
            elif self.planet.state == PlanetState.COMPLETED:
                self._surfaces['completed_msg'] = body_font.render(
                    "Great job! Planet mastered!",
                    True, self.COLORS['success']
                )
            elif self.planet.state == PlanetState.CURRENT:
                self._surfaces['current_msg'] = body_font.render(
                    "Current location - Keep going!",
                    True, self.COLORS['warning']
                )
            else:
                self._surfaces['visited_msg'] = body_font.render(
                    "Visited - Return to practice",
                    True, self.COLORS['value']
                )
            
        except Exception as e:
            # Fallback surfaces - simplified rendering
            self._title_surface = pygame.Surface((200, 30), pygame.SRCALPHA)
    
    def _get_status_text(self) -> str:
        """Get status text based on planet state."""
        status_map = {
            PlanetState.LOCKED: "Locked",
            PlanetState.VISITED: "Visited",
            PlanetState.COMPLETED: "Completed",
            PlanetState.CURRENT: "Current Location"
        }
        return status_map.get(self.planet.state, "Unknown")
    
    def update(self, delta_time: float):
        """Update panel animation state."""
        # Fade in/out
        if self._fade_alpha < self._target_alpha:
            self._fade_alpha = min(self._target_alpha, 
                                   self._fade_alpha + 255 * delta_time)
        elif self._fade_alpha > self._target_alpha:
            self._fade_alpha = max(self._target_alpha,
                                   self._fade_alpha - 255 * delta_time)
        
        # Slide animation
        target_offset = 0
        if self._slide_offset != target_offset:
            self._slide_offset += (target_offset - self._slide_offset) * 5 * delta_time
    
    def draw(self):
        """Render the planet details panel."""
        if not self.planet or self._fade_alpha == 0:
            return
        
        # Calculate panel position (centered)
        panel_rect = pygame.Rect(
            (self.screen.get_width() - self.PANEL_WIDTH) // 2,
            (self.screen.get_height() - self.PANEL_HEIGHT) // 2,
            self.PANEL_WIDTH,
            self.PANEL_HEIGHT
        )
        
        # Draw semi-transparent panel container
        container = pygame.Surface((self.PANEL_WIDTH, self.PANEL_HEIGHT), pygame.SRCALPHA)
        container.set_alpha(self._fade_alpha)
        
        # Background with rounded corners (simplified as rectangle)
        container.fill((*self.COLORS['background'], 240))
        
        # Border
        pygame.draw.rect(
            container,
            self.COLORS['border'],
            container.get_rect(),
            width=3,
            border_radius=self.BORDER_RADIUS
        )
        
        # Draw title
        if self._title_surface:
            title_x = (self.PANEL_WIDTH - self._title_surface.get_width()) // 2
            container.blit(self._title_surface, (title_x, self.PADDING))
        
        # Draw status
        if 'status' in self._surfaces:
            status = self._surfaces['status']
            status_x = (self.PANEL_WIDTH - status.get_width()) // 2
            container.blit(status, (status_x, self.PADDING + 35))
        
        # Draw stats in grid layout
        y_offset = self.PADDING + 90
        x_offset = self.PADDING
        
        if 'words_mastered' in self._surfaces:
            container.blit(self._surfaces['words_mastered'], (x_offset, y_offset))
        
        if 'accuracy' in self._surfaces:
            acc = self._surfaces['accuracy']
            container.blit(acc, (x_offset + 200, y_offset))
        
        y_offset += 40
        if 'attempts' in self._surfaces:
            container.blit(self._surfaces['attempts'], (x_offset, y_offset))
        
        # Draw message
        message_key = None
        if self.planet.state == PlanetState.LOCKED:
            message_key = 'locked_msg'
        elif self.planet.state == PlanetState.COMPLETED:
            message_key = 'completed_msg'
            y_offset += 30
        elif self.planet.state == PlanetState.CURRENT:
            message_key = 'current_msg'
            y_offset += 30
        else:
            message_key = 'visited_msg'
            y_offset += 30
        
        if y_offset < self.PANEL_HEIGHT - 60 and message_key and message_key in self._surfaces:
            msg = self._surfaces[message_key]
            msg_x = (self.PANEL_WIDTH - msg.get_width()) // 2
            container.blit(msg, (msg_x, y_offset))
        
        # Draw close button
        self._draw_close_button(container)
        
        # Blit container to screen
        self.screen.blit(container, panel_rect.topleft)
        
        # Store close button rect for click detection (adjusted for screen position)
        self.close_button_rect = pygame.Rect(
            panel_rect.x + self.PANEL_WIDTH - 70,
            panel_rect.y + self.PADDING + 10,
            50, 30
        )
    
    def _draw_close_button(self, container: pygame.Surface):
        """Draw the close button on the panel."""
        # Button background
        button_rect = pygame.Rect(
            self.PANEL_WIDTH - 70,
            self.PADDING + 10,
            50, 30
        )
        
        # Button colors (with hover effect)
        button_color = (220, 53, 69)  # Red for close button
        pygame.draw.rect(
            container,
            button_color,
            button_rect,
            border_radius=5
        )
        
        # Button border
        pygame.draw.rect(
            container,
            (255, 255, 255),
            button_rect,
            width=2,
            border_radius=5
        )
        
        # Close text
        body_font = self.typography.body
        close_text = body_font.render("X", True, (255, 255, 255))
        text_x = (button_rect.width - close_text.get_width()) // 2
        text_y = (button_rect.height - close_text.get_height()) // 2
        container.blit(close_text, (button_rect.x + text_x, button_rect.y + text_y))
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle input events.
        
        Args:
            event: Pygame event
            
        Returns:
            True if event was handled
        """
        if not self.visible:
            return False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.close_button_rect:
                if self.close_button_rect.collidepoint(event.pos):
                    self._close_panel()
                    return True
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                self._close_panel()
                return True
        
        return False
    
    def _close_panel(self):
        """Close the details panel."""
        self.visible = False
        self._target_alpha = 0
        
        # Wait for fade out before triggering callback
        if self.on_close:
            # Defer callback until fade complete (simple approach: call immediately)
            self.on_close()


def create_planet_details_panel(
    screen: pygame.Surface,
    typography: Typography,
    audio_system: Optional[AudioSystem] = None
) -> PlanetDetailsPanel:
    """Create a PlanetDetailsPanel instance."""
    return PlanetDetailsPanel(screen, typography, audio_system)
"""
Captain Display Component (STORY-004-04)

Renders Captain Cosmos character with animations and speech bubbles.
Captain Cosmos is the friendly robot mascot who guides players.
"""

import pygame
import math
import logging
from typing import Tuple, Optional
from src.components.captain_cosmos import CaptainCosmos, CaptainState


class CaptainDisplay:
    """
    Renders Captain Cosmos character UI component.
    
    Features:
    - Procedurally drawn robot character (no external assets required)
    - Multiple animation states: idle, talking, celebrating, encouraging
    - Speech bubble with text display
    - Smooth state transitions
    - Bobbing/floating idle animation
    
    Position: Bottom-left corner during gameplay (non-intrusive)
    Size: Approximately 100x150px
    """
    
    # Colors
    CAPTAIN_BLUE = (30, 144, 255)       # Dodger blue for suit
    CAPTAIN_WHITE = (240, 240, 240)     # White accents
    CAPTAIN_YELLOW = (255, 215, 0)      # Gold/yellow accents
    CAPTAIN_DARK = (20, 20, 40)         # Dark blue/black for helmet/eyes
    SPEECH_BUBBLE_WHITE = (255, 255, 255)
    SPEECH_BUBBLE_BORDER = (30, 144, 255)
    TEXT_COLOR = (30, 30, 30)
    
    # Dimensions
    CHARACTER_WIDTH = 100
    CHARACTER_HEIGHT = 150
    SPEECH_BUBBLE_PADDING = 15
    
    # Positions (relative to screen)
    DEFAULT_POSITION = (50, 500)  # Bottom-left corner
    SPEECH_BUBBLE_OFFSET_Y = -20  # Above character head
    
    # Animation timing
    BOB_DURATION_MS = 1000         # 1 second full bob cycle
    BOB_AMOUNT = 5                 # Bob up/down 5px
    STATE_TRANSITION_MS = 200      # 200ms transition
    SPEECH_BUBBLE_DURATION_MS = 3000  # 3 seconds speech bubble
    
    # Font
    FONT_SIZE = 24
    
    def __init__(
        self,
        screen: pygame.Surface,
        captain: CaptainCosmos,
        position: Tuple[int, int] = DEFAULT_POSITION
    ):
        """
        Initialize Captain display.
        
        Args:
            screen: Pygame surface for rendering
            captain: CaptainCosmos instance for state/captain_cosmos data
            position: Display position (default: bottom-left)
        """
        self.screen = screen
        self.captain = captain
        self.position = position
        
        # Animation state
        self._last_update_time: float = 0
        self._bob_offset: float = 0
        self._current_state: CaptainState = CaptainState.IDLE
        self._state_transition_start: float = 0
        
        # Speech bubble
        self._speech_text: str = ""
        self._speech_timer: float = 0
        self._speech_alpha: float = 0  # For fade in/out
        
        # Font
        self._font = pygame.font.Font(None, self.FONT_SIZE)
        
        # Render target (offscreen surface for character)
        self._character_surface: Optional[pygame.Surface] = None
        self._speech_surface: Optional[pygame.Surface] = None
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("CaptainDisplay initialized")
    
    def update(self, dt: float) -> None:
        """
        Update animation state.
        
        Args:
            dt: Delta time in seconds since last frame
        """
        # Update bob animation (idle state)
        if self._current_state == CaptainState.IDLE:
            self._bob_offset = math.sin(pygame.time.get_ticks() / 1000.0 * 2 * math.pi) * self.BOB_AMOUNT
        
        # Update speech bubble timer
        if self._speech_timer > 0:
            self._speech_timer -= dt * 1000
            
            # Fade in/out
            if self._speech_timer < 500:
                # Fade out (last 500ms)
                self._speech_alpha = (self._speech_timer / 500) * 255
            elif self._speech_timer > 2500:
                # Fade in (first 500ms)
                self._speech_alpha = min(255, (2500 - self._speech_timer) / 500 * 255)
        
        # Sync state with CaptainCosmos
        new_state = self.captain.get_state()
        if new_state != self._current_state:
            self._current_state = new_state
            self._state_transition_start = pygame.time.get_ticks()
        
        # Update character surface
        self._render_character()
        
        # Update speech bubble surface
        if self._speech_text:
            self._render_speech_bubble()
    
    def show_speech_bubble(self, text: str, duration: float = 3.0) -> None:
        """
        Display speech bubble with text.
        
        Args:
            text: Text to display in bubble
            duration: Duration in seconds (default 3.0)
        """
        self._speech_text = text
        self._speech_timer = duration * 1000  # Convert to ms
        self._speech_alpha = 255
    
    def hide_speech_bubble(self) -> None:
        """Hide speech bubble immediately."""
        self._speech_text = ""
        self._speech_timer = 0
        self._speech_alpha = 0
    
    def _render_character(self) -> None:
        """Render Captain character to offscreen surface."""
        self._character_surface = pygame.Surface(
            (self.CHARACTER_WIDTH, self.CHARACTER_HEIGHT),
            pygame.SRCALPHA
        )
        
        # Apply bob offset
        y_offset = self._bob_offset
        
        # Calculate animation intensity based on state
        state = self._current_state
        if state == CaptainState.CELEBRATING:
            anim_intensity = 1.0  # Full animation
        elif state == CaptainState.TALKING:
            anim_intensity = 0.5  # Moderate animation
        else:
            anim_intensity = 0.0  # Minimal animation
        
        # Draw character components
        self._draw_body(y_offset)
        self._draw_head(y_offset, anim_intensity)
        self._draw_arms(y_offset, anim_intensity, state)
        self._draw_antenna(y_offset)
    
    def _draw_body(self, y_offset: float) -> None:
        """Draw Captain's body (astronaut suit)."""
        if not self._character_surface:
            return
        
        x = self.CHARACTER_WIDTH // 2
        base_y = 80 + y_offset
        
        # Body (rounded rectangle shape)
        body_rect = pygame.Rect(x - 35, base_y, 70, 50)
        pygame.draw.ellipse(self._character_surface, self.CAPTAIN_BLUE, body_rect)
        
        # Chest panel (yellow accent)
        panel_rect = pygame.Rect(x - 15, base_y + 10, 30, 25)
        pygame.draw.ellipse(self._character_surface, self.CAPTAIN_YELLOW, panel_rect)
        
        # Belt
        belt_rect = pygame.Rect(x - 35, base_y + 35, 70, 8)
        pygame.draw.rect(self._character_surface, self.CAPTAIN_DARK, belt_rect)
    
    def _draw_head(self, y_offset: float, anim_intensity: float) -> None:
        """Draw Captain's head (helmet)."""
        if not self._character_surface:
            return
        
        x = self.CHARACTER_WIDTH // 2
        base_y = 50 + y_offset
        
        # Helmet (large circle)
        helmet_radius = 35
        pygame.draw.circle(
            self._character_surface,
            self.CAPTAIN_WHITE,
            (x, base_y),
            helmet_radius
        )
        
        # Helmet outline
        pygame.draw.circle(
            self._character_surface,
            self.CAPTAIN_BLUE,
            (x, base_y),
            helmet_radius,
            3
        )
        
        # Visor (dark area)
        visor_rect = pygame.Rect(x - 20, base_y - 10, 40, 25)
        pygame.draw.ellipse(self._character_surface, self.CAPTAIN_DARK, visor_rect)
        
        # Eyes (change based on state)
        eye_y = base_y
        if anim_intensity > 0.5:  # Celebrating - excited eyes
            eye_open = 8
        elif anim_intensity > 0.2:  # Talking - animating
            eye_open = 7 + int(math.sin(pygame.time.get_ticks() / 100) * 3)
        else:  # Normal - calm
            eye_open = 6
        
        # Left eye
        pygame.draw.circle(
            self._character_surface,
            (255, 255, 255),
            (x - 10, eye_y),
            eye_open
        )
        
        # Right eye
        pygame.draw.circle(
            self._character_surface,
            (255, 255, 255),
            (x + 10, eye_y),
            eye_open
        )
    
    def _draw_arms(self, y_offset: float, anim_intensity: float, state: CaptainState) -> None:
        """Draw Captain's arms."""
        if not self._character_surface:
            return
        
        base_y = 80 + y_offset
        
        # Left arm
        left_hand_y = base_y + 30
        if state == CaptainState.CELEBRATING:
            left_hand_y = base_y + 10  # Arms up!
        elif anim_intensity > 0.3:
            left_hand_y = base_y + 20  # Slightly animated
        
        pygame.draw.circle(
            self._character_surface,
            self.CAPTAIN_BLUE,
            (25, left_hand_y),
            12
        )
        pygame.draw.circle(
            self._character_surface,
            self.CAPTAIN_YELLOW,
            (25, left_hand_y),
            12,
            3
        )
        
        # Right arm
        right_hand_y = base_y + 30
        if state == CaptainState.CELEBRATING:
            right_hand_y = base_y + 10  # Arms up!
        elif state == CaptainState.HINT_MODE:
            right_hand_y = base_y + 15  # Hand on chin (thinking pose)
        elif anim_intensity > 0.3:
            right_hand_y = base_y + 20
        
        pygame.draw.circle(
            self._character_surface,
            self.CAPTAIN_BLUE,
            (75, right_hand_y),
            12
        )
        pygame.draw.circle(
            self._character_surface,
            self.CAPTAIN_YELLOW,
            (75, right_hand_y),
            12,
            3
        )
    
    def _draw_antenna(self, y_offset: float) -> None:
        """Draw Captain's antenna."""
        if not self._character_surface:
            return
        
        x = self.CHARACTER_WIDTH // 2
        antenna_top = 35 + y_offset
        
        # Antenna stick
        pygame.draw.line(
            self._character_surface,
            self.CAPTAIN_DARK,
            (x, antenna_top),
            (x, antenna_top - 15),
            3
        )
        
        # Glowing tip (pulses when talking)
        glow_size = 6
        if self._current_state == CaptainState.TALKING:
            glow_size += int(math.sin(pygame.time.get_ticks() / 50) * 3)
        
        pygame.draw.circle(
            self._character_surface,
            self.CAPTAIN_YELLOW,
            (x, antenna_top - 18),
            glow_size
        )
    
    def _render_speech_bubble(self) -> None:
        """Render speech bubble to offscreen surface."""
        if not self._speech_text:
            self._speech_surface = None
            return
        
        # Ensure alpha is a valid integer in range [0, 255]
        alpha = max(0, min(255, int(round(self._speech_alpha))))
        
        # Measure text
        text_surface = self._font.render(self._speech_text, True, self.TEXT_COLOR)
        
        bubble_width = text_surface.get_width() + self.SPEECH_BUBBLE_PADDING * 2
        bubble_height = text_surface.get_height() + self.SPEECH_BUBBLE_PADDING * 2
        
        # Create bubble surface
        self._speech_surface = pygame.Surface((bubble_width, bubble_height), pygame.SRCALPHA)
        
        # Draw rounded bubble background
        bubble_rect = pygame.Rect(0, 0, bubble_width, bubble_height)
        
        # Fill background (transparent)
        self._speech_surface.fill((0, 0, 0, 0))
        
        # Create RGBA colors with validated alpha
        bubble_color = (self.SPEECH_BUBBLE_WHITE[0], self.SPEECH_BUBBLE_WHITE[1], 
                        self.SPEECH_BUBBLE_WHITE[2], alpha)
        border_color = (self.SPEECH_BUBBLE_BORDER[0], self.SPEECH_BUBBLE_BORDER[1],
                        self.SPEECH_BUBBLE_BORDER[2], alpha)
        
        # Draw rounded rectangle body
        pygame.draw.rect(
            self._speech_surface,
            bubble_color,
            bubble_rect,
            border_radius=10
        )
        
        # Draw border
        pygame.draw.rect(
            self._speech_surface,
            border_color,
            bubble_rect,
            3,
            border_radius=10
        )
        
        # Draw triangle pointer (points to Captain's head)
        pointer_points = [
            (bubble_width // 2 - 10, bubble_height),
            (bubble_width // 2 + 10, bubble_height),
            (bubble_width // 2, bubble_height - 10),
        ]
        pygame.draw.polygon(
            self._speech_surface,
            bubble_color,
            pointer_points
        )
        pygame.draw.polygon(
            self._speech_surface,
            border_color,
            pointer_points,
            2
        )
        
        # Draw text (centered)
        text_rect = text_surface.get_rect(center=(bubble_width // 2, bubble_height // 2))
        self._speech_surface.blit(text_surface, text_rect)
    
    def render(self) -> None:
        """Render Captain and speech bubble to screen."""
        # Calculate render position for character
        char_x, char_y = self.position
        char_y += self._bob_offset
        
        # Render character
        if self._character_surface:
            char_dest_rect = self._character_surface.get_rect(
                bottomleft=(char_x, char_y + self.CHARACTER_HEIGHT)
            )
            self.screen.blit(self._character_surface, char_dest_rect)
        
        # Render speech bubble (above character's head)
        if self._speech_surface and self._speech_alpha > 0:
            bubble_x = char_x + self.CHARACTER_WIDTH // 2
            bubble_y = char_y - 40
            
            # Center bubble horizontally on character
            if self._speech_surface:
                bubble_dest_rect = self._speech_surface.get_rect(
                    center=(bubble_x, bubble_y)
                )
                self.screen.blit(self._speech_surface, bubble_dest_rect)
    
    def set_state(self, state: CaptainState) -> None:
        """
        Set Captain's animation state.
        
        Args:
            state: Target CaptainState
        """
        self._current_state = state
        self._state_transition_start = pygame.time.get_ticks()
    
    def on_tts_start(self) -> None:
        """Called when TTS begins (updates visual state)."""
        self._current_state = CaptainState.TALKING
        if self.captain.current_line:
            self.show_speech_bubble(self.captain.current_line.text)
    
    def on_tts_complete(self) -> None:
        """Called when TTS completes (updates visual state)."""
        self.hide_speech_bubble()
        self._current_state = CaptainState.IDLE


# Helper function for creating CaptainDisplay instance
def create_captain_display(
    screen: pygame.Surface,
    captain: CaptainCosmos,
    position: Tuple[int, int] = CaptainDisplay.DEFAULT_POSITION
) -> CaptainDisplay:
    """
    Factory function to create a CaptainDisplay instance.
    
    Args:
        screen: Pygame surface for rendering
        captain: CaptainCosmos instance
        position: Display position
        
    Returns:
        Configured CaptainDisplay instance
        
    Example:
        captain = get_captain_cosmos()
        captain_display = create_captain_display(screen, captain, (50, 500))
    """
    return CaptainDisplay(screen, captain, position)
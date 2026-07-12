"""
Streak Display Component (STORY-004-01)

Renders the streak counter with visual effects (flame icon, pulse animation).
Displays consecutive correct answers in the top-right corner of the screen.
"""

import pygame
from typing import Tuple, Optional
from src.components.streak_tracker import StreakTracker


class StreakDisplay:
    """
    Renders the streak counter UI component.
    
    Features:
    - Fire/flame icon with streak number
    - Golden yellow color scheme (#FFD700)
    - Pulse animation when streak increments
    - Hidden when streak is 0 (non-punitive design)
    - Star particle effects for streak 5+
    
    Position: Top-right corner (default)
    """
    
    # Colors
    GOLDEN_YELLOW = (255, 215, 0)   # #FFD700
    ORANGE = (255, 165, 0)          # Accent for flame gradient
    DARK_BG = (0, 0, 0, 180)        # Semi-transparent background
    GRAY = (128, 128, 128)          # For when hidden/disabled
    
    # Positions
    DEFAULT_POSITION = (800, 20)    # Top-right corner
    HORIZONTAL_PADDING = 20
    VERTICAL_PADDING = 20
    
    # Animation constants
    PULSE_DURATION_MS = 100         # 100ms pulse when streak increments
    PULSE_SCALE_MIN = 1.0
    PULSE_SCALE_MAX = 1.2
    
    # Visual settings
    FONT_SIZE = 48
    ICON_SIZE = 32                  # 32x32 flame icon
    STAR_COUNT_HIGH_STREAK = 5      # Stars for streak 5+
    
    def __init__(
        self,
        screen: pygame.Surface,
        streak_tracker: StreakTracker,
        font_size: int = FONT_SIZE,
        position: Tuple[int, int] = DEFAULT_POSITION
    ):
        """
        Initialize the streak display.
        
        Args:
            screen: Pygame surface for rendering
            streak_tracker: StreakTracker instance for streak data
            font_size: Font size for streak number (default 48)
            position: Display position (default top-right)
        """
        self.screen = screen
        self.tracker = streak_tracker
        self.font = pygame.font.Font(None, font_size)
        self.position = position
        
        # Animation state
        self._pulse_start_time: Optional[float] = None
        self._pulse_scale: float = 1.0
        self._current_streak: int = 0
        
        # Load or create assets
        self._flame_surface: Optional[pygame.Surface] = None
        self._star_surfaces: list = []
        self._load_assets()
    
    def _load_assets(self) -> None:
        """Load flame icon and create visual assets."""
        self._create_flame_icon()
        self._create_star_assets()
    
    def _create_flame_icon(self) -> None:
        """Create a procedural flame icon (golden/orange gradient)."""
        self._flame_surface = pygame.Surface((self.ICON_SIZE, self.ICON_SIZE), pygame.SRCALPHA)
        
        # Draw flame shape (simple teardrop/circle gradient)
        # Outer glow (orange)
        pygame.draw.circle(
            self._flame_surface,
            (*self.ORANGE, 150),
            (self.ICON_SIZE // 2, self.ICON_SIZE // 2 + 2),
            self.ICON_SIZE // 2
        )
        
        # Inner flame (golden yellow)
        pygame.draw.circle(
            self._flame_surface,
            (*self.GOLDEN_YELLOW, 255),
            (self.ICON_SIZE // 2, self.ICON_SIZE // 2),
            self.ICON_SIZE // 3
        )
    
    def _create_star_assets(self) -> None:
        """Create star particle assets for high streak effects."""
        self._star_surfaces = []
        for _ in range(self.STAR_COUNT_HIGH_STREAK):
            star = pygame.Surface((16, 16), pygame.SRCALPHA)
            # Draw a simple 4-point star
            center = (8, 8)
            points = [
                (center[0], 0),
                (center[0] + 6, center[1] - 6),
                (center[0] + 16, center[1]),
                (center[0] + 6, center[1] + 6),
                (center[0], center[1] + 16),
                (center[0] - 6, center[1] + 6),
                (center[0] - 16, center[1]),
                (center[0] - 6, center[1] - 6)
            ]
            pygame.draw.polygon(star, (*self.GOLDEN_YELLOW, 200), points)
            self._star_surfaces.append(star)
    
    def update_streak(self, streak: int) -> None:
        """
        Update the displayed streak value.
        
        Triggers pulse animation when streak increments.
        
        Args:
            streak: New streak value
        """
        # Trigger pulse animation if streak increased
        if streak > self._current_streak and streak > 0:
            self._pulse_start_time = pygame.time.get_ticks()
        
        self._current_streak = streak
    
    def _get_pulse_scale(self) -> float:
        """
        Calculate current pulse scale factor.
        
        Returns:
            Scale factor (1.0 to 1.2 during pulse, 1.0 otherwise)
        """
        if self._pulse_start_time is None:
            return 1.0
        
        elapsed = pygame.time.get_ticks() - self._pulse_start_time
        if elapsed >= self.PULSE_DURATION_MS:
            self._pulse_start_time = None
            return 1.0
        
        # Pulse up and down over duration
        progress = elapsed / self.PULSE_DURATION_MS
        # Sine wave: 1.0 -> 1.2 -> 1.0
        import math
        scale = self.PULSE_SCALE_MIN + (self.PULSE_SCALE_MAX - self.PULSE_SCALE_MIN) * math.sin(progress * math.pi)
        return scale
    
    def _render_streak_hidden(self) -> None:
        """Render nothing when streak is 0 (hidden state)."""
        # Do nothing - streak display is hidden when count is 0
        pass
    
    def _render_streak_visible(self, position: Tuple[int, int]) -> None:
        """
        Render the streak display when visible.
        
        Args:
            position: Position to render at
        """
        x, y = position
        
        # Get pulse scale
        scale = self._get_pulse_scale()
        
        # Calculate scaled dimensions
        scaled_icon_size = int(self.ICON_SIZE * scale)
        scaled_font_size = int(self.FONT_SIZE * scale)
        
        # Create scaled font
        scaled_font = pygame.font.Font(None, scaled_font_size)
        
        # Render streak number
        streak_text = str(self._current_streak)
        text_surface = scaled_font.render(streak_text, True, self.GOLDEN_YELLOW)
        
        # Calculate positions (flame icon to the left of number)
        icon_y = y + (scaled_font_size - scaled_icon_size) // 2
        
        # Draw semi-transparent dark circle background
        total_width = scaled_icon_size + 10 + text_surface.get_width()
        total_height = max(scaled_icon_size, text_surface.get_height())
        bg_center_x = x + total_width // 2
        bg_center_y = y + total_height // 2 + 4
        bg_radius = max(total_width, total_height) // 2 + 10
        
        # Create background surface
        bg_surface = pygame.Surface((bg_radius * 2, bg_radius * 2), pygame.SRCALPHA)
        dark_bg = (*self.DARK_BG[:3], self.DARK_BG[3])  # Keep alpha
        pygame.draw.circle(bg_surface, dark_bg, (bg_radius, bg_radius), bg_radius)
        
        # Blit background
        bg_dest_x = x - bg_radius + scaled_icon_size // 2
        bg_dest_y = y - bg_radius // 2
        self.screen.blit(bg_surface, (bg_dest_x, bg_dest_y))
        
        # Draw flame icon (with pulse scale)
        if self._flame_surface:
            scaled_flame = pygame.transform.scale(
                self._flame_surface,
                (scaled_icon_size, scaled_icon_size)
            )
            icon_x = x
            icon_y = y + (scaled_font_size - scaled_icon_size) // 2
            self.screen.blit(scaled_flame, (icon_x, icon_y))
        
        # Draw streak number
        text_x = x + scaled_icon_size + 10
        text_y = y + (scaled_font_size - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (text_x, text_y))
        
        # Draw star particles for high streak (5+)
        if self._current_streak >= 5:
            self._render_star_particles(bg_center_x, bg_center_y)
    
    def _render_star_particles(self, center_x: int, center_y: int) -> None:
        """
        Render star particle effects around the streak display.
        
        Args:
            center_x: Center X position for star distribution
            center_y: Center Y position for star distribution
        """
        import math
        import random
        
        # Use time-based seed for natural variation (milliseconds for uniqueness)
        import time
        time_seed = int(time.time() * 1000) % 100000
        random.seed(time_seed)
        
        radius = 50  # Radius for star distribution
        for i, star in enumerate(self._star_surfaces):
            angle = (2 * math.pi * i) / len(self._star_surfaces)
            # Add some variation
            angle += random.uniform(-0.2, 0.2)
            
            star_x = center_x + int(radius * math.cos(angle))
            star_y = center_y + int(radius * math.sin(angle))
            
            # Pulsing alpha based on time
            alpha = 150 + int(50 * math.sin(pygame.time.get_ticks() / 200 + i))
            star_with_alpha = star.copy()
            star_with_alpha.set_alpha(max(0, min(255, alpha)))
            
            self.screen.blit(star_with_alpha, (star_x - 8, star_y - 8))
    
    def render(self, position: Optional[Tuple[int, int]] = None) -> None:
        """
        Render the streak display on the screen.
        
        Args:
            position: Optional position override, uses default if None
        """
        current_pos = position if position else self.position
        
        # Don't render if streak is 0 (hidden state, non-punitive design)
        if self._current_streak == 0:
            self._render_streak_hidden()
            return
        
        # Render visible streak display
        self._render_streak_visible(current_pos)
    
    def update(self, current_time: float = None) -> None:
        """
        Update display state.
        
        Should be called each frame during the game loop.
        Checks for streak changes and updates animations.
        
        Args:
            current_time: Optional current time (not used but kept for interface consistency)
        """
        # Update from tracker
        new_streak = self.tracker.get_current_streak()
        
        if new_streak != self._current_streak:
            self.update_streak(new_streak)
    
    def trigger_pulse(self) -> None:
        """
        Manually trigger pulse animation.
        
        Useful for external triggers (e.g., streak bonuses).
        """
        self._pulse_start_time = pygame.time.get_ticks()


# Factory function
def create_streak_display(
    screen: pygame.Surface,
    streak_tracker: StreakTracker,
    font_size: int = StreakDisplay.FONT_SIZE,
    position: Tuple[int, int] = StreakDisplay.DEFAULT_POSITION
) -> StreakDisplay:
    """
    Create a StreakDisplay instance.
    
    Args:
        screen: Pygame surface for rendering
        streak_tracker: StreakTracker instance
        font_size: Font size for streak number
        position: Default position
        
    Returns:
        Configured StreakDisplay instance
    """
    return StreakDisplay(
        screen=screen,
        streak_tracker=streak_tracker,
        font_size=font_size,
        position=position
    )
"""
Focus indicator rendering for Word Quest.

Provides visual feedback for keyboard focus on interactive elements.
"""

import pygame
from typing import Optional


class FocusIndicator:
    """
    Renders focus indicators around focused UI elements.
    
    Draws a visible border with pulsing glow effect around
    elements that have keyboard focus.
    """
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize focus indicator.
        
        Args:
            screen: Pygame surface to render on
        """
        self.screen = screen
        self.indicator_color = (255, 215, 0)  # Gold (#FFD700)
        self.indicator_width = 3
        self.border_radius = 8
        self.pulse_alpha = 180
        self.pulse_direction = 1
        self.pulse_speed = 5
        self.enabled = True
        self._current_rect: Optional[pygame.Rect] = None
        
    def render(self, rect: pygame.Rect) -> None:
        """
        Draw focus indicator around a rectangle.
        
        Args:
            rect: Rectangle to draw indicator around
        """
        if not self.enabled:
            return
            
        self._current_rect = rect
        border_width = self.indicator_width
        
        # Create outer glow with pulse effect
        glow_width = 4
        glow_surface = pygame.Surface(
            (rect.width + 2 * (glow_width + 8), 
             rect.height + 2 * (glow_width + 8)), 
            pygame.SRCALPHA
        )
        
        # Pulsing glow color
        glow_color = (*self.indicator_color, self.pulse_alpha)
        glow_rect = glow_surface.get_rect()
        pygame.draw.rect(
            glow_surface, 
            glow_color, 
            glow_rect, 
            width=glow_width, 
            border_radius=self.border_radius + 2
        )
        
        # Center glow around border rect
        border_rect = rect.inflate(border_width * 2, border_width * 2)
        glow_rect = glow_surface.get_rect(center=border_rect.center)
        self.screen.blit(glow_surface, glow_rect)
        
        # Draw solid inner border
        pygame.draw.rect(
            self.screen, 
            self.indicator_color, 
            border_rect,
            width=border_width, 
            border_radius=self.border_radius
        )
        
    def update(self, delta_time: float) -> None:
        """
        Update pulse animation.
        
        Args:
            delta_time: Time since last update in seconds
        """
        if not self.enabled:
            return
            
        # Update pulse alpha
        self.pulse_alpha += self.pulse_speed * delta_time * 60
        
        if self.pulse_alpha >= 220:
            self.pulse_direction = -1
        elif self.pulse_alpha <= 120:
            self.pulse_direction = 1
            
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable focus indicators.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        
    @property
    def is_enabled(self) -> bool:
        """Check if focus indicators are enabled."""
        return self.enabled
        
    def set_color(self, color: tuple) -> None:
        """
        Set the focus indicator color.
        
        Args:
            color: RGB tuple
        """
        self.indicator_color = color
        
    def set_width(self, width: int) -> None:
        """
        Set the indicator border width.
        
        Args:
            width: Border width in pixels
        """
        self.indicator_width = width
        
    def set_pulse_speed(self, speed: float) -> None:
        """
        Set the pulse animation speed.
        
        Args:
            speed: Pulse speed multiplier
        """
        self.pulse_speed = speed


class FocusIndicatorManager:
    """
    Manages focus indicators across multiple screens.
    
    Provides a centralized system for tracking and rendering
    focus indicators throughout the game.
    """
    
    _instance: Optional['FocusIndicatorManager'] = None
    
    def __new__(cls):
        """Singleton pattern for global focus manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        """Initialize global focus manager."""
        if self._initialized:
            return
            
        self.indicators: dict = {}  # screen_name -> FocusIndicator
        self.current_indicator: Optional[FocusIndicator] = None
        self.enabled = True
        
    def register_screen(self, name: str, screen: pygame.Surface) -> FocusIndicator:
        """
        Register a screen for focus indicators.
        
        Args:
            name: Screen identifier
            screen: Pygame surface
            
        Returns:
            FocusIndicator for this screen
        """
        indicator = FocusIndicator(screen)
        self.indicators[name] = indicator
        return indicator
        
    def set_active_screen(self, name: str) -> None:
        """
        Set the currently active screen.
        
        Args:
            name: Screen identifier
        """
        if name in self.indicators:
            self.current_indicator = self.indicators[name]
        else:
            self.current_indicator = None
            
    def render(self, rect: pygame.Rect) -> None:
        """
        Render focus indicator on active screen.
        
        Args:
            rect: Rectangle to draw indicator around
        """
        if self.current_indicator and self.enabled:
            self.current_indicator.render(rect)
            
    def update(self, delta_time: float) -> None:
        """
        Update all focus indicators.
        
        Args:
            delta_time: Time since last update
        """
        if not self.enabled:
            return
            
        for indicator in self.indicators.values():
            indicator.update(delta_time)
            
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable all focus indicators.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        for indicator in self.indicators.values():
            indicator.set_enabled(enabled)
            
    @property
    def is_enabled(self) -> bool:
        """Check if focus indicators are globally enabled."""
        return self.enabled
        
    def clear(self) -> None:
        """Clear all registered screens."""
        self.indicators.clear()
        self.current_indicator = None
"""
Screen Manager

Manages the screen stack and screen transitions for Word Quest.
Provides a clean API for switching between game screens.
"""

import pygame
from abc import ABC, abstractmethod
from typing import List, Optional, Type, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class Screen(ABC):
    """
    Base abstract class for all game screens.
    
    All screens must implement the three core methods:
    - handle_event(): Process input events
    - update(): Update game logic
    - draw(): Render the screen
    
    Lifecycle:
    1. Screen is created
    2. on_enter() is called when screen becomes active
    3. handle_event(), update(), draw() are called in the game loop
    4. on_exit() is called when screen is left
    """
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize the screen.
        
        Args:
            screen: The main pygame display surface
        """
        self.screen = screen
        self.screen_rect = screen.get_rect()
        self._next_screen: Optional[Type['Screen']] = None
        self._exit_flag = False
        
    @property
    def next_screen(self) -> Optional[Type['Screen']]:
        """Get the requested next screen class."""
        return self._next_screen
    
    @next_screen.setter
    def next_screen(self, value: Optional[Type['Screen']]):
        """Set the requested next screen class."""
        self._next_screen = value
        
    @property
    def should_exit(self) -> bool:
        """Check if screen requests to exit the game."""
        return self._exit_flag
    
    def request_exit(self):
        """Signal that the game should exit."""
        self._exit_flag = True
        
    def request_next_screen(self, screen_class: Type['Screen']):
        """Request to transition to another screen."""
        self._next_screen = screen_class
        
    @abstractmethod
    def handle_event(self, event: Any) -> None:
        """
        Handle input events.
        
        Args:
            event: The pygame event to handle
        """
        pass
        
    @abstractmethod
    def update(self) -> None:
        """
        Update the screen's game logic.
        
        Called once per frame before draw().
        """
        pass
        
    @abstractmethod
    def draw(self) -> None:
        """
        Draw the screen.
        
        Called once per frame after update().
        Should draw to self.screen.
        """
        pass
        
    def on_enter(self) -> None:
        """
        Called when the screen becomes active.
        
        Override for initialization that depends on the screen being active.
        """
        logger.debug(f"Screen entering: {self.__class__.__name__}")
        pass
        
    def on_exit(self) -> None:
        """
        Called when the screen is deactivated.
        
        Override for cleanup when leaving the screen.
        """
        logger.debug(f"Screen exiting: {self.__class__.__name__}")
        pass
        
    def on_escape(self) -> None:
        """
        Handle Escape key press.
        
        Default behavior: request to go back to previous screen.
        Override for custom escape behavior.
        """
        self._next_screen = None  # Signal to pop screen
        
    def on_mouse_move(self, pos: tuple) -> None:
        """
        Handle mouse motion events.
        
        Args:
            pos: Mouse position (x, y)
        """
        pass
        
    def on_mouse_click(self, button: int, pos: tuple) -> None:
        """
        Handle mouse button click events.
        
        Args:
            button: Mouse button number (1=left, 2=middle, 3=right)
            pos: Mouse position (x, y)
        """
        pass


class ScreenManager:
    """
    Manages the stack of active screens.
    
    Provides methods for:
    - Pushing new screens onto the stack
    - Popping screens off the stack
    - Replacing the current screen
    - Getting the current screen
    
    The screen at the top of the stack is the active screen.
    """
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize the screen manager.
        
        Args:
            screen: The main pygame display surface
        """
        self.screen = screen
        self._screen_stack: List[Screen] = []
        self._current_screen: Optional[Screen] = None
        self._running = True
        
    @property
    def current_screen(self) -> Optional[Screen]:
        """Get the currently active screen."""
        return self._current_screen
        
    @property
    def screen_stack(self) -> List[Screen]:
        """Get the screen stack (read-only)."""
        return self._screen_stack.copy()
        
    @property
    def is_running(self) -> bool:
        """Check if the screen manager is running."""
        return self._running
        
    def push_screen(self, screen: Screen) -> None:
        """
        Push a new screen onto the stack.
        
        The current screen is paused and on_exit() is called.
        The new screen's on_enter() is called.
        
        Args:
            screen: The screen instance to push
        """
        # Exit current screen if exists
        if self._current_screen is not None:
            self._current_screen.on_exit()
            
        # Push new screen
        self._screen_stack.append(screen)
        self._current_screen = screen
        
        # Enter new screen
        screen.on_enter()
        
        logger.debug(f"Pushed screen: {screen.__class__.__name__} "
                    f"(stack size: {len(self._screen_stack)})")
        
    def pop_screen(self) -> Optional[Screen]:
        """
        Pop the current screen off the stack.
        
        The previous screen (if any) becomes active and its on_enter() is called.
        
        Returns:
            The popped screen, or None if stack was empty
        """
        if not self._screen_stack:
            logger.warning("Attempted to pop from empty screen stack")
            return None
            
        # Exit current screen
        if self._current_screen is not None:
            self._current_screen.on_exit()
            
        # Pop screen
        popped = self._screen_stack.pop()
        
        if self._screen_stack:
            # Activate previous screen
            self._current_screen = self._screen_stack[-1]
            self._current_screen.on_enter()
        else:
            self._current_screen = None
            
        logger.debug(f"Popped screen: {popped.__class__.__name__} "
                    f"(stack size: {len(self._screen_stack)})")
                    
        return popped
        
    def replace_screen(self, screen: Screen) -> None:
        """
        Replace the current screen without going back.
        
        The current screen is removed and replaced with the new one.
        
        Args:
            screen: The screen instance to replace with
        """
        # Exit current screen
        if self._current_screen is not None:
            self._current_screen.on_exit()
            
        # Replace screen
        if self._screen_stack:
            self._screen_stack[-1] = screen
        else:
            self._screen_stack.append(screen)
            
        self._current_screen = screen
        screen.on_enter()
        
        logger.debug(f"Replaced screen with: {screen.__class__.__name__}")
        
    def clear_stack(self) -> None:
        """Clear all screens from the stack and exit."""
        while self._screen_stack:
            self.pop_screen()
            
        self._running = False
        logger.debug("Cleared screen stack")
        
    def handle_event(self, event: Any) -> None:
        """
        Forward event to current screen.
        
        Args:
            event: The pygame event to forward
        """
        if self._current_screen:
            self._current_screen.handle_event(event)
            
            # Check for screen transition requests
            if self._current_screen.next_screen is not None:
                self.pop_screen()
            elif self._current_screen.should_exit:
                self._running = False
                
    def update(self) -> None:
        """Forward update call to current screen."""
        if self._current_screen:
            self._current_screen.update()
            
            # Check for screen transition requests
            if self._current_screen.next_screen is not None:
                self.pop_screen()
            elif self._current_screen.should_exit:
                self._running = False
                
    def draw(self) -> None:
        """Forward draw call to current screen."""
        if self._current_screen:
            self._current_screen.draw()
            
    def run(self) -> None:
        """
        Run the main game loop.
        
        Handles events, updates, and drawing at the target FPS.
        """
        clock = pygame.time.Clock()
        
        while self._running and self._screen_stack:
            # Handle events
            for event in pygame.event.get():
                self.handle_event(event)
                
            # Update current screen
            self.update()
            
            # Draw current screen
            self.draw()
            
            # Update display
            pygame.display.flip()
            
            # Cap frame rate
            clock.tick(60)
            
        logger.info("Screen manager loop ended")

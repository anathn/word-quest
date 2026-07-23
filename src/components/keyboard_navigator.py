"""
Keyboard navigation component for Word Quest.

Provides focus management and keyboard navigation support for accessible
gameplay without mouse input.
"""

from typing import List, Optional, Dict, Callable
from abc import ABC, abstractmethod
import pygame


class Focusable(ABC):
    """
    Abstract base class for UI elements that can receive keyboard focus.
    
    Mixin/base class for elements that can be navigated to using Tab key
    and activated with Enter/Space.
    """
    
    def __init__(self):
        self._is_focused: bool = False
        self._tab_index: int = 0
        self._can_focus: bool = True
        
    @property
    def is_focused(self) -> bool:
        """Check if this element currently has focus."""
        return self._is_focused and self._can_focus
    
    @property
    def tab_index(self) -> int:
        """Get the tab order index."""
        return self._tab_index
    
    @tab_index.setter
    def tab_index(self, value: int) -> None:
        """Set the tab order index."""
        self._tab_index = value
        
    @property
    def can_focus(self) -> bool:
        """Check if this element can receive focus."""
        return self._can_focus
    
    @can_focus.setter
    def can_focus(self, value: bool) -> None:
        """Set whether this element can receive focus."""
        self._can_focus = value
        if not value and self._is_focused:
            self._is_focused = False
            self._on_focus_lost()
    
    @abstractmethod
    def on_focus(self) -> None:
        """
        Called when this element receives focus.
        
        Override to add focus-specific behavior (e.g., visual changes, sounds).
        """
        pass
    
    @abstractmethod
    def on_focus_lost(self) -> None:
        """
        Called when this element loses focus.
        
        Override to clean up focus-specific state.
        """
        pass
    
    @abstractmethod
    def on_activate(self) -> None:
        """
        Called when activated (e.g., Enter key pressed).
        
        Override to define button/interactive element action.
        """
        pass
    
    def on_key_down(self, key: int) -> bool:
        """
        Handle key press while focused.
        
        Args:
            key: Pygame key constant
            
        Returns:
            True if the key was handled, False otherwise
        """
        return False
    
    def _on_focus(self) -> None:
        """Internal method to set focus and call callback."""
        self._is_focused = True
        self.on_focus()
        
    def _on_focus_lost(self) -> None:
        """Internal method to clear focus and call callback."""
        self._is_focused = False
        self.on_focus_lost()


class KeyboardNavigator:
    """
    Manages keyboard focus and navigation across the game.
    
    Tracks all focusable elements, manages focus transitions, and
    handles keyboard input for navigation.
    """
    
    def __init__(self):
        self.focusable_elements: List[Focusable] = []
        self.current_focus: Optional[Focusable] = None
        self.navigation_order: List[Focusable] = []
        self._enabled: bool = True
        
    def register(self, element: Focusable) -> None:
        """
        Register a focusable element for keyboard navigation.
        
        Args:
            element: Focusable UI element to register
        """
        if element not in self.focusable_elements:
            self.focusable_elements.append(element)
            self._rebuild_navigation_order()
            
    def unregister(self, element: Focusable) -> None:
        """
        Unregister a focusable element.
        
        Args:
            element: Focusable UI element to unregister
        """
        if element in self.focusable_elements:
            element._on_focus_lost()
            self.focusable_elements.remove(element)
            self._rebuild_navigation_order()
            
            # If current focus was removed, move to next element
            if self.current_focus == element:
                if self.navigation_order:
                    self._focus_element(self.navigation_order[0])
                else:
                    self.current_focus = None
            
    def _rebuild_navigation_order(self) -> None:
        """Sort elements by tab_index to determine focus order."""
        self.navigation_order = sorted(
            [e for e in self.focusable_elements if e.can_focus],
            key=lambda e: e.tab_index
        )
        
    def focus_next(self) -> None:
        """Move focus to the next element in tab order."""
        if not self.navigation_order:
            return
            
        if self.current_focus is None:
            self._focus_element(self.navigation_order[0])
            return
            
        try:
            current_index = self.navigation_order.index(self.current_focus)
            next_index = (current_index + 1) % len(self.navigation_order)
            self._focus_element(self.navigation_order[next_index])
        except (ValueError, IndexError):
            # Element not found or list changed, focus first
            self._focus_element(self.navigation_order[0])
        
    def focus_previous(self) -> None:
        """Move focus to the previous element in tab order."""
        if not self.navigation_order:
            return
            
        if self.current_focus is None:
            self._focus_element(self.navigation_order[-1])
            return
            
        try:
            current_index = self.navigation_order.index(self.current_focus)
            prev_index = (current_index - 1) % len(self.navigation_order)
            self._focus_element(self.navigation_order[prev_index])
        except (ValueError, IndexError):
            # Element not found or list changed, focus last
            self._focus_element(self.navigation_order[-1])
            
    def _focus_element(self, element: Focusable) -> None:
        """
        Set focus to a specific element.
        
        Args:
            element: Element to receive focus
        """
        if element is self.current_focus:
            return
            
        if self.current_focus:
            self.current_focus._on_focus_lost()
            
        self.current_focus = element
        element._on_focus()
        
    def activate_current(self) -> None:
        """Activate the currently focused element."""
        if self.current_focus:
            self.current_focus.on_activate()
            
    def handle_key(self, key: int, mods: int = 0) -> bool:
        """
        Handle keyboard input for navigation.
        
        Args:
            key: Pygame key constant
            mods: Pygame modifier flags
            
        Returns:
            True if the key was handled by navigator, False otherwise
        """
        if not self._enabled:
            return False
            
        # First, let focused element handle the key
        if self.current_focus:
            if self.current_focus.on_key_down(key):
                return True
                
        # Then handle global navigation
        if key == pygame.K_TAB:
            if mods & pygame.KMOD_SHIFT:
                self.focus_previous()
            else:
                self.focus_next()
            return True
        elif key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
            self.activate_current()
            return True
        elif key == pygame.K_ESCAPE:
            self._handle_escape()
            return True
            
        return False
    
    def _handle_escape(self) -> None:
        """Handle Escape key (close dialog, cancel action)."""
        if self.current_focus:
            # Let focused element handle first - can add on_escape callback
            pass
            
    def set_focus(self, element: Focusable) -> None:
        """
        Set focus to a specific element.
        
        Args:
            element: Element to receive focus
        """
        if element in self.focusable_elements and element.can_focus:
            self._focus_element(element)
            
    def clear_focus(self) -> None:
        """Clear focus from current element."""
        if self.current_focus:
            self.current_focus._on_focus_lost()
            self.current_focus = None
            
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable keyboard navigation.
        
        Args:
            enabled: True to enable, False to disable
        """
        self._enabled = enabled
        if not enabled:
            self.clear_focus()
            
    @property
    def is_enabled(self) -> bool:
        """Check if keyboard navigation is enabled."""
        return self._enabled
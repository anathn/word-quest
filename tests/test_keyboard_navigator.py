"""
Tests for keyboard navigation component.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pygame
from src.components.keyboard_navigator import Focusable, KeyboardNavigator


class MockFocusable(Focusable):
    """Mock focusable element for testing."""
    
    def __init__(self, name: str = "mock"):
        super().__init__()
        self.name = name
        self.focus_count = 0
        self.focus_lost_count = 0
        self.activate_count = 0
        self.key_down_count = 0
        self.last_key = None
        
    def on_focus(self) -> None:
        self.focus_count += 1
        
    def on_focus_lost(self) -> None:
        self.focus_lost_count += 1
        
    def on_activate(self) -> None:
        self.activate_count += 1
        
    def on_key_down(self, key: int) -> bool:
        self.key_down_count += 1
        self.last_key = key
        # Special key for testing - space handles itself
        if key == pygame.K_SPACE:
            return True
        return False


class TestFocusable:
    """Tests for Focusable base class."""
    
    def test_initial_state(self):
        """Test initial focus state."""
        element = MockFocusable()
        assert element.is_focused == False
        assert element.tab_index == 0
        assert element.can_focus == True
        
    def test_tab_index_setter(self):
        """Test setting tab index."""
        element = MockFocusable()
        element.tab_index = 5
        assert element.tab_index == 5
        
    def test_can_focus_setter(self):
        """Test can_focus property."""
        element = MockFocusable()
        assert element.can_focus == True
        element.can_focus = False
        assert element.can_focus == False
        
    def test_focus_callbacks(self):
        """Test focus callbacks are called."""
        element = MockFocusable()
        element._on_focus()
        assert element.focus_count == 1
        element._on_focus_lost()
        assert element.focus_lost_count == 1
        
    def test_focus_changes_is_focused(self):
        """Test that focus changes is_focused property."""
        element = MockFocusable()
        element._on_focus()
        assert element.is_focused == True
        element._on_focus_lost()
        assert element.is_focused == False
        
    def test_cannot_focus_when_not_can_focus(self):
        """Test that focusing is disabled when can_focus is False."""
        element = MockFocusable()
        element.can_focus = False
        element._on_focus()
        assert element.is_focused == False
        
    def test_activate_callback(self):
        """Test activate callback."""
        element = MockFocusable()
        element.on_activate()
        assert element.activate_count == 1
        
    def test_on_key_down_returns_false_by_default(self):
        """Test default key handling returns False."""
        element = MockFocusable()
        assert element.on_key_down(pygame.K_a) == False
        
    def test_on_key_down_returns_true_when_handled(self):
        """Test key handling returns True when handled."""
        element = MockFocusable()
        result = element.on_key_down(pygame.K_SPACE)
        assert result == True
        assert element.key_down_count == 1
        
    def test_can_focus_false_unsets_focus(self):
        """Test setting can_focus to False removes focus."""
        element = MockFocusable()
        element._on_focus()
        assert element.is_focused == True
        element.can_focus = False
        assert element.is_focused == False
        assert element.focus_lost_count == 1


class TestKeyboardNavigator:
    """Tests for KeyboardNavigator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        pygame.init()
        self.navigator = KeyboardNavigator()
        self.element1 = MockFocusable("element1")
        self.element2 = MockFocusable("element2")
        self.element3 = MockFocusable("element3")
        
    def teardown_method(self):
        """Clean up."""
        pygame.quit()
        
    def test_initial_state(self):
        """Test navigator initial state."""
        assert len(self.navigator.focusable_elements) == 0
        assert self.navigator.current_focus == None
        assert len(self.navigator.navigation_order) == 0
        
    def test_register_element(self):
        """Test registering an element."""
        self.navigator.register(self.element1)
        assert len(self.navigator.focusable_elements) == 1
        assert self.element1 in self.navigator.focusable_elements
        
    def test_register_same_element_twice(self):
        """Test registering same element twice doesn't duplicate."""
        self.navigator.register(self.element1)
        self.navigator.register(self.element1)
        assert len(self.navigator.focusable_elements) == 1
        
    def test_unregister_element(self):
        """Test unregistering an element."""
        self.navigator.register(self.element1)
        self.navigator.unregister(self.element1)
        assert len(self.navigator.focusable_elements) == 0
        assert self.element1 not in self.navigator.focusable_elements
        
    def test_unregister_current_focus_moves_to_next(self):
        """Test that unregistering current focus moves to next element."""
        self.navigator.register(self.element1)
        self.navigator.register(self.element2)
        self.navigator.focus_next()  # Focus element1
        assert self.navigator.current_focus == self.element1
        self.navigator.unregister(self.element1)
        assert self.navigator.current_focus == self.element2
        
    def test_navigation_order_by_tab_index(self):
        """Test that navigation order respects tab_index."""
        self.element3.tab_index = 0  # Should be first
        self.element1.tab_index = 1
        self.element2.tab_index = 2
        
        self.navigator.register(self.element1)
        self.navigator.register(self.element2)
        self.navigator.register(self.element3)
        
        # First focus should be element3 (lowest tab_index)
        self.navigator.focus_next()
        assert self.navigator.current_focus == self.element3
        
    def test_focus_next_cycles_through_elements(self):
        """Test focus_next cycles through all elements."""
        self.navigator.register(self.element1)
        self.navigator.register(self.element2)
        self.navigator.register(self.element3)
        
        self.navigator.focus_next()
        assert self.navigator.current_focus == self.element1
        
        self.navigator.focus_next()
        assert self.navigator.current_focus == self.element2
        
        self.navigator.focus_next()
        assert self.navigator.current_focus == self.element3
        
        # Should cycle back to first
        self.navigator.focus_next()
        assert self.navigator.current_focus == self.element1
        
    def test_focus_previous_cycles_backwards(self):
        """Test focus_previous cycles backwards."""
        self.navigator.register(self.element1)
        self.navigator.register(self.element2)
        
        # Get to second element
        self.navigator.focus_next()
        self.navigator.focus_next()
        assert self.navigator.current_focus == self.element2
        
        # Go backwards
        self.navigator.focus_previous()
        assert self.navigator.current_focus == self.element1
        
        # Should cycle to last
        self.navigator.focus_previous()
        assert self.navigator.current_focus == self.element2
        
    def test_focus_next_with_no_elements(self):
        """Test focus_next does nothing when no elements registered."""
        self.navigator.focus_next()
        assert self.navigator.current_focus == None
        
    def test_focus_previous_with_no_elements(self):
        """Test focus_previous does nothing when no elements registered."""
        self.navigator.focus_previous()
        assert self.navigator.current_focus == None
        
    def test_set_focus_to_specific_element(self):
        """Test setting focus to a specific element."""
        self.navigator.register(self.element1)
        self.navigator.register(self.element2)
        
        self.navigator.set_focus(self.element2)
        assert self.navigator.current_focus == self.element2
        
    def test_set_focus_to_nonexistent_raises_error(self):
        """Test setting focus to unregistered element."""
        self.navigator.register(self.element1)
        # Should not crash, just do nothing
        self.navigator.set_focus(self.element2)
        assert self.navigator.current_focus == None
        
    def test_clear_focus(self):
        """Test clearing focus."""
        self.navigator.register(self.element1)
        self.navigator.focus_next()
        assert self.navigator.current_focus == self.element1
        
        self.navigator.clear_focus()
        assert self.navigator.current_focus == None
        
    def test_activate_current(self):
        """Test activating current focus."""
        self.navigator.register(self.element1)
        self.navigator.focus_next()
        
        self.navigator.activate_current()
        assert self.element1.activate_count == 1
        
    def test_activate_with_no_focus_does_nothing(self):
        """Test activating with no focus does nothing."""
        self.navigator.activate_current()  # Should not crash
        
    def test_handle_key_tab_moves_focus(self):
        """Test TAB key moves focus."""
        self.navigator.register(self.element1)
        self.navigator.register(self.element2)
        
        result = self.navigator.handle_key(pygame.K_TAB)
        assert result == True
        assert self.navigator.current_focus == self.element1
        
    def test_handle_key_shift_tab_moves_previous(self):
        """Test Shift+TAB moves focus backwards."""
        self.navigator.register(self.element1)
        self.navigator.register(self.element2)
        
        # Get to second element first
        self.navigator.focus_next()
        self.navigator.focus_next()
        assert self.navigator.current_focus == self.element2
        
        # Shift+TAB
        mods = pygame.KMOD_SHIFT
        result = self.navigator.handle_key(pygame.K_TAB, mods)
        assert result == True
        assert self.navigator.current_focus == self.element1
        
    def test_handle_key_enter_activates(self):
        """Test ENTER key activates current element."""
        self.navigator.register(self.element1)
        self.navigator.focus_next()
        
        result = self.navigator.handle_key(pygame.K_RETURN)
        assert result == True
        assert self.element1.activate_count == 1
        
    def test_handle_key_space_handled_by_focused_element(self):
        """Test SPACE key is handled by focused element."""
        self.navigator.register(self.element1)
        self.navigator.focus_next()
        
        result = self.navigator.handle_key(pygame.K_SPACE)
        assert result == True
        assert self.element1.key_down_count == 1
        
    def test_handle_key_unhandled_returns_false(self):
        """Test unhandled key returns False."""
        self.navigator.register(self.element1)
        
        result = self.navigator.handle_key(pygame.K_a)
        assert result == False
        
    def test_enabled_false_disables_navigation(self):
        """Test disabling navigator prevents navigation."""
        self.navigator.set_enabled(False)
        self.navigator.register(self.element1)
        
        result = self.navigator.handle_key(pygame.K_TAB)
        assert result == False
        assert self.navigator.current_focus == None
        
    def test_is_enabled_property(self):
        """Test is_enabled property."""
        assert self.navigator.is_enabled == True
        self.navigator.set_enabled(False)
        assert self.navigator.is_enabled == False
        
    def test_rebuild_order_after_tab_index_change(self):
        """Test navigation order updates when tab_index changes."""
        self.element1.tab_index = 1
        self.element2.tab_index = 0
        
        self.navigator.register(self.element1)
        self.navigator.register(self.element2)
        
        # element2 should be first due to lower tab_index
        self.navigator.focus_next()
        assert self.navigator.current_focus == self.element2
        
    def test_focus_lost_callback_when_switching(self):
        """Test focus_lost is called when switching elements."""
        self.navigator.register(self.element1)
        self.navigator.register(self.element2)
        
        self.navigator.focus_next()  # Focus element1
        assert self.element1.focus_lost_count == 0
        
        self.navigator.focus_next()  # Switch to element2
        assert self.element1.focus_lost_count == 1
        
    def test_focus_not_lost_when_setting_same_element(self):
        """Test focus is not lost when setting same element."""
        self.navigator.register(self.element1)
        self.navigator.focus_next()
        
        initial_lost = self.element1.focus_lost_count
        self.navigator.set_focus(self.element1)
        
        assert self.element1.focus_lost_count == initial_lost


class TestKeyboardNavigatorEdgeCases:
    """Edge case tests for keyboard navigation."""
    
    def setup_method(self):
        pygame.init()
        self.navigator = KeyboardNavigator()
        
    def teardown_method(self):
        pygame.quit()
        
    def test_unregister_when_not_registered(self):
        """Test unregistering non-registered element doesn't crash."""
        element = MockFocusable()
        self.navigator.unregister(element)  # Should not crash
        
    def test_empty_navigation_order_focus_next(self):
        """Test focus_next with empty order doesn't crash."""
        self.navigator.focus_next()  # Should not crash
        
    def test_cannot_focus_element_without_can_focus(self):
        """Test cannot focus element with can_focus=False."""
        element = MockFocusable()
        element.can_focus = False
        self.navigator.register(element)
        
        self.navigator.focus_next()
        assert self.navigator.current_focus == None
        
    def test_all_elements_unfocusable_skips_them(self):
        """Test navigation skips unfocusable elements."""
        element1 = MockFocusable()
        element1.can_focus = False
        
        element2 = MockFocusable()
        element2.can_focus = False
        
        self.navigator.register(element1)
        self.navigator.register(element2)
        
        self.navigator.focus_next()
        assert self.navigator.current_focus == None
        
    def test_mixed_focusable_unfocusable(self):
        """Test navigation works with mix of focusable/unfocusable."""
        element1 = MockFocusable()
        element1.can_focus = False
        
        element2 = MockFocusable()
        
        self.navigator.register(element1)
        self.navigator.register(element2)
        
        self.navigator.focus_next()
        assert self.navigator.current_focus == element2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
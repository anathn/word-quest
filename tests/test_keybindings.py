"""
Tests for keybindings component.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pygame
from src.components.keybindings import Keybindings


class TestKeybindings:
    """Tests for Keybindings class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        pygame.init()
        self.bindings = Keybindings()
        
    def teardown_method(self):
        """Clean up."""
        pygame.quit()
        
    def test_initial_state(self):
        """Test bindings are initialized with defaults."""
        assert self.bindings.get_key('navigate_next') == pygame.K_TAB
        assert self.bindings.get_key('activate') == [pygame.K_RETURN, pygame.K_KP_ENTER]
        
    def test_get_default_binding(self):
        """Test getting default binding by action name."""
        key = self.bindings.get_key('navigate_next')
        assert key == pygame.K_TAB
        
    def test_get_key_without_binding(self):
        """Test getting non-existent action returns None."""
        key = self.bindings.get_key('nonexistent')
        assert key is None
        
    def test_bind_action(self):
        """Test binding an action to a new key."""
        self.bindings.bind('custom_action', pygame.K_x)
        assert self.bindings.get_key('custom_action') == pygame.K_x
        
    def test_overwrite_existing_binding(self):
        """Test overwriting existing binding."""
        assert self.bindings.get_key('activate') == [pygame.K_RETURN, pygame.K_KP_ENTER]
        self.bindings.bind('activate', pygame.K_a)
        assert self.bindings.get_key('activate') == pygame.K_a
        
    def test_bind_with_modifier(self):
        """Test binding with modifier key."""
        self.bindings.bind('custom', pygame.K_c, pygame.KMOD_CTRL)
        key = self.bindings.get_key('custom')
        assert key == (pygame.K_c, pygame.KMOD_CTRL)
        
    def test_unbind_restores_default(self):
        """Test unbinding restores default binding."""
        self.bindings.bind('navigate_next', pygame.K_n)
        assert self.bindings.get_key('navigate_next') == pygame.K_n
        
        self.bindings.unbind('navigate_next')
        assert self.bindings.get_key('navigate_next') == pygame.K_TAB
        
    def test_unbind_nonexistent_does_nothing(self):
        """Test unbinding non-existent action doesn't crash."""
        self.bindings.unbind('nonexistent')  # Should not crash
        
    def test_register_callback(self):
        """Test registering callback for action."""
        callback_called = False
        
        def my_callback():
            nonlocal callback_called
            callback_called = True
            
        self.bindings.register_callback('test_action', my_callback)
        self.bindings.bind('test_action', pygame.K_t)
        
        # Trigger the action
        self.bindings.handle_key(pygame.K_t)
        assert callback_called == True
        
    def test_unregister_callback(self):
        """Test unregistering callback."""
        callback_called = False
        
        def my_callback():
            nonlocal callback_called
            callback_called = True
            
        self.bindings.register_callback('test_action', my_callback)
        self.bindings.unregister_callback('test_action')
        
        self.bindings.bind('test_action', pygame.K_t)
        self.bindings.handle_key(pygame.K_t)
        
        assert callback_called == False
        
    def test_handle_key_matches_simple_binding(self):
        """Test key matching for simple (int) binding."""
        self.bindings.bind('test', pygame.K_a)
        result = self.bindings.handle_key(pygame.K_a)
        assert result == True
        
    def test_handle_key_no_match(self):
        """Test key matching when no binding matches."""
        result = self.bindings.handle_key(pygame.K_z)
        assert result == False
        
    def test_handle_key_matches_list_binding(self):
        """Test key matching for list binding."""
        # 'activate' has list binding [K_RETURN, K_KP_ENTER]
        result = self.bindings.handle_key(pygame.K_RETURN)
        assert result == True
        
        result = self.bindings.handle_key(pygame.K_KP_ENTER)
        assert result == True
        
    def test_handle_key_matches_tuple_binding(self):
        """Test key matching for tuple (key + mods) binding."""
        # navigate_previous is (K_TAB, KMOD_SHIFT)
        result = self.bindings.handle_key(pygame.K_TAB, pygame.KMOD_SHIFT)
        assert result == True
        
    def test_handle_key_tuple_no_mod_match(self):
        """Test tuple binding requires modifier match."""
        # K_TAB alone should not match navigate_previous (needs SHIFT)
        result = self.bindings.handle_key(pygame.K_TAB)
        # This depends on other TAB bindings, let's use a test-specific binding
        self.bindings.bind('ctrl_test', pygame.K_c, pygame.KMOD_CTRL)
        result = self.bindings.handle_key(pygame.K_c)  # No modifier
        assert result == False
        
    def test_handle_event(self):
        """Test handling pygame KEYDOWN event."""
        self.bindings.bind('test', pygame.K_x)
        
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_x)
        result = self.bindings.handle_event(event)
        
        assert result == True
        
    def test_handle_event_wrong_type(self):
        """Test handle_event returns False for non-KEYDOWN."""
        event = pygame.event.Event(pygame.KEYUP, key=pygame.K_x)
        result = self.bindings.handle_event(event)
        assert result == False
        
    def test_trigger_action_calls_callback(self):
        """Test that _trigger_action calls the registered callback."""
        called = False
        
        def callback():
            nonlocal called
            called = True
            
        self.bindings.register_callback('test', callback)
        self.bindings._trigger_action('test')
        
        assert called == True
        
    def test_trigger_action_no_callback(self):
        """Test _trigger_action does nothing for unregistered action."""
        # Should not crash
        self.bindings._trigger_action('nonexistent')
        
    def test_reset_to_defaults(self):
        """Test reset to defaults."""
        self.bindings.bind('navigate_next', pygame.K_n)
        self.bindings.reset_to_defaults()
        assert self.bindings.get_key('navigate_next') == pygame.K_TAB
        
    def test_get_all_bindings(self):
        """Test getting all bindings."""
        all_bindings = self.bindings.get_all_bindings()
        assert isinstance(all_bindings, dict)
        assert 'navigate_next' in all_bindings
        
    def test_get_action_description(self):
        """Test getting action description."""
        desc = self.bindings.get_action_description('navigate_next')
        assert 'Move focus' in desc
        
    def test_get_action_description_unknown(self):
        """Test description for unknown action."""
        desc = self.bindings.get_action_description('unknown_action')
        assert desc == 'unknown_action'
        
    def test_get_readable_key(self):
        """Test getting readable key name."""
        key_name = self.bindings.get_readable_key(pygame.K_RETURN)
        assert key_name == 'Enter'
        
    def test_get_readable_key_space(self):
        """Test space key name."""
        key_name = self.bindings.get_readable_key(pygame.K_SPACE)
        assert key_name == 'Space'
        
    def test_get_readable_key_unknown(self):
        """Test unknown key uses pygame key name."""
        # K_a should return 'A'
        key_name = self.bindings.get_readable_key(pygame.K_a)
        assert key_name == 'A' or key_name == 'a'.title()
        
    def test_get_readable_binding_simple(self):
        """Test readable binding for simple int."""
        binding_str = self.bindings.get_readable_binding(pygame.K_TAB)
        assert 'Tab' in binding_str
        
    def test_get_readable_binding_list(self):
        """Test readable binding for list."""
        binding = [pygame.K_RETURN, pygame.K_KP_ENTER]
        binding_str = self.bindings.get_readable_binding(binding)
        assert 'any of:' in binding_str
        
    def test_get_readable_binding_tuple(self):
        """Test readable binding for tuple with modifier."""
        binding = (pygame.K_c, pygame.KMOD_CTRL)
        binding_str = self.bindings.get_readable_binding(binding)
        assert 'Ctrl+C' in binding_str or 'Ctrl + C' in binding_str or 'C' in binding_str
        
    def test_get_keyboard_shortcuts_reference(self):
        """Test generating shortcuts reference text."""
        ref = self.bindings.get_keyboard_shortcuts_reference()
        assert isinstance(ref, str)
        assert 'Keyboard Shortcuts' in ref
        assert len(ref) > 0


class TestKeybindingsEdgeCases:
    """Edge case tests for keybindings."""
    
    def setup_method(self):
        pygame.init()
        self.bindings = Keybindings()
        
    def teardown_method(self):
        pygame.quit()
        
    def test_callback_exception_handling(self):
        """Test that callback exceptions don't crash the system."""
        def bad_callback():
            raise Exception("Callback error")
            
        self.bindings.register_callback('bad', bad_callback)
        self.bindings.bind('bad', pygame.K_b)
        
        # Should not crash
        result = self.bindings.handle_key(pygame.K_b)
        assert result == True  # Action was matched
        
    def test_multiple_callbacks_for_different_actions(self):
        """Test multiple callbacks work independently."""
        called1 = False
        called2 = False
        
        def callback1():
            nonlocal called1
            called1 = True
            
        def callback2():
            nonlocal called2
            called2 = True
            
        self.bindings.register_callback('action1', callback1)
        self.bindings.register_callback('action2', callback2)
        self.bindings.bind('action1', pygame.K_1)
        self.bindings.bind('action2', pygame.K_2)
        
        self.bindings.handle_key(pygame.K_1)
        assert called1 == True
        assert called2 == False
        
        called1 = False
        self.bindings.handle_key(pygame.K_2)
        assert called1 == False
        assert called2 == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
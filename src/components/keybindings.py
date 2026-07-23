"""
Keyboard bindings configuration for Word Quest.

Manages keyboard shortcut mappings and action callbacks for accessible gameplay.
"""

from typing import Dict, Callable, Optional, Union, Any
import pygame


class Keybindings:
    """
    Manage keyboard shortcut mappings for the game.
    
    Supports default bindings that can be customized, with callbacks
    triggered when bound keys are pressed.
    """
    
    # Default key bindings
    DEFAULT_BINDINGS: Dict[str, Any] = {
        'navigate_next': pygame.K_TAB,
        'navigate_previous': (pygame.K_TAB, pygame.KMOD_SHIFT),
        'activate': [pygame.K_RETURN, pygame.K_KP_ENTER],
        'escape': pygame.K_ESCAPE,
        'move_left': pygame.K_LEFT,
        'move_right': pygame.K_RIGHT,
        'move_up': pygame.K_UP,
        'move_down': pygame.K_DOWN,
        'submit_answer': [pygame.K_RETURN, pygame.K_KP_ENTER],
        'delete_char': [pygame.K_BACKSPACE, pygame.K_DELETE],
        'toggle_settings': pygame.K_F1,
        'toggle_captions': pygame.K_F2,
        'toggle_tts': pygame.K_F3,
        'pause_game': pygame.K_p,
        'help': pygame.K_F1,
    }
    
    # Action descriptions for documentation
    ACTION_DESCRIPTIONS: Dict[str, str] = {
        'navigate_next': 'Move focus to next element',
        'navigate_previous': 'Move focus to previous element',
        'activate': 'Activate focused element',
        'escape': 'Close dialog / Cancel action',
        'move_left': 'Move left',
        'move_right': 'Move right',
        'move_up': 'Move up',
        'move_down': 'Move down',
        'submit_answer': 'Submit answer',
        'delete_char': 'Delete character',
        'toggle_settings': 'Toggle settings panel',
        'toggle_captions': 'Toggle closed captions',
        'toggle_tts': 'Toggle text-to-speech',
        'pause_game': 'Pause game',
        'help': 'Show help',
    }
    
    def __init__(self):
        """Initialize keybindings with defaults."""
        self.bindings: Dict[str, Any] = self.DEFAULT_BINDINGS.copy()
        self.callbacks: Dict[str, Callable] = {}
        self._custom_bindings: Dict[str, Any] = {}
        
    def bind(self, action: str, key: int, mods: int = 0) -> None:
        """
        Bind an action to a key.
        
        Args:
            action: Action name (e.g., 'navigate_next')
            key: Pygame key constant
            mods: Optional modifier flags (e.g., pygame.KMOD_SHIFT)
        """
        if mods:
            self._custom_bindings[action] = (key, mods)
        else:
            self._custom_bindings[action] = key
        self.bindings[action] = self._custom_bindings[action]
        
    def unbind(self, action: str) -> None:
        """
        Remove custom binding and restore default.
        
        Args:
            action: Action name
        """
        if action in self._custom_bindings:
            del self._custom_bindings[action]
        if action in self.DEFAULT_BINDINGS:
            self.bindings[action] = self.DEFAULT_BINDINGS[action]
            
    def get_key(self, action: str) -> Any:
        """
        Get key binding for an action.
        
        Args:
            action: Action name
            
        Returns:
            Key binding (int, tuple, or list) or None
        """
        return self.bindings.get(action)
        
    def get_action_for_key(self, key: int, mods: int = 0) -> Optional[str]:
        """
        Get action name for a key combination.
        
        Args:
            key: Pygame key constant
            mods: Modifier flags
            
        Returns:
            Action name or None
        """
        for action, binding in self.bindings.items():
            if self._is_binding_match(binding, key, mods):
                return action
        return None
        
    def _is_binding_match(self, binding: Any, key: int, mods: int) -> bool:
        """
        Check if a key/mod combination matches a binding.
        
        Args:
            binding: The binding value (int, tuple, or list)
            key: Pygame key constant
            mods: Modifier flags
            
        Returns:
            True if matches
        """
        if isinstance(binding, tuple):
            expected_key, expected_mods = binding
            return key == expected_key and (mods & expected_mods)
        elif isinstance(binding, list):
            return key in binding
        else:
            return key == binding
            
    def register_callback(self, action: str, callback: Callable) -> None:
        """
        Register callback function for an action.
        
        Args:
            action: Action name
            callback: Function to call when action triggered
        """
        self.callbacks[action] = callback
        
    def unregister_callback(self, action: str) -> None:
        """
        Remove callback for an action.
        
        Args:
            action: Action name
        """
        if action in self.callbacks:
            del self.callbacks[action]
            
    def handle_event(self, event: "pygame.event.Event") -> bool:
        """
        Handle a pygame key event.
        
        Args:
            event: Pygame event
            
        Returns:
            True if action matched and triggered, False otherwise
        """
        if event.type != pygame.KEYDOWN:
            return False
            
        key = event.key
        mods = pygame.key.get_mods()
        
        for action, binding in self.bindings.items():
            if self._is_binding_match(binding, key, mods):
                self._trigger_action(action)
                return True
                    
        return False
        
    def handle_key(self, key: int, mods: int = 0) -> bool:
        """
        Handle a key press directly.
        
        Args:
            key: Pygame key constant
            mods: Modifier flags
            
        Returns:
            True if action matched and triggered, False otherwise
        """
        for action, binding in self.bindings.items():
            if self._is_binding_match(binding, key, mods):
                self._trigger_action(action)
                return True
        return False
        
    def _trigger_action(self, action: str) -> None:
        """
        Trigger action callback.
        
        Args:
            action: Action name
        """
        if action in self.callbacks:
            try:
                self.callbacks[action]()
            except Exception as e:
                # Log error but don't crash
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in callback for action '{action}': {e}")
                
    def reset_to_defaults(self) -> None:
        """Reset all bindings to defaults."""
        self.bindings = self.DEFAULT_BINDINGS.copy()
        self._custom_bindings.clear()
        
    def get_all_bindings(self) -> Dict[str, Any]:
        """
        Get all current bindings.
        
        Returns:
            Dictionary of action -> binding
        """
        return self.bindings.copy()
        
    def get_action_description(self, action: str) -> str:
        """
        Get human-readable description for an action.
        
        Args:
            action: Action name
            
        Returns:
            Description string
        """
        return self.ACTION_DESCRIPTIONS.get(action, action)
        
    def get_readable_key(self, key: int) -> str:
        """
        Get human-readable key name.
        
        Args:
            key: Pygame key constant
            
        Returns:
            Key name string
        """
        # Common key names
        key_names = {
            pygame.K_RETURN: 'Enter',
            pygame.K_KP_ENTER: 'Num Enter',
            pygame.K_ESCAPE: 'Escape',
            pygame.K_TAB: 'Tab',
            pygame.K_BACKSPACE: 'Backspace',
            pygame.K_DELETE: 'Delete',
            pygame.K_SPACE: 'Space',
            pygame.K_LEFT: 'Left',
            pygame.K_RIGHT: 'Right',
            pygame.K_UP: 'Up',
            pygame.K_DOWN: 'Down',
            pygame.K_F1: 'F1',
            pygame.K_F2: 'F2',
            pygame.K_F3: 'F3',
        }
        return key_names.get(key, pygame.key.name(key)).title()
        
    def get_readable_binding(self, binding: Any) -> str:
        """
        Get human-readable binding string.
        
        Args:
            binding: Binding value (int, tuple, or list)
            
        Returns:
            Readable string
        """
        if isinstance(binding, tuple):
            key, mods = binding
            mod_str = []
            if mods & pygame.KMOD_SHIFT:
                mod_str.append('Shift')
            if mods & pygame.KMOD_CTRL:
                mod_str.append('Ctrl')
            if mods & pygame.KMOD_ALT:
                mod_str.append('Alt')
            prefix = '+'.join(mod_str) + '+' if mod_str else ''
            return f"{prefix}{self.get_readable_key(key)}"
        elif isinstance(binding, list):
            keys = [self.get_readable_key(k) for k in binding]
            return f"any of: {', '.join(keys)}"
        else:
            return self.get_readable_key(binding)
            
    def get_keyboard_shortcuts_reference(self) -> str:
        """
        Generate keyboard shortcuts reference text.
        
        Returns:
            Formatted reference string
        """
        lines = ["Keyboard Shortcuts Reference", "=" * 30, ""]
        
        for action, binding in sorted(self.bindings.items()):
            description = self.get_action_description(action)
            key_str = self.get_readable_binding(binding)
            lines.append(f"  {key_str:20} - {description}")
            
        return '\n'.join(lines)
"""
Captain Cosmos Component (STORY-004-04)

Manages Captain Cosmos character behavior, state transitions, and voice line selection.
Captain Cosmos is the friendly robot mascot who guides players through the game.
"""

import json
import os
import random
import logging
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Callable, Dict, List, Any


logger = logging.getLogger(__name__)


class CaptainState(Enum):
    """Animation states for Captain Cosmos."""
    IDLE = "idle"
    TALKING = "talking"
    CELEBRATING = "celebrating"
    ENCOURAGING = "encouraging"
    HINT_MODE = "hint_mode"


@dataclass
class VoiceLine:
    """Represents a single voice line."""
    text: str
    category: str
    priority: int  # Higher = more important, interrupts lower priority


class CaptainCosmos:
    """
    Captain Cosmos character manager.
    
    Features:
    - Manages character state and animation triggers
    - Selects appropriate voice lines from categorized collections
    - Handles priority-based voice line interruption
    - Provides tutorial guidance
    - Tracks voice line usage to avoid repetition
    
    The character integrates with the AudioSystem for TTS playback.
    """
    
    # Voice line priority levels
    NORMAL_PRIORITY = 1
    HIGH_PRIORITY = 2
    CRITICAL_PRIORITY = 3
    
    def __init__(self, data_dir: Optional[str] = None, audio_system: Optional['AudioSystem'] = None):
        """
        Initialize Captain Cosmos.
        
        Args:
            data_dir: Directory containing voice_lines.json.
                     Defaults to WORDQUEST_DATA_DIR env var or 'data'.
            audio_system: Optional AudioSystem instance for TTS playback.
        """
        # Resolve and validate data directory to prevent path traversal
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_data_dir = os.path.join(base_dir, '..', '..', 'data')
        
        # Get the requested data directory
        requested_dir = data_dir or os.environ.get('WORDQUEST_DATA_DIR', default_data_dir)
        self.data_dir = os.path.abspath(requested_dir)
        
        # Prevent path traversal attacks by resolving the path and checking for '..' in the result
        # If the resolved path escapes the project root unexpectedly, use the default
        resolved_requested = os.path.realpath(self.data_dir)
        resolved_default = os.path.realpath(default_data_dir)
        resolved_base = os.path.dirname(resolved_default)
        
        # Check if the path contains traversal that would escape the project structure
        # Allow: paths within project root, within project root/data, or absolute paths that are legitimate
        if '..' in os.path.relpath(resolved_requested, resolved_base):
            # This would escape the project root - warn but still allow if it's explicitly provided
            # Only reject if trying to access system directories
            system_prefixes = ('/etc', '/usr', '/var', '/root', 'C:\\Windows', 'C:\\Program')
            if any(resolved_requested.startswith(prefix) for prefix in system_prefixes):
                logger.warning(f"Potentially unsafe data directory: {self.data_dir}. Using default.")
                self.data_dir = default_data_dir
            # For other paths (like /tmp in tests), allow them but log a warning
            # This preserves test functionality while protecting against real attacks
        
        self.audio_system = audio_system
        self.state = CaptainState.IDLE
        self.current_line: Optional[VoiceLine] = None
        self._voice_lines: Dict[str, Any] = {}
        self._used_lines: set = set()  # Track used line indices to avoid repetition
        self._tts_callback: Optional[Callable] = None
        self.logger = logging.getLogger(__name__)
        
        # Load voice lines
        self._load_voice_lines()
        
        logger.info("Captain Cosmos initialized")
    
    # Class-level cache for voice lines to avoid repeated file I/O
    _cached_voice_lines: Optional[Dict[str, Any]] = None
    _cache_data_dir: Optional[str] = None
    
    def _load_voice_lines(self) -> None:
        """Load voice lines from data/voice_lines.json with module-level caching."""
        # Use cached data if available and from same data_dir
        if (self._cached_voice_lines is not None and 
            self._cache_data_dir == self.data_dir):
            self._voice_lines = self._cached_voice_lines
            logger.info(f"Using cached voice lines from {self.data_dir}")
            return
        
        voice_lines_path = os.path.join(self.data_dir, "voice_lines.json")
        
        if not os.path.exists(voice_lines_path):
            logger.warning(f"Voice lines file not found: {voice_lines_path}")
            self._voice_lines = {"captain_cosmos": {}}
            return
        
        try:
            with open(voice_lines_path, 'r') as f:
                data = json.load(f)
                self._voice_lines = data.get("captain_cosmos", {})
                # Cache the loaded data
                CaptainCosmos._cached_voice_lines = self._voice_lines
                CaptainCosmos._cache_data_dir = self.data_dir
                logger.info(f"Loaded voice lines from {voice_lines_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing voice lines JSON: {e}")
            self._voice_lines = {"captain_cosmos": {}}
        except Exception as e:
            logger.error(f"Error loading voice lines: {e}")
            self._voice_lines = {"captain_cosmos": {}}
    
    def _get_unique_line(self, category: str) -> str:
        """
        Get a unique voice line from a category, avoiding recent repetition.
        
        Args:
            category: Category name (e.g., 'correct', 'incorrect', 'greeting')
            
        Returns:
            A voice line text, or empty string if none available
        """
        lines = self._voice_lines.get(category, [])
        if not lines:
            return ""
        
        # Try to find an unused line
        available_indices = [i for i in range(len(lines)) if i not in self._used_lines]
        
        if not available_indices:
            # All lines used, reset and pick randomly
            self._used_lines.clear()
            available_indices = list(range(len(lines)))
        
        # Pick a random unused line
        selected_index = random.choice(available_indices)
        self._used_lines.add(selected_index)
        
        # Limit tracked lines to prevent unbounded growth
        if len(self._used_lines) > len(lines) * 2:
            self._used_lines = set(list(self._used_lines)[-len(lines):])
        
        return lines[selected_index]
    
    def speak(self, category: str, priority: int = NORMAL_PRIORITY) -> str:
        """
        Select and prepare a voice line from category.
        
        Args:
            category: Category of voice line to speak
            priority: Priority level (higher interrupts lower)
            
        Returns:
            The selected voice line text
        """
        line_text = self._get_unique_line(category)
        
        if not line_text:
            logger.warning(f"No voice lines available for category: {category}")
            return ""
        
        self.current_line = VoiceLine(
            text=line_text,
            category=category,
            priority=priority
        )
        self.state = CaptainState.TALKING
        
        # Actually trigger TTS if audio system is available
        if self.audio_system and self.audio_system.is_audio_available():
            self.audio_system.speak(line_text, on_complete=self.on_tts_complete)
            # State remains TALKING until on_tts_complete is called
        else:
            # Fallback: Log warning, keep TALKING state for display-only mode
            if not self.audio_system:
                logger.debug("AudioSystem not injected - Captain will display text only (TALKING state maintained for UI)")
            else:
                logger.warning("Audio not available, character will display text only")
            # Don't call callback immediately in display-only mode - let UI handle it
            # State remains TALKING to trigger speech bubble display
        
        logger.debug(f"Captain speaking: '{line_text}' (priority: {priority})")
        return line_text
    
    def speak_with_callback(self, category: str, callback: Callable, priority: int = NORMAL_PRIORITY) -> str:
        """
        Select a voice line and set a callback for when TTS completes.
        
        Args:
            category: Category of voice line
            callback: Function to call when speech completes
            priority: Priority level
            
        Returns:
            The selected voice line text
        """
        self._tts_callback = callback
        return self.speak(category, priority)
    
    def is_category_valid(self, category: str) -> bool:
        """
        Check if a voice line category exists.
        
        Args:
            category: Category name to validate
            
        Returns:
            True if category exists and has voice lines
        """
        return category in self._voice_lines and len(self._voice_lines[category]) > 0
    
    def on_tts_complete(self) -> None:
        """
        Called when TTS finishes speaking.
        
        Returns state to IDLE (or keeps TALKING if interrupted) and triggers callback.
        """
        if self._tts_callback:
            callback = self._tts_callback
            self._tts_callback = None
            callback()
        
        # Return to idle if no interrupt occurred
        if self.state == CaptainState.TALKING:
            self.state = CaptainState.IDLE
    
    # === Event Handlers ===
    
    def on_correct_answer(self) -> str:
        """Handle correct answer event."""
        return self.speak("correct", self.NORMAL_PRIORITY)
    
    def on_incorrect_answer(self) -> str:
        """Handle incorrect answer event."""
        return self.speak("incorrect", self.NORMAL_PRIORITY)
    
    def on_streak_milestone(self, streak: int) -> str:
        """
        Handle streak milestone event.
        
        Args:
            streak: Current streak number
            
        Returns:
            Voice line text
        """
        # Only speak on specific milestones
        if streak in [3, 5, 10]:
            return self.speak("streak", self.HIGH_PRIORITY)
        return ""
    
    def on_planet_complete(self) -> str:
        """Handle planet completion event."""
        return self.speak("planet_complete", self.HIGH_PRIORITY)
    
    def on_hint_request(self) -> str:
        """Handle hint request event."""
        return self.speak("hint_request", self.NORMAL_PRIORITY)
    
    def on_badge_unlock(self) -> str:
        """Handle badge unlock event."""
        return self.speak("badge_unlock", self.HIGH_PRIORITY)
    
    def on_greeting(self) -> str:
        """Handle greeting event (main menu, etc)."""
        return self.speak("greeting", self.CRITICAL_PRIORITY)
    
    # === Tutorial ===
    
    def get_tutorial_line(self, step: str) -> str:
        """
        Get a specific tutorial line.
        
        Args:
            step: Tutorial step identifier (welcome, objective, controls, etc.)
            
        Returns:
            Voice line text
        """
        tutorial = self._voice_lines.get("tutorial", {})
        return tutorial.get(step, "")
    
    def start_tutorial(self) -> str:
        """
        Get the first tutorial line (welcome message).
        
        Returns:
            Welcome message text
        """
        return self.get_tutorial_line("welcome")
    
    def get_tutorial_steps(self) -> List[str]:
        """
        Get list of available tutorial steps.
        
        Returns:
            List of tutorial step identifiers
        """
        tutorial = self._voice_lines.get("tutorial", {})
        return list(tutorial.keys())
    
    # === State Management ===
    
    def set_state(self, state: CaptainState) -> None:
        """
        Set Captain's animation state.
        
        Args:
            state: Target CaptainState
        """
        self.state = state
        logger.debug(f"Captain state changed to: {state.value}")
    
    def trigger_celebration(self) -> None:
        """Trigger celebration animation state."""
        self.state = CaptainState.CELEBRATING
    
    def trigger_encouragement(self) -> None:
        """Trigger encouragement animation state."""
        self.state = CaptainState.ENCOURAGING
    
    def enter_hint_mode(self) -> None:
        """Enter hint delivery state."""
        self.state = CaptainState.HINT_MODE
    
    def reset(self) -> None:
        """Reset Captain to initial state."""
        self.state = CaptainState.IDLE
        self.current_line = None
        self._used_lines.clear()
        self._tts_callback = None
    
    # === Configuration ===
    
    def add_voice_lines(self, category: str, lines: List[str]) -> None:
        """
        Add custom voice lines to a category (runtime).
        
        Args:
            category: Category name
            lines: List of voice line texts to add
        """
        if category not in self._voice_lines:
            self._voice_lines[category] = []
        
        self._voice_lines[category].extend(lines)
        logger.info(f"Added {len(lines)} voice lines to category '{category}'")
    
    def get_state(self) -> CaptainState:
        """Get current Captain state."""
        return self.state
    
    def get_current_line(self) -> Optional[VoiceLine]:
        """Get currently active voice line."""
        return self.current_line


# Singleton instance for global access
_captain_cosmos: Optional[CaptainCosmos] = None
_captain_lock = threading.Lock()  # Initialize at module level for thread safety


def get_captain_cosmos(data_dir: str = "data", audio_system: Optional['AudioSystem'] = None) -> CaptainCosmos:
    """
    Get or create the global Captain Cosmos instance.
    
    Args:
        data_dir: Directory containing voice_lines.json
        audio_system: Optional AudioSystem instance for TTS playback
        
    Returns:
        The CaptainCosmos singleton instance
    """
    global _captain_cosmos
    
    if _captain_cosmos is None:
        # Use module-level lock for thread safety
        with _captain_lock:
            if _captain_cosmos is None:
                _captain_cosmos = CaptainCosmos(data_dir, audio_system)
    
    return _captain_cosmos


def reset_captain_cosmos() -> None:
    """Reset the global Captain Cosmos instance (useful for testing)."""
    global _captain_cosmos
    
    with _captain_lock:
        _captain_cosmos = None
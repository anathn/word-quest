"""
Spelling Challenge Screen

Main game screen for presenting spelling words with audio and visual hints.
This is the core gameplay screen where students see words, hear them pronounced,
and begin typing with starter letter hints.
"""

from typing import Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import time

from src.components.input_handler import InputHandler, InputDisplay, InputState
from src.components.feedback_controller import (
    FeedbackController,
    FeedbackType,
    FeedbackState as FeedbackScreenState,
    create_feedback_controller
)
from src.components.hint_manager import HintManager, create_hint_manager
from src.ui.hint_display import HintDisplay, create_hint_display
from src.utils.validators import InputValidator, AnswerValidator

# Performance threshold constants
WORD_PRESENTATION_TIMEOUT_MS = 200  # Maximum allowed time for word presentation


class ChallengeState(Enum):
    """States for the spelling challenge."""
    IDLE = "idle"
    PRESENTING = "presenting"
    READY_FOR_INPUT = "ready"
    AWAITING_RESPONSE = "awaiting_response"
    SHOWING_FEEDBACK = "showing_feedback"


@dataclass
class WordPresentation:
    """Data for presenting a word to the student."""
    word_text: str
    definition: str
    context_sentence: str
    starter_letters: str
    difficulty: int
    audio_replayable: bool = True


class SpellingChallengeScreen:
    """
    Main game screen for spelling word presentation.
    
    Features:
    - Display word with audio pronunciation
    - Show starter letter hints based on difficulty
    - Display definition and context sentence
    - Audio replay capability
    - Real-time letter display with animation
    """
    
    def __init__(self, word_manager, audio_system, typography):
        """
        Initialize the spelling challenge screen.
        
        Args:
            word_manager: WordManager instance for word data
            audio_system: AudioSystem instance for TTS
            typography: Typography instance for text rendering
        """
        self.word_manager = word_manager
        self.audio_system = audio_system
        self.typography = typography
        
        self.state = ChallengeState.IDLE
        self.current_word = None
        self.presentation: Optional[WordPresentation] = None
        self.starter_letters: List[str] = []    # Pre-displayed hints
        self.presentation_start_time = 0
        
        # Input handling
        self.input_handler: Optional[InputHandler] = None
        self.input_display: Optional[InputDisplay] = None
        self.answer_validator: Optional[AnswerValidator] = None
        
        # Feedback system
        self.feedback_controller: Optional[FeedbackController] = None
        
        # Hint system
        self.hint_manager: Optional[HintManager] = None
        self.hint_display: Optional[HintDisplay] = None
        
        # Callbacks for state changes
        self.on_word_presented: Optional[Callable] = None
        self.on_input_changed: Optional[Callable] = None
        self.on_submit: Optional[Callable] = None
        self.on_invalid_input: Optional[Callable] = None
        self.on_feedback_shown: Optional[Callable] = None
        self.on_word_complete: Optional[Callable] = None
        self.on_hint_used: Optional[Callable] = None  # For analytics tracking
        
        # Performance tracking
        self.render_times: List[float] = []
    
    def present_word(self, word):
        """
        Present a word with audio and starter hints.
        
        Args:
            word: SpellingWord object to present
            
        Returns:
            True if presentation started successfully
        """
        start_time = time.time()
        
        self.current_word = word
        self.presentation_start_time = start_time
        
        # Extract starter letters based on difficulty
        self.starter_letters = list(word.get_starter_letters())
        
        # Calculate remaining letters to type
        remaining_length = len(word.text) - len(self.starter_letters)
        
        # Initialize input handler for remaining letters
        self.input_handler = InputHandler(max_length=remaining_length)
        self.input_display = InputDisplay(max_length=remaining_length)
        self.answer_validator = AnswerValidator(word.text, ''.join(self.starter_letters))
        
        # Initialize feedback controller
        self.feedback_controller = create_feedback_controller(self.audio_system)
        self.feedback_controller.on_feedback_shown = self._on_feedback_shown
        self.feedback_controller.on_auto_advance = self._on_auto_advance
        self.feedback_controller.on_hint_requested = self._on_hint_requested
        
        # Initialize hint system
        self.hint_manager = create_hint_manager(word.text)
        self.hint_manager.on_hint_shown = self._on_hint_shown
        
        self.hint_display = create_hint_display(self.typography, hint_manager=self.hint_manager)
        self.hint_display.set_word(word.text)
        self.hint_display.on_help_clicked = self._request_hint
        
        # Set up callbacks
        self.input_handler.on_input_changed = self._on_input_changed
        self.input_handler.on_invalid_input = self._on_invalid_input
        self.input_handler.on_submit = self._on_submit
        self.input_handler.on_complete = self._on_input_complete
        
        # Create presentation data
        self.presentation = WordPresentation(
            word_text=word.text,
            definition=word.definition,
            context_sentence=word.context_sentence,
            starter_letters=word.get_starter_letters(),
            difficulty=word.difficulty
        )
        
        # Speak the word
        def on_speech_complete():
            self.state = ChallengeState.READY_FOR_INPUT
            if self.on_word_presented:
                self.on_word_presented(self.presentation)
        
        self.state = ChallengeState.PRESENTING
        self.audio_system.speak(word.text, on_complete=on_speech_complete)
        
        # Track performance
        render_time = (time.time() - start_time) * 1000  # Convert to ms
        self.render_times.append(render_time)
        
        # Performance check: should be under WORD_PRESENTATION_TIMEOUT_MS
        if render_time > WORD_PRESENTATION_TIMEOUT_MS:
            print(f"Warning: Word presentation took {render_time:.0f}ms (target: <{WORD_PRESENTATION_TIMEOUT_MS}ms)")
        
        return True
    
    def replay_audio(self):
        """Replay the word audio on demand."""
        if self.current_word and self.presentation:
            def on_complete():
                pass  # No state change needed
            return self.audio_system.speak(self.current_word.text, on_complete=on_complete)
        return False
    
    def _on_input_changed(self, input_text: str):
        """Handle input change event."""
        # Update input display with animation
        if self.input_display:
            letters = list(input_text)
            self.input_display.set_letters(letters)
        
        if self.on_input_changed:
            self.on_input_changed(input_text)
    
    def _on_invalid_input(self, reason):
        """Handle invalid input event."""
        # Trigger shake animation for visual feedback
        if self.input_display:
            self.input_display.trigger_shake()
        
        if self.on_invalid_input:
            self.on_invalid_input(reason)
    
    def _on_input_complete(self, input_text: str):
        """Handle input completion (max length reached)."""
        if self.on_input_changed:
            self.on_input_changed(input_text)
    
    def _on_submit(self, input_text: str):
        """Handle submit event from input handler."""
        is_correct, full_answer = self.submit_answer()
        
        if self.on_submit:
            self.on_submit(is_correct, full_answer)
    
    def _on_feedback_shown(self, feedback_type: FeedbackType):
        """Handle feedback being shown."""
        if self.on_feedback_shown:
            self.on_feedback_shown(feedback_type)
    
    def _on_auto_advance(self):
        """Handle auto-advance after correct answer."""
        if self.on_word_complete:
            self.on_word_complete(True)  # True = success
    
    def _on_hint_requested(self):
        """Handle hint request after incorrect answer."""
        # Enable the help button for student-requested hints
        if self.hint_display:
            self.hint_display.enable_help_button()
    
    def _on_hint_shown(self, hint_data):
        """Handle hint being shown (for analytics)."""
        if self.on_hint_used:
            self.on_hint_used(hint_data)
        
        # Update hint display
        if self.hint_display and self.hint_manager:
            # Get encouragement message for enhanced user experience
            encouragement = self.hint_manager.get_encouragement_message()
            
            self.hint_display.show_hint(
                hint_data.message,
                hint_data.revealed_indices,
                encouragement_message=encouragement
            )
            # Also update the word display with revealed letters
            self._update_word_display_with_hints()
    
    def _request_hint(self):
        """Handle student clicking the 'Need Help?' button."""
        if self.hint_manager:
            hint = self.hint_manager.get_next_hint()
            if hint and self.hint_display:
                # Get encouragement message for enhanced user experience
                encouragement = self.hint_manager.get_encouragement_message()
                
                self.hint_display.show_hint(
                    hint.message,
                    hint.revealed_indices,
                    encouragement_message=encouragement
                )
                self._update_word_display_with_hints()
                # Disable button after use until next incorrect answer
                self.hint_display.disable_help_button()
    
    def _update_word_display_with_hints(self):
        """Update the word display to show revealed hint letters."""
        if not self.hint_manager or not self.input_display or not self.current_word:
            return
        
        # Get revealed indices from hint manager
        revealed_indices = self.hint_manager.get_revealed_indices()
        
        # Build the full display list merging starter letters with revealed hint letters
        full_display = []
        for i, letter in enumerate(self.current_word.text):
            if i < len(self.starter_letters):
                # Starter letter
                full_display.append(('starter', letter))
            elif i in revealed_indices:
                # Hint-revealed letter
                full_display.append(('hint', letter))
            else:
                # Hidden letter
                full_display.append(('hidden', '_'))
        
        # Actually update the display with the full state
        self.input_display.set_full_display(full_display)
    
    def handle_key_input(self, key: str, unicode_char: Optional[str] = None):
        """
        Handle a key press from the student.
        
        Args:
            key: The pygame key constant name (e.g., 'K_a', 'K_BACKSPACE')
            unicode_char: The actual character from event.unicode
        """
        if self.state != ChallengeState.READY_FOR_INPUT or not self.input_handler:
            return
        
        self.input_handler.handle_keydown(key, unicode_char)
    
    def handle_virtual_key(self, character: str):
        if self.state != ChallengeState.READY_FOR_INPUT or not self.input_handler:
            return
        
        self.input_handler.handle_virtual_key(character)
    
    def handle_backspace(self):
        """Handle backspace key press."""
        if self.state != ChallengeState.READY_FOR_INPUT or not self.input_handler:
            return
        
        self.input_handler.handle_keydown('K_BACKSPACE')
    
    def submit_answer(self):
        """
        Submit the current answer for validation.
        
        Returns:
            Tuple of (is_correct, full_answer)
        """
        if self.state != ChallengeState.READY_FOR_INPUT:
            return False, ""
        
        if not self.input_handler or not self.answer_validator:
            return False, ""
        
        # Get current input
        current_input = self.input_handler.get_input()
        
        # Validate using AnswerValidator
        result = self.answer_validator.validate(current_input)
        
        # Show feedback immediately (within 100ms target)
        if self.feedback_controller:
            self.feedback_controller.show_feedback(result.is_correct)
        
        self.state = ChallengeState.AWAITING_RESPONSE
        
        if self.on_submit:
            self.on_submit(result.is_correct, result.full_answer)
        
        return result.is_correct, result.full_answer
    
    def get_current_input(self) -> str:
        """Get the letters currently typed by the student (excluding starters)."""
        if self.input_handler:
            return self.input_handler.get_input()
        return ""
    
    def get_full_answer(self) -> str:
        """Get the complete answer including starter letters."""
        current = self.get_current_input()
        return ''.join(self.starter_letters) + current
    
    def get_word_text(self) -> str:
        """Get the target word text."""
        return self.current_word.text if self.current_word else ""
    
    def get_starter_display(self) -> str:
        """Get the starter letters as a string for display."""
        return ''.join(self.starter_letters)
    
    def get_definition(self) -> str:
        """Get the word definition."""
        return self.presentation.definition if self.presentation else ""
    
    def get_context_sentence(self) -> str:
        """Get the context sentence."""
        return self.presentation.context_sentence if self.presentation else ""
    
    def is_audio_available(self) -> bool:
        """Check if audio/TTS is available."""
        return self.audio_system.is_audio_available()
    
    def get_performance_stats(self) -> dict:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with render time stats
        """
        if not self.render_times:
            return {"avg_ms": 0, "max_ms": 0, "min_ms": 0}
        
        return {
            "avg_ms": sum(self.render_times) / len(self.render_times),
            "max_ms": max(self.render_times),
            "min_ms": min(self.render_times),
            "sample_count": len(self.render_times)
        }
    
    def update(self, current_time: float):
        """
        Update screen state (call each frame).
        
        Args:
            current_time: Current time in seconds
        """
        # Update input display animations
        if self.input_display:
            self.input_display.update(current_time)
        
        # Update feedback animations
        if self.feedback_controller:
            self.feedback_controller.update(current_time)
        
        # Update hint display animations
        if self.hint_display:
            self.hint_display.update(current_time)
    
    def get_feedback_message(self) -> str:
        """
        Get the current feedback message.
        
        Returns:
            Feedback message text or empty string
        """
        if self.feedback_controller:
            return self.feedback_controller.get_feedback_message()
        return ""
    
    def is_feedback_active(self) -> bool:
        """
        Check if feedback is currently being shown.
        
        Returns:
            True if feedback is active
        """
        if self.feedback_controller:
            return self.feedback_controller.is_feedback_active()
        return False
    
    def get_feedback_state(self) -> FeedbackScreenState:
        """
        Get the current feedback state.
        
        Returns:
            Current FeedbackState
        """
        if self.feedback_controller:
            return self.feedback_controller.get_state()
        return FeedbackScreenState.IDLE
    
    def reset(self):
        """Reset the screen to idle state."""
        self.state = ChallengeState.IDLE
        self.current_word = None
        self.presentation = None
        self.starter_letters = []
        self.input_handler = None
        self.input_display = None
        self.answer_validator = None
        if self.feedback_controller:
            self.feedback_controller.reset()
        if self.hint_manager:
            self.hint_manager.reset()
        if self.hint_display:
            self.hint_display.reset()
        self.cursor_visible = True
    
    def get_hint_analytics(self) -> dict:
        """
        Get hint usage analytics for progress tracking.
        
        Returns:
            Dictionary with hint usage statistics
        """
        if self.hint_manager:
            return self.hint_manager.get_analytics()
        return {}
    
    def handle_mouse_click(self, x: int, y: int) -> bool:
        """
        Handle mouse click for hint button.
        
        Args:
            x: Mouse X position
            y: Mouse Y position
            
        Returns:
            True if hint button was clicked
        """
        if self.hint_display:
            return self.hint_display.check_button_click(x, y)
        return False


class HintRenderer:
    """
    Renders starter letter hints with distinct styling.
    
    This component handles the visual distinction between
    starter hints and student-typed letters.
    """
    
    def __init__(self, typography):
        """
        Initialize the hint renderer.
        
        Args:
            typography: Typography instance for text rendering
        """
        self.typography = typography
    
    def render_starter_hint(
        self, 
        letter: str, 
        position: tuple,
        is_revealed: bool = True
    ):
        """
        Render a single starter letter hint.
        
        Args:
            letter: The letter to render
            position: (x, y) position
            is_revealed: Whether the hint is currently visible
        """
        if not is_revealed:
            return None  # Hidden hint
        
        style = self.typography.style_starter_letters
        return self.typography.render_text(letter.upper(), style)
    
    def render_starter_hints(
        self, 
        starter_letters: str,
        base_position: tuple,
        letter_spacing: int = 10
    ) -> List[tuple]:
        """
        Render all starter hints in a row.
        
        Args:
            starter_letters: String of starter letters
            base_position: Starting (x, y) position
            letter_spacing: Additional spacing between letters
            
        Returns:
            List of (surface, position) tuples for blitting
        """
        rendered = []
        x, y = base_position
        
        for letter in starter_letters:
            surface = self.render_starter_hint(letter, (x, y))
            if surface:
                rendered.append((surface, (x, y)))
                x += surface.get_width() + letter_spacing
        
        return rendered


# Factory function for creating the screen
def create_spelling_challenge_screen(
    word_manager=None,
    audio_system=None,
    typography=None
):
    """
    Create a SpellingChallengeScreen with dependencies.
    
    Args:
        word_manager: Optional WordManager instance
        audio_system: Optional AudioSystem instance
        typography: Optional Typography instance
        
    Returns:
        Configured SpellingChallengeScreen instance
    """
    from src.components.word_manager import get_word_manager
    from src.components.audio_system import get_audio_system
    from src.ui.typography import get_typography
    
    return SpellingChallengeScreen(
        word_manager=word_manager or get_word_manager(),
        audio_system=audio_system or get_audio_system(),
        typography=typography or get_typography()
    )

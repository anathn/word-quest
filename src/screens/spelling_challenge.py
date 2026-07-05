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
        self.displayed_letters: List[str] = []  # Letters student has typed
        self.starter_letters: List[str] = []    # Pre-displayed hints
        self.presentation_start_time = 0
        self.cursor_visible = True
        self.cursor_blink_timer = 0
        
        # Callbacks for state changes
        self.on_word_presented: Optional[Callable] = None
        self.on_input_changed: Optional[Callable] = None
        self.on_submit: Optional[Callable] = None
        
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
        self.displayed_letters = []
        self.presentation_start_time = start_time
        
        # Extract starter letters based on difficulty
        self.starter_letters = list(word.get_starter_letters())
        
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
    
    def handle_key_input(self, key: str):
        """
        Handle a key press from the student.
        
        Args:
            key: The character pressed
        """
        if self.state != ChallengeState.READY_FOR_INPUT:
            return
        
        # Validate input - only allow A-Z characters
        if not key or not key.isalpha() or len(key) != 1:
            return  # Reject non-alphabetic or multi-character input
        
        # Add letter to displayed letters
        self.displayed_letters.append(key.lower())
        self.cursor_visible = True
        
        if self.on_input_changed:
            self.on_input_changed(self.get_current_input())
    
    def handle_backspace(self):
        """Handle backspace key press."""
        if self.state != ChallengeState.READY_FOR_INPUT:
            return
        
        if self.displayed_letters:
            self.displayed_letters.pop()
            self.cursor_visible = True
            
            if self.on_input_changed:
                self.on_input_changed(self.get_current_input())
    
    def submit_answer(self):
        """
        Submit the current answer for validation.
        
        Returns:
            Tuple of (is_correct, full_answer)
        """
        if self.state != ChallengeState.READY_FOR_INPUT:
            return False, ""
        
        full_answer = self.get_full_answer()
        is_correct = self._check_answer(full_answer)
        
        self.state = ChallengeState.AWAITING_RESPONSE
        
        if self.on_submit:
            self.on_submit(is_correct, full_answer)
        
        return is_correct, full_answer
    
    def get_current_input(self) -> str:
        """Get the letters currently typed by the student (excluding starters)."""
        return ''.join(self.displayed_letters)
    
    def get_full_answer(self) -> str:
        """Get the complete answer including starter letters."""
        return ''.join(self.starter_letters) + self.get_current_input()
    
    def _check_answer(self, answer: str) -> bool:
        """
        Check if the answer matches the target word.
        
        Args:
            answer: The student's answer
            
        Returns:
            True if correct, False otherwise
        """
        if not self.current_word:
            return False
        
        # Case-insensitive comparison, strip whitespace
        return answer.strip().lower() == self.current_word.text.lower()
    
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
    
    def reset(self):
        """Reset the screen to idle state."""
        self.state = ChallengeState.IDLE
        self.current_word = None
        self.presentation = None
        self.displayed_letters = []
        self.starter_letters = []
        self.cursor_visible = True


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

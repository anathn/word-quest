"""
Planet Results Screen

Displays planet completion results and determines next actions based on
mastery threshold (4/5 correct unlocks next planet, 2-3/5 retries, 0-1/5 needs help).
"""

from typing import Optional, Callable, List, Dict
from dataclasses import dataclass
from enum import Enum
import time

from src.components.planet_manager import PlanetManager, PlanetStatus, PlanetResult
from src.components.audio_system import AudioSystem
from src.ui.typography import Typography


class ResultsState(Enum):
    """State of the results screen."""
    IDLE = "idle"
    SHOWING_RESULTS = "showing_results"
    AWAITING_ACTION = "awaiting_action"


@dataclass
class WordResultDisplay:
    """Display data for a single word result."""
    word_text: str
    is_correct: bool
    attempts: int
    is_mastered: bool  # First-attempt correct


class PlanetResultsScreen:
    """
    Screen for displaying planet completion results.
    
    Features:
    - Show results for all 5 words in the planet
    - Display mastery status (completed/retry/needs_help)
    - Provide appropriate next action button
    - Play appropriate audio feedback
    - Support accessibility (visual + audio)
    - Trigger planet transition on successful completion (STORY-001-06)
    """
    
    def __init__(self, typography: Typography, audio_system: AudioSystem):
        """
        Initialize the planet results screen.
        
        Args:
            typography: Typography instance for text rendering
            audio_system: AudioSystem instance for audio feedback
        """
        self.typography = typography
        self.audio_system = audio_system
        
        self.state = ResultsState.IDLE
        self.planet_result: Optional[PlanetResult] = None
        self.word_displays: List[WordResultDisplay] = []
        self.results_start_time = 0
        
        # Planet info for transition (STORY-001-06)
        self.current_planet_number: int = 0
        self.total_planets: int = 12
        
        # Callbacks
        self.on_continue: Optional[Callable[[], None]] = None
        self.on_retry: Optional[Callable[[], None]] = None
        self.on_practice: Optional[Callable[[], None]] = None
        self.on_transition_to_next_planet: Optional[Callable[[str, str, int, int, float], None]] = None  # from_planet, to_planet, from_num, to_num, progress
        
        # UI element positions (will be set by game)
        self.title_position = (400, 100)
        self.results_position = (400, 250)
        self.button_position = (400, 500)
    
    def show_results(self, planet_result: PlanetResult):
        """
        Display planet results.
        
        Args:
            planet_result: PlanetResult from PlanetManager
        """
        self.planet_result = planet_result
        self.state = ResultsState.SHOWING_RESULTS
        self.results_start_time = time.time()
        
        # Build word display list
        self.word_displays = [
            WordResultDisplay(
                word_text=wr.word_text,
                is_correct=wr.correct,
                attempts=wr.attempts,
                is_mastered=wr.first_attempt
            )
            for wr in planet_result.word_results
        ]
        
        # Play appropriate audio based on result
        self._play_result_audio()
        
        # Transition to awaiting action after showing results
        self.state = ResultsState.AWAITING_ACTION
    
    def _play_result_audio(self):
        """Play audio feedback based on planet result."""
        if not self.planet_result:
            return
        
        status = self.planet_result.status
        
        if status == PlanetStatus.COMPLETED:
            # Victory fanfare
            self.audio_system.play_victory_fanfare()
            self.audio_system.speak("Planet complete! Great job!")
        elif status == PlanetStatus.RETRY:
            # Encouraging tone
            self.audio_system.play_encouraging_tone()
            self.audio_system.speak(f"Good effort! {self.planet_result.first_attempt_correct} out of 5 words mastered.")
        else:  # NEEDS_HELP
            # Gentle, supportive message
            self.audio_system.play_gentle_tone()
            self.audio_system.speak(f"Let's practice more. {self.planet_result.first_attempt_correct} out of 5 words mastered.")
    
    def get_title_text(self) -> str:
        """Get the title text for the results screen."""
        if not self.planet_result:
            return ""
        
        status = self.planet_result.status
        
        if status == PlanetStatus.COMPLETED:
            return "Planet Complete!"
        elif status == PlanetStatus.RETRY:
            return "Good Effort!"
        else:  # NEEDS_HELP
            return "Let's Practice More"
    
    def get_summary_text(self) -> str:
        """Get the summary text for the results screen."""
        if not self.planet_result:
            return ""
        
        status = self.planet_result.status
        correct = self.planet_result.first_attempt_correct
        total = self.planet_result.total_words
        
        if status == PlanetStatus.COMPLETED:
            return f"You mastered {correct} out of {total} words on the first try!"
        elif status == PlanetStatus.RETRY:
            return f"You mastered {correct} out of {total} words. Let's try again!"
        else:  # NEEDS_HELP
            return f"You mastered {correct} out of {total} words. Let's practice more!"
    
    def get_action_button_text(self) -> str:
        """Get the text for the action button."""
        if not self.planet_result:
            return "Continue"
        
        status = self.planet_result.status
        
        if status == PlanetStatus.COMPLETED:
            return "Continue to Next Planet"
        elif status == PlanetStatus.RETRY:
            return "Try Again"
        else:  # NEEDS_HELP
            return "Practice More"
    
    def get_action_button_color(self) -> tuple:
        """Get the color for the action button."""
        if not self.planet_result:
            return (255, 255, 255)  # White
        
        status = self.planet_result.status
        
        if status == PlanetStatus.COMPLETED:
            return (34, 139, 34)  # Forest green
        elif status == PlanetStatus.RETRY:
            return (255, 140, 0)  # Dark orange
        else:  # NEEDS_HELP
            return (30, 144, 255)  # Dodger blue
    
    def handle_action_button_click(self):
        """Handle action button click."""
        if not self.planet_result:
            return
        
        status = self.planet_result.status
        
        if status == PlanetStatus.COMPLETED:
            # Trigger transition to next planet (STORY-001-06)
            if self.on_transition_to_next_planet and self.planet_result.unlock_next:
                # Calculate planet numbers
                from_planet_num = self.current_planet_number
                to_planet_num = from_planet_num + 1
                progress = to_planet_num / self.total_planets
                
                self.on_transition_to_next_planet(
                    self.planet_result.planet_name,
                    f"Planet {self.planet_result.planet_name}",  # to_planet name
                    from_planet_num,
                    to_planet_num,
                    progress
                )
            elif self.on_continue:
                self.on_continue()
        elif status == PlanetStatus.RETRY:
            if self.on_retry:
                self.on_retry()
        else:  # NEEDS_HELP
            if self.on_practice:
                self.on_practice()
    
    def get_word_results_display(self) -> List[WordResultDisplay]:
        """Get the list of word results for display."""
        return self.word_displays.copy()
    
    def is_mastered(self) -> bool:
        """Check if the planet was mastered (4+ first-attempt correct)."""
        return self.planet_result is not None and self.planet_result.status == PlanetStatus.COMPLETED
    
    def needs_retry(self) -> bool:
        """Check if the planet needs to be retried (2-3 first-attempt correct)."""
        return self.planet_result is not None and self.planet_result.status == PlanetStatus.RETRY
    
    def needs_help(self) -> bool:
        """Check if the student needs help (0-1 first-attempt correct)."""
        return self.planet_result is not None and self.planet_result.status == PlanetStatus.NEEDS_HELP
    
    def should_unlock_next(self) -> bool:
        """Check if the next planet should be unlocked."""
        return self.planet_result is not None and self.planet_result.unlock_next
    
    def should_notify_parent(self) -> bool:
        """Check if parent notification should be triggered."""
        return self.planet_result is not None and self.planet_result.notify_parent
    
    def get_progress_percent(self) -> float:
        """Get the mastery percentage."""
        if not self.planet_result or self.planet_result.total_words == 0:
            return 0.0
        return self.planet_result.first_attempt_correct / self.planet_result.total_words
    
    def set_planet_info(self, planet_number: int, total_planets: int):
        """
        Set planet information for transition tracking.
        
        Args:
            planet_number: Current planet number (1-indexed)
            total_planets: Total planets in the galaxy
        """
        self.current_planet_number = planet_number
        self.total_planets = total_planets
    
    def update(self, current_time: float):
        """
        Update screen state (call each frame).
        
        Args:
            current_time: Current time in seconds
        """
        # Animation updates if needed
        pass
    
    def get_performance_ms(self) -> float:
        """
        Get time elapsed since results display started.
        
        Returns:
            Time in milliseconds since show_results was called
        """
        if self.results_start_time == 0:
            return 0.0
        import time
        return (time.time() - self.results_start_time) * 1000
    
    def reset(self):
        """
        Reset the screen to idle state.
        
        Clears all result data and returns to initial state.
        """
        self.state = ResultsState.IDLE
        self.planet_result = None
        self.word_displays.clear()
        self.results_start_time = 0


# Factory function
def create_planet_results_screen(typography: Typography, audio_system: AudioSystem) -> PlanetResultsScreen:
    """
    Create a PlanetResultsScreen instance.
    
    Args:
        typography: Typography instance
        audio_system: AudioSystem instance
        
    Returns:
        Configured PlanetResultsScreen instance
    """
    return PlanetResultsScreen(typography, audio_system)

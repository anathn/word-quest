"""
Planet Manager Component

Manages planet state, word sets, and completion logic.
Tracks word performance within a planet (5-word set) and determines
mastery based on the 80% threshold.
"""

from typing import List, Dict, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import random


class PlanetStatus(Enum):
    """Status of a planet's completion."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    RETRY = "retry"
    NEEDS_HELP = "needs_help"


@dataclass
class WordResult:
    """Result data for a single word attempt."""
    word_id: str
    word_text: str
    correct: bool
    attempts: int
    first_attempt: bool = field(init=False)
    
    def __post_init__(self):
        self.first_attempt = self.attempts == 1


@dataclass
class PlanetResult:
    """Result data for an entire planet."""
    planet_id: str
    planet_name: str
    total_words: int
    correct_words: int
    first_attempt_correct: int
    status: PlanetStatus
    word_results: List[WordResult] = field(default_factory=list)
    notify_parent: bool = False
    unlock_next: bool = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'planet_id': self.planet_id,
            'planet_name': self.planet_name,
            'total_words': self.total_words,
            'correct_words': self.correct_words,
            'first_attempt_correct': self.first_attempt_correct,
            'status': self.status.value,
            'notify_parent': self.notify_parent,
            'unlock_next': self.unlock_next,
            'word_results': [
                {
                    'word_id': wr.word_id,
                    'word_text': wr.word_text,
                    'correct': wr.correct,
                    'attempts': wr.attempts,
                    'first_attempt': wr.first_attempt
                }
                for wr in self.word_results
            ]
        }


class PlanetManager:
    """
    Manages planet state and completion logic.
    
    Features:
    - Track word results within a planet (5-word set)
    - Determine mastery based on first-attempt accuracy
    - 4/5 correct (80%) unlocks next planet
    - 2-3/5 correct replays same planet
    - 0-1/5 correct triggers parent notification
    """
    
    WORDS_PER_PLANET = 5
    MASTERY_THRESHOLD = 4  # 4/5 = 80%
    RETRY_THRESHOLD = 2    # 2/5 minimum for retry (not needs_help)
    
    def __init__(self, planet_id: str, planet_name: str, word_list: List):
        """
        Initialize the planet manager.
        
        Args:
            planet_id: Unique identifier for the planet
            planet_name: Display name for the planet
            word_list: List of SpellingWord objects for this planet
            
        Raises:
            ValueError: If word_list is empty
        """
        if not word_list:
            raise ValueError(f"Planet {planet_id} must have at least 1 word")
        
        self.planet_id = planet_id
        self.planet_name = planet_name
        self.words = word_list[:self.WORDS_PER_PLANET]  # Ensure exactly 5 words
        self.word_results: List[WordResult] = []
        self.current_word_index = 0
        self.is_complete = False
        
        # Callback for analytics
        self.on_word_recorded: Optional[Callable[[Dict], None]] = None
        self.on_planet_complete: Optional[Callable[[PlanetResult], None]] = None
    
    def get_current_word(self):
        """
        Get the current word to present.
        
        Returns:
            The current SpellingWord or None if complete
        """
        if self.current_word_index < len(self.words):
            return self.words[self.current_word_index]
        return None
    
    def get_next_word(self):
        """
        Move to and get the next word.
        
        Returns:
            The next SpellingWord or None if complete
        """
        if self.current_word_index < len(self.words):
            self.current_word_index += 1
            return self.get_current_word()
        return None
    
    def get_word_index(self) -> int:
        """Get the current word index (0-based)."""
        return self.current_word_index
    
    def get_words_remaining(self) -> int:
        """Get the number of words remaining in the planet."""
        return self.WORDS_PER_PLANET - len(self.word_results)
    
    def record_word_result(self, word_id: str, word_text: str, correct: bool, attempts: int):
        """
        Record the result for a word.
        
        Args:
            word_id: Unique identifier for the word
            word_text: The word text
            correct: Whether the word was spelled correctly
            attempts: Number of attempts to spell the word correctly
        """
        result = WordResult(
            word_id=word_id,
            word_text=word_text,
            correct=correct,
            attempts=attempts
        )
        self.word_results.append(result)
        
        # Notify callback
        if self.on_word_recorded:
            self.on_word_recorded({
                'word_id': word_id,
                'correct': correct,
                'attempts': attempts,
                'first_attempt': result.first_attempt,
                'progress': f"{len(self.word_results)}/{self.WORDS_PER_PLANET} words"
            })
        
        # Check if planet is complete
        if len(self.word_results) >= self.WORDS_PER_PLANET:
            self.is_complete = True
            if self.on_planet_complete:
                planet_result = self.get_completion_status()
                self.on_planet_complete(planet_result)
    
    def get_completion_status(self) -> PlanetResult:
        """
        Determine the planet completion status.
        
        Returns:
            PlanetResult with status and metadata
        """
        total = len(self.word_results)
        first_attempt_correct = sum(1 for r in self.word_results if r.first_attempt)
        
        # Determine status
        if total < self.WORDS_PER_PLANET:
            status = PlanetStatus.IN_PROGRESS
            notify_parent = False
            unlock_next = False
        elif first_attempt_correct >= self.MASTERY_THRESHOLD:
            status = PlanetStatus.COMPLETED
            notify_parent = False
            unlock_next = True
        elif first_attempt_correct >= self.RETRY_THRESHOLD:
            status = PlanetStatus.RETRY
            notify_parent = False
            unlock_next = False
        else:
            status = PlanetStatus.NEEDS_HELP
            notify_parent = True
            unlock_next = False
        
        return PlanetResult(
            planet_id=self.planet_id,
            planet_name=self.planet_name,
            total_words=self.WORDS_PER_PLANET,
            correct_words=first_attempt_correct,
            first_attempt_correct=first_attempt_correct,
            status=status,
            word_results=self.word_results.copy(),
            notify_parent=notify_parent,
            unlock_next=unlock_next
        )
    
    def get_progress_text(self) -> str:
        """
        Get a progress string for display.
        
        Returns:
            Progress text like "3/5 words"
        """
        return f"{len(self.word_results)}/{self.WORDS_PER_PLANET} words"
    
    def get_progress_percent(self) -> float:
        """
        Get progress as a percentage.
        
        Returns:
            Progress percentage (0.0 to 1.0)
        """
        return len(self.word_results) / self.WORDS_PER_PLANET
    
    def get_status_message(self) -> str:
        """
        Get a user-friendly status message.
        
        Returns:
            Status message for display
        """
        status = self.get_completion_status()
        
        if status.status == PlanetStatus.IN_PROGRESS:
            return f"Keep going! {len(self.word_results)}/{self.WORDS_PER_PLANET} words done."
        elif status.status == PlanetStatus.COMPLETED:
            return "Planet Complete! Great job!"
        elif status.status == PlanetStatus.RETRY:
            return "Good effort! Let's try again."
        else:  # NEEDS_HELP
            return "Let's practice more. You can do it!"
    
    def get_encouragement_message(self) -> str:
        """
        Get an encouragement message based on progress.
        
        Returns:
            Encouraging message for the student
        """
        status = self.get_completion_status()
        
        if status.status == PlanetStatus.COMPLETED:
            messages = [
                "Amazing! You mastered this planet!",
                "Fantastic spelling! Planet complete!",
                "You're a spelling superstar!",
                "Perfect! Next planet awaits!"
            ]
        elif status.status == PlanetStatus.RETRY:
            messages = [
                "Good effort! Let's try again.",
                "You're getting there! One more time.",
                "Keep practicing, you'll get it!",
                "Almost there! Try again."
            ]
        elif status.status == PlanetStatus.NEEDS_HELP:
            messages = [
                "Let's practice more. You can do it!",
                "Don't give up! Practice makes perfect.",
                "I believe in you! Let's try again.",
                "Every expert was once a beginner!"
            ]
        else:
            messages = [
                "You're doing great!",
                "Keep up the good work!",
                "Great job so far!",
                "Keep going!"
            ]
        
        return random.choice(messages)
    
    def reset(self):
        """Reset the planet manager for a retry."""
        self.word_results.clear()
        self.current_word_index = 0
        self.is_complete = False
    
    def shuffle_words(self):
        """Shuffle the word order for retry sessions."""
        random.shuffle(self.words)
    
    def get_word_results(self) -> List[WordResult]:
        """Get all word results."""
        return self.word_results.copy()
    
    def is_planet_complete(self) -> bool:
        """Check if the planet is complete."""
        return self.is_complete


# Factory function
def create_planet_manager(planet_id: str, planet_name: str, word_list: List) -> PlanetManager:
    """
    Create a PlanetManager instance.
    
    Args:
        planet_id: Planet identifier
        planet_name: Planet display name
        word_list: List of words for this planet
        
    Returns:
        Configured PlanetManager instance
    """
    return PlanetManager(planet_id, planet_name, word_list)

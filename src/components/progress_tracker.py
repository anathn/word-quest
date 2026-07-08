"""
Progress Tracker Component

Tracks student progress including hint usage, attempts, and session data.
Integrates SessionTracker from STORY-002-01 for comprehensive session metrics.
"""

from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
import time
from unittest.mock import MagicMock

from src.components.planet_manager import PlanetManager, PlanetResult
from src.components.session_tracker import SessionTracker, create_session_tracker

# TYPE_CHECKING for circular import avoidance
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.components.data_store import DataStore


@dataclass
class LegacyWordAttempt:
    """Legacy data for a single word attempt (for backward compatibility).
    
    Note: Use session_tracker.WordAttempt for new session tracking code.
    """
    word_id: str
    word_text: str
    attempts: int = 0
    hints_used: int = 0
    first_attempt_correct: bool = True
    completion_time: float = 0.0  # Seconds
    timestamp: float = 0.0


@dataclass
class PlanetData:
    """Data for a planet's word set."""
    planet_id: str
    planet_name: str
    words_completed: int = 0
    first_attempt_correct: int = 0
    total_attempts: int = 0
    word_results: List[Dict] = field(default_factory=list)


@dataclass
class SessionData:
    """Data for a practice session."""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    words_attempted: int = 0
    words_correct: int = 0
    total_hints_used: int = 0
    word_attempts: List[LegacyWordAttempt] = field(default_factory=list)
    current_planet_id: Optional[str] = None
    planets_completed: List[PlanetData] = field(default_factory=list)


@dataclass
class GalaxyProgress:
    """Galaxy/solar system progress tracking."""
    total_planets: int = 0  # Must be explicitly configured from word list metadata
    completed_planets: int = 0
    current_planet_number: int = 1
    unlocked_planets: int = 0  # Begins locked until total_planets is set


class ProgressTracker:
    """
    Tracks student progress for analytics.
    
    Features (MVP - STORY-001-04):
    - Track hint usage per word
    - Track attempts per word
    - Basic session data collection
    
    Features (STORY-001-05):
    - Planet-level tracking
    - Mastery threshold detection
    
    Features (STORY-001-06):
    - Galaxy progress tracking
    
    Features (STORY-002-01):
    - Full session metrics via SessionTracker
    - Accuracy rate calculation
    - Time spent tracking
    - Streak tracking
    
    Features (STORY-002-03):
    - Words mastered tracking (100% first-attempt accuracy)
    - Progress display in "X/Y words" format
    - Real-time counter updates
    """
    
    def __init__(
        self,
        student_id: str = "student_1",
        data_store: Optional['DataStore'] = None
    ):
        """
        Initialize the progress tracker.
        
        Args:
            student_id: Unique identifier for the student
            data_store: Optional DataStore instance for persistence (STORY-002-02)
        """
        # Legacy session tracking (maintained for compatibility)
        self.current_session: Optional[SessionData] = None
        self.word_history: Dict[str, LegacyWordAttempt] = {}
        self.sessions: List[SessionData] = []
        
        # Current word tracking
        self.current_word_id: Optional[str] = None
        self.current_word_start_time: Optional[float] = None
        
        # Planet tracking (STORY-001-05)
        self.current_planet_id: Optional[str] = None
        self.current_planet_name: Optional[str] = None
        self.planet_word_results: List[Dict] = []
        
        # Galaxy tracking (STORY-001-06)
        self.galaxy_progress = GalaxyProgress()
        
        # Data store for persistence (STORY-002-02)
        self.data_store = data_store
        
        # Session tracker (STORY-002-01) - now with optional persistence
        self.session_tracker = create_session_tracker(
            student_id=student_id,
            data_store=data_store
        )
        
        # Mastered words tracking (STORY-002-03)
        self.mastered_words: Set[str] = set()
        self.total_words_in_list: int = 0
        
        # Callbacks for analytics
        self.on_hint_used: Optional[Callable[[Dict], None]] = None
        self.on_word_complete: Optional[Callable[[Dict], None]] = None
        self.on_planet_complete: Optional[Callable[[Dict], None]] = None
    
    def start_session(self, session_id: str) -> SessionData:
        """
        Start a new practice session.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            The new SessionData object
        """
        self.current_session = SessionData(
            session_id=session_id,
            start_time=time.time()
        )
        self.sessions.append(self.current_session)
        
        # Initialize SessionTracker (STORY-002-01)
        self.session_tracker.start_session(session_id=session_id)
        
        return self.current_session
    
    def end_session(self):
        """End the current session."""
        if self.current_session:
            self.current_session.end_time = time.time()
            self.current_session = None
            
            # Complete session in SessionTracker (STORY-002-01)
            self.session_tracker.complete_session()
    
    def start_word(self, word_id: str, word_text: str):
        """
        Start tracking a new word.
        
        Args:
            word_id: Unique identifier for the word
            word_text: The word text
        """
        # End previous word tracking if any
        if self.current_word_id:
            self._complete_word_tracking()
        
        self.current_word_id = word_id
        self.current_word_start_time = time.time()
        
        # Initialize or update word attempt data
        if word_id not in self.word_history:
            self.word_history[word_id] = LegacyWordAttempt(
                word_id=word_id,
                word_text=word_text
            )
        
        # Track with SessionTracker (STORY-002-01)
        self.session_tracker.start_word(word_id, word_text)
    
    def record_attempt(self, is_correct: bool):
        """
        Record an attempt on the current word.
        
        Args:
            is_correct: Whether the attempt was correct
        """
        if not self.current_word_id:
            return
        
        legacy_attempt = self.word_history[self.current_word_id]
        legacy_attempt.attempts += 1
        
        if legacy_attempt.attempts == 1:
            legacy_attempt.first_attempt_correct = is_correct
        
        if self.current_session:
            self.current_session.words_attempted += 1
            if is_correct:
                self.current_session.words_correct += 1
        
        # Track with SessionTracker (STORY-002-01)
        self.session_tracker.record_attempt(is_correct)
    
    def record_hint_usage(self, hint_count: int = 1):
        """
        Record hint usage for the current word.
        
        Args:
            hint_count: Number of hints used (default 1)
        """
        if not self.current_word_id:
            return
        
        legacy_attempt = self.word_history[self.current_word_id]
        legacy_attempt.hints_used += hint_count
        
        if self.current_session:
            self.current_session.total_hints_used += hint_count
        
        # Track with SessionTracker (STORY-002-01)
        for _ in range(hint_count):
            self.session_tracker.record_hint()
        
        # Notify callback
        if self.on_hint_used:
            self.on_hint_used({
                'word_id': self.current_word_id,
                'hints_used': legacy_attempt.hints_used
            })
    
    def complete_word(self, is_correct: bool):
        """
        Mark the current word as complete.
        
        Args:
            is_correct: Whether the final answer was correct
        """
        self.record_attempt(is_correct)
        
        # Check if word is mastered (STORY-002-03) BEFORE completing tracking
        # Word is mastered if spelled correctly on first attempt with no hints
        mastered_newly = False
        if self.current_word_id and is_correct:
            legacy_attempt = self.word_history.get(self.current_word_id)
            if legacy_attempt and legacy_attempt.attempts == 1 and legacy_attempt.hints_used == 0:
                mastered_newly = self.mark_word_mastered(self.current_word_id)
        
        self._complete_word_tracking()
        
        # Track with SessionTracker (STORY-002-01)
        self.session_tracker.complete_word(is_correct)
        
        # Notify callback
        if self.on_word_complete and self.current_word_id:
            legacy_attempt = self.word_history[self.current_word_id]
            self.on_word_complete({
                'word_id': self.current_word_id,
                'attempts': legacy_attempt.attempts,
                'hints_used': legacy_attempt.hints_used,
                'is_correct': is_correct,
                'just_mastered': mastered_newly
            })
    
    def _complete_word_tracking(self):
        """Complete tracking for the current word."""
        if self.current_word_id and self.current_word_start_time:
            # Update completion time
            if self.current_word_id in self.word_history:
                self.word_history[self.current_word_id].completion_time = (
                    time.time() - self.current_word_start_time
                )
        
        self.current_word_id = None
        self.current_word_start_time = None
    
    # Words Mastered Methods (STORY-002-03)
    
    def get_word_stats(self, word_id: str) -> Optional[LegacyWordAttempt]:
        """
        Get statistics for a specific word.
        
        Args:
            word_id: The word identifier
            
        Returns:
            WordAttempt data or None
        """
        return self.word_history.get(word_id)
    
    def get_words_needing_practice(self, min_attempts: int = 2) -> List[LegacyWordAttempt]:
        """
        Get list of words that need more practice.
        
        Args:
            min_attempts: Minimum attempts to be considered for practice
            
        Returns:
            List of WordAttempt objects sorted by attempts (descending)
        """
        words = [
            wa for wa in self.word_history.values()
            if wa.attempts >= min_attempts
        ]
        return sorted(words, key=lambda w: w.attempts, reverse=True)
    
    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """
        Get statistics for a specific session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Dictionary with session statistics
        """
        for session in self.sessions:
            if session.session_id == session_id:
                return {
                    'session_id': session.session_id,
                    'duration': (session.end_time or time.time()) - session.start_time,
                    'words_attempted': session.words_attempted,
                    'words_correct': session.words_correct,
                    'accuracy': (
                        session.words_correct / session.words_attempted
                        if session.words_attempted > 0 else 0
                    ),
                    'total_hints_used': session.total_hints_used
                }
        return None
    
    def get_overall_stats(self) -> Dict:
        """
        Get overall progress statistics.
        
        Returns:
            Dictionary with overall statistics
        """
        total_attempts = sum(wa.attempts for wa in self.word_history.values())
        total_correct = sum(
            1 for wa in self.word_history.values()
            if wa.first_attempt_correct
        )
        
        return {
            'total_words': len(self.word_history),
            'total_attempts': total_attempts,
            'first_attempt_correct': total_correct,
            'overall_accuracy': total_correct / len(self.word_history) if self.word_history else 0,
            'total_hints_used': sum(wa.hints_used for wa in self.word_history.values()),
            'sessions_completed': len(self.sessions)
        }
    
    def start_planet(self, planet_id: str, planet_name: str):
        """
        Start tracking a new planet.
        
        Args:
            planet_id: Unique identifier for the planet
            planet_name: Display name for the planet
        """
        self.current_planet_id = planet_id
        self.current_planet_name = planet_name
        self.planet_word_results.clear()
        
        if self.current_session:
            self.current_session.current_planet_id = planet_id
    
    def record_planet_word_result(self, word_id: str, word_text: str, correct: bool, attempts: int):
        """
        Record a word result for the current planet.
        
        Args:
            word_id: The word identifier
            word_text: The word text
            correct: Whether the word was spelled correctly
            attempts: Number of attempts
        """
        result = {
            'word_id': word_id,
            'word_text': word_text,
            'correct': correct,
            'attempts': attempts,
            'first_attempt': attempts == 1
        }
        self.planet_word_results.append(result)
        
        # Check if planet is complete (5 words)
        if len(self.planet_word_results) >= 5:
            self._complete_planet()
    
    def _complete_planet(self):
        """
        Process planet completion and determine mastery.
        
        Uses PlanetManager logic to determine completion status,
        avoiding duplication of mastery threshold calculations.
        """
        if not self.current_planet_id:
            return
        
        # Create a temporary PlanetManager to determine status
        # This avoids duplicating the mastery threshold logic
        # We pass a dummy word list to satisfy the constructor's validation
        # since we only need the status calculation logic.
        temp_manager = PlanetManager(
            self.current_planet_id,
            self.current_planet_name or '',
            [MagicMock()]  # Dummy word to avoid ValueError
        )
        
        # Manually set word results to match what was tracked
        # We need to create WordResult objects for the calculation
        from src.components.planet_manager import WordResult
        word_results = []
        for r in self.planet_word_results:
            word_results.append(WordResult(
                word_id=r['word_id'],
                word_text=r['word_text'],
                correct=r['correct'],
                attempts=r['attempts']
            ))
        temp_manager.word_results = word_results
        
        # Get completion status from PlanetManager (single source of truth)
        planet_result: PlanetResult = temp_manager.get_completion_status()
        
        # Create planet data for session tracking
        planet_data = PlanetData(
            planet_id=self.current_planet_id,
            planet_name=self.current_planet_name or '',
            words_completed=len(self.planet_word_results),
            first_attempt_correct=planet_result.first_attempt_correct,
            total_attempts=sum(r['attempts'] for r in self.planet_word_results),
            word_results=self.planet_word_results.copy()
        )
        
        if self.current_session:
            self.current_session.planets_completed.append(planet_data)
        
        # Notify callback with status from PlanetManager
        if self.on_planet_complete:
            self.on_planet_complete({
                'planet_id': self.current_planet_id,
                'planet_name': self.current_planet_name,
                'status': planet_result.status.value,
                'first_attempt_correct': planet_result.first_attempt_correct,
                'total_words': 5,
                'unlock_next': planet_result.unlock_next,
                'notify_parent': planet_result.notify_parent,
                'word_results': self.planet_word_results
            })
        
        # Update galaxy progress if planet was completed (STORY-001-06)
        if planet_result.unlock_next:
            self.galaxy_progress.completed_planets += 1
            self.galaxy_progress.current_planet_number = self.galaxy_progress.completed_planets + 1
            self.galaxy_progress.unlocked_planets = min(
                self.galaxy_progress.completed_planets + 1,
                self.galaxy_progress.total_planets
            )
        
        # Reset planet tracking
        self.current_planet_id = None
        self.current_planet_name = None
        self.planet_word_results.clear()
    
    def reset(self):
        """Reset the tracker (useful for testing)."""
        self.current_session = None
        self.word_history.clear()
        self.sessions.clear()
        self.current_word_id = None
        self.current_word_start_time = None
        self.current_planet_id = None
        self.current_planet_name = None
        self.planet_word_results.clear()
        self.galaxy_progress.completed_planets = 0
        self.galaxy_progress.current_planet_number = 1
        self.galaxy_progress.unlocked_planets = 1
        
        # Reset SessionTracker (STORY-002-01)
        self.session_tracker.reset()
        
        # Reset mastered words tracking (STORY-002-03)
        self.mastered_words.clear()
        self.total_words_in_list = 0
    
    # Words Mastered Methods (STORY-002-03)
    
    def mark_word_mastered(self, word_id: str) -> bool:
        """
        Mark a word as mastered (100% first-attempt accuracy).
        
        Args:
            word_id: The word identifier to mark as mastered
            
        Returns:
            True if word was newly mastered, False if already mastered
        """
        if word_id not in self.mastered_words:
            self.mastered_words.add(word_id)
            # TODO: Persist to data_store once STORY-002-02 integration is complete
            return True
        return False
    
    def get_mastered_count(self) -> int:
        """
        Get the count of mastered words.
        
        Returns:
            Number of words mastered
        """
        return len(self.mastered_words)
    
    def get_total_words(self) -> int:
        """
        Get the total number of words in the word list.
        
        Returns:
            Total word count from word list
        """
        return self.total_words_in_list
    
    def set_total_words(self, total: int):
        """
        Set the total number of words in the word list.
        
        Args:
            total: Total word count
        """
        self.total_words_in_list = total
    
    def get_progress_text(self) -> str:
        """
        Get the progress text in "X/Y words" format.
        
        Returns:
            Formatted progress string (e.g., "23/50 words")
        """
        mastered = self.get_mastered_count()
        total = self.get_total_words()
        return f"{mastered}/{total} words"
    
    def get_mastered_words(self) -> Set[str]:
        """
        Get the set of mastered word IDs.
        
        Returns:
            Set of mastered word identifiers
        """
        return self.mastered_words.copy()
    
    def is_word_mastered(self, word_id: str) -> bool:
        """
        Check if a word is mastered.
        
        Args:
            word_id: The word identifier to check
            
        Returns:
            True if word is mastered, False otherwise
        """
        return word_id in self.mastered_words
    
    # Galaxy Progress Methods (STORY-001-06)
    
    def update_galaxy_progress(self, planets_completed: int, total_planets: int):
        """
        Update galaxy progress based on completed planets.
        
        Args:
            planets_completed: Number of planets successfully completed
            total_planets: Total number of planets in the galaxy
        """
        self.galaxy_progress.completed_planets = planets_completed
        self.galaxy_progress.total_planets = total_planets
        self.galaxy_progress.current_planet_number = planets_completed + 1
        self.galaxy_progress.unlocked_planets = min(planets_completed + 1, total_planets)
    
    def get_galaxy_progress_percent(self) -> float:
        """
        Get overall galaxy progress as a percentage.
        
        Returns:
            Progress percentage (0.0 to 1.0)
        """
        if self.galaxy_progress.total_planets == 0:
            return 0.0
        return self.galaxy_progress.completed_planets / self.galaxy_progress.total_planets
    
    def get_current_planet_number(self) -> int:
        """
        Get the current planet number.
        
        Returns:
            Current planet number (1-indexed)
        """
        return self.galaxy_progress.current_planet_number
    
    def get_total_planets(self) -> int:
        """
        Get the total number of planets in the galaxy.
        
        Returns:
            Total planet count
        """
        return self.galaxy_progress.total_planets
    
    def get_unlocked_planets(self) -> int:
        """
        Get the number of unlocked planets.
        
        Returns:
            Number of accessible planets
        """
        return self.galaxy_progress.unlocked_planets
    
    def set_total_planets(self, total: int):
        """
        Set the total number of planets.
        
        Args:
            total: Total planet count
        """
        self.galaxy_progress.total_planets = total


# Factory function
def create_progress_tracker(
    student_id: str = "student_1",
    data_store: Optional['DataStore'] = None
) -> ProgressTracker:
    """
    Create a ProgressTracker instance.
    
    Args:
        student_id: Student identifier
        data_store: Optional DataStore instance for persistence (STORY-002-02)
        
    Returns:
        Configured ProgressTracker instance
    """
    return ProgressTracker(student_id=student_id, data_store=data_store)

"""
Progress Tracker Component

Tracks student progress including hint usage, attempts, and session data.
Integrates SessionTracker from STORY-002-01 for comprehensive session metrics.
"""

from typing import Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
import time
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from src.components.planet_manager import PlanetManager, PlanetResult
from src.components.session_tracker import SessionTracker, create_session_tracker
from src.components.streak_tracker import StreakTracker, create_streak_tracker
from src.components.badge_system import BadgeManager, create_badge_manager

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
    
    Features (STORY-002-04):
    - Accuracy rate calculation
    - Trend analysis (improving/stable/declining)
    - Session comparison
    - Weekly average comparison
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
        self._word_attempt_recorded: bool = False  # Track if record_attempt was called
        
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
        
        # Streak tracker (STORY-004-01)
        self.streak_tracker = create_streak_tracker()
        
        # Badge system (STORY-004-03)
        self.badge_manager = create_badge_manager(student_id=student_id, data_store=data_store)
        
        # Mastered words tracking (STORY-002-03)
        self.mastered_words: Set[str] = set()
        self.total_words_in_list: int = 0
        
        # Load persisted data from DataStore (STORY-002-02 integration)
        if self.data_store:
            load_result = self.data_store.load(student_id)
            if load_result.data:
                # Load mastered words from persistence
                if 'mastered_words' in load_result.data:
                    self.mastered_words = set(load_result.data['mastered_words'])
                # Load total words count from persistence (avoid reset to 0)
                if 'total_words_in_list' in load_result.data:
                    self.total_words_in_list = load_result.data['total_words_in_list']
        
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
        
        # Initialize badge tracking for session (STORY-004-03)
        if self.badge_manager:
            self.badge_manager.start_session()
        
        return self.current_session
    
    def end_session(self):
        """End the current session."""
        if self.current_session:
            self.current_session.end_time = time.time()
            self.current_session = None
            
            # Complete session in SessionTracker (STORY-002-01)
            self.session_tracker.complete_session()
            
            # End badge tracking session and persist (STORY-004-03)
            if self.badge_manager:
                self.badge_manager.end_session()
    
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
        self._word_attempt_recorded = False  # Reset for new word
        
        # Initialize or update word attempt data
        if word_id not in self.word_history:
            self.word_history[word_id] = LegacyWordAttempt(
                word_id=word_id,
                word_text=word_text
            )
        
        # Track with SessionTracker (STORY-002-01)
        self.session_tracker.start_word(word_id, word_text)
        
        # Notify badge manager (STORY-004-03)
        if self.badge_manager:
            self.badge_manager.on_word_started()
    
    def record_attempt(self, is_correct: bool):
        """
        Record an attempt on the current word.
        
        Args:
            is_correct: Whether the attempt was correct
        """
        if not self.current_word_id:
            return
        
        # Track that record_attempt was called
        self._word_attempt_recorded = True
        
        # Update legacy tracking
        legacy_attempt = self.word_history[self.current_word_id]
        legacy_attempt.attempts += 1
        
        if legacy_attempt.attempts == 1:
            legacy_attempt.first_attempt_correct = is_correct
        
        if self.current_session:
            self.current_session.words_attempted += 1
            if is_correct:
                self.current_session.words_correct += 1
        
        # Track with SessionTracker (STORY-002-01) - record each attempt
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
            is_correct: Whether the final answer was correct (used for session tracking)
        """
        # Note: record_attempt should be called before complete_word for each attempt
        # including the final one. If record_attempt was not called, we record the
        # attempt here to handle the case where complete_word is called directly.
        
        # Record the final attempt in legacy tracking only if record_attempt wasn't called
        if not self._word_attempt_recorded:
            self.record_attempt(is_correct)
        
        # Capture session tracker state BEFORE complete_word resets it
        # Word is mastered if spelled correctly on first attempt with no hints (STORY-002-03)
        session_tracker = self.session_tracker
        would_be_mastered = (
            is_correct and 
            session_tracker.is_current_word_mastered(is_correct=is_correct)
        )
        
        # Track with SessionTracker (STORY-002-01) - this records the final attempt
        # if no attempts were recorded yet, otherwise just finalizes the word tracking
        self.session_tracker.complete_word(is_correct)
        
        # Check if word is mastered and mark it
        mastered_newly = False
        if self.current_word_id and would_be_mastered:
            mastered_newly = self.mark_word_mastered(self.current_word_id)
        
        self._complete_word_tracking()
        
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
            
            # Notify badge manager (STORY-004-03)
            if self.badge_manager:
                completion_time = legacy_attempt.completion_time
                self.badge_manager.on_word_completed(
                    attempts=legacy_attempt.attempts,
                    hints_used=legacy_attempt.hints_used,
                    is_first_attempt_correct=(legacy_attempt.attempts == 1 and is_correct),
                    completion_time=completion_time
                )
    
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
    
    def get_words_needing_practice(self, limit: int = 10) -> List[Dict]:
        """Get words that need more practice, sorted by attempts (most first).
        
        Identifies words that were NOT mastered on first attempt and ranks them
        by total attempts (highest attempts = most challenging).
        
        A word is considered "mastered" if it was spelled correctly on the first
        attempt in ANY session. Words that were never mastered on the first attempt
        are included in the practice list.
        
        Args:
            limit: Maximum number of words to return (default 10)
            
        Returns:
            List of dictionaries with:
            - word: The word text
            - attempts: Total attempts for this word
            - first_attempt_correct: Whether first attempt was correct
            - label: Formatted display label (e.g., "because - 3 attempts")
        """
        # Collect words from word_history (STORY-002-04 tracking)
        # This is the authoritative source for attempt counts
        word_attempts = {}  # word_id -> {'word': str, 'attempts': int, 'first_attempt_correct': bool}
        
        for word_id, attempt_data in self.word_history.items():
            # Check if word was ever mastered on first attempt in any session
            # A word is mastered if it's in the mastered_words set
            if word_id not in self.mastered_words:
                word_attempts[word_id] = {
                    'word': attempt_data.word_text,
                    'attempts': attempt_data.attempts,
                    'first_attempt_correct': attempt_data.first_attempt_correct
                }
        
        # Sort by attempts (descending) and return top N
        sorted_words = sorted(
            word_attempts.items(),
            key=lambda x: x[1]['attempts'],
            reverse=True
        )[:limit]
        
        # Format for display
        result = []
        for word_id, data in sorted_words:
            result.append({
                'word': data['word'],
                'attempts': data['attempts'],
                'first_attempt_correct': data['first_attempt_correct'],
                'label': f"{data['word']} - {data['attempts']} attempt{'s' if data['attempts'] != 1 else ''}"
            })
        
        return result
    
    def format_practice_list(self, limit: int = 10) -> List[Dict]:
        """Format practice list for display.
        
        Args:
            limit: Maximum number of words to include
            
        Returns:
            List of formatted practice word entries
        """
        return self.get_words_needing_practice(limit=limit)
    
    def get_practice_list_empty_message(self) -> str:
        """Get encouraging message when no words need practice.
        
        Returns:
            Encouraging message string (matches story specification)
        """
        return "Great job! No words need practice"
    
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
        
        # Notify badge manager about planet completion (STORY-004-03)
        # Perfect planet = 5/5 correct on first attempt
        if self.badge_manager:
            is_perfect = (planet_result.first_attempt_correct == 5)
            self.badge_manager.on_planet_completed(perfect=is_perfect)
        
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
        
        # Reset StreakTracker (STORY-004-01)
        self.streak_tracker.reset()
        
        # Reset BadgeManager session (STORY-004-03)
        if self.badge_manager:
            self.badge_manager.start_session()
        
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
            
            # Persist to data store if available (STORY-002-02 integration)
            if self.data_store:
                # Get current progress data from SessionTracker
                progress_data = {
                    'student_id': self.session_tracker.student_id,
                    'sessions': self.session_tracker.sessions,
                    'mastered_words': list(self.mastered_words),
                    'needs_practice': list(self.session_tracker.needs_practice)
                }
                self.data_store.save(self.session_tracker.student_id, progress_data)
            
            return True
        
        # Notify badge manager for Word Warrior badge (STORY-004-03)
        if self.badge_manager:
            self.badge_manager.on_word_mastered()
        
        return False
    
    # Streak Tracker Methods (STORY-004-01)
    
    def record_correct_answer(self) -> int:
        """Record a correct answer and update streak.
        
        Returns:
            New streak value after incrementing
        """
        streak = self.streak_tracker.record_correct_answer()
        
        # Notify badge manager (STORY-004-03)
        if self.badge_manager:
            self.badge_manager.on_correct_answer(streak=streak)
        
        return streak
    
    def record_incorrect_answer(self) -> None:
        """Record an incorrect answer and reset streak.
        
        Note: This is non-punitive - no negative feedback, just reset.
        """
        self.streak_tracker.record_incorrect_answer()
        
        # Notify badge manager (STORY-004-03)
        if self.badge_manager:
            self.badge_manager.on_incorrect_answer()
    
    def get_current_streak(self) -> int:
        """Get the current streak value.
        
        Returns:
            Current consecutive correct answer count
        """
        return self.streak_tracker.get_current_streak()
    
    def get_best_streak(self) -> int:
        """Get the best streak achieved in this session.
        
        Returns:
            Highest streak reached
        """
        return self.streak_tracker.get_best_streak()
    
    def reset_session_streak(self) -> None:
        """Reset streak for a new session (preserves best streak)."""
        self.streak_tracker.reset_session()
    
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
        
        # Persist total words count if data_store available (STORY-002-02)
        if self.data_store and self.session_tracker:
            progress_data = {
                'student_id': self.session_tracker.student_id,
                'sessions': self.session_tracker.sessions,
                'mastered_words': list(self.mastered_words),
                'needs_practice': list(self.session_tracker.needs_practice),
                'total_words_in_list': self.total_words_in_list
            }
            self.data_store.save(self.session_tracker.student_id, progress_data)
    
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
    
    # Accuracy Rate Calculation Methods (STORY-002-04)
    
    def calculate_accuracy(self, session_id: str = None) -> float:
        """Calculate accuracy percentage for sessions.
        
        Args:
            session_id: Optional specific session ID. If None, calculates
                       across all sessions.
            
        Returns:
            Accuracy percentage (0.0 to 100.0)
        """
        sessions = self.session_tracker.completed_sessions
        
        if not sessions:
            return 0.0
        
        # Filter to specific session if provided
        if session_id:
            sessions = [s for s in sessions if s.session_id == session_id]
            if not sessions:
                return 0.0
        
        # Calculate overall accuracy across selected sessions
        total_correct = 0
        total_attempts = 0
        
        for session in sessions:
            for word in session.words:
                total_correct += 1 if word.correct else 0
                total_attempts += word.total_attempts
        
        if total_attempts == 0:
            return 0.0
        
        return (total_correct / total_attempts) * 100
    
    def get_session_accuracy(self, session_id: str) -> float:
        """Get accuracy for a specific session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Accuracy percentage for the session
        """
        for session in self.session_tracker.completed_sessions:
            if session.session_id == session_id:
                return session.overall_accuracy * 100
        return 0.0
    
    def _get_sorted_sessions(self) -> List:
        """Get completed sessions sorted by start time.
        
        Returns:
            List of SessionSummary objects sorted by start_time
        """
        return sorted(
            self.session_tracker.completed_sessions,
            key=lambda s: s.start_time
        )
    
    def get_accuracy_trend(self) -> str:
        """Determine trend compared to previous session.
        
        Compares current session accuracy to the previous session.
        Trend threshold is 5% (adjustable).
        
        Returns:
            "improving" if accuracy increased by >5%
            "declining" if accuracy decreased by >5%
            "stable" if change is within 5%
            "new" if no previous session to compare
        """
        sessions = self._get_sorted_sessions()
        
        if len(sessions) < 2:
            return "new"
        
        # Compare last session to previous session
        last_accuracy = sessions[-1].overall_accuracy * 100
        prev_accuracy = sessions[-2].overall_accuracy * 100
        
        diff = last_accuracy - prev_accuracy
        
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"
    
    def get_weekly_average_accuracy(self, weeks: int = 1) -> float:
        """Calculate average accuracy over specified weeks.
        
        Args:
            weeks: Number of weeks to calculate average for (default 1)
            
        Returns:
            Average accuracy percentage
        """
        cutoff_date = datetime.now() - timedelta(weeks=weeks)
        relevant_sessions = [
            s for s in self.session_tracker.completed_sessions
            if s.start_time >= cutoff_date
        ]
        
        if not relevant_sessions:
            return 0.0
        
        total_accuracy = sum(s.overall_accuracy * 100 for s in relevant_sessions)
        return total_accuracy / len(relevant_sessions)
    
    def get_accuracy_display(self) -> Dict:
        """Get formatted accuracy display data.
        
        Returns:
            Dictionary with:
            - percentage: Current accuracy (rounded to 1 decimal)
            - trend_symbol: Arrow symbol (↑, →, ↓, -)
            - trend_label: Text description of trend
            - trend: Raw trend value ("improving"/"stable"/"declining"/"new")
        """
        accuracy = self.calculate_accuracy()
        trend = self.get_accuracy_trend()
        
        trend_symbols = {
            "improving": ("↑", "Improving"),
            "stable": ("→", "Stable"),
            "declining": ("↓", "Needs Practice"),
            "new": ("-", "New")
        }
        
        symbol, label = trend_symbols.get(trend, ("?", "Unknown"))
        
        return {
            "percentage": round(accuracy, 1),
            "trend_symbol": symbol,
            "trend_label": label,
            "trend": trend
        }
    
    def get_accuracy_comparison(self) -> Dict:
        """Get detailed accuracy comparison data.
        
        Returns:
            Dictionary with:
            - current_session_accuracy: Most recent session accuracy
            - previous_session_accuracy: Previous session accuracy
            - weekly_average_accuracy: Average over past week
            - trend: Trend indicator
            - improvement_percent: Percent change from previous session
        """
        sessions = self._get_sorted_sessions()
        
        current_accuracy = 0.0
        previous_accuracy = 0.0
        
        if len(sessions) >= 1:
            current_accuracy = sessions[-1].overall_accuracy * 100
        
        if len(sessions) >= 2:
            previous_accuracy = sessions[-2].overall_accuracy * 100
        
        improvement = current_accuracy - previous_accuracy
        
        return {
            "current_session_accuracy": round(current_accuracy, 1),
            "previous_session_accuracy": round(previous_accuracy, 1),
            "weekly_average_accuracy": round(self.get_weekly_average_accuracy(), 1),
            "trend": self.get_accuracy_trend(),
            "improvement_percent": round(improvement, 1)
        }
    
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

"""
Session Tracker Component

Comprehensive session data collection that tracks all relevant metrics during
gameplay for later analysis and progress visualization.

This component implements STORY-002-01: Session Data Collection.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import uuid


@dataclass
class WordAttempt:
    """Data for a single word attempt in a session."""
    word: str
    word_id: str
    correct: bool
    first_attempt_correct: bool
    total_attempts: int
    hints_used: int
    time_seconds: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SessionSummary:
    """Aggregated statistics for a practice session."""
    session_id: str
    student_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    planet_completed: Optional[str] = None
    words: List[WordAttempt] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate session duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def words_attempted(self) -> int:
        """Get total words attempted in session."""
        return len(self.words)
    
    @words_attempted.setter
    def words_attempted(self, value: int):
        """Setter for words_attempted (used internally)."""
        pass  # Read-only property, this just prevents assignment errors
    
    @property
    def words_correct(self) -> int:
        """Get count of words spelled correctly on first attempt."""
        return sum(1 for w in self.words if w.first_attempt_correct)
    

    
    @property
    def accuracy(self) -> float:
        """Calculate first-attempt accuracy rate for the session.
        
        This measures the percentage of words spelled correctly on the first attempt.
        For overall accuracy (correct attempts / total attempts), see overall_accuracy.
        """
        if not self.words:
            return 0.0
        return sum(1 for w in self.words if w.first_attempt_correct) / len(self.words)
    
    @property
    def overall_accuracy(self) -> float:
        """Calculate overall accuracy rate for the session.
        
        This measures the percentage of total attempts that were correct,
        accounting for multiple attempts per word.
        """
        if not self.words:
            return 0.0
        total_correct = sum(1 for w in self.words if w.correct)
        total_attempts = sum(w.total_attempts for w in self.words)
        return total_correct / total_attempts if total_attempts > 0 else 0.0
    
    @property
    def best_streak(self) -> int:
        """Calculate the longest streak of first-attempt correct answers."""
        max_streak = 0
        current_streak = 0
        for word in self.words:
            if word.first_attempt_correct:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        return max_streak
    
    @property
    def total_hints_used(self) -> int:
        """Get total hints used in session."""
        return sum(w.hints_used for w in self.words)
    
    @property
    def avg_time_per_word(self) -> float:
        """Calculate average time spent per word."""
        if not self.words:
            return 0.0
        return sum(w.time_seconds for w in self.words) / len(self.words)
    
    def to_dict(self) -> Dict:
        """Convert session summary to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'student_id': self.student_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'planet_completed': self.planet_completed,
            'words_attempted': self.words_attempted,
            'words_correct': self.words_correct,
            'first_attempt_accuracy': self.accuracy,
            'overall_accuracy': self.overall_accuracy,
            'best_streak': self.best_streak,
            'total_hints_used': self.total_hints_used,
            'avg_time_per_word': self.avg_time_per_word,
            'duration_seconds': self.duration_seconds,
            'words': [
                {
                    'word': w.word,
                    'word_id': w.word_id,
                    'correct': w.correct,
                    'first_attempt_correct': w.first_attempt_correct,
                    'total_attempts': w.total_attempts,
                    'hints_used': w.hints_used,
                    'time_seconds': w.time_seconds,
                    'timestamp': w.timestamp.isoformat()
                }
                for w in self.words
            ]
        }


class SessionTracker:
    """
    Collects and aggregates session metrics for progress tracking.
    
    Features:
    - Track words attempted per session
    - Track first-attempt accuracy per word
    - Track total attempts per word
    - Track time spent on each word (seconds)
    - Track hint usage frequency per word
    - Track session duration (start to end time)
    - Track best streak length in session
    - Tag session with date/time and planet completed
    
    Performance: Data collection adds < 10ms overhead per word
    """
    
    def __init__(self, student_id: str):
        """
        Initialize the session tracker.
        
        Args:
            student_id: Unique identifier for the student
        """
        self.student_id = student_id
        self.current_session: Optional[SessionSummary] = None
        self.completed_sessions: List[SessionSummary] = []
        self.pending_sessions: List[SessionSummary] = []  # Queue for failed saves
        
        # Current word tracking for timing
        self._current_word: Optional[str] = None
        self._current_word_id: Optional[str] = None
        self._word_start_time: Optional[datetime] = None
        self._word_attempts: int = 0
        self._word_hints_used: int = 0
        self._word_first_attempt_correct: Optional[bool] = None  # Track first attempt result
        self._word_final_correct: bool = False  # Track if word was eventually spelled correctly
        
        # Streak tracking
        self._current_streak: int = 0
        self._last_activity: Optional[datetime] = None  # For idle timeout check
        
        # Idle timeout configuration (30 minutes)
        self.IDLE_TIMEOUT_SECONDS = 1800
    
    def _generate_session_id(self) -> str:
        """
        Generate a unique session identifier.
        
        Format: {student_id}_{timestamp}_{uuid_short}
        
        Returns:
            Unique session ID string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{self.student_id}_{timestamp}_{unique_id}"
    
    def start_session(self, session_id: Optional[str] = None) -> SessionSummary:
        """
        Start a new practice session.
        
        Args:
            session_id: Optional custom session ID (auto-generated if not provided)
            
        Returns:
            The new SessionSummary object
        """
        # Validate student_id
        if not self.student_id:
            raise ValueError("student_id cannot be empty")
        
        # End any existing session
        if self.current_session:
            self.complete_session()
        
        self.current_session = SessionSummary(
            session_id=session_id or self._generate_session_id(),
            student_id=self.student_id,
            start_time=datetime.now()
        )
        
        # Reset word tracking
        self._current_word = None
        self._current_word_id = None
        self._word_start_time = None
        self._word_attempts = 0
        self._word_hints_used = 0
        self._current_streak = 0
        self._last_activity = datetime.now()
        
        return self.current_session
    
    def start_word(self, word_id: str, word_text: str):
        """
        Start tracking a new word.
        
        Args:
            word_id: Unique identifier for the word
            word_text: The word text being attempted
        """
        # Check for idle timeout before starting new word
        self.check_idle_timeout()
        
        # Complete tracking for previous word if any
        if self._current_word:
            self._complete_word_tracking()
        
        self._current_word_id = word_id
        self._current_word = word_text
        self._word_start_time = datetime.now()
        self._word_attempts = 0
        self._word_hints_used = 0
        self._word_first_attempt_correct = None
        self._word_final_correct = False
    
    def record_attempt(self, is_correct: bool):
        """
        Record an attempt on the current word.
        
        Args:
            is_correct: Whether the attempt was correct
        """
        if not self._current_word:
            return
        
        # Track if first attempt was correct
        is_first_attempt = (self._word_attempts == 0)
        if is_first_attempt:
            self._word_first_attempt_correct = is_correct
        
        self._word_attempts += 1
        
        # Update last activity for idle timeout
        self._last_activity = datetime.now()
        
        # Track streak (use is_first_attempt, not _word_attempts after increment)
        if is_correct and is_first_attempt:
            self._current_streak += 1
        elif not is_correct:
            self._current_streak = 0
    
    def record_hint(self):
        """Record usage of a hint for the current word."""
        if self._current_word:
            self._word_hints_used += 1
            self._last_activity = datetime.now()
    
    def complete_word(self, is_correct: bool):
        """
        Mark the current word as complete and record all metrics.
        
        Args:
            is_correct: Whether the final answer was correct
        """
        # Record final attempt
        self.record_attempt(is_correct)
        
        # Track final correctness for WordAttempt.correct field
        self._word_final_correct = is_correct
        
        # Complete word tracking and add to session
        self._complete_word_tracking()
        
        # Check for idle timeout
        self.check_idle_timeout()
    
    def _complete_word_tracking(self):
        """Complete tracking for the current word and add to session."""
        if not self._current_word or not self._word_start_time:
            return
        
        # Calculate time spent with error handling
        try:
            time_spent = (datetime.now() - self._word_start_time).total_seconds()
            # Validate time is non-negative (handle edge case where clock adjustments occur)
            time_spent = max(0.0, time_spent)
        except (TypeError, ValueError, OverflowError) as e:
            import logging
            logging.warning(f"Time calculation error: {e}, defaulting to 0")
            time_spent = 0.0
        
        # Determine if first attempt was correct
        # If we never recorded any attempts, default to False
        first_attempt_correct = self._word_first_attempt_correct if self._word_first_attempt_correct is not None else False
        
        # Create word attempt record
        # correct reflects whether the word was eventually spelled correctly
        # Allow total_attempts to be 0 if no attempts were recorded (edge case)
        attempt = WordAttempt(
            word=self._current_word,
            word_id=self._current_word_id or "",
            correct=self._word_final_correct,
            first_attempt_correct=first_attempt_correct,
            total_attempts=self._word_attempts,  # Don't fake 0 as 1
            hints_used=self._word_hints_used,
            time_seconds=time_spent,
            timestamp=datetime.now()
        )
        
        # Add to session
        if self.current_session:
            self.current_session.words.append(attempt)
        
        # Reset word tracking
        self._current_word = None
        self._current_word_id = None
        self._word_start_time = None
        self._word_attempts = 0
        self._word_hints_used = 0
        self._word_first_attempt_correct = None
        self._word_final_correct = False
    
    def complete_session(self, planet: Optional[str] = None) -> Optional[SessionSummary]:
        """
        Complete the current session.
        
        Args:
            planet: Optional planet identifier that was completed
            
        Returns:
            The completed SessionSummary or None if no session active
        """
        if not self.current_session:
            return None
        
        # Complete any word in progress
        if self._current_word:
            self._complete_word_tracking()
        
        # Finalize session
        self.current_session.end_time = datetime.now()
        self.current_session.planet_completed = planet
        
        # Attempt to save session (in-memory for now, TODO: implement persistence)
        session = self.current_session
        if not self.save_session(session):
            # Save failed, queue for later
            self.pending_sessions.append(session)
        
        # Reset current session
        self.current_session = None
        self._current_streak = 0
        self._last_activity = None
        
        return session
    
    def save_session(self, session: SessionSummary) -> bool:
        """
        Attempt to save session to disk.
        
        Args:
            session: The session to save
            
        Returns:
            True if save succeeded, False otherwise
        """
        try:
            # TODO: Implement actual file save (integrate with STORY-002-02)
            # For now, just track in memory
            self.completed_sessions.append(session)
            return True
        except Exception as e:
            import logging
            logging.error(f"Failed to save session: {e}")
            return False
    
    def flush_pending_sessions(self) -> int:
        """
        Retry saving pending sessions from the queue.
        
        Returns:
            Number of sessions successfully saved
        """
        saved_count = 0
        failed = []
        for session in self.pending_sessions:
            if self.save_session(session):
                saved_count += 1
            else:
                failed.append(session)
        self.pending_sessions = failed
        return saved_count
    
    def check_idle_timeout(self):
        """
        Check if idle timeout has been exceeded and auto-complete session if so.
        
        Completes the session if no activity for IDLE_TIMEOUT_SECONDS (30 minutes).
        """
        if not self._last_activity or not self.current_session:
            return
        
        idle_time = (datetime.now() - self._last_activity).total_seconds()
        if idle_time > self.IDLE_TIMEOUT_SECONDS:
            import logging
            logging.info(f"Idle timeout ({idle_time:.0f}s > {self.IDLE_TIMEOUT_SECONDS}s), auto-completing session")
            self.complete_session()
    
    def get_current_session_stats(self) -> Optional[Dict]:
        """
        Get current session statistics (for live display).
        
        Returns:
            Dictionary with current session stats or None
        """
        if not self.current_session:
            return None
        
        return {
            'session_id': self.current_session.session_id,
            'words_attempted': self.current_session.words_attempted,
            'words_correct': self.current_session.words_correct,
            'first_attempt_accuracy': self.current_session.accuracy,
            'overall_accuracy': self.current_session.overall_accuracy,
            'best_streak': self.current_session.best_streak,
            'duration_seconds': self.current_session.duration_seconds,
            'total_hints_used': self.current_session.total_hints_used
        }
    
    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """
        Get statistics for a specific completed session.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Dictionary with session statistics or None
        """
        for session in self.completed_sessions:
            if session.session_id == session_id:
                return session.to_dict()
        return None
    
    def get_all_sessions(self) -> List[Dict]:
        """
        Get all completed sessions.
        
        Returns:
            List of session dictionaries
        """
        return [session.to_dict() for session in self.completed_sessions]
    
    def get_recent_sessions(self, count: int = 10) -> List[Dict]:
        """
        Get the most recent sessions.
        
        Args:
            count: Number of sessions to return
            
        Returns:
            List of recent session dictionaries
        """
        return [session.to_dict() for session in self.completed_sessions[-count:]]
    
    def reset(self):
        """Reset the tracker (useful for testing)."""
        self.current_session = None
        self.completed_sessions.clear()
        self.pending_sessions.clear()
        self._current_word = None
        self._current_word_id = None
        self._word_start_time = None
        self._word_attempts = 0
        self._word_hints_used = 0
        self._current_streak = 0
        self._word_first_attempt_correct = None
        self._word_final_correct = False
        self._last_activity = None


# Factory function
def create_session_tracker(student_id: str = "student_1") -> SessionTracker:
    """
    Create a SessionTracker instance.
    
    Args:
        student_id: Student identifier
        
    Returns:
        Configured SessionTracker instance
    """
    return SessionTracker(student_id=student_id)

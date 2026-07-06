"""
Progress Tracker Component

Tracks student progress including hint usage, attempts, and session data.
This component will be expanded in STORY-002-01 for full session tracking.
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import time


@dataclass
class WordAttempt:
    """Data for a single word attempt."""
    word_id: str
    word_text: str
    attempts: int = 0
    hints_used: int = 0
    first_attempt_correct: bool = True
    completion_time: float = 0.0  # Seconds
    timestamp: float = 0.0


@dataclass
class SessionData:
    """Data for a practice session."""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    words_attempted: int = 0
    words_correct: int = 0
    total_hints_used: int = 0
    word_attempts: List[WordAttempt] = field(default_factory=list)


class ProgressTracker:
    """
    Tracks student progress for analytics.
    
    Features (MVP - STORY-001-04):
    - Track hint usage per word
    - Track attempts per word
    - Basic session data collection
    
    Features (Future - STORY-002-01):
    - Full session metrics
    - Accuracy rate calculation
    - Time spent tracking
    - Streak tracking
    """
    
    def __init__(self):
        """Initialize the progress tracker."""
        self.current_session: Optional[SessionData] = None
        self.word_history: Dict[str, WordAttempt] = {}
        self.sessions: List[SessionData] = []
        
        # Current word tracking
        self.current_word_id: Optional[str] = None
        self.current_word_start_time: Optional[float] = None
        
        # Callbacks for analytics
        self.on_hint_used: Optional[callable] = None
        self.on_word_complete: Optional[callable] = None
    
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
        return self.current_session
    
    def end_session(self):
        """End the current session."""
        if self.current_session:
            self.current_session.end_time = time.time()
            self.current_session = None
    
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
            self.word_history[word_id] = WordAttempt(
                word_id=word_id,
                word_text=word_text
            )
    
    def record_attempt(self, is_correct: bool):
        """
        Record an attempt on the current word.
        
        Args:
            is_correct: Whether the attempt was correct
        """
        if not self.current_word_id:
            return
        
        word_attempt = self.word_history[self.current_word_id]
        word_attempt.attempts += 1
        
        if word_attempt.attempts == 1:
            word_attempt.first_attempt_correct = is_correct
        
        if self.current_session:
            self.current_session.words_attempted += 1
            if is_correct:
                self.current_session.words_correct += 1
    
    def record_hint_usage(self, hint_count: int = 1):
        """
        Record hint usage for the current word.
        
        Args:
            hint_count: Number of hints used (default 1)
        """
        if not self.current_word_id:
            return
        
        word_attempt = self.word_history[self.current_word_id]
        word_attempt.hints_used += hint_count
        
        if self.current_session:
            self.current_session.total_hints_used += hint_count
        
        # Notify callback
        if self.on_hint_used:
            self.on_hint_used({
                'word_id': self.current_word_id,
                'hints_used': word_attempt.hints_used
            })
    
    def complete_word(self, is_correct: bool):
        """
        Mark the current word as complete.
        
        Args:
            is_correct: Whether the final answer was correct
        """
        self.record_attempt(is_correct)
        self._complete_word_tracking()
        
        # Notify callback
        if self.on_word_complete and self.current_word_id:
            word_attempt = self.word_history[self.current_word_id]
            self.on_word_complete({
                'word_id': self.current_word_id,
                'attempts': word_attempt.attempts,
                'hints_used': word_attempt.hints_used,
                'is_correct': is_correct
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
    
    def get_word_stats(self, word_id: str) -> Optional[WordAttempt]:
        """
        Get statistics for a specific word.
        
        Args:
            word_id: The word identifier
            
        Returns:
            WordAttempt data or None
        """
        return self.word_history.get(word_id)
    
    def get_words_needing_practice(self, min_attempts: int = 2) -> List[WordAttempt]:
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
    
    def reset(self):
        """Reset the tracker (useful for testing)."""
        self.current_session = None
        self.word_history.clear()
        self.sessions.clear()
        self.current_word_id = None
        self.current_word_start_time = None


# Factory function
def create_progress_tracker() -> ProgressTracker:
    """
    Create a ProgressTracker instance.
    
    Returns:
        Configured ProgressTracker instance
    """
    return ProgressTracker()

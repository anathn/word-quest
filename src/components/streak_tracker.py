"""
Streak Tracker Component (STORY-004-01)

Tracks consecutive correct answers and maintains streak data across sessions.
Implements non-punitive streak tracking for student motivation.
"""

from typing import Optional


class StreakTracker:
    """
    Manages streak state for consecutive correct answers.
    
    Features:
    - Increment streak on correct answer
    - Reset streak on incorrect answer (no penalty)
    - Track best streak across sessions
    - Persist streak data to profile
    
    The streak is non-punitive: breaking a streak doesn't trigger negative
    feedback or game over, it simply resets the counter to 0.
    """
    
    def __init__(self):
        """Initialize the streak tracker with default values."""
        self._current_streak: int = 0
        self._best_streak: int = 0
        self._streak_start_time: Optional[float] = None
    
    def record_correct_answer(self) -> int:
        """
        Record a correct answer and increment the streak.
        
        Returns:
            The new streak value after incrementing
        """
        self._current_streak += 1
        
        # Update best streak if current exceeds it
        if self._current_streak > self._best_streak:
            self._best_streak = self._current_streak
        
        # Track when streak started (for the first answer)
        if self._current_streak == 1:
            import time
            self._streak_start_time = time.time()
        
        return self._current_streak
    
    def record_incorrect_answer(self) -> None:
        """
        Record an incorrect answer and reset the streak.
        
        Note: This is non-punitive - no negative feedback is triggered,
        the streak simply resets to 0.
        """
        self._current_streak = 0
        self._streak_start_time = None
    
    def get_current_streak(self) -> int:
        """
        Get the current streak value.
        
        Returns:
            Current consecutive correct answer count
        """
        return self._current_streak
    
    def get_best_streak(self) -> int:
        """
        Get the best streak achieved in this session.
        
        Returns:
            Highest streak reached in current session
        """
        return self._best_streak
    
    def get_all_time_best_streak(self) -> int:
        """
        Get the best streak from profile data.
        
        Returns:
            Highest streak ever achieved (persisted)
        """
        # In MVP, this returns the session best.
        # Future: Load from persisted profile data
        return self._best_streak
    
    def set_best_streak(self, best: int) -> None:
        """
        Set the best streak from persisted data.
        
        Args:
            best: Best streak value to restore
        """
        self._best_streak = max(best, self._best_streak)
    
    def reset_session(self) -> None:
        """
        Reset the streak for a new session.
        
        Current streak resets to 0, but best streak persists.
        """
        self._current_streak = 0
        self._streak_start_time = None
        # Note: _best_streak is preserved across sessions
    
    def reset(self) -> None:
        """
        Complete reset (for testing).
        
        Resets both current and best streak.
        """
        self._current_streak = 0
        self._best_streak = 0
        self._streak_start_time = None
    
    def to_dict(self) -> dict:
        """
        Convert streak data to dictionary for serialization.
        
        Returns:
            Dictionary with streak data
        """
        return {
            'current_streak': self._current_streak,
            'best_streak': self._best_streak,
            'streak_start_time': self._streak_start_time
        }
    
    def from_dict(self, data: dict) -> None:
        """
        Restore streak data from dictionary.
        
        Args:
            data: Dictionary with streak data
        """
        self._current_streak = data.get('current_streak', 0)
        self._best_streak = data.get('best_streak', 0)
        self._streak_start_time = data.get('streak_start_time')


# Factory function
def create_streak_tracker() -> StreakTracker:
    """
    Create a StreakTracker instance.
    
    Returns:
        Configured StreakTracker instance
    """
    return StreakTracker()
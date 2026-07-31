"""
Statistics Calculator for Student Progress Stats (STORY-007-04)

Provides age-appropriate statistics calculation and formatting
for the Simple Progress Stats display component.

Focuses on positive, encouraging metrics that celebrate achievements
rather than highlighting failures.
"""

from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class StatsCalculator:
    """
    Calculates and formats statistics for student progress display.
    
    This class converts raw progress data into kid-friendly, encouraging
    statistics that are easy for 3rd graders to understand.
    
    Features:
    - Words mastered count with total curriculum size
    - Kid-friendly accuracy format ("X out of Y times")
    - Best streak achievement display
    - Total practice time in friendly format
    - Today's practice summary
    - Upward trend indicators for improving metrics
    """
    
    def __init__(self, progress_tracker):
        """
        Initialize the stats calculator.
        
        Args:
            progress_tracker: ProgressTracker instance with student progress data
        """
        self.progress = progress_tracker
        self._trend_cache: Dict[str, Tuple[float, datetime]] = {}
    
    def get_words_mastered(self) -> int:
        """
        Get total words mastered count.
        
        Returns:
            Number of words mastered (first-attempt correct, zero hints)
        """
        return self.progress.get_mastered_count()
    
    def get_total_words(self) -> int:
        """
        Get total words in the curriculum.
        
        Returns:
            Total number of words in the word list
        """
        return self.progress.get_total_words()
    
    def get_words_mastered_display(self) -> Dict:
        """
        Get words mastered in display format.
        
        Returns:
            Dictionary with:
            - text: Formatted display text (e.g., "23/50 words")
            - mastered: Number of words mastered
            - total: Total words in curriculum
            - icon: Star emoji
        """
        mastered = self.get_words_mastered()
        total = self.get_total_words()
        
        return {
            "text": f"{mastered}/{total} words",
            "mastered": mastered,
            "total": total,
            "icon": "⭐"
        }
    
    def get_accuracy_display(self) -> Dict:
        """
        Get accuracy rate in kid-friendly format.
        
        Converts percentage to "X out of Y" format for better understanding.
        Always uses encouraging language, never highlights failures.
        
        Returns:
            Dictionary with:
            - text: Encouraging message ("You get it right X out of Y times!")
            - ratio: {"numerator": int, "denominator": int}
            - trend: "up", "stable", "down", or "new"
            - icon: Target emoji
        """
        total_attempts = self._get_total_attempts()
        correct_answers = self._get_total_correct()
        
        if total_attempts == 0:
            return {
                "text": "Keep practicing!",
                "ratio": {"numerator": 0, "denominator": 0},
                "trend": "new",
                "icon": "🎯"
            }
        
        accuracy = correct_answers / total_attempts
        
        # Convert to "X out of Y" format
        # Round to nearest 10 for simplicity (matches story spec)
        denominator = 10
        numerator = round(accuracy * denominator)
        
        # Ensure numerator doesn't exceed denominator
        numerator = min(numerator, denominator)
        
        # Build encouraging message based on accuracy
        if accuracy >= 0.8:
            message = f"You get it right {numerator} out of {denominator} times! Great job!"
        elif accuracy >= 0.5:
            message = f"You get it right {numerator} out of {denominator} times!"
        else:
            message = f"You get it right {numerator} out of {denominator} times - keep practicing!"
        
        return {
            "text": message,
            "ratio": {"numerator": numerator, "denominator": denominator},
            "trend": self.calculate_accuracy_trend(),
            "icon": "🎯"
        }
    
    def get_best_streak_display(self) -> Dict:
        """
        Get best streak achievement display.
        
        Returns:
            Dictionary with:
            - text: Encouraging streak message
            - value: Best streak number
            - icon: Fire emoji
        """
        best_streak = self.progress.get_best_streak()
        
        if best_streak == 0:
            return {
                "text": "Start a streak!",
                "value": 0,
                "icon": "🔥"
            }
        elif best_streak >= 10:
            return {
                "text": f"Your best streak: {best_streak} correct! Amazing!",
                "value": best_streak,
                "icon": "🔥"
            }
        else:
            return {
                "text": f"Your best streak: {best_streak} correct!",
                "value": best_streak,
                "icon": "🔥"
            }
    
    def get_total_practice_time(self) -> Dict:
        """
        Get total practice time in kid-friendly format.
        
        Returns:
            Dictionary with:
            - text: Friendly time display
            - seconds: Total practice time in seconds
            - icon: Timer emoji
        """
        total_seconds = self._get_total_practice_seconds()
        
        if total_seconds < 300:  # Less than 5 minutes
            return {
                "text": "Just getting started!",
                "seconds": total_seconds,
                "icon": "⏱️"
            }
        elif total_seconds < 3600:  # Less than 1 hour
            minutes = total_seconds // 60
            return {
                "text": f"You've practiced for {minutes} minutes!",
                "seconds": total_seconds,
                "icon": "⏱️"
            }
        elif total_seconds < 7200:  # Less than 2 hours
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if minutes > 0:
                return {
                    "text": f"You've practiced for {hours} hour and {minutes} minutes!",
                    "seconds": total_seconds,
                    "icon": "⏱️"
                }
            else:
                return {
                    "text": f"You've practiced for {hours} hour!",
                    "seconds": total_seconds,
                    "icon": "⏱️"
                }
        else:
            hours = total_seconds // 3600
            return {
                "text": f"You've practiced for {hours} hours!",
                "seconds": total_seconds,
                "icon": "⏱️"
            }
    
    def get_today_summary(self) -> Optional[Dict]:
        """
        Get today's practice summary.
        
        Returns:
            Dictionary with:
            - text: Today's summary message
            - words: Total words attempted today
            - correct: Words correct today
            - icon: Calendar emoji
            Or None if no practice today
        """
        today = datetime.now().date()
        today_data = self._get_day_data(today)
        
        if not today_data or today_data['total_count'] == 0:
            return None
        
        correct = today_data['correct_count']
        total = today_data['total_count']
        
        # Use encouraging language, avoid highlighting failures
        if correct > 0:
            text = f"Today: {total} words, {correct} correct!"
        else:
            text = f"Today: {total} words!"
        
        return {
            "text": text,
            "words": total,
            "correct": correct,
            "icon": "📅"
        }
    
    def calculate_accuracy_trend(self) -> str:
        """
        Calculate if accuracy is improving, stable, or declining.
        
        Compares recent week's accuracy to previous week.
        Threshold: 5% change is considered significant.
        
        Returns:
            "up" if improving by >= 5%
            "down" if declining by >= 5%
            "stable" if change is within 5%
            "new" if no previous data to compare
        """
        try:
            recent = self._get_week_accuracy(weeks=1)
            previous = self._get_week_accuracy(weeks=2, offset=1)
            
            if previous == 0:
                return "new"
            
            diff = recent - previous
            
            if diff >= 0.05:
                return "up"  # Improving
            elif diff <= -0.05:
                return "down"  # Declining
            return "stable"
        except Exception as e:
            logger.warning(f"Error calculating accuracy trend: {e}")
            return "new"
    
    def get_all_stats(self) -> Dict:
        """
        Get all statistics in one call.
        
        Returns:
            Dictionary with all stat display data
        """
        return {
            "words_mastered": self.get_words_mastered_display(),
            "accuracy": self.get_accuracy_display(),
            "best_streak": self.get_best_streak_display(),
            "practice_time": self.get_total_practice_time(),
            "today": self.get_today_summary()
        }
    
    # Private helper methods
    
    def _get_total_attempts(self) -> int:
        """Get total attempts across all sessions."""
        return self.progress.session_tracker._get_total_attempts()
    
    def _get_total_correct(self) -> int:
        """Get total correct answers across all sessions."""
        return self.progress.session_tracker._get_total_correct()
    
    def _get_total_practice_seconds(self) -> int:
        """Get total practice time in seconds."""
        return self.progress.session_tracker.get_total_practice_seconds()
    
    def _get_day_data(self, date: datetime.date) -> Optional[Dict]:
        """
        Get practice data for a specific day.
        
        Args:
            date: The date to query
            
        Returns:
            Dictionary with correct_count and total_count, or None if no data
        """
        sessions = self.progress.session_tracker.completed_sessions
        
        # Filter sessions for the specific date
        day_sessions = []
        for session in sessions:
            session_date = datetime.fromtimestamp(session.start_time).date()
            if session_date == date:
                day_sessions.append(session)
        
        if not day_sessions:
            return None
        
        # Aggregate data
        total_correct = 0
        total_count = 0
        
        for session in day_sessions:
            for word in session.words:
                total_count += 1
                if word.correct:
                    total_correct += 1
        
        return {
            'correct_count': total_correct,
            'total_count': total_count
        }
    
    def _get_week_accuracy(self, weeks: int = 1, offset: int = 0) -> float:
        """
        Get average accuracy for a specific week.
        
        Args:
            weeks: Number of weeks to include
            offset: Weeks to offset from current week (0 = current week)
            
        Returns:
            Accuracy percentage (0.0 to 1.0)
        """
        now = datetime.now()
        end_date = now - timedelta(weeks=offset)
        start_date = end_date - timedelta(weeks=weeks)
        
        sessions = self.progress.session_tracker.completed_sessions
        
        # Filter sessions for the date range
        relevant_sessions = []
        for session in sessions:
            session_date = datetime.fromtimestamp(session.start_time)
            if start_date <= session_date < end_date:
                relevant_sessions.append(session)
        
        if not relevant_sessions:
            return 0.0
        
        # Calculate average accuracy
        total_accuracy = sum(s.overall_accuracy for s in relevant_sessions)
        return total_accuracy / len(relevant_sessions)
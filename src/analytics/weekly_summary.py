"""
Weekly Summary Generator

Generates weekly progress summaries from session data.
Implements STORY-003-05: Weekly Summary View
"""

from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any
import logging

from src.models.summary_data import WeeklySummary, Trend
from src.components.session_tracker import SessionTracker, SessionSummary
from src.analytics.trend_calculator import TrendCalculator


logger = logging.getLogger(__name__)


class WeeklySummaryGenerator:
    """
    Generates weekly progress summaries from session data.
    
    This class aggregates session data to produce weekly statistics
    including words mastered, accuracy rates, and practice time.
    """
    
    def __init__(self, session_tracker: SessionTracker):
        """
        Initialize the weekly summary generator.
        
        Args:
            session_tracker: SessionTracker instance with collected session data
        """
        self.session_tracker = session_tracker
        self.trend_calculator = TrendCalculator(self)
    
    def get_week_for_date(self, target_date: date) -> tuple[date, date]:
        """
        Get start (Monday) and end (Sunday) dates for the week containing target_date.
        
        Args:
            target_date: Any date within the desired week
            
        Returns:
            Tuple of (week_start, week_end) dates
        """
        # weekday() returns 0 for Monday, 6 for Sunday
        start = target_date - timedelta(days=target_date.weekday())
        end = start + timedelta(days=6)
        return start, end
    
    def generate_summary(self, student_id: str, target_date: Optional[date] = None, calculate_trends: bool = True) -> WeeklySummary:
        """
        Generate weekly summary for a student.
        
        Args:
            student_id: ID of the student
            target_date: Target date for the week (default: today)
            calculate_trends: Whether to calculate trends (default: True)
            
        Returns:
            WeeklySummary with aggregated statistics
        """
        if target_date is None:
            target_date = date.today()
        
        week_start, week_end = self.get_week_for_date(target_date)
        
        # Get all sessions for this week and student
        sessions = self._get_sessions_for_week(student_id, week_start, week_end)
        
        # Calculate metrics from session data
        words_per_session = []
        correct_answers = 0
        total_attempts = 0
        total_time = 0.0
        word_accuracy: Dict[str, Dict[str, int]] = {}  # word -> {correct: int, total: int}
        best_streak = 0
        current_streak = 0
        
        for session in sessions:
            # Accumulate session time
            total_time += session.duration_seconds / 60.0  # Convert to minutes
            
            for word_attempt in session.words:
                words_per_session.append(word_attempt.word)
                total_attempts += word_attempt.total_attempts
                
                # Track correctness for streak calculation
                # Streak counts consecutive words that were ultimately answered correctly
                # (regardless of whether it was on the first attempt)
                if word_attempt.correct:  # Word was ultimately answered correctly
                    if word_attempt.first_attempt_correct:
                        correct_answers += 1
                    current_streak += 1
                    best_streak = max(best_streak, current_streak)
                else:
                    # Word was never answered correctly - reset streak
                    current_streak = 0
                
                # Track per-word accuracy
                word = word_attempt.word
                if word not in word_accuracy:
                    word_accuracy[word] = {"correct": 0, "total": 0}
                
                word_accuracy[word]["total"] += 1
                if word_attempt.first_attempt_correct:
                    word_accuracy[word]["correct"] += 1
        
        # Calculate derived metrics
        words_practiced = len(set(words_per_session)) if words_per_session else 0
        accuracy_rate = correct_answers / total_attempts if total_attempts > 0 else 0.0
        
        # Words mastered (80%+ accuracy, at least 2 attempts)
        mastered = [
            word for word, data in word_accuracy.items()
            if data["total"] >= 2 and (data["correct"] / data["total"]) >= 0.8
        ]
        
        # Words needing practice (<50% accuracy, at least 3 attempts)
        needing_practice = [
            word for word, data in word_accuracy.items()
            if data["total"] >= 3 and (data["correct"] / data["total"]) < 0.5
        ]
        
        num_sessions = len(sessions)
        summary = WeeklySummary(
            week_start=week_start,
            week_end=week_end,
            student_id=student_id,
            words_mastered=len(mastered),
            words_practiced=words_practiced,
            accuracy_rate=accuracy_rate,
            total_sessions=num_sessions,
            total_time_minutes=int(total_time),
            best_streak=best_streak,
            avg_session_length=total_time / num_sessions if num_sessions > 0 else 0.0,
            words_mastered_list=sorted([w.upper() for w in mastered])[:10],  # Top 10
            words_needing_practice=sorted([w.upper() for w in needing_practice])[:10]
        )
        
        # Add trends by comparing to previous week (only if requested)
        if calculate_trends:
            summary = self.trend_calculator.calculate_trends_for_summary(
                summary, student_id, week_start
            )
        
        logger.info(f"Generated summary for {student_id} week {week_start} to {week_end}: "
                   f"{summary.words_mastered} words mastered, {accuracy_rate:.1%} accuracy")
        
        return summary
    
    def _get_sessions_for_week(self, student_id: str, week_start: date, week_end: date) -> List[SessionSummary]:
        """
        Get all sessions for a student within a week.
        
        Args:
            student_id: ID of the student
            week_start: Start of the week (Monday)
            week_end: End of the week (Sunday)
            
        Returns:
            List of SessionSummary objects
        """
        end_inclusive = week_end + timedelta(days=1)  # Include entire Sunday
        
        # Get sessions from the session tracker
        all_sessions = self.session_tracker.get_all_sessions(student_id)
        
        # Filter sessions that fall within the week
        filtered_sessions = []
        for session in all_sessions:
            try:
                # Handle both datetime objects and ISO format strings
                if isinstance(session.start_time, datetime):
                    session_date = session.start_time.date()
                else:
                    session_date = datetime.fromisoformat(session.start_time).date()
                if week_start <= session_date <= week_end:
                    filtered_sessions.append(session)
            except (ValueError, AttributeError) as e:
                logger.warning(f"Skipping session with invalid date: {e}")
                continue
        
        return filtered_sessions
    
    # Note: Trend calculations are now delegated to TrendCalculator class
    # for better separation of concerns. See trend_calculator.py
    
    def get_weekly_history(self, student_id: str, weeks: int = 4, reference_date: Optional[date] = None) -> List[WeeklySummary]:
        """
        Get summary history for the last N weeks including current week.
        
        Args:
            student_id: ID of the student
            weeks: Number of weeks to include (default: 4)
            reference_date: Reference date for "current" week (default: today)
            
        Returns:
            List of WeeklySummary objects, sorted chronologically
        """
        if reference_date is None:
            reference_date = date.today()
        
        history = []
        for i in range(weeks - 1, -1, -1):
            target_date = reference_date - timedelta(weeks=i)
            try:
                summary = self.generate_summary(student_id, target_date)
                history.append(summary)
            except Exception as e:
                logger.warning(f"Error generating summary for week {i}: {e}")
                # Create empty summary for this week
                week_start, week_end = self.get_week_for_date(target_date)
                empty_summary = WeeklySummary(
                    week_start=week_start,
                    week_end=week_end,
                    student_id=student_id
                )
                history.append(empty_summary)
        
        # Sort by week start date
        return sorted(history, key=lambda s: s.week_start)
    
    def has_sufficient_data(self, student_id: str, min_weeks: int = 2) -> bool:
        """
        Check if there's sufficient data for meaningful trends.
        
        Args:
            student_id: ID of the student
            min_weeks: Minimum number of weeks with data required
            
        Returns:
            True if sufficient data exists
        """
        history = self.get_weekly_history(student_id, weeks=4)
        weeks_with_data = sum(1 for s in history if s.has_data())
        return weeks_with_data >= min_weeks
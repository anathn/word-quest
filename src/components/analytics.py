"""
Analytics Component

Provides data analysis and calculation for progress visualization.
Implements STORY-002-06: Progress Graph (Fluency Trend)

This component calculates weekly averages from session data for graphing.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, NamedTuple
from collections import defaultdict
import logging


class DataPoint(NamedTuple):
    """Represents a single data point on a progress graph."""
    week: str  # Week label (e.g., "2026-W27")
    average: float  # Average attempts per word for that week
    word_count: int  # Number of words attempted that week


class AnalyticsEngine:
    """
    MLearnings analytics engine for calculating progress metrics.
    
    Provides weekly fluency trends from session data.
    """
    
    def __init__(self, sessions: List[Dict]):
        """
        Initialize the analytics engine.
        
        Args:
            sessions: List of session data dictionaries
        """
        self.sessions = sessions
        self._weekly_cache: Optional[Dict] = None
    
    def get_weekly_averages(self, weeks: int = 8, end_date: Optional[datetime] = None) -> List[DataPoint]:
        """Calculate average attempts per word for each week.
        
        Args:
            weeks: Number of weeks to include (default 8)
            end_date: End date for the range (default: today)
            
        Returns:
            List of DataPoint objects, one per week, sorted chronologically.
            Weeks with no data have average=0.
            
        Example:
            analytics = AnalyticsEngine(sessions)
            weekly_data = analytics.get_weekly_averages(weeks=8)
            # Returns: [DataPoint(week='2026-W20', average=2.3, word_count=5), ...]
        """
        if end_date is None:
            end_date = datetime.now()
        
        import calendar
        
        # Clear cache to force recalculation
        self._weekly_cache = None
        
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)
        start_date = end_date - timedelta(weeks=weeks)
        
        # Group sessions by ISO week number
        weekly_data = defaultdict(list)
        
        for session in self.sessions:
            try:
                session_date = datetime.fromisoformat(session['start_time'])
            except (KeyError, ValueError):
                # Skip malformed session data
                continue
            
            # Only include sessions within the requested range
            if session_date < start_date or session_date > end_date:
                continue
            
            # Use ISO calendar for consistent week numbering
            iso_cal = session_date.isocalendar()
            week_key = f"{iso_cal[0]}-W{iso_cal[1]:02d}"
            
            # Collect attempts from all words in this session
            for word in session.get('words', []):
                attempts = word.get('total_attempts', 1)
                if attempts > 0:  # Only count words with actual attempts
                    weekly_data[week_key].append(attempts)
        
        # Calculate averages for each week
        weekly_averages = []
        for week_key, attempts_list in sorted(weekly_data.items()):
            avg = float(sum(attempts_list)) / len(attempts_list) if attempts_list else 0.0
            word_count = len(attempts_list)
            weekly_averages.append(DataPoint(week=week_key, average=avg, word_count=word_count))
        
        # Fill in missing weeks to ensure continuous data
        weekly_averages = self._fill_gaps(weekly_averages, weeks, start_date, end_date)
        
        return weekly_averages
    
    def _fill_gaps(
        self, 
        data: List[DataPoint], 
        weeks: int, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[DataPoint]:
        """Ensure continuous week data by filling missing weeks with zeros.
        
        Args:
            data: Existing data points
            weeks: Number of weeks to include
            start_date: Start of the date range
            end_date: End of the date range
            
        Returns:
            Data points with gaps filled. Uses ISO week numbering.
        """
        # Create a dict of existing data for quick lookup
        existing = {point.week: point for point in data}
        
        # Generate all week keys from end_date going backward
        # This ensures we get the most recent 'weeks' number of ISO weeks
        result = []
        for i in range(weeks - 1, -1, -1):
            check_date = end_date - timedelta(weeks=i)
            iso_cal = check_date.isocalendar()
            week_key = f"{iso_cal[0]}-W{iso_cal[1]:02d}"
            
            if week_key in existing:
                result.insert(0, existing[week_key])
            else:
                # Check if any data point has this week key (handle year boundaries)
                found = False
                for dp in data:
                    if dp.week == week_key:
                        result.insert(0, dp)
                        found = True
                        break
                if not found:
                    result.insert(0, DataPoint(week=week_key, average=0.0, word_count=0))
        
        return result
    
    def _get_week_key(self, week_offset: int, start_date: datetime) -> str:
        """Get the ISO week key for a given offset from start_date.
        
        Args:
            week_offset: Number of weeks from start_date (0 = first week)
            start_date: The reference start date
            
        Returns:
            ISO week string (e.g., "2026-W27")
        """
        target_date = start_date + timedelta(weeks=week_offset)
        iso_cal = target_date.isocalendar()
        return f"{iso_cal[0]}-W{iso_cal[1]:02d}"
    
    def get_trend_direction(self, data: List[DataPoint]) -> str:
        """Determine the overall trend direction from data points.
        
        Args:
            data: List of DataPoint objects in chronological order
            
        Returns:
            "improving" if average attempts are decreasing over time
            "declining" if average attempts are increasing over time
            "stable" if there's minimal change or all data is zero/empty
            "insufficient" if not enough data points
            
        Note: Since lower attempts = better fluency, a downward slope in attempts
              means improvement.
        """
        if len(data) < 2:
            return "insufficient"
        
        # Filter out weeks with no data
        valid_data = [d for d in data if d.word_count > 0]
        
        if len(valid_data) < 2:
            return "insufficient"
        
        # Check if all averages are zero
        all_zeros = all(d.average == 0 for d in valid_data)
        if all_zeros:
            return "stable"
        
        # Compare first and last non-zero weeks
        first_avg = valid_data[0].average
        last_avg = valid_data[-1].average
        
        if first_avg == 0 and last_avg == 0:
            return "stable"
        
        # Calculate percentage change
        try:
            percent_change = ((last_avg - first_avg) / first_avg) * 100 if first_avg > 0 else 0
        except ZeroDivisionError:
            percent_change = 0
        
        if percent_change < -10:
            # Decreasing attempts = improvement
            return "improving"
        elif percent_change > 10:
            # Increasing attempts = declining
            return "declining"
        else:
            return "stable"
    
    def get_insufficient_data_message(self) -> str:
        """Get user-friendly message for insufficient data.
        
        Returns:
            Helpful message string
        """
        return "Not enough data for graph. Complete at least 2 practice sessions."
    
    def calculate_fluency_score(self, data: List[DataPoint]) -> float:
        """Calculate a simple fluency score (lower is better).
        
        Args:
            data: List of DataPoint objects
            
        Returns:
            Fluency score (lower = more fluent)
        """
        valid_data = [d.average for d in data if d.word_count > 0]
        
        if not valid_data:
            return 0.0
        
        # Weight recent weeks more heavily
        weights = [i + 1 for i in range(len(valid_data))]
        total_weight = sum(weights)
        
        weighted_sum = sum(avg * weight for avg, weight in zip(valid_data, weights))
        return weighted_sum / total_weight if total_weight > 0 else 0.0


def create_analytics_engine(sessions: List[Dict]) -> AnalyticsEngine:
    """
    Factory function to create an AnalyticsEngine instance.
    
    Args:
        sessions: List of session data dictionaries
        
    Returns:
        Configured AnalyticsEngine instance
    """
    return AnalyticsEngine(sessions=sessions)
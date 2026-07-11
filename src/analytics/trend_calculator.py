"""  
Trend Calculator

Calculates week-over-week trends for various metrics.
Extracted from WeeklySummaryGenerator for better separation of concerns.
Implements STORY-003-05: Weekly Summary View
"""

from datetime import timedelta, date
from typing import Optional, List

from src.models.summary_data import WeeklySummary, Trend


class TrendCalculator:
    """
    Calculates trends for weekly metrics by comparing to previous periods.
    
    This class is responsible for determining whether metrics are improving,
    declining, or stable compared to previous weeks.
    """
    
    # Thresholds for trend determination
    ACCURACY_TRESHOLD = 0.05  # 5% change is significant
    MASTERED_THRESHOLD = 2    # More than 2 words difference is significant
    
    def __init__(self, summary_generator):
        """
        Initialize the trend calculator.
        
        Args:
            summary_generator: WeeklySummaryGenerator for fetching summary data
        """
        self.summary_generator = summary_generator
    
    def calculate_accuracy_trend(self, student_id: str, current_week_start: date) -> Optional[Trend]:
        """
        Compare accuracy to previous week.
        
        Args:
            student_id: ID of the student
            current_week_start: Start of current week (Monday)
            
        Returns:
            Trend indicating improvement, decline, or stability
        """
        prev_week_start = current_week_start - timedelta(weeks=1)
        
        try:
            prev_summary = self.summary_generator.generate_summary(
                student_id, prev_week_start + timedelta(days=3), 
                calculate_trends=False
            )
            current_summary = self.summary_generator.generate_summary(
                student_id, current_week_start + timedelta(days=3), 
                calculate_trends=False
            )
            
            # Handle edge case of no data
            if prev_summary.words_practiced == 0 and current_summary.words_practiced == 0:
                return Trend.STABLE
            
            if prev_summary.words_practiced == 0:
                # No previous data but current has data = improving
                if current_summary.accuracy_rate > 0:
                    return Trend.IMPROVING
                return Trend.STABLE
            
            if current_summary.words_practiced == 0:
                # Current week has no data but previous did
                return Trend.STABLE
            
            # Calculate percentage point difference
            diff = current_summary.accuracy_rate - prev_summary.accuracy_rate
            
            if diff > self.ACCURACY_THRESHOLD:
                return Trend.IMPROVING
            elif diff < -self.ACCURACY_THRESHOLD:
                return Trend.DECLINING
            else:
                return Trend.STABLE
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error calculating accuracy trend: {e}")
            return None
    
    def calculate_mastered_trend(self, student_id: str, current_week_start: date) -> Optional[Trend]:
        """
        Compare words mastered to previous week.
        
        Args:
            student_id: ID of the student
            current_week_start: Start of current week (Monday)
            
        Returns:
            Trend indicating improvement, decline, or stability
        """
        prev_week_start = current_week_start - timedelta(weeks=1)
        
        try:
            prev_summary = self.summary_generator.generate_summary(
                student_id, prev_week_start + timedelta(days=3), 
                calculate_trends=False
            )
            current_summary = self.summary_generator.generate_summary(
                student_id, current_week_start + timedelta(days=3), 
                calculate_trends=False
            )
            
            diff = current_summary.words_mastered - prev_summary.words_mastered
            
            if diff > self.MASTERED_THRESHOLD:
                return Trend.IMPROVING
            elif diff < -self.MASTERED_THRESHOLD:
                return Trend.DECLINING
            else:
                return Trend.STABLE
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error calculating mastered trend: {e}")
            return None
    
    def calculate_trends_for_summary(self, summary: WeeklySummary, student_id: str, 
                                      current_week_start: date) -> WeeklySummary:
        """
        Calculate and attach trends to an existing summary.
        
        Args:
            summary: WeeklySummary to attach trends to
            student_id: ID of the student
            current_week_start: Start of current week
            
        Returns:
            Same summary with trend_accuracy and trend_mastered populated
        """
        summary.trend_accuracy = self.calculate_accuracy_trend(student_id, current_week_start)
        summary.trend_mastered = self.calculate_mastered_trend(student_id, current_week_start)
        return summary
    
    def get_trend_direction(self, current_value: float, previous_value: float, 
                            threshold: float) -> Trend:
        """
        Generic trend calculation for any numeric metric.
        
        Args:
            current_value: Current period value
            previous_value: Previous period value
            threshold: Minimum change to be considered significant
            
        Returns:
            Trend indicating direction of change
        """
        if previous_value == 0 and current_value == 0:
            return Trend.STABLE
        
        if previous_value == 0:
            return Trend.IMPROVING if current_value > 0 else Trend.STABLE
        
        diff = current_value - previous_value
        
        if diff > threshold:
            return Trend.IMPROVING
        elif diff < -threshold:
            return Trend.DECLINING
        else:
            return Trend.STABLE
    
    def calculate_multi_week_trend(self, summaries: List[WeeklySummary], 
                                    metric: str = "accuracy_rate") -> Optional[Trend]:
        """
        Calculate overall trend across multiple weeks.
        
        Args:
            summaries: List of WeeklySummary objects (chronologically ordered)
            metric: Metric to analyze ("accuracy_rate" or "words_mastered")
            
        Returns:
            Overall trend direction
        """
        if len(summaries) < 2:
            return None
        
        # Filter out empty summaries
        valid_summaries = [s for s in summaries if s.has_data()]
        if len(valid_summaries) < 2:
            return None
        
        # Compare first and last weeks
        first = valid_summaries[0]
        last = valid_summaries[-1]
        
        if metric == "accuracy_rate":
            return self.get_trend_direction(
                last.accuracy_rate, first.accuracy_rate, self.ACCURACY_THRESHOLD
            )
        elif metric == "words_mastered":
            return self.get_trend_direction(
                float(last.words_mastered), float(first.words_mastered), 
                self.MASTERED_THRESHOLD
            )
        
        return Trend.STABLE
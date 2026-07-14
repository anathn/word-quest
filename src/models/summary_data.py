"""
Summary Data Models

Data models for weekly progress summaries.
Implements STORY-003-05: Weekly Summary View
"""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional
from enum import Enum


class Trend(Enum):
    """Trend direction for metrics."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    
    def __str__(self):
        return self.value
    
    def get_symbol(self) -> str:
        """Get Unicode symbol for trend."""
        symbols = {
            "improving": "↑",
            "stable": "→",
            "declining": "↓"
        }
        return symbols.get(self.value, "-")
    
    def get_color(self) -> tuple:
        """Get color for trend display."""
        colors = {
            "improving": (76, 175, 80),      # Green
            "stable": (158, 158, 158),       # Gray
            "declining": (244, 67, 54)       # Red
        }
        return colors.get(self.value, (158, 158, 158))


@dataclass
class WeeklySummary:
    """
    Aggregated data model for a week's statistics.
    
    Attributes:
        week_start: Start date of the week (Monday)
        week_end: End date of the week (Sunday)
        student_id: ID of the student
        words_mastered: Count of words with 80%+ accuracy
        words_practiced: Total unique words attempted
        accuracy_rate: Accuracy rate (0.0 to 1.0)
        total_sessions: Number of practice sessions
        total_time_minutes: Total practice time in minutes
        best_streak: Best consecutive correct answers streak
        avg_session_length: Average session length in minutes
        words_mastered_list: List of mastered word spellings
        words_needing_practice: List of words with <50% accuracy
        trend_accuracy: Week-over-week accuracy trend
        trend_mastered: Week-over-week mastered words trend
    """
    week_start: date
    week_end: date
    student_id: str
    words_mastered: int = 0
    words_practiced: int = 0
    accuracy_rate: float = 0.0
    total_sessions: int = 0
    total_time_minutes: int = 0
    best_streak: int = 0
    avg_session_length: float = 0.0
    words_mastered_list: List[str] = field(default_factory=list)
    words_needing_practice: List[str] = field(default_factory=list)
    trend_accuracy: Optional[Trend] = None
    trend_mastered: Optional[Trend] = None
    
    def to_dict(self) -> dict:
        """Convert summary to dictionary for serialization."""
        return {
            "week_start": self.week_start.isoformat(),
            "week_end": self.week_end.isoformat(),
            "student_id": self.student_id,
            "words_mastered": self.words_mastered,
            "words_practiced": self.words_practiced,
            "accuracy_rate": self.accuracy_rate,
            "total_sessions": self.total_sessions,
            "total_time_minutes": self.total_time_minutes,
            "best_streak": self.best_streak,
            "avg_session_length": self.avg_session_length,
            "words_mastered_list": self.words_mastered_list,
            "words_needing_practice": self.words_needing_practice,
            "trend_accuracy": self.trend_accuracy.value if self.trend_accuracy else None,
            "trend_mastered": self.trend_mastered.value if self.trend_mastered else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "WeeklySummary":
        """Create WeeklySummary from dictionary."""
        from datetime import date as dt_date
        return cls(
            week_start=dt_date.fromisoformat(data["week_start"]),
            week_end=dt_date.fromisoformat(data["week_end"]),
            student_id=data["student_id"],
            words_mastered=data.get("words_mastered", 0),
            words_practiced=data.get("words_practiced", 0),
            accuracy_rate=data.get("accuracy_rate", 0.0),
            total_sessions=data.get("total_sessions", 0),
            total_time_minutes=data.get("total_time_minutes", 0),
            best_streak=data.get("best_streak", 0),
            avg_session_length=data.get("avg_session_length", 0.0),
            words_mastered_list=data.get("words_mastered_list", []),
            words_needing_practice=data.get("words_needing_practice", []),
            trend_accuracy=Trend(data["trend_accuracy"]) if data.get("trend_accuracy") else None,
            trend_mastered=Trend(data["trend_mastered"]) if data.get("trend_mastered") else None
        )
    
    def has_data(self) -> bool:
        """Check if the summary has any practice data."""
        return self.total_sessions > 0 or self.words_practiced > 0
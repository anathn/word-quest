"""
Progress Summarizer Module

Generates encouraging, age-appropriate text summaries of student progress.
Part of STORY-007-03: Progress Journal
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random

from src.components.progress_tracker import ProgressTracker


@dataclass
class WeekData:
    """Aggregated data for a single week."""
    week_start: datetime
    week_end: datetime
    total_words: int = 0
    mastered_words: List[str] = field(default_factory=list)
    weak_words: List[str] = field(default_factory=list)
    best_streak: int = 0
    sessions_count: int = 0
    total_attempts: int = 0
    correct_attempts: int = 0
    total_time_seconds: float = 0.0
    accuracy_percent: float = 0.0
    accuracy_improved: bool = False


@dataclass
class JournalEntry:
    """A single journal entry for a week."""
    period: str
    lines: List[str]
    mastered_count: int
    needs_practice: Optional[Dict[str, Any]]
    week_data: WeekData


class ProgressSummarizer:
    """
    Analyzes progress data and generates encouraging, age-appropriate summaries.
    
    Uses simple language at approximately 3rd grade reading level.
    Maintains consistently encouraging tone.
    """
    
    def __init__(self, progress_tracker: ProgressTracker):
        """
        Initialize the summarizer.
        
        Args:
            progress_tracker: ProgressTracker instance with session data
        """
        self.progress_tracker = progress_tracker
        self.templates = LanguageTemplates()
    
    def generate_weekly_summary(self, week_start: datetime, week_end: datetime) -> JournalEntry:
        """
        Generate an encouraging summary for a specific week.
        
        Args:
            week_start: Start date of the week
            week_end: End date of the week
            
        Returns:
            JournalEntry with summary data
        """
        week_data = self._gather_week_data(week_start, week_end)
        
        summary_parts = []
        
        # Opening encouragement
        summary_parts.append(self.templates.get_opening(week_data.total_words))
        
        # Words mastered this week
        if week_data.mastered_words:
            mastered_list = self._format_word_list(week_data.mastered_words[:5])
            if len(week_data.mastered_words) > 5:
                mastered_list += " and more!"
            summary_parts.append(f"This week you mastered: {mastered_list}")
        
        # Progress observation
        if week_data.accuracy_improved:
            summary_parts.append("You're getting faster at spelling!")
        elif week_data.accuracy_percent >= 70:
            summary_parts.append("You're doing great!")
        elif week_data.sessions_count > 0:
            summary_parts.append("Keep practicing - you're making progress!")
        
        # Streak highlight
        if week_data.best_streak >= 5:
            summary_parts.append(f"Amazing! Your streak of {week_data.best_streak} correct was fantastic!")
        elif week_data.best_streak >= 3:
            summary_parts.append(f"Great streak of {week_data.best_streak} - keep it up!")
        
        # Closing encouragement
        summary_parts.append(self.templates.get_closing(len(week_data.mastered_words)))
        
        # Practice recommendation
        needs_practice = None
        if week_data.weak_words:
            needs_practice = self.get_needs_practice_section(week_data.weak_words)
        
        period = f"Week of {week_start.strftime('%B %d')}"
        
        return JournalEntry(
            period=period,
            lines=summary_parts,
            mastered_count=len(week_data.mastered_words),
            needs_practice=needs_practice,
            week_data=week_data
        )
    
    def _gather_week_data(self, week_start: datetime, week_end: datetime) -> WeekData:
        """Collect all data for a specific week."""
        week_data = WeekData(
            week_start=week_start,
            week_end=week_end
        )
        
        # Get sessions from progress tracker
        sessions = self.progress_tracker.session_tracker.get_sessions_for_week(week_start, week_end)
        
        if not sessions:
            return week_data
        
        week_data.sessions_count = len(sessions)
        
        # Aggregate session data
        mastered_set = set()
        weak_set = {}  # word_text -> attempts
        
        for session in sessions:
            week_data.total_time_seconds += session.duration_seconds
            
            for word_attempt in session.words:
                week_data.total_words += 1
                week_data.total_attempts += word_attempt.total_attempts
                if word_attempt.correct:
                    week_data.correct_attempts += 1
                
                # Track streaks - not available from WordAttempt, skip for now
                
                # Track mastered words (first-attempt correct, zero hints)
                if word_attempt.first_attempt_correct and word_attempt.hints_used == 0:
                    mastered_set.add(word_attempt.word)
                
                # Track weak words (multiple attempts)
                if word_attempt.total_attempts > 1:
                    if word_attempt.word not in weak_set:
                        weak_set[word_attempt.word] = 0
                    weak_set[word_attempt.word] += word_attempt.total_attempts
        
        week_data.mastered_words = list(mastered_set)
        week_data.weak_words = sorted(weak_set.keys(), key=lambda w: weak_set[w], reverse=True)[:5]
        
        # Calculate accuracy
        if week_data.total_attempts > 0:
            week_data.accuracy_percent = (week_data.correct_attempts / week_data.total_attempts) * 100
        
        # Check if accuracy improved vs previous week
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_end - timedelta(days=7)
        prev_sessions = self.progress_tracker.session_tracker.get_sessions_for_week(prev_week_start, prev_week_end)
        
        if prev_sessions:
            prev_attempts = 0
            prev_correct = 0
            for session in prev_sessions:
                for word_attempt in session.words:
                    prev_attempts += word_attempt.total_attempts
                    if word_attempt.correct:
                        prev_correct += 1
            
            if prev_attempts > 0:
                prev_accuracy = (prev_correct / prev_attempts) * 100
                week_data.accuracy_improved = week_data.accuracy_percent > prev_accuracy
        
        return week_data
    
    def _format_word_list(self, words: List[str]) -> str:
        """Format a list of words for display."""
        if not words:
            return ""
        
        # Capitalize first letter of each word
        formatted = [word.upper() for word in words]
        return ", ".join(formatted)
    
    def get_needs_practice_section(self, weak_words: List[str]) -> Dict[str, Any]:
        """Generate gentle suggestion for practice words."""
        if not weak_words:
            return None
        
        word_list = ", ".join([w.upper() for w in weak_words[:3]])
        return {
            "title": "Words to Practice",
            "text": f"Keep practicing: {word_list}",
            "tone": "encouraging",
            "words": weak_words
        }
    
    def generate_welcome_message(self) -> List[str]:
        """Generate welcome message for new students with no progress."""
        return [
            "Welcome to your Progress Journal!",
            "This is where you can see how well you're doing!",
            "Start practicing and you'll see your progress here!",
            "You're going to do great!"
        ]


class LanguageTemplates:
    """
    Pre-written phrases at 3rd grade reading level.
    
    All language is encouraging, positive, and age-appropriate.
    """
    
    OPENINGS = {
        "active": [
            "Wow, you're really working hard!",
            "Great job this week!",
            "You're doing awesome!",
            "Look how much you've practiced!"
        ],
        "steady": [
            "Good practice this week!",
            "You're making progress!",
            "Keep it up! Great work!",
            "You're getting better every day!"
        ],
        "light": [
            "Nice job this week!",
            "Good job practicing!",
            "You're doing great!",
            "Well done!"
        ]
    }
    
    CLOSINGS = {
        "many_mastered": [
            "Keep going - you're a spelling star!",
            "You're getting so good at spelling!",
            "Amazing work! Keep it up!",
            "You're a spelling champion!"
        ],
        "some_mastered": [
            "Keep practicing and you'll get even better!",
            "You're on your way! Great work!",
            "Keep going - you can do it!",
            "Every word you learn makes you stronger!"
        ],
        "few_mastered": [
            "Keep trying - you're making progress!",
            "Learning takes time. You're doing great!",
            "Mistakes help us learn. Keep going!",
            "Practice makes progress. You've got this!"
        ]
    }
    
    def get_opening(self, word_count: int) -> str:
        """Select appropriate opening based on activity level."""
        if word_count >= 10:
            return random.choice(self.OPENINGS["active"])
        elif word_count >= 5:
            return random.choice(self.OPENINGS["steady"])
        else:
            return random.choice(self.OPENINGS["light"])
    
    def get_closing(self, mastered_count: int) -> str:
        """Select appropriate closing based on success."""
        if mastered_count >= 5:
            return random.choice(self.CLOSINGS["many_mastered"])
        elif mastered_count >= 2:
            return random.choice(self.CLOSINGS["some_mastered"])
        else:
            return random.choice(self.CLOSINGS["few_mastered"])
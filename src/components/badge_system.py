"""
Badge System (STORY-004-03)

Manages achievement badges, tracking unlock conditions, and progress.
Implements a badge collection system with rarity tiers and milestone tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum
from datetime import datetime
import json
import os
import logging
import time

from src.components.data_store import DataStore


logger = logging.getLogger(__name__)


class Rarity(Enum):
    """Badge rarity tiers."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    LEGENDARY = "legendary"


# Rarity color scheme mappings
RARITY_COLORS = {
    Rarity.COMMON: (192, 192, 192),       # Silver
    Rarity.UNCOMMON: (205, 127, 50),      # Bronze
    Rarity.RARE: (255, 215, 0),           # Gold
    Rarity.LEGENDARY: (255, 0, 255)       # Rainbow (animated in UI)
}


@dataclass
class Badge:
    """Represents a badge definition."""
    id: str
    name: str
    description: str
    icon_path: str
    rarity: Rarity
    unlock_condition: str
    color_scheme: str
    unlocked_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Badge':
        """Create Badge from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            icon_path=data['icon_path'],
            rarity=Rarity(data['rarity']),
            unlock_condition=data['unlock_condition'],
            color_scheme=data.get('color_scheme', 'silver'),
            unlocked_at=datetime.fromisoformat(data['unlocked_at']) if data.get('unlocked_at') else None
        )
    
    def to_dict(self) -> Dict:
        """Convert Badge to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon_path': self.icon_path,
            'rarity': self.rarity.value,
            'unlock_condition': self.unlock_condition,
            'color_scheme': self.color_scheme,
            'unlocked_at': self.unlocked_at.isoformat() if self.unlocked_at else None
        }


@dataclass
class BadgeProgress:
    """Tracks progress toward a badge."""
    badge_id: str
    current: int
    target: int
    is_complete: bool = False
    
    def progress_percent(self) -> float:
        """Get progress as percentage (0.0 to 1.0)."""
        if self.target == 0:
            return 1.0 if self.is_complete else 0.0
        return min(1.0, self.current / self.target)
    
    def get_progress_text(self) -> str:
        """Get formatted progress text (e.g., '3/10')."""
        return f"{self.current}/{self.target}"


@dataclass
class BadgeTracker:
    """
    Tracks progress toward badges.
    
    Tracks:
    - Speed Speller: Words completed in current 5-minute window
    - Perseverance: Maximum attempts on a single word
    - Perfect Planet: Count of perfect planets (5/5 first attempt)
    - Streak Master: Max streak achieved
    - Word Warrior: Total mastered words
    - Comeback Kid: Tracking words with 3+ failed attempts
    """
    # Speed Speller
    speed_speller_words: int = 0
    speed_speller_start_time: Optional[float] = None
    
    # Perseverance
    current_word_attempts: int = 0
    max_word_attempts: int = 0
    
    # Perfect Planet
    perfect_planets_earned: int = 0
    
    # Word Warrior
    total_words_mastered: int = 0
    
    # Comeback Kid
    current_word_incorrect: int = 0
    had_3plus_incorrect: bool = False  # Flag for current word


class BadgeManager:
    """
    Manages achievement badges.
    
    Features:
    - Load badge definitions from JSON
    - Track unlock conditions in real-time
    - Store unlocked badges in student profile
    - Persist badges across sessions
    - Track progress toward badges
    
    Badge Types:
    - Speed Speller: Complete 10 words in under 5 minutes
    - Perseverance: Master a word after 5+ attempts
    - Perfect Planet: Get 5/5 correct on first attempt
    - Streak Master: Achieve a 10-word streak
    - Word Warrior: Master 25 words total
    - Comeback Kid: Correct answer after 3+ incorrect attempts
    """
    
    BADGE_DEFS_PATH = "data/badge_definitions.json"
    
    def __init__(self, student_id: str = "student_1", data_store: Optional[DataStore] = None):
        """
        Initialize the badge manager.
        
        Args:
            student_id: Unique identifier for the student
            data_store: Optional DataStore for persistence
        """
        self.student_id = student_id
        self.data_store = data_store
        
        # Badge definitions
        self.badges: Dict[str, Badge] = {}
        
        # Unlocked badges
        self.unlocked_badges: Dict[str, Badge] = {}
        
        # Progress tracking
        self.progress: Dict[str, BadgeProgress] = {}
        
        # Event tracker for one-time unlocks
        self._speed_speller_unlocked: bool = False
        self._perseverance_unlocked: bool = False
        self._perfect_planet_unlocked: bool = False
        self._streak_master_unlocked: bool = False
        self._word_warrior_unlocked: bool = False
        self._comeback_kid_unlocked: bool = False
        
        # Progress tracker
        self.tracker = BadgeTracker()
        
        # Callbacks
        self.on_badge_unlocked: Optional[callable] = None
        
        # Load definitions and persisted data
        self._load_badge_definitions()
        self._load_unlocked_badges()
        
        # Initialize progress for all badges
        self._initialize_progress()
    
    def _load_badge_definitions(self):
        """Load badge definitions from JSON file."""
        try:
            path = self.BADGE_DEFS_PATH
            if not os.path.isabs(path):
                # Resolve relative to project root
                path = os.path.join(os.path.dirname(__file__), '..', '..', path)
            
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                
                for badge_data in data.get('badges', []):
                    badge = Badge.from_dict(badge_data)
                    self.badges[badge.id] = badge
                logger.info(f"Loaded {len(self.badges)} badge definitions")
            else:
                logger.warning(f"Badge definitions not found: {path}")
        except Exception as e:
            logger.error(f"Error loading badge definitions: {e}")
    
    def _load_unlocked_badges(self):
        """Load unlocked badges from DataStore."""
        if not self.data_store:
            return
        
        try:
            load_result = self.data_store.load(self.student_id)
            if load_result.data and 'unlocked_badges' in load_result.data:
                for badge_data in load_result.data['unlocked_badges']:
                    badge = Badge.from_dict(badge_data)
                    self.unlocked_badges[badge.id] = badge
                logger.info(f"Loaded {len(self.unlocked_badges)} unlocked badges")
        except Exception as e:
            logger.error(f"Error loading unlocked badges: {e}")
    
    def _initialize_progress(self):
        """Initialize progress for all badges."""
        # Speed Speller: 10 words in 5 minutes
        self.progress['speed_speller'] = BadgeProgress('speed_speller', 0, 10, False)
        
        # Perseverance: 5+ attempts on a word
        self.progress['perseverance'] = BadgeProgress('perseverance', 0, 5, False)
        
        # Perfect Planet: 1 perfect planet
        self.progress['perfect_planet'] = BadgeProgress('perfect_planet', 0, 1, False)
        
        # Streak Master: 10 word streak
        self.progress['streak_master'] = BadgeProgress('streak_master', 0, 10, False)
        
        # Word Warrior: 25 mastered words
        self.progress['word_warrior'] = BadgeProgress('word_warrior', 0, 25, False)
        
        # Comeback Kid: 3+ incorrect then correct
        self.progress['comeback_kid'] = BadgeProgress('comeback_kid', 0, 1, False)
    
    def _save_unlocked_badges(self):
        """Save unlocked badges to DataStore."""
        if not self.data_store:
            return
        
        try:
            badge_list = [badge.to_dict() for badge in self.unlocked_badges.values()]
            progress_data = {
                'student_id': self.student_id,
                'unlocked_badges': badge_list
            }
            # Only save badges, progress is session-only for most badges
            self.data_store.save(self.student_id, progress_data)
        except Exception as e:
            logger.error(f"Error saving unlocked badges: {e}")
    
    def start_session(self):
        """Reset session-specific tracking when starting a new session."""
        self.tracker.speed_speller_start_time = time.time()
        self.tracker.speed_speller_words = 0
        self.tracker.current_word_attempts = 0
        self.tracker.current_word_incorrect = 0
        self.tracker.had_3plus_incorrect = False
        self._update_speed_speller_progress()
    
    def _update_speed_speller_progress(self):
        """Update progress for Speed Speller badge."""
        self.progress['speed_speller'].current = self.tracker.speed_speller_words
        if self.tracker.speed_speller_words >= 10:
            self.progress['speed_speller'].is_complete = True
    
    def end_session(self):
        """End session - persist any new unlocks."""
        self._save_unlocked_badges()
    
    # Event handlers for badge tracking
    
    def on_word_started(self):
        """Called when a word starts being worked on."""
        self.tracker.current_word_attempts = 0
        self.tracker.current_word_incorrect = 0
        self.tracker.had_3plus_incorrect = False
    
    def on_word_completed(self, attempts: int, hints_used: int, is_first_attempt_correct: bool, completion_time: float):
        """
        Called when a word is completed.
        
        Args:
            attempts: Total number of attempts
            hints_used: Number of hints used
            is_first_attempt_correct: Whether correct on first try
            completion_time: Time to complete in seconds
        """
        # Track max attempts for Perseverance
        self.tracker.max_word_attempts = max(self.tracker.max_word_attempts, attempts)
        
        # Speed Speller - word completed in session
        self.tracker.speed_speller_words += 1
        self._update_speed_speller_progress()
        
        # Check for Speed Speller unlock
        if not self._speed_speller_unlocked:
            elapsed = time.time() - (self.tracker.speed_speller_start_time or 0)
            if self.tracker.speed_speller_words >= 10 and elapsed < 300:  # 5 minutes
                self._unlock_badge('speed_speller')
        
        # Perseverance - master after 5+ attempts
        if attempts >= 5 and not self._perseverance_unlocked:
            # Only unlock if this word is considered "mastered" (correct on final attempt)
            # We'll check this at the end - if they finally got it right after many tries
            if attempts >= 5:
                self._unlock_badge('perseverance')
        
        # Comeback Kid - correct after 3+ incorrect
        if self.tracker.had_3plus_incorrect and attempts > 1:
            # They had 3+ incorrect and then got it right (attempts > 1 means they eventually got it)
            if not self._comeback_kid_unlocked:
                self._unlock_badge('comeback_kid')
        
        # Update progress for current word attempts
        self.progress['perseverance'].current = self.tracker.max_word_attempts
        if self.tracker.max_word_attempts >= 5:
            self.progress['perseverance'].is_complete = True
        
        # Reset for next word
        self.tracker.current_word_attempts = 0
        self.tracker.current_word_incorrect = 0
    
    def on_incorrect_answer(self):
        """Called when student gives an incorrect answer."""
        self.tracker.current_word_attempts += 1
        self.tracker.current_word_incorrect += 1
        
        if self.tracker.current_word_incorrect >= 3:
            self.tracker.had_3plus_incorrect = True
        
        # Update Perseverance progress
        self.progress['perseverance'].current = self.tracker.current_word_attempts
    
    def on_correct_answer(self, streak: int = 0):
        """
        Called when student gives a correct answer.
        
        Args:
            streak: Current streak value (for Streak Master tracking)
        """
        # Update Streak Master progress
        self.progress['streak_master'].current = streak
        
        if streak >= 10 and not self._streak_master_unlocked:
            self._unlock_badge('streak_master')
    
    def on_planet_completed(self, perfect: bool):
        """
        Called when a planet is completed.
        
        Args:
            perfect: Whether 5/5 were correct on first attempt
        """
        if perfect and not self._perfect_planet_unlocked:
            self.tracker.perfect_planets_earned += 1
            self._unlock_badge('perfect_planet')
        
        # Update Perfect Planet progress
        self.progress['perfect_planet'].current = self.tracker.perfect_planets_earned
        if perfect:
            self.progress['perfect_planet'].is_complete = True
    
    def on_word_mastered(self):
        """Called when a word is mastered (first attempt correct, no hints)."""
        self.tracker.total_words_mastered += 1
        
        # Update Word Warrior progress
        self.progress['word_warrior'].current = self.tracker.total_words_mastered
        
        if self.tracker.total_words_mastered >= 25 and not self._word_warrior_unlocked:
            self._unlock_badge('word_warrior')
    
    # Badge unlocking
    
    def _unlock_badge(self, badge_id: str):
        """
        Unlock a badge.
        
        Args:
            badge_id: Badge identifier to unlock
        """
        if badge_id in self.unlocked_badges:
            return  # Already unlocked
        
        badge = self.badges.get(badge_id)
        if not badge:
            logger.warning(f"Badge not found: {badge_id}")
            return
        
        badge.unlocked_at = datetime.now()
        self.unlocked_badges[badge_id] = badge
        
        # Mark progress as complete
        if badge_id in self.progress:
            self.progress[badge_id].is_complete = True
        
        # Set unlock flag
        unlock_flags = {
            'speed_speller': '_speed_speller_unlocked',
            'perseverance': '_perseverance_unlocked',
            'perfect_planet': '_perfect_planet_unlocked',
            'streak_master': '_streak_master_unlocked',
            'word_warrior': '_word_warrior_unlocked',
            'comeback_kid': '_comeback_kid_unlocked'
        }
        flag = unlock_flags.get(badge_id)
        if flag:
            setattr(self, flag, True)
        
        # Update progress
        if badge_id in self.progress:
            self.progress[badge_id].current = self.progress[badge_id].target
        
        logger.info(f"Badge unlocked: {badge.name}")
        
        # Notify callback
        if self.on_badge_unlocked:
            self.on_badge_unlocked(badge)
    
    def check_and_unlock_badge(self, badge_id: str, conditions_met: bool):
        """
        Check and potentially unlock a badge.
        
        Args:
            badge_id: Badge identifier
            conditions_met: Whether unlock conditions are met
        """
        if conditions_met:
            self._unlock_badge(badge_id)
    
    # Progress getters
    
    def get_progress(self, badge_id: str) -> Optional[BadgeProgress]:
        """
        Get progress toward a specific badge.
        
        Args:
            badge_id: Badge identifier
            
        Returns:
            BadgeProgress or None if badge not found
        """
        return self.progress.get(badge_id)
    
    def get_all_badges(self) -> List[Badge]:
        """
        Get all available badges.
        
        Returns:
            List of all Badge objects
        """
        return list(self.badges.values())
    
    def get_unlocked_badges(self) -> List[Badge]:
        """
        Get all unlocked badges.
        
        Returns:
            List of unlocked Badge objects
        """
        return list(self.unlocked_badges.values())
    
    def get_locked_badges(self) -> List[Badge]:
        """
        Get all locked badges.
        
        Returns:
            List of locked Badge objects
        """
        return [b for b in self.badges.values() if b.id not in self.unlocked_badges]
    
    def is_badge_unlocked(self, badge_id: str) -> bool:
        """
        Check if a badge is unlocked.
        
        Args:
            badge_id: Badge identifier
            
        Returns:
            True if unlocked, False otherwise
        """
        return badge_id in self.unlocked_badges
    
    def get_badge_by_id(self, badge_id: str) -> Optional[Badge]:
        """
        Get badge by ID.
        
        Args:
            badge_id: Badge identifier
            
        Returns:
            Badge or None
        """
        return self.badges.get(badge_id)
    
    def get_unlocked_count(self) -> int:
        """
        Get count of unlocked badges.
        
        Returns:
            Number of unlocked badges
        """
        return len(self.unlocked_badges)
    
    def get_total_count(self) -> int:
        """
        Get total number of badges.
        
        Returns:
            Total badge count
        """
        return len(self.badges)
    
    def get_progress_summary(self) -> Dict:
        """
        Get summary of all badge progress.
        
        Returns:
            Dictionary with badge progress information
        """
        return {
            badge_id: {
                'current': prog.current,
                'target': prog.target,
                'percent': prog.progress_percent(),
                'complete': prog.is_complete
            }
            for badge_id, prog in self.progress.items()
        }


# Factory function
def create_badge_manager(student_id: str = "student_1", data_store: Optional[DataStore] = None) -> BadgeManager:
    """
    Create a BadgeManager instance.
    
    Args:
        student_id: Student identifier
        data_store: Optional DataStore for persistence
        
    Returns:
        Configured BadgeManager instance
    
    Example:
        >>> # Create badge manager
        >>> manager = create_badge_manager(student_id="student_1", data_store=data_store)
        >>> 
        >>> # Set up callback for badge unlocks
        >>> def on_badge_unlocked(badge):
        ...     print(f"🏆 Badge Unlocked! {badge.name}")
        >>> 
        >>> manager.on_badge_unlocked = on_badge_unlocked
        >>> 
        >>> # Start a new session
        >>> manager.start_session()
        >>> 
        >>> # Track events
        >>> manager.on_word_started()
        >>> manager.on_incorrect_answer()
        >>> manager.on_correct_answer(streak=3)
        >>> manager.on_word_completed(attempts=2, hints_used=1, is_first_attempt_correct=False, completion_time=30.0)
        >>> 
        >>> # Check progress
        >>> progress = manager.get_progress('streak_master')
        >>> print(f"Streak Master: {progress.get_progress_text()}")
        >>> 
        >>> # Get unlocked badges
        >>> unlocked = manager.get_unlocked_badges()
        >>> for badge in unlocked:
        ...     print(f"  - {badge.name} ({badge.rarity.value})")
        >>> 
        >>> # End session (persists unlocks)
        >>> manager.end_session()
    """
    return BadgeManager(student_id=student_id, data_store=data_store)
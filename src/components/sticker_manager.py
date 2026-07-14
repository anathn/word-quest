"""
Sticker Collection System (STORY-004-06)

Manages sticker definitions, unlock conditions, and persistence.
Implements a sticker collection system with rarity tiers and milestone tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable
from enum import Enum
from datetime import datetime
import json
import os
import logging
import time

from src.components.data_store import DataStore


logger = logging.getLogger(__name__)


class StickerRarity(Enum):
    """Sticker rarity tiers."""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


# Rarity color scheme (RGB tuples)
RARITY_COLORS = {
    StickerRarity.COMMON: (192, 192, 192),      # Silver
    StickerRarity.UNCOMMON: (205, 127, 50),     # Bronze
    StickerRarity.RARE: (255, 215, 0),          # Gold
    StickerRarity.EPIC: (255, 105, 180),        # Hot pink
    StickerRarity.LEGENDARY: (192, 0, 255)      # Rainbow (animated in UI)
}

# Sticker unlock thresholds
STREAK_STICKER_REQUIRED = 15
WORDS_MASTERED_FOR_STICKER = 50
SPEED_DEMON_MAX_SECONDS = 180  # 3 minutes
SOLAR_SYSTEM_PLANETS_REQUIRED = 3


@dataclass
class StickerDefinition:
    """Represents a sticker definition."""
    id: str
    name: str
    description: str
    rarity: StickerRarity
    unlock_condition: str
    category: str
    color_scheme: str
    unlocked_at: Optional[datetime] = None
    unlock_context: Optional[dict] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StickerDefinition':
        """Create StickerDefinition from dictionary."""
        return cls(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            rarity=StickerRarity(data['rarity']),
            unlock_condition=data['unlock_condition'],
            category=data['category'],
            color_scheme=data.get('color_scheme', 'silver'),
            unlocked_at=datetime.fromisoformat(data['unlocked_at']) if data.get('unlocked_at') else None,
            unlock_context=data.get('unlock_context')
        )
    
    def to_dict(self) -> Dict:
        """Convert StickerDefinition to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'rarity': self.rarity.value,
            'unlock_condition': self.unlock_condition,
            'category': self.category,
            'color_scheme': self.color_scheme,
            'unlocked_at': self.unlocked_at.isoformat() if self.unlocked_at else None,
            'unlock_context': self.unlock_context
        }


@dataclass
class StickerProgress:
    """Tracks progress toward a sticker."""
    sticker_id: str
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
class StickerTracker:
    """
    Tracks progress toward stickers.
    
    Tracks:
    - Planets completed (for Planet Winner)
    - Perfect planets (for Flawless Victory)
    - Planet completion times (for Speed Demon)
    - Full hint usage (for Hint Helper)
    - Failed then cleared planets (for Comeback Champion)
    - Solar systems completed (for Galaxy Explorer)
    - Current streak (for Streak King/Queen)
    - Words mastered (for Word Master)
    - Games played times (for Early Bird/Night Owl)
    """
    # Progress tracking
    planets_completed: int = 0
    perfect_planets: int = 0
    fast_planet_completions: int = 0
    full_hint_solves: int = 0
    failed_planets: Set[str] = field(default_factory=set)
    cleared_after_fail: Set[str] = field(default_factory=set)
    completed_solar_systems: Set[str] = field(default_factory=set)
    solar_system_planets: Dict[str, Set[str]] = field(default_factory=dict)  # {solar_system: {planet_ids}}
    current_streak: int = 0
    words_mastered: int = 0
    early_bird_games: int = 0
    night_owl_games: int = 0
    
    # One-time unlock flags
    planet_winner_unlocked: bool = False
    flawless_victory_unlocked: bool = False
    speed_demon_unlocked: bool = False
    hint_helper_unlocked: bool = False
    comeback_champion_unlocked: bool = False
    galaxy_explorer_unlocked: bool = False
    streak_king_unlocked: bool = False
    streak_queen_unlocked: bool = False
    word_master_unlocked: bool = False
    early_bird_unlocked: bool = False
    night_owl_unlocked: bool = False


class StickerManager:
    """
    Manages achievement stickers.
    
    Features:
    - Load sticker definitions from JSON
    - Track unlock conditions in real-time
    - Store unlocked stickers in student profile
    - Persist stickers across sessions
    - Track progress toward stickers
    
    Sticker Types:
    - Planet Winner: Complete any planet
    - Flawless Victory: Complete planet 5/5 first attempt
    - Speed Demon: Complete planet in under 3 minutes
    - Hint Helper: Solve word after using all hints
    - Comeback Champion: Complete planet after failing
    - Galaxy Explorer: Complete 3 planets in solar system
    - Streak King/Queen: 15-word streak
    - Word Master: 50 words mastered
    - Early Bird: Play before 9am
    - Night Owl: Play after 7pm
    """
    
    STICKER_DEFS_PATH = "data/sticker_definitions.json"
    
    def __init__(self, student_id: str = "student_1", data_store: Optional[DataStore] = None, is_female: bool = True):
        """
        Initialize the sticker manager.
        
        Args:
            student_id: Unique identifier for the student
            data_store: Optional DataStore for persistence
            is_female: Student's gender (affects Streak King vs Queen)
        """
        self.student_id = student_id
        self.data_store = data_store
        self.is_female = is_female
        
        # Sticker definitions
        self.stickers: Dict[str, StickerDefinition] = {}
        
        # Unlocked stickers
        self.unlocked_stickers: Dict[str, StickerDefinition] = {}
        
        # Progress tracking
        self.progress: Dict[str, StickerProgress] = {}
        
        # Event tracker
        self.tracker = StickerTracker()
        
        # Callback
        self.on_sticker_unlocked: Optional[Callable[[StickerDefinition], None]] = None
        
        # Load definitions and persisted data
        self._load_sticker_definitions()
        self._load_unlocked_stickers()
        
        # Initialize progress for all stickers
        self._initialize_progress()
        
        # Track planets in current session for solar system tracking
        self._current_solar_system_planets: Set[str] = set()
        self._current_planet_start_time: Optional[float] = None
    
    def _load_sticker_definitions(self):
        """Load sticker definitions from JSON file."""
        try:
            path = self.STICKER_DEFS_PATH
            if not os.path.isabs(path):
                path = os.path.join(os.path.dirname(__file__), '..', '..', path)
            
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                
                for sticker_data in data.get('stickers', []):
                    sticker = StickerDefinition.from_dict(sticker_data)
                    self.stickers[sticker.id] = sticker
                logger.info(f"Loaded {len(self.stickers)} sticker definitions")
            else:
                logger.warning(f"Sticker definitions not found: {path}")
        except Exception as e:
            logger.error(f"Error loading sticker definitions: {e}")
    
    def _load_unlocked_stickers(self):
        """Load unlocked stickers from DataStore."""
        if not self.data_store:
            return
        
        try:
            load_result = self.data_store.load(self.student_id)
            if load_result.data and 'unlocked_stickers' in load_result.data:
                for sticker_data in load_result.data['unlocked_stickers']:
                    sticker = StickerDefinition.from_dict(sticker_data)
                    self.unlocked_stickers[sticker.id] = sticker
                logger.info(f"Loaded {len(self.unlocked_stickers)} unlocked stickers")
        except Exception as e:
            logger.error(f"Error loading unlocked stickers: {e}")
    
    def _initialize_progress(self):
        """Initialize progress for all stickers."""
        # Planet Winner: 1 planet completed
        self.progress['planet_winner'] = StickerProgress('planet_winner', 0, 1, False)
        
        # Flawless Victory: 1 perfect planet
        self.progress['flawless_victory'] = StickerProgress('flawless_victory', 0, 1, False)
        
        # Speed Demon: 1 fast planet
        self.progress['speed_demon'] = StickerProgress('speed_demon', 0, 1, False)
        
        # Hint Helper: 1 full hint solve
        self.progress['hint_helper'] = StickerProgress('hint_helper', 0, 1, False)
        
        # Comeback Champion: 1 failed-then-cleared planet
        self.progress['comeback_champion'] = StickerProgress('comeback_champion', 0, 1, False)
        
        # Galaxy Explorer: 3 solar systems
        self.progress['galaxy_explorer'] = StickerProgress('galaxy_explorer', 0, SOLAR_SYSTEM_PLANETS_REQUIRED, False)
        
        # Streak King/Queen: 15 streak
        self.progress['streak_king'] = StickerProgress('streak_king', 0, STREAK_STICKER_REQUIRED, False)
        self.progress['streak_queen'] = StickerProgress('streak_queen', 0, STREAK_STICKER_REQUIRED, False)
        
        # Word Master: 50 words
        self.progress['word_master'] = StickerProgress('word_master', 0, WORDS_MASTERED_FOR_STICKER, False)
        
        # Early Bird: 1 game before 9am
        self.progress['early_bird'] = StickerProgress('early_bird', 0, 1, False)
        
        # Night Owl: 1 game after 7pm
        self.progress['night_owl'] = StickerProgress('night_owl', 0, 1, False)
    
    def _save_unlocked_stickers(self):
        """Save unlocked stickers to DataStore."""
        if not self.data_store:
            return
        
        try:
            sticker_list = [sticker.to_dict() for sticker in self.unlocked_stickers.values()]
            progress_data = {
                'student_id': self.student_id,
                'unlocked_stickers': sticker_list
            }
            self.data_store.save(self.student_id, progress_data)
        except Exception as e:
            logger.error(f"Error saving unlocked stickers: {e}")
    
    def start_session(self, hour: int):
        """
        Start a new game session.

        Args:
            hour: Current hour (0-23) for time-based stickers
        """
        self._current_solar_system_planets = set()
        
        # Check time-based stickers (only unlock once)
        if hour < 9:
            if not self.tracker.early_bird_unlocked:
                self._unlock_sticker('early_bird', {"time": f"{hour}:00"})
        
        if hour >= 19:
            if not self.tracker.night_owl_unlocked:
                self._unlock_sticker('night_owl', {"time": f"{hour}:00"})
    
    def end_session(self):
        """End session - persist any new unlocks."""
        self._save_unlocked_stickers()
    
    # Event handlers for sticker tracking
    
    def start_planet(self, planet_id: str, solar_system: str):
        """
        Called when a planet starts.

        Args:
            planet_id: Unique planet identifier
            solar_system: Solar system the planet belongs to
        """
        self._current_planet_start_time = time.time()
    
    def on_planet_completed(self, planet_id: str, solar_system: str, score: int, 
                           total_attempts: int, first_attempt_correct: bool,
                           hints_used: int):
        """
        Called when a planet is completed.
        
        Args:
            planet_id: Planet identifier
            solar_system: Solar system name
            score: Words correct out of 5
            total_attempts: Total attempts across all words
            first_attempt_correct: Whether all 5 were correct on first try
            hints_used: Total hints used
        """
        self.tracker.planets_completed += 1
        
        # Planet Winner
        if not self.tracker.planet_winner_unlocked:
            self._unlock_sticker('planet_winner', {"planet": planet_id})
        
        # Flawless Victory
        if first_attempt_correct and not self.tracker.flawless_victory_unlocked:
            self._unlock_sticker('flawless_victory', {"planet": planet_id})
        
        # Speed Demon
        if self._current_planet_start_time:
            elapsed = time.time() - self._current_planet_start_time
            if elapsed < SPEED_DEMON_MAX_SECONDS and not self.tracker.speed_demon_unlocked:
                self._unlock_sticker('speed_demon', {"time": f"{elapsed:.1f}s"})
        
        # Comeback Champion
        if planet_id in self.tracker.failed_planets and not self.tracker.comeback_champion_unlocked:
            self._unlock_sticker('comeback_champion', {"planet": planet_id})
            self.tracker.cleared_after_fail.add(planet_id)
        
        # Track solar system completion
        if solar_system not in self.tracker.solar_system_planets:
            self.tracker.solar_system_planets[solar_system] = set()
        self.tracker.solar_system_planets[solar_system].add(planet_id)
        
        # Galaxy Explorer - check if solar system is complete (3 planets)
        current_system_planets = self.tracker.solar_system_planets.get(solar_system, set())
        if len(current_system_planets) >= SOLAR_SYSTEM_PLANETS_REQUIRED and solar_system not in self.tracker.completed_solar_systems:
            self.tracker.completed_solar_systems.add(solar_system)
            if not self.tracker.galaxy_explorer_unlocked:
                self._unlock_sticker('galaxy_explorer', {"system": solar_system})
        
        # Update progress
        self.progress['planet_winner'].current = self.tracker.planets_completed
        self.progress['flawless_victory'].current = self.tracker.perfect_planets
        self.progress['speed_demon'].current = self.tracker.fast_planet_completions
        self.progress['galaxy_explorer'].current = len(self.tracker.completed_solar_systems)
        
        # Mark progress complete where applicable
        if self.tracker.planet_winner_unlocked:
            self.progress['planet_winner'].is_complete = True
        if self.tracker.flawless_victory_unlocked:
            self.progress['flawless_victory'].is_complete = True
        if self.tracker.speed_demon_unlocked:
            self.progress['speed_demon'].is_complete = True
        if self.tracker.galaxy_explorer_unlocked:
            self.progress['galaxy_explorer'].is_complete = True
    
    def on_planet_failed(self, planet_id: str):
        """
        Called when a planet is failed.
        
        Args:
            planet_id: Planet identifier
        """
        self.tracker.failed_planets.add(planet_id)
    
    def on_full_hint_solved(self):
        """Called when a word is solved after using all hints."""
        self.tracker.full_hint_solves += 1
        
        if not self.tracker.hint_helper_unlocked:
            self._unlock_sticker('hint_helper')
        
        self.progress['hint_helper'].current = self.tracker.full_hint_solves
        if self.tracker.hint_helper_unlocked:
            self.progress['hint_helper'].is_complete = True
    
    def on_streak_update(self, streak: int):
        """
        Called when streak is updated.
        
        Args:
            streak: Current streak value
        """
        self.tracker.current_streak = streak
        
        # Update progress for both King and Queen
        self.progress['streak_king'].current = streak
        self.progress['streak_queen'].current = streak
        
        # Streak King (male)
        if self.is_female and streak >= STREAK_STICKER_REQUIRED and not self.tracker.streak_queen_unlocked:
            self._unlock_sticker('streak_queen', {"streak": streak})
        elif not self.is_female and streak >= STREAK_STICKER_REQUIRED and not self.tracker.streak_king_unlocked:
            self._unlock_sticker('streak_king', {"streak": streak})
    
    def on_word_mastered(self):
        """Called when a word is mastered."""
        self.tracker.words_mastered += 1
        
        self.progress['word_master'].current = self.tracker.words_mastered
        
        if not self.tracker.word_master_unlocked and self.tracker.words_mastered >= WORDS_MASTERED_FOR_STICKER:
            self._unlock_sticker('word_master', {"total": self.tracker.words_mastered})
        
        if self.tracker.word_master_unlocked:
            self.progress['word_master'].is_complete = True
    
    # Sticker unlocking
    
    def _unlock_sticker(self, sticker_id: str, context: dict = None):
        """
        Unlock a sticker.
        
        Args:
            sticker_id: Sticker identifier to unlock
            context: Optional context data about the unlock
        """
        if sticker_id in self.unlocked_stickers:
            return None  # Already unlocked
        
        sticker = self.stickers.get(sticker_id)
        if not sticker:
            logger.warning(f"Sticker not found: {sticker_id}")
            return None
        
        # Mark as unlocked in tracker
        tracker_flag = f"{sticker_id}_unlocked"
        if hasattr(self.tracker, tracker_flag):
            setattr(self.tracker, tracker_flag, True)
        
        # Mark progress as complete
        if sticker_id in self.progress:
            self.progress[sticker_id].is_complete = True
        
        sticker.unlocked_at = datetime.now()
        sticker.unlock_context = context
        self.unlocked_stickers[sticker_id] = sticker
        
        logger.info(f"Sticker unlocked: {sticker.name}")
        
        # Notify callback
        if self.on_sticker_unlocked:
            self.on_sticker_unlocked(sticker)
        
        return sticker
    
    # Progress getters
    
    def get_progress(self, sticker_id: str) -> Optional[StickerProgress]:
        """
        Get progress toward a specific sticker.
        
        Args:
            sticker_id: Sticker identifier
            
        Returns:
            StickerProgress or None
        """
        return self.progress.get(sticker_id)
    
    def get_all_stickers(self) -> List[StickerDefinition]:
        """
        Get all available stickers.
        
        Returns:
            List of all StickerDefinition objects
        """
        return list(self.stickers.values())
    
    def get_unlocked_stickers(self) -> List[StickerDefinition]:
        """
        Get all unlocked stickers.
        
        Returns:
            List of unlocked StickerDefinition objects
        """
        return list(self.unlocked_stickers.values())
    
    def get_locked_stickers(self) -> List[StickerDefinition]:
        """
        Get all locked stickers.
        
        Returns:
            List of locked StickerDefinition objects
        """
        return [s for s in self.stickers.values() if s.id not in self.unlocked_stickers]
    
    def is_sticker_unlocked(self, sticker_id: str) -> bool:
        """
        Check if a sticker is unlocked.
        
        Args:
            sticker_id: Sticker identifier
            
        Returns:
            True if unlocked, False otherwise
        """
        return sticker_id in self.unlocked_stickers
    
    def get_sticker_by_id(self, sticker_id: str) -> Optional[StickerDefinition]:
        """
        Get sticker by ID.
        
        Args:
            sticker_id: Sticker identifier
            
        Returns:
            Sticker or None
        """
        return self.stickers.get(sticker_id)
    
    def get_unlocked_count(self) -> int:
        """
        Get count of unlocked stickers.
        
        Returns:
            Number of unlocked stickers
        """
        return len(self.unlocked_stickers)
    
    def get_total_count(self) -> int:
        """
        Get total number of stickers.
        
        Returns:
            Total sticker count
        """
        return len(self.stickers)
    
    def get_progress_summary(self) -> Dict:
        """
        Get summary of all sticker progress.
        
        Returns:
            Dictionary with sticker progress information
        """
        return {
            sticker_id: {
                'current': prog.current,
                'target': prog.target,
                'percent': prog.progress_percent(),
                'complete': prog.is_complete
            }
            for sticker_id, prog in self.progress.items()
        }
    
    def get_stickers_by_category(self, category: str) -> List[StickerDefinition]:
        """
        Get stickers filtered by category.
        
        Args:
            category: Category name ('progression', 'skill', 'special')
            
        Returns:
            List of StickerDefinition objects in the category
        """
        return [s for s in self.stickers.values() if s.category == category]
    
    def get_new_unlocks_since(self, timestamp: datetime) -> List[StickerDefinition]:
        """
        Get stickers unlocked since a given timestamp.
        
        Args:
            timestamp: Timestamp to check since
            
        Returns:
            List of newly unlocked stickers
        """
        return [
            s for s in self.unlocked_stickers.values()
            if s.unlocked_at and s.unlocked_at > timestamp
        ]


# Factory function
def create_sticker_manager(
    student_id: str = "student_1",
    data_store: Optional[DataStore] = None,
    is_female: bool = True
) -> StickerManager:
    """
    Create a StickerManager instance.
    
    Args:
        student_id: Student identifier
        data_store: Optional DataStore for persistence
        is_female: Student's gender (affects Streak King vs Queen)
        
    Returns:
        Configured StickerManager instance
    
    Example:
        >>> # Create sticker manager
        >>> manager = create_sticker_manager(student_id="student_1", data_store=data_store)
        >>> 
        >>> # Set up callback for sticker unlocks
        >>> def on_sticker_unlocked(sticker):
        ...     print(f"New Sticker! {sticker.name}")
        >>> 
        >>> manager.on_sticker_unlocked = on_sticker_unlocked
        >>> 
        >>> # Start a new session
        >>> manager.start_session(hour=8)  # Early bird!
        >>> 
        >>> # Track events
        >>> manager.start_planet("mars", "solar_system_1")
        >>> manager.on_planet_completed("mars", "solar_system_1", score=5, 
        ...                              total_attempts=5, first_attempt_correct=True,
        ...                              hints_used=0)
        >>> 
        >>> # Check progress
        >>> progress = manager.get_progress('flawless_victory')
        >>> print(f"Flawless Victory: {progress.get_progress_text()}")
        >>> 
        >>> # Get unlocked stickers
        >>> unlocked = manager.get_unlocked_stickers()
        >>> for sticker in unlocked:
        ...     print(f"  - {sticker.name} ({sticker.rarity.value})")
        >>> 
        >>> # End session (persists unlocks)
        >>> manager.end_session()
    """
    return StickerManager(student_id=student_id, data_store=data_store, is_female=is_female)
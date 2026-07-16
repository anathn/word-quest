"""
Streak Bonus Manager (STORY-004-02)

Manages streak bonus milestones and triggers special animations at streak thresholds.
Implements visual rewards for maintaining consecutive correct answers.
"""

from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum


class BonusType(Enum):
    """Types of streak bonus animations."""
    GOLDEN_ROCKET = "golden_rocket"
    PLANET_DISCOVERY = "planet_discovery"


@dataclass
class BonusMilestone:
    """Represents a streak bonus milestone."""
    streak_threshold: int
    bonus_type: BonusType
    message: str
    triggered: bool = False


class StreakBonusManager:
    """
    Manages streak bonus milestones and triggers.
    
    Features:
    - Detect when streak reaches milestone thresholds (3, 5)
    - Track which bonuses have been triggered in current session
    - Provide callbacks for animation trigger
    - Reset milestones for new sessions
    
    Milestones:
    - 3-word streak: Golden rocket boost animation
    - 5-word streak: Special planet discovery animation
    """
    
    def __init__(self):
        """Initialize the streak bonus manager with default milestones."""
        self.milestones = [
            BonusMilestone(
                streak_threshold=3,
                bonus_type=BonusType.GOLDEN_ROCKET,
                message="3-word streak! GOLDEN BOOST!"
            ),
            BonusMilestone(
                streak_threshold=5,
                bonus_type=BonusType.PLANET_DISCOVERY,
                message="5-word streak! NEW PLANET DISCOVERED!"
            ),
        ]
        self.active_bonus: Optional[BonusMilestone] = None
        self._on_bonus_triggered: Optional[Callable] = None
        self._previous_streak = 0  # Track previous streak for milestone detection
    
    @property
    def on_bonus_triggered(self) -> Optional[Callable]:
        """Callback when a bonus milestone is triggered."""
        return self._on_bonus_triggered
    
    @on_bonus_triggered.setter
    def on_bonus_triggered(self, callback: Callable):
        """
        Set callback for bonus triggered event.
        
        Args:
            callback: Function to call when bonus is triggered
        """
        self._on_bonus_triggered = callback
    
    def check_milestone(self, streak: int) -> Optional[BonusMilestone]:
        """
        Check if current streak triggered a bonus milestone.
        
        Only triggers milestones when the streak EXACTLY matches the threshold
        AND we haven't already surpassed that threshold.
        
        Args:
            streak: Current streak value
            
        Returns:
            BonusMilestone if a milestone was triggered, None otherwise
        """
        for milestone in self.milestones:
            threshold = milestone.streak_threshold
            # Only trigger if:
            # 1. Streak exactly matches threshold
            # 2. We haven't already surpassed this threshold (previous_streak < threshold)
            # 3. Not yet triggered
            if (streak == threshold and 
                self._previous_streak < threshold and 
                not milestone.triggered):
                milestone.triggered = True
                self.active_bonus = milestone
                
                # Trigger callback if set
                if self._on_bonus_triggered:
                    self._on_bonus_triggered(milestone)
                
                self._previous_streak = streak
                return milestone
        
        self._previous_streak = streak
        return None
    
    def get_active_bonus(self) -> Optional[BonusMilestone]:
        """
        Get the currently active bonus (being animation).
        
        Returns:
            Active BonusMilestone or None
        """
        return self.active_bonus
    
    def clear_active_bonus(self):
        """Clear the active bonus after animation completes."""
        self.active_bonus = None
    
    def reset_session(self):
        """
        Reset all milestones for a new session.
        
        Allows bonuses to trigger again in new sessions.
        """
        for milestone in self.milestones:
            milestone.triggered = False
        self.active_bonus = None
        self._previous_streak = 0  # Reset streak tracking for new session
    
    def get_triggered_milestones(self) -> list:
        """
        Get list of all triggered milestones.
        
        Returns:
            List of triggered BonusMilestone objects
        """
        return [m for m in self.milestones if m.triggered]
    
    def is_bonus_available(self, streak: int) -> bool:
        """
        Check if a bonus is available for the given streak.
        
        Args:
            streak: Streak value to check
            
        Returns:
            True if bonus available and not yet triggered
        """
        for milestone in self.milestones:
            if streak == milestone.streak_threshold and not milestone.triggered:
                return True
        return False


# Factory function
def create_streak_bonus_manager() -> StreakBonusManager:
    """
    Create a StreakBonusManager instance.
    
    Returns:
        Configured StreakBonusManager instance
    
    Example:
        >>> # Create and use a streak bonus manager
        >>> manager = create_streak_bonus_manager()
        >>> 
        >>> # Set up callback for bonus triggered events
        >>> def on_bonus_triggered(bonus):
        ...     print(f"Bonus triggered: {bonus.message}")
        >>> 
        >>> manager.on_bonus_triggered = on_bonus_triggered
        >>> 
        >>> # Check for milestones after each correct answer
        >>> new_streak = 3  # From streak tracker
        >>> bonus = manager.check_milestone(new_streak)
        >>> if bonus:
        ...     # Start bonus animation
        ...     print(f"Milestone reached! {bonus.message}")
        >>> 
        >>> # Reset for new game session
        >>> manager.reset_session()
    """
    return StreakBonusManager()
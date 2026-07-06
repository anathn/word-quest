"""
Hint Manager Component

Manages progressive hint escalation for spelling words.
Provides escalating assistance from letter count to full letter revelation.
"""

from typing import Optional, List, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import time


class HintLevel(Enum):
    """Hint escalation levels."""
    NONE = 0           # No hints given
    LETTER_COUNT = 1   # First hint: show letter count
    LETTER_REVEAL = 2  # Second hint+: reveal letters one by one
    FULL_REVEAL = 3    # All letters revealed


@dataclass
class HintData:
    """Data for a single hint."""
    level: int
    hint_type: HintLevel
    message: str
    revealed_indices: Set[int] = field(default_factory=set)


class HintManager:
    """
    Manages hint escalation for spelling words.
    
    Features:
    - Progressive hint escalation (letter count → letter reveals)
    - No penalty for using hints
    - Tracks hint usage for analytics
    - Handles edge cases (short words)
    
    Hint Escalation Flow:
    1. First incorrect answer → Hint level 1: "This word has X letters"
    2. Second incorrect answer → Hint level 2: "The 1st letter is 'A'"
    3. Third incorrect answer → Hint level 3: "The 2nd letter is 'B'"
    4. Continue until all letters revealed or student answers correctly
    """
    
    # Encouraging messages for each hint level
    HINT_MESSAGES = {
        0: "",  # No hint
        1: "This word has {} letters",
        2: "The 1st letter is '{}'",
        3: "The 2nd letter is '{}'",
        4: "The 3rd letter is '{}'",
        5: "The 4th letter is '{}'",
        6: "The 5th letter is '{}'",
        7: "The 6th letter is '{}'",
        8: "The 7th letter is '{}'",
        9: "The 8th letter is '{}'",
        10: "The 9th letter is '{}'",
        11: "The 10th letter is '{}'",
    }
    
    # Ordinal suffixes for letter positions
    ORDINAL_SUFFIXES = {
        1: "1st", 2: "2nd", 3: "3rd",
        4: "4th", 5: "5th", 6: "6th",
        7: "7th", 8: "8th", 9: "9th",
        10: "10th", 11: "11th", 12: "12th"
    }
    
    def __init__(self, word: str):
        """
        Initialize the hint manager for a word.
        
        Args:
            word: The target spelling word
        """
        self.word = word.upper()
        self.word_length = len(word)
        
        # Hint state
        self.current_level = 0  # 0 = no hints
        self.revealed_indices: Set[int] = set()
        self.hint_history: List[HintData] = []
        
        # Analytics tracking
        self.hint_usage_count = 0
        self.first_hint_timestamp: Optional[float] = None
        self.last_hint_timestamp: Optional[float] = None
        
        # Callbacks
        self.on_hint_shown: Optional[Callable[[HintData], None]] = None
        
        # Edge case: very short words (1-2 letters) skip to faster reveals
        self.is_short_word = self.word_length <= 2
    
    def get_next_hint(self) -> Optional[HintData]:
        """
        Generate the next hint based on current escalation level.
        
        Returns:
            HintData for the next hint, or None if fully revealed
        """
        # Already fully revealed
        if self.current_level > self.word_length:
            return None
        
        if self.current_level == 0:
            # First hint: letter count
            self.current_level = 1
            message = self.HINT_MESSAGES[1].format(self.word_length)
            hint = HintData(
                level=1,
                hint_type=HintLevel.LETTER_COUNT,
                message=message
            )
            self._record_hint(hint)
            return hint
        
        elif self.current_level <= self.word_length:
            # Letter-by-letter reveal
            # Calculate index BEFORE incrementing: current_level=1 → index 0, current_level=2 → index 1, etc.
            next_idx = self.current_level - 1
            self.current_level += 1
            
            if next_idx >= self.word_length:
                # All letters already revealed
                return None
            
            letter = self.word[next_idx]
            self.revealed_indices.add(next_idx)
            
            # Build hint message
            ordinal = self.ORDINAL_SUFFIXES.get(next_idx + 1, f"{next_idx + 1}th")
            message = f"The {ordinal} letter is '{letter}'"
            
            hint = HintData(
                level=self.current_level,
                hint_type=HintLevel.LETTER_REVEAL,
                message=message,
                revealed_indices=self.revealed_indices.copy()
            )
            self._record_hint(hint)
            return hint
        
        else:
            # Full reveal
            self.current_level = self.word_length + 1
            self.revealed_indices = set(range(self.word_length))
            
            message = f"The word is: {self.word}"
            hint = HintData(
                level=self.current_level,
                hint_type=HintLevel.FULL_REVEAL,
                message=message,
                revealed_indices=self.revealed_indices.copy()
            )
            self._record_hint(hint)
            return hint
    
    def escalate(self):
        """Move to the next hint level (deprecated, use get_next_hint)."""
        self.get_next_hint()
    
    def get_revealed_pattern(self) -> str:
        """
        Get the current word pattern with revealed letters shown.
        
        Returns:
            String with revealed letters and underscores for hidden letters,
            separated by spaces (e.g., "H _ L _ O")
        """
        result = []
        for i, letter in enumerate(self.word):
            if i in self.revealed_indices:
                result.append(letter)
            else:
                result.append('_')
        return ' '.join(result)
    
    def get_revealed_letters(self) -> Set[int]:
        """
        Get the set of revealed letter indices.
        
        Returns:
            Set of indices that have been revealed
        """
        return self.revealed_indices.copy()
    
    def is_letter_revealed(self, index: int) -> bool:
        """
        Check if a specific letter index has been revealed.
        
        Args:
            index: The letter index to check
            
        Returns:
            True if the letter is revealed
        """
        return index in self.revealed_indices
    
    def is_fully_revealed(self) -> bool:
        """
        Check if all letters have been revealed.
        
        Returns:
            True if all letters are revealed
        """
        return len(self.revealed_indices) >= self.word_length
    
    def get_hint_count(self) -> int:
        """
        Get the total number of hints given.
        
        Returns:
            Number of hints provided
        """
        return self.hint_usage_count
    
    def reset(self):
        """Reset the hint manager to initial state."""
        self.current_level = 0
        self.revealed_indices.clear()
        self.hint_history.clear()
        self.hint_usage_count = 0
        self.first_hint_timestamp = None
        self.last_hint_timestamp = None
    
    def _record_hint(self, hint: HintData):
        """Record hint usage for analytics."""
        self.hint_usage_count += 1
        self.hint_history.append(hint)
        
        now = time.time()
        if self.first_hint_timestamp is None:
            self.first_hint_timestamp = now
        self.last_hint_timestamp = now
        
        # Notify callback
        if self.on_hint_shown:
            self.on_hint_shown(hint)
    
    def get_analytics(self) -> dict:
        """
        Get hint usage analytics.
        
        Returns:
            Dictionary with hint usage statistics
        """
        return {
            "word": self.word,
            "hint_count": self.hint_usage_count,
            "current_level": self.current_level,
            "revealed_indices": list(self.revealed_indices),
            "first_hint_timestamp": self.first_hint_timestamp,
            "last_hint_timestamp": self.last_hint_timestamp,
            "is_fully_revealed": self.is_fully_revealed()
        }
    
    def get_encouragement_message(self) -> str:
        """
        Get an encouraging message based on hint usage.
        
        Returns:
            Encouraging text for the student
        """
        if self.hint_usage_count == 0:
            return "You've got this!"
        elif self.hint_usage_count == 1:
            return "You're getting closer!"
        elif self.hint_usage_count <= 3:
            return "Keep trying, you're doing great!"
        else:
            return "Great effort! You're almost there!"


# Factory function
def create_hint_manager(word: str) -> HintManager:
    """
    Create a HintManager instance for a word.
    
    Args:
        word: The spelling word to manage hints for
        
    Returns:
        Configured HintManager instance
    """
    return HintManager(word)

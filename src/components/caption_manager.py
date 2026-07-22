"""
Caption Manager Component (STORY-006-03)

Manages caption queue, display timing, and state for closed captions.
Provides text backup for all audio content including Captain Cosmos voice lines,
sound effects descriptions, and environmental audio cues.
"""

import time
import json
import os
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Deque, List, Dict, Any
from enum import Enum


logger = logging.getLogger(__name__)


class CaptionIntensity(Enum):
    """Caption intensity levels for accessibility."""
    FULL = "full"        # All captions including SFX descriptions
    REDUCED = "reduced"  # Only dialogue, no SFX descriptions
    OFF = "off"          # No captions


@dataclass
class Caption:
    """Represents a single caption message."""
    text: str
    duration: float = 3.0  # seconds to display
    speaker: Optional[str] = None
    caption_id: str = ""
    timestamp: float = 0.0
    is_sfx: bool = False
    intensity_required: CaptionIntensity = CaptionIntensity.FULL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert caption to dictionary."""
        return {
            'text': self.text,
            'duration': self.duration,
            'speaker': self.speaker,
            'caption_id': self.caption_id,
            'timestamp': self.timestamp,
            'is_sfx': self.is_sfx,
            'intensity_required': self.intensity_required.value
        }


class CaptionManager:
    """
    Central manager for caption queue, display timing, and state.
    
    Features:
    - Queue-based caption display system
    - Timing control for caption duration
    - Support for multiple intensity modes (full, reduced, off)
    - Caption history tracking for analytics
    - Integration with audio system for synchronized display
    
    Usage:
        manager = CaptionManager(caption_display)
        manager.show_caption("Welcome!", speaker="Captain Cosmos")
        manager.update(delta_time)  # Call every frame
    """
    
    def __init__(self, caption_display: Optional[Any] = None, data_dir: Optional[str] = None):
        """
        Initialize the caption manager.
        
        Args:
            caption_display: Optional CaptionDisplay instance for rendering
            data_dir: Directory for caption data. Defaults to 'data'.
        """
        # Resolve data directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_data_dir = os.path.join(base_dir, '..', '..', 'data')
        self.data_dir = data_dir or os.environ.get('WORDQUEST_DATA_DIR', default_data_dir)
        
        self.display = caption_display
        self.caption_queue: Deque[Caption] = deque()
        self.current_caption: Optional[Caption] = None
        self.enabled = True
        self.expires_at = 0.0
        self.caption_history: List[Caption] = []
        self._intensity_mode = CaptionIntensity.FULL
        self._captions_db: Dict[str, str] = {}
        
        # Load captions database
        self._load_captions_db()
        
        logger.info("CaptionManager initialized")
    
    def _load_captions_db(self) -> None:
        """Load captions database from JSON file."""
        captions_file = os.path.join(self.data_dir, 'captions.json')
        try:
            if os.path.exists(captions_file):
                with open(captions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._captions_db = data.get('captions', {})
                    logger.info(f"Loaded {len(self._captions_db)} caption templates")
            else:
                # Initialize with default captions
                self._init_default_captions()
                logger.info("Initialized default captions database")
        except Exception as e:
            logger.error(f"Error loading captions database: {e}")
            self._init_default_captions()
    
    def _init_default_captions(self) -> None:
        """Initialize default captions if database doesn't exist."""
        self._captions_db = {
            'captain_cosmos': {
                'welcome': "Welcome aboard, Space Speller! I'm Captain Cosmos!",
                'good_job': "Excellent spelling! You're a star traveler!",
                'try_again': "No worries, mistakes help us learn. Try again!",
                'streak_3': "Amazing! You're on a roll with 3 in a row!",
                'streak_5': "Incredible! 5 perfect words! You've discovered a new planet!",
                'planet_complete': "Planet cleared! Ready for the next adventure?",
                'hint_1': "Here's a hint: The word has {count} letters.",
                'hint_2': "The {n} letter is '{char}'.",
                'hint_final': "The word is: {word}"
            },
            'system': {
                'level_complete': "Planet Complete! 5 out of 5 words mastered!",
                'game_over': "Great game! See you next time!",
                'save_complete': "Progress saved successfully",
                'loaded': "Profile loaded - ready to explore!"
            },
            'sfx_descriptions': {
                'correct_chime': "[SUCCESSFUL CHIME]",
                'incorrect_tone': "[GENTLE DESCENDING TONE]",
                'streak_bonus': "[EXCITING BOOST SOUND]",
                'planet_bloom': "[MAGICAL SPARKLE SOUND]"
            }
        }
    
    def get_caption(self, category: str, key: str, **kwargs) -> Optional[str]:
        """
        Get caption text from database.
        
        Args:
            category: Caption category (e.g., 'captain_cosmos', 'system')
            key: Caption key within category
            **kwargs: Format arguments for the caption text
            
        Returns:
            Caption text or None if not found
        """
        try:
            category_dict = self._captions_db.get(category, {})
            caption_text = category_dict.get(key)
            
            if caption_text and kwargs:
                caption_text = caption_text.format(**kwargs)
            
            return caption_text
        except Exception as e:
            logger.error(f"Error getting caption {category}.{key}: {e}")
            return None
    
    def show_caption(self, text: str, duration: float = 3.0,
                    speaker: Optional[str] = None, 
                    caption_id: str = "",
                    is_sfx: bool = False) -> None:
        """
        Show a caption immediately.
        
        Args:
            text: Caption text to display
            duration: How long to show the caption (seconds)
            speaker: Optional speaker name (e.g., "Captain Cosmos")
            caption_id: Unique identifier for this caption
            is_sfx: Whether this is a sound effect description
        """
        if not self.enabled or not text:
            return
            
        # Check intensity mode for SFX captions
        if is_sfx and self._intensity_mode == CaptionIntensity.REDUCED:
            return
            
        caption = Caption(
            text=text,
            duration=duration,
            speaker=speaker,
            caption_id=caption_id,
            timestamp=time.time(),
            is_sfx=is_sfx,
            intensity_required=self._intensity_mode if not is_sfx else CaptionIntensity.REDUCED
        )
        
        self.current_caption = caption
        self.expires_at = time.time() + duration
        self.caption_history.append(caption)
        
        if self.display:
            self.display.show_caption(caption)
        
        logger.debug(f"Caption shown: {speaker}: {text}")
    
    def queue_caption(self, caption: Caption) -> None:
        """
        Add caption to queue for later display.
        
        Args:
            caption: Caption object to queue
        """
        # Check intensity mode
        if caption.is_sfx and self._intensity_mode == CaptionIntensity.REDUCED:
            return
            
        self.caption_queue.append(caption)
        logger.debug(f"Caption queued: {caption.caption_id}")
    
    def queue_caption_by_id(self, category: str, key: str, 
                           duration: float = 3.0,
                           speaker: Optional[str] = None,
                           **kwargs) -> None:
        """
        Queue a caption from the database by category and key.
        
        Args:
            category: Caption category
            key: Caption key
            duration: Display duration
            speaker: Optional speaker name
            **kwargs: Format arguments
        """
        text = self.get_caption(category, key, **kwargs)
        if text:
            caption = Caption(
                text=text,
                duration=duration,
                speaker=speaker,
                caption_id=f"{category}.{key}"
            )
            self.queue_caption(caption)
    
    def show_caption_by_id(self, category: str, key: str,
                          duration: float = 3.0,
                          speaker: Optional[str] = None,
                          is_sfx: bool = False,
                          **kwargs) -> None:
        """
        Show a caption from the database immediately.
        
        Args:
            category: Caption category
            key: Caption key
            duration: Display duration
            speaker: Optional speaker name
            is_sfx: Whether this is a sound effect description
            **kwargs: Format arguments
        """
        text = self.get_caption(category, key, **kwargs)
        if text:
            self.show_caption(
                text=text,
                duration=duration,
                speaker=speaker,
                caption_id=f"{category}.{key}",
                is_sfx=is_sfx
            )
    
    def update(self, delta_time: float) -> None:
        """
        Update caption state (call every frame).
        
        Args:
            delta_time: Time elapsed since last frame (seconds)
        """
        if not self.enabled:
            return
            
        current_time = time.time()
        
        # Check if current caption expired
        if self.current_caption and current_time >= self.expires_at:
            self.current_caption = None
            if self.display:
                self.display.hide_caption()
            logger.debug("Caption expired and hidden")
            
        # Show next caption if queue has items and no current caption
        if not self.current_caption and self.caption_queue:
            next_caption = self.caption_queue.popleft()
            self.show_caption(
                text=next_caption.text,
                duration=next_caption.duration,
                speaker=next_caption.speaker,
                caption_id=next_caption.caption_id,
                is_sfx=next_caption.is_sfx
            )
    
    def clear(self) -> None:
        """Clear all captions."""
        self.caption_queue.clear()
        self.current_caption = None
        if self.display:
            self.display.hide_caption()
        logger.debug("All captions cleared")
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable captions.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        if not enabled:
            self.clear()
        logger.info(f"Captions {'enabled' if enabled else 'disabled'}")
    
    def set_intensity_mode(self, mode: CaptionIntensity) -> None:
        """
        Set caption intensity mode for accessibility.
        
        Args:
            mode: Intensity mode (FULL, REDUCED, or OFF)
        """
        old_mode = self._intensity_mode
        self._intensity_mode = mode
        
        # If turning off, clear captions
        if mode == CaptionIntensity.OFF:
            self.enabled = False
        else:
            self.enabled = True
        
        logger.info(f"Caption intensity set to: {mode.value}")
    
    def get_intensity_mode(self) -> CaptionIntensity:
        """Get current intensity mode."""
        return self._intensity_mode
    
    def get_caption_history(self, limit: int = 10) -> List[Caption]:
        """
        Get recent caption history.
        
        Args:
            limit: Maximum number of captions to return
            
        Returns:
            List of recent captions (most recent first)
        """
        return list(reversed(self.caption_history[-limit:]))
    
    def skip_celebration(self) -> None:
        """Skip any queued celebration captions."""
        self.caption_queue.clear()
        logger.debug("Celebration captions skipped")
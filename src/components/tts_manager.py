"""
TTS Manager Component

Provides high-level TTS functionality with queue management,
state tracking, and game integration.
"""

from typing import Optional, List, Dict, Any, Callable
from threading import Thread, Lock
from queue import Queue, Empty
import logging
import time

from .tts_engine import TTSEngine, create_tts_engine
from .tts_settings import TTSSettings, TTSConfigManager

logger = logging.getLogger(__name__)


class TTSManager:
    """
    Manages TTS functionality with speech queue, state tracking,
    and game integration.
    """
    
    def __init__(self, config_manager: Optional[TTSConfigManager] = None):
        """
        Initialize TTS Manager.
        
        Args:
            config_manager: Optional TTS config manager for persistence
        """
        self.engine: TTSEngine = create_tts_engine()
        self.config_manager = config_manager or TTSConfigManager()
        
        # Load settings from config
        self.config_manager.load()
        self.settings: TTSSettings = self.config_manager.settings
        
        # Speech queue and threading
        self.speech_queue: Queue = Queue()
        self._speaker_thread: Optional[Thread] = None
        self._running = False
        self._lock = Lock()
        
        # State tracking
        self._is_speaking = False
        self._current_text: Optional[str] = None
        
        # Callbacks
        self._on_speech_start: Optional[Callable[[], None]] = None
        self._on_speech_end: Optional[Callable[[], None]] = None
        
        # Initialize TTS engine
        self._initialized = self.engine.initialize()
        if not self._initialized:
            logger.warning("TTS engine failed to initialize")
        
        logger.info(f"TTS Manager initialized (enabled={self.settings.enabled}, "
                   f"speed={self.settings.speed}, volume={self.settings.volume})")
    
    @property
    def is_enabled(self) -> bool:
        """Check if TTS is enabled"""
        return self.settings.enabled and self._initialized
    
    @property
    def is_initialized(self) -> bool:
        """Check if TTS manager is initialized"""
        return self._initialized
    
    def start(self) -> None:
        """Start TTS speaker thread"""
        if not self.is_enabled:
            logger.debug("TTS not enabled, not starting speaker thread")
            return
            
        with self._lock:
            if self._running:
                return
                
            self._running = True
            self._speaker_thread = Thread(target=self._speaker_loop, daemon=True)
            self._speaker_thread.start()
            logger.info("TTS speaker thread started")
    
    def stop(self) -> None:
        """Stop TTS and clear queue"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            self.speech_queue.clear()
            
            if self.engine.is_speaking():
                self.engine.stop()
            
            if self._speaker_thread and self._speaker_thread.is_alive():
                # Wait briefly for thread to finish
                self._speaker_thread.join(timeout=1.0)
            
            self._speaker_thread = None
            self._is_speaking = False
            self._current_text = None
            logger.info("TTS speaker thread stopped")
    
    def speak_word(self, word: str, spell_out: bool = False) -> None:
        """
        Speak a word, optionally spelling it letter by letter.
        
        Args:
            word: The word to speak
            spell_out: If True, spell the word letter by letter
        """
        if not self.is_enabled:
            return
            
        if not word or not word.strip():
            logger.warning("Empty word provided to speak_word")
            return
        
        word = word.strip()
        
        with self._lock:
            if spell_out:
                text = " ".join(word.upper())
            else:
                text = word
            
            self.speech_queue.put(text)
            logger.debug(f"TTS queue word: '{text}' (spell_out={spell_out})")
    
    def speak_letters(self, word: str) -> None:
        """
        Spell word letter by letter.
        
        Args:
            word: The word to spell out
        """
        if not self.is_enabled:
            return
            
        if not word or not word.strip():
            logger.warning("Empty word provided to speak_letters")
            return
        
        word = word.strip()
        letters = " ".join(word.upper())
        
        # Clear queue and speak letters first
        with self._lock:
            self.speech_queue.queue.clear()
            self.speech_queue.put(letters)
            logger.debug(f"TTS spelling letters: '{letters}'")
    
    def speak_continuously(self, words: List[str]) -> None:
        """
        Speak a list of words continuously.
        
        Args:
            words: List of words to speak in sequence
        """
        if not self.is_enabled:
            return
            
        with self._lock:
            for word in words:
                if word and word.strip():
                    self.speech_queue.put(word.strip())
            logger.debug(f"TTS queue continuous words: {words}")
    
    def clear_queue(self) -> None:
        """Clear the speech queue without stopping speech"""
        with self._lock:
            self.speech_queue.queue.clear()
            logger.debug("TTS speech queue cleared")
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable TTS.
        
        Args:
            enabled: True to enable, False to disable
        """
        old_enabled = self.settings.enabled
        self.settings.enabled = enabled
        
        if enabled and not old_enabled:
            # Re-enable TTS
            if self._initialized:
                self.start()
                logger.info("TTS enabled")
        elif not enabled and old_enabled:
            # Disable TTS
            self.stop()
            logger.info("TTS disabled")
        
        self.config_manager.settings = self.settings
        self.config_manager.save()
    
    def set_speed(self, speed: float) -> None:
        """
        Set speech speed (0.5 to 2.0).
        
        Args:
            speed: Speed multiplier (0.5 = slow, 1.0 = normal, 2.0 = fast)
        """
        speed = max(0.5, min(2.0, speed))
        self.settings.speed = speed
        self.config_manager.settings = self.settings
        self.config_manager.save()
        logger.debug(f"TTS speed set to {speed}x")
    
    def set_volume(self, volume: float) -> None:
        """
        Set speech volume (0.0 to 1.0).
        
        Args:
            volume: Volume level (0.0 = mute, 1.0 = max)
        """
        volume = max(0.0, min(1.0, volume))
        self.settings.volume = volume
        self.config_manager.settings = self.settings
        self.config_manager.save()
        logger.debug(f"TTS volume set to {volume}")
    
    def set_voice(self, voice_id: str) -> bool:
        """
        Set the voice to use.
        
        Args:
            voice_id: Voice identifier
            
        Returns:
            True if voice was set successfully
        """
        success = self.engine.set_voice(voice_id)
        if success:
            self.settings.voice_id = voice_id
            self.config_manager.settings = self.settings
            self.config_manager.save()
            logger.info(f"TTS voice set to: {voice_id}")
        return success
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        return self.engine.get_available_voices()
    
    def get_settings(self) -> TTSSettings:
        """Get current TTS settings"""
        return self.settings
    
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        return self._is_speaking
    
    def get_current_text(self) -> Optional[str]:
        """Get the text currently being spoken"""
        return self._current_text
    
    def update(self) -> None:
        """
        Update TTS state (call each frame if using main loop).
        Can be used to track speech state in game loop.
        """
        if not self.is_enabled:
            return
        
        # Check if engine finished speaking
        if self._is_speaking and not self.engine.is_speaking():
            self._is_speaking = False
            if self._on_speech_end:
                self._on_speech_end()
            
            logger.debug("TTS speech ended")
    
    def on_speech_start(self, callback: Callable[[], None]) -> None:
        """
        Set callback for when speech starts.
        
        Args:
            callback: Function to call when speech begins
        """
        self._on_speech_start = callback
    
    def on_speech_end(self, callback: Callable[[], None]) -> None:
        """
        Set callback for when speech ends.
        
        Args:
            callback: Function to call when speech ends
        """
        self._on_speech_end = callback
    
    def _speaker_loop(self) -> None:
        """Background thread that processes speech queue"""
        logger.debug("TTS speaker loop started")
        
        while self._running:
            try:
                # Get text from queue with timeout
                text = self.speech_queue.get(timeout=0.2)
                
                # Mark as speaking
                self._current_text = text
                self._is_speaking = True
                
                # Call speech start callback
                if self._on_speech_start:
                    self._on_speech_start()
                
                # Speak the text
                self.engine.speak(text, self.settings.speed, self.settings.volume)
                
                # Mark as not speaking
                self._is_speaking = False
                self._current_text = None
                
                # Call speech end callback
                if self._on_speech_end:
                    self._on_speech_end()
                    
            except Empty:
                # Queue empty, continue loop
                continue
            except Exception as e:
                logger.error(f"TTS speaker loop error: {e}")
                continue
        
        logger.debug("TTS speaker loop ended")
    
    def cleanup(self) -> None:
        """Cleanup TTS resources"""
        logger.info("Cleaning up TTS Manager...")
        self.stop()
        self.engine.cleanup()
        logger.info("TTS Manager cleanup complete")
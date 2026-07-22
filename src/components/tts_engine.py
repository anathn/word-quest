"""
Text-to-Speech (TTS) Engine Component

Provides cross-platform text-to-speech functionality using pyttsx3.
Supports adjustable speech speed, volume, and voice selection.
"""

import pyttsx3
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class TTSEngine(ABC):
    """Abstract base class for TTS engines"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the TTS engine. Returns True on success."""
        pass
    
    @abstractmethod
    def speak(self, text: str, speed: float = 1.0, 
              volume: float = 1.0) -> None:
        """Speak text at given speed and volume"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop current speech"""
        pass
    
    @abstractmethod
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        pass
    
    @abstractmethod
    def set_voice(self, voice_id: str) -> bool:
        """Set the voice to use. Returns True on success."""
        pass


class PlatformTTSWrapper(TTSEngine):
    """Platform-specific TTS implementation using pyttsx3"""
    
    def __init__(self):
        self.engine: Optional[pyttsx3.Engine] = None
        self.initialized = False
        self._lock = Lock()
        self._current_voice_id: Optional[str] = None
        self._base_rate = 200  # words per minute (default)
        
    def initialize(self) -> bool:
        """Initialize the pyttsx3 engine"""
        with self._lock:
            if self.initialized:
                return True
                
            try:
                logger.info("Initializing TTS engine...")
                self.engine = pyttsx3.init()
                
                # Set default properties
                self._base_rate = self.engine.getProperty('rate')
                self.engine.setProperty('rate', self._base_rate)
                self.engine.setProperty('volume', 1.0)
                
                self.initialized = True
                logger.info(f"TTS engine initialized successfully (base rate: {self._base_rate} wpm)")
                return True
            except Exception as e:
                logger.error(f"TTS initialization failed: {e}")
                self.initialized = False
                return False
    
    def speak(self, text: str, speed: float = 1.0, volume: float = 1.0) -> None:
        """Speak text with adjustable speed and volume"""
        if not self.initialized or not self.engine:
            logger.warning("TTS engine not initialized, cannot speak")
            return
            
        if not text or not text.strip():
            logger.debug("Empty text provided to TTS, skipping")
            return
        
        # Stop any ongoing speech to prevent overlap
        if self.is_speaking():
            self.stop()
            
        with self._lock:
            try:
                # Adjust properties
                adjusted_rate = int(self._base_rate * speed)
                self.engine.setProperty('rate', adjusted_rate)
                self.engine.setProperty('volume', volume)
                
                # Speak
                self.engine.say(text)
                self.engine.runAndWait()
                
                # Reset to default voice if needed (pyttsx3 may change it)
                if self._current_voice_id and self.initialized:
                    voices = self.engine.getProperty('voices')
                    if voices:
                        self.engine.setProperty('voice', self._current_voice_id)
                        
            except Exception as e:
                logger.error(f"TTS speak error: {e}")
    
    def stop(self) -> None:
        """Stop current speech"""
        if not self.initialized or not self.engine:
            return
            
        with self._lock:
            try:
                if self.is_speaking():
                    self.engine.stop()
                    logger.debug("TTS speech stopped")
            except Exception as e:
                logger.error(f"TTS stop error: {e}")
    
    def is_speaking(self) -> bool:
        """Check if currently speaking"""
        if not self.initialized or not self.engine:
            return False
            
        try:
            # pyttsx3 doesn't have a direct is_playing() method
            # We'll use a workaround by checking the queue
            return self.engine.isProcessing() if hasattr(self.engine, 'isProcessing') else False
        except Exception:
            return False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices"""
        if not self.initialized or not self.engine:
            return []
            
        try:
            voices = self.engine.getProperty('voices')
            if voices:
                return [
                    {
                        'id': voice.id,
                        'name': voice.name,
                        'gender': voice.gender if hasattr(voice, 'gender') else 'Unknown',
                        'age': voice.age if hasattr(voice, 'age') else 'Unknown'
                    }
                    for voice in voices
                ]
            return []
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []
    
    def set_voice(self, voice_id: str) -> bool:
        """Set the voice to use. Returns True on success."""
        if not self.initialized or not self.engine:
            return False
            
        try:
            # Validate voice exists in available voices
            voices = self.get_available_voices()
            if not any(voice['id'] == voice_id for voice in voices):
                logger.error(f"Voice '{voice_id}' not found in available voices")
                return False
            
            self.engine.setProperty('voice', voice_id)
            self._current_voice_id = voice_id
            logger.info(f"TTS voice set to: {voice_id}")
            return True
        except Exception as e:
            logger.error(f"Error setting voice: {e}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup TTS resources"""
        # Don't use lock here to avoid deadlock with stop()
        if self.initialized and self.engine:
            try:
                # Call stop directly without acquiring lock (stop will acquire it)
                with self._lock:
                    should_stop = self.initialized and self.is_speaking()
                if should_stop:
                    self.stop()  # stop() will acquire lock internally
                self.engine = None
                self.initialized = False
                logger.info("TTS engine cleanup complete")
            except Exception as e:
                logger.error(f"TTS cleanup error: {e}")


class FallbackTTSEngine(TTSEngine):
    """Fallback TTS engine that does nothing when pyttsx3 is unavailable"""
    
    def __init__(self):
        logger.warning("Using fallback TTS engine (pyttsx3 unavailable)")
        
    def initialize(self) -> bool:
        """Stub initialization"""
        return False
    
    def speak(self, text: str, speed: float = 1.0, volume: float = 1.0) -> None:
        """Stub speak - does nothing"""
        pass
    
    def stop(self) -> None:
        """Stub stop - does nothing"""
        pass
    
    def is_speaking(self) -> bool:
        """Always returns False"""
        return False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Returns empty list"""
        return []
    
    def set_voice(self, voice_id: str) -> bool:
        """Always returns False"""
        return False


def create_tts_engine() -> TTSEngine:
    """
    Factory function to create a TTS engine.
    Returns PlatformTTSWrapper if pyttsx3 is available, otherwise FallbackTTSEngine.
    """
    try:
        import pyttsx3
        return PlatformTTSWrapper()
    except ImportError:
        logger.warning("pyttsx3 not installed, using fallback TTS engine")
        return FallbackTTSEngine()
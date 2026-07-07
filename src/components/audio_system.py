"""
Audio System Component

Manages text-to-speech (TTS) integration and audio playback for the game.
Provides a unified interface for speaking words, playing sound effects,
and handling audio fallback scenarios.
"""

import threading
import queue
from typing import Optional, Callable
import json
import os
import math
import wave
import struct


class AudioSystem:
    """
    Manages all audio-related functionality including TTS and sound effects.
    
    Features:
    - Text-to-speech using pyttsx3 with gTTS fallback
    - Non-blocking audio playback
    - Audio replay capability
    - Graceful degradation when TTS unavailable
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the audio system.
        
        Args:
            data_dir: Directory containing audio assets and configuration.
                     Defaults to WORDQUEST_DATA_DIR env var or 'src/data'.
        """
        self.data_dir = data_dir or os.environ.get('WORDQUEST_DATA_DIR', 'src/data')
        self.audio_available = True
        self.tts_engine = None
        self.tts_engine_type = None  # 'pyttsx3', 'gtts', or None
        self.volume = 1.0
        self.speech_rate = 150  # words per minute
        self._playback_queue = queue.Queue()
        self._playback_thread = None
        self._stop_playback = False
        self._current_callback: Optional[Callable] = None
        
        # Initialize TTS
        self._init_tts()
        
        # Load audio configuration
        self._load_config()
    
    def _init_tts(self) -> bool:
        """
        Initialize the text-to-speech engine.
        
        Tries pyttsx3 first (offline), then falls back to gTTS (online).
        
        Returns:
            True if TTS initialized successfully, False otherwise
        """
        # Try pyttsx3 first (offline, works without internet)
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', self.speech_rate)
            self.tts_engine.setProperty('volume', self.volume)
            self.tts_engine_type = 'pyttsx3'
            return True
        except Exception as e:
            print(f"pyttsx3 not available: {e}")
        
        # Fall back to gTTS (requires internet)
        try:
            from gtts import gTTS
            self.tts_engine_type = 'gtts'
            return True
        except Exception as e:
            print(f"gTTS not available: {e}")
        
        # No TTS available
        self.audio_available = False
        self.tts_engine_type = None
        print("Warning: No TTS engine available. Text-only mode enabled.")
        return False
    
    def _load_config(self):
        """Load audio configuration from file if available."""
        config_path = os.path.join(self.data_dir, "audio_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.volume = config.get('volume', 1.0)
                    self.speech_rate = config.get('speech_rate', 150)
                    
                    # Update engine properties if available
                    if self.tts_engine and self.tts_engine_type == 'pyttsx3':
                        self.tts_engine.setProperty('rate', self.speech_rate)
                        self.tts_engine.setProperty('volume', self.volume)
            except Exception as e:
                print(f"Error loading audio config: {e}")
    
    def speak(self, text: str, on_complete: Optional[Callable] = None) -> bool:
        """
        Speak text using text-to-speech.
        
        Args:
            text: The text to speak
            on_complete: Optional callback when speech completes
            
        Returns:
            True if speech started successfully, False otherwise
        """
        if not self.audio_available or not text:
            if on_complete:
                on_complete()
            return False
        
        self._current_callback = on_complete
        
        if self.tts_engine_type == 'pyttsx3':
            return self._speak_pyttsx3(text, on_complete)
        elif self.tts_engine_type == 'gtts':
            return self._speak_gtts(text, on_complete)
        
        return False
    
    def _speak_pyttsx3(self, text: str, on_complete: Optional[Callable] = None) -> bool:
        """Speak using pyttsx3 engine."""
        try:
            def on_end_callback(_):
                if on_complete:
                    on_complete()
            
            self.tts_engine.say(text)
            self.tts_engine.connect('end-phrase', on_end_callback)
            self.tts_engine.runAndWait()
            return True
        except Exception as e:
            print(f"pyttsx3 speak error: {e}")
            if on_complete:
                on_complete()
            return False
    
    def _speak_gtts(self, text: str, on_complete: Optional[Callable] = None) -> bool:
        """Speak using gTTS engine (requires internet)."""
        try:
            from gtts import gTTS
            import tempfile
            
            # Guard pygame import - required for audio playback
            try:
                import pygame
            except ImportError:
                print("pygame required for gTTS playback. Install with: pip install pygame")
                if on_complete:
                    on_complete()
                return False
            
            # Generate speech audio
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                tmp_path = tmp.name
            tts.save(tmp_path)
            
            # Play using pygame (only init if not already initialized)
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
            except Exception as e:
                print(f"Error initializing pygame mixer: {e}")
                if on_complete:
                    on_complete()
                return False
            
            # Clean up after playback
            def cleanup():
                while pygame.mixer.music.get_busy():
                    pass
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass  # File may already be deleted
                if on_complete:
                    on_complete()
            
            threading.Thread(target=cleanup, daemon=True).start()
            return True
            
        except Exception as e:
            print(f"gTTS speak error: {e}")
            if on_complete:
                on_complete()
            return False
    
    def stop(self):
        """Stop any currently playing audio."""
        self._stop_playback = True
        if self.tts_engine and self.tts_engine_type == 'pyttsx3':
            try:
                self.tts_engine.stop()
            except:
                pass
    
    def set_volume(self, volume: float):
        """
        Set the audio volume.
        
        Args:
            volume: Volume level from 0.0 (mute) to 1.0 (max)
        """
        self.volume = max(0.0, min(1.0, volume))
        
        if self.tts_engine and self.tts_engine_type == 'pyttsx3':
            self.tts_engine.setProperty('volume', self.volume)
    
    def set_speech_rate(self, rate: int):
        """
        Set the speech rate.
        
        Args:
            rate: Words per minute (typical range: 100-200)
        """
        self.speech_rate = max(50, min(300, rate))
        
        if self.tts_engine and self.tts_engine_type == 'pyttsx3':
            self.tts_engine.setProperty('rate', self.speech_rate)
    
    def is_audio_available(self) -> bool:
        """Check if audio/TTS is available."""
        return self.audio_available
    
    def get_engine_type(self) -> Optional[str]:
        """Get the current TTS engine type."""
        return self.tts_engine_type
    
    def test_audio(self) -> bool:
        """
        Test audio functionality.
        
        Returns:
            True if audio works, False otherwise
        """
        return self.speak("Test audio.", on_complete=lambda: None)
    
    def play_sfx(self, sfx_name: str, volume: float = 1.0) -> bool:
        """
        Play a sound effect from asset file.
        
        Args:
            sfx_name: Name of the SFX file (without extension)
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            True if playback started successfully
        """
        # Try pygame first
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            # Construct file paths (try .ogg first, then .wav)
            assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'audio')
            ogg_path = os.path.join(assets_dir, f'{sfx_name}.ogg')
            wav_path = os.path.join(assets_dir, f'{sfx_name}.wav')
            
            # Determine which file to use
            sfx_path = ogg_path if os.path.exists(ogg_path) else (
                wav_path if os.path.exists(wav_path) else None
            )
            
            if not sfx_path:
                print(f"Warning: SFX file not found: {ogg_path} or {wav_path}")
                return False
            
            # Load and play
            sound = pygame.mixer.Sound(sfx_path)
            sound.set_volume(volume)
            sound.play()
            
            return True
        except Exception as e:
            print(f"Error playing SFX '{sfx_name}': {e}")
            return False
    
    def generate_tone(self, filename: str, frequency: float, duration: float, volume: float = 0.7, sample_rate: int = 44100):
        """
        Generate a simple sine wave tone and save to WAV file.
        
        Args:
            filename: Output filename
            frequency: Frequency in Hz
            duration: Duration in seconds
            volume: Volume level (0.0 to 1.0)
            sample_rate: Sample rate in Hz
        """
        num_samples = int(sample_rate * duration)
        
        with wave.open(filename, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            
            for i in range(num_samples):
                # Sine wave
                value = int(volume * 32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
                wav_file.writeframes(struct.pack('<h', value))


# Singleton instance for global access
_audio_system: Optional[AudioSystem] = None
_audio_system_lock = threading.Lock()


def get_audio_system(data_dir: str = "src/data") -> AudioSystem:
    """
    Get or create the global audio system instance.
    
    Args:
        data_dir: Directory containing audio assets
        
    Returns:
        The AudioSystem singleton instance
    """
    global _audio_system
    if _audio_system is None:
        with _audio_system_lock:
            if _audio_system is None:
                _audio_system = AudioSystem(data_dir)
    return _audio_system


def reset_audio_system():
    """Reset the global audio system (useful for testing)."""
    global _audio_system
    with _audio_system_lock:
        _audio_system = None

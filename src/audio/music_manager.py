"""
Music Manager Module

Background music playback and management system.
Handles track loading, playback, transitions, volume control, and procedural music generation.
"""

import pygame
import numpy as np
import wave
import io
import os
import logging
from typing import Optional, Dict
from enum import Enum
import math

logger = logging.getLogger(__name__)

from .music_config import (
    MusicState,
    MusicTrack,
    MUSIC_CONFIG,
    PROCEDURAL_CONFIG,
    AudioDefaults,
    AudioPaths,
    get_music_track
)


class MusicManager:
    """
    Central background music management system.
    
    Features:
    - Procedural ambient music generation (no external files required)
    - Smooth fade transitions between tracks
    - Volume control with persistence support
    - Mute/unmute functionality
    - State-based music selection
    - Graceful handling when audio unavailable
    
    For MVP: Uses procedural generation to avoid external audio dependencies.
    For Production: Can load pre-composed OGG files from data/sounds/music/
    """
    
    def __init__(self):
        """Initialize the music manager."""
        self._music_volume = AudioDefaults.MUSIC_VOLUME
        self._is_muted = AudioDefaults.OVERALL_MUTE
        self._current_state: Optional[MusicState] = None
        self._is_playing = False
        self._is_paused = False
        self._initialized = False
        self._mixer_initialized = False
        self._audio_available = True
        self._current_track: Optional[MusicTrack] = None
        self._music_channel: Optional[pygame.mixer.Channel] = None
        
        # Track whether music is actively playing (not just paused)
        self._active_music = False
        
        # Track fallback state
        self._initialization_error: Optional[str] = None
        
    def initialize(self) -> bool:
        """
        Initialize pygame mixer for music playback.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
        
        try:
            if not pygame.mixer.get_init():
                # Initialize mixer with music-appropriate settings
                pygame.mixer.init(
                    frequency=PROCEDURAL_CONFIG["sample_rate"],
                    size=-16,  # 16-bit signed
                    channels=PROCEDURAL_CONFIG["channels"],
                    buffer=PROCEDURAL_CONFIG["buffer_size"]
                )
                self._mixer_initialized = True
                
            # Try to get a music channel
            try:
                # pygame.mixer.music uses a dedicated channel
                self._active_music = False
            except Exception:
                pass
                
            self._initialized = True
            return True
            
        except Exception as e:
            self._initialization_error = str(e)
            self._audio_available = False
            print(f"Warning: Could not initialize pygame mixer for music: {e}")
            print("Background music will be unavailable.")
            self._initialized = True
            return False
    
    def play(self, state: MusicState) -> bool:
        """
        Play music for the specified game state with fade transition.
        
        Args:
            state: MusicState to play music for
            
        Returns:
            True if music started successfully, False otherwise
        """
        if not self._initialized:
            if not self.initialize():
                return False
        
        if not self._audio_available:
            return False
        
        if not pygame.mixer.get_init():
            return False
        
        try:
            track = get_music_track(state)
            
            # If already playing this state, just ensure it's not paused
            if self._current_state == state and self._is_playing:
                if self._is_paused:
                    self.resume()
                return True
            
            # Stop current music with fade if playing different track
            if self._is_playing and self._current_state != state:
                self.stop(fade_ms=track.fade_ms)
            
            # Generate and play new track
            self._current_state = state
            self._current_track = track
            
            # Generate procedural audio or load file
            if track.file_path and os.path.exists(track.file_path):
                # Use external file if available
                self._play_file(track)
            else:
                # Generate procedural music (MVP default)
                self._play_procedural(track)
            
            self._is_playing = True
            self._is_paused = False
            self._active_music = True
            
            return True
            
        except Exception as e:
            print(f"Error playing music for {state}: {e}")
            return False
    
    def stop(self, fade_ms: int = 500) -> bool:
        """
        Stop music playback with optional fade out.
        
        Args:
            fade_ms: Fade out duration in milliseconds
            
        Returns:
            True if stopped successfully
        """
        if not self._mixer_initialized or not pygame.mixer.get_init():
            return False
        
        try:
            if fade_ms > 0 and self._is_playing:
                pygame.mixer.music.fadeout(fade_ms)
                # Wait for fade to complete (non-blocking)
            else:
                pygame.mixer.music.stop()
            
            self._is_playing = False
            self._active_music = False
            return True
        except Exception as e:
            print(f"Error stopping music: {e}")
            return False
    
    def pause(self) -> bool:
        """
        Pause music playback.
        
        Returns:
            True if paused successfully
        """
        if not self._is_playing:
            return True
        
        try:
            pygame.mixer.music.pause()
            self._is_paused = True
            return True
        except Exception as e:
            print(f"Error pausing music: {e}")
            return False
    
    def resume(self) -> bool:
        """
        Resume paused music playback.
        
        Returns:
            True if resumed successfully
        """
        if not self._is_paused:
            return self._is_playing
        
        try:
            pygame.mixer.music.unpause()
            self._is_paused = False
            return True
        except Exception as e:
            print(f"Error resuming music: {e}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """
        Set music volume (0.0-1.0).
        
        Args:
            volume: Volume level from 0.0 (mute) to 1.0 (max)
            
        Returns:
            True if volume set successfully
        """
        try:
            volume = max(AudioDefaults.MIN_VOLUME, 
                        min(AudioDefaults.MAX_VOLUME, volume))
            self._music_volume = volume
            
            # Apply to current music if mixer is available
            if (self._is_playing and not self._is_muted and 
                pygame.mixer.get_init() and self._mixer_initialized):
                pygame.mixer.music.set_volume(volume)
            
            return True
        except Exception as e:
            print(f"Error setting music volume: {e}")
            return False
    
    def get_volume(self) -> float:
        """
        Get current music volume.
        
        Returns:
            Volume level from 0.0 to 1.0
        """
        return self._music_volume
    
    # Alias for backwards compatibility (deprecated)
    getVolume = get_volume
    
    def toggle_mute(self) -> bool:
        """
        Toggle music mute state.
        
        Returns:
            New mute state (True = muted)
        """
        self._is_muted = not self._is_muted
        
        if pygame.mixer.get_init() and self._mixer_initialized:
            if self._is_muted:
                pygame.mixer.music.set_volume(0.0)
            elif self._is_playing:
                pygame.mixer.music.set_volume(self._music_volume)
        
        return self._is_muted
    
    def mute(self) -> bool:
        """
        Mute music playback.
        
        Returns:
            True if muted successfully
        """
        self._is_muted = True
        if pygame.mixer.get_init() and self._mixer_initialized:
            pygame.mixer.music.set_volume(0.0)
        return True
    
    def unmute(self) -> bool:
        """
        Unmute music playback.
        
        Returns:
            True if unmuted successfully
        """
        self._is_muted = False
        if pygame.mixer.get_init() and self._mixer_initialized and self._is_playing:
            pygame.mixer.music.set_volume(self._music_volume)
        return True
    
    def is_muted(self) -> bool:
        """
        Check if music is muted.
        
        Returns:
            True if muted, False otherwise
        """
        return self._is_muted
    
    def is_playing(self) -> bool:
        """
        Check if music is currently playing.
        
        Returns:
            True if playing, False otherwise
        """
        return self._is_playing and self._active_music
    
    def is_paused(self) -> bool:
        """
        Check if music is paused.
        
        Returns:
            True if paused, False otherwise
        """
        return self._is_paused
    
    def get_current_state(self) -> Optional[MusicState]:
        """
        Get current music state.
        
        Returns:
            Current MusicState or None if not playing
        """
        return self._current_state
    
    def is_initialized(self) -> bool:
        """
        Check if music manager is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self._initialized
    
    def is_audio_available(self) -> bool:
        """
        Check if audio system is available.
        
        Returns:
            True if audio works, False otherwise
        """
        return self._audio_available
    
    def get_initialization_error(self) -> Optional[str]:
        """
        Get initialization error message.
        
        Returns:
            Error message or None
        """
        return self._initialization_error
    
    # Persistence methods for music settings
    
    def load_settings(self, preferences):
        """
        Load music settings from player preferences.
        
        Args:
            preferences: PlayerPreferencesManager instance
        """
        try:
            self._music_volume = preferences.get_music_volume()
            self._is_muted = preferences.get_music_muted()
            
            # Apply to mixer if playing and initialized
            if (self._is_playing and not self._is_muted and 
                pygame.mixer.get_init() and self._mixer_initialized):
                pygame.mixer.music.set_volume(self._music_volume)
        except Exception as e:
            print(f"Error loading music settings: {e}")
    
    def save_settings(self, preferences):
        """
        Save current music settings to player preferences.
        
        Args:
            preferences: PlayerPreferencesManager instance
        """
        try:
            preferences.set_music_volume(self._music_volume)
            preferences.set_music_muted(self._is_muted)
        except Exception as e:
            print(f"Error saving music settings: {e}")
    
    def _play_file(self, track: MusicTrack) -> bool:
        """
        Play music from an external file.
        
        Args:
            track: MusicTrack with file_path
            
        Returns:
            True if started successfully
        """
        try:
            # Fade in for smooth start
            pygame.mixer.music.load(track.file_path)
            pygame.mixer.music.set_volume(self._music_volume if not self._is_muted else 0.0)
            pygame.mixer.music.play(fade_ms=track.fade_ms)
            self._active_music = True
            return True
        except Exception as e:
            print(f"Error loading music file {track.file_path}: {e}")
            return False
    
    def _play_procedural(self, track: MusicTrack) -> bool:
        """
        Generate and play music procedurally (MVP approach).
        
        Args:
            track: MusicTrack configuration
            
        Returns:
            True if generation and playback started
        """
        try:
            # Generate audio data
            audio_data = self._generate_ambient_music(track)
            
            # Create pygame Sound object and play via music channel
            sound = pygame.mixer.Sound(buffer=audio_data)
            
            # Set volume and play with fade
            sound.set_volume(self._music_volume if not self._is_muted else 0.0)
            
            # For procedural music, we'll use the music channel
            # Note: pygame.mixer.music expects file-like objects for long tracks
            # For shorter procedural loops, we can play via a channel
            
            # Write to temporary buffer and play
            import io
            buffer = io.BytesIO()
            
            # Write WAV format
            with wave.open(buffer, 'wb') as wav_file:
                wav_file.setnchannels(PROCEDURAL_CONFIG["channels"])
                wav_file.setsampwidth(2)  # 16-bit = 2 bytes
                wav_file.setframerate(PROCEDURAL_CONFIG["sample_rate"])
                wav_file.writeframes(audio_data)
            
            buffer.seek(0)
            
            # Load and play
            pygame.mixer.music.load(buffer)
            pygame.mixer.music.set_volume(self._music_volume if not self._is_muted else 0.0)
            pygame.mixer.music.play()
            
            if track.should_loop:
                pygame.mixer.music.set_endevent(pygame.USER_EVENT + 1)
            
            self._active_music = True
            return True
            
        except Exception as e:
            print(f"Error generating procedural music: {e}")
            return False
    
    def _generate_ambient_music(self, track: MusicTrack) -> bytes:
        """
        Generate ambient music as raw bytes.
        
        Args:
            track: MusicTrack with generation parameters
            
        Returns:
            Raw audio bytes in 16-bit stereo format
        """
        # Calculate number of samples
        # Use short duration for testing to prevent hangs
        duration = track.duration
        if os.environ.get('TESTING', '0') == '1':
            duration = min(duration, 1.0)  # Cap at 1 second for tests
        num_samples = int(duration * PROCEDURAL_CONFIG["sample_rate"])
        
        # Create time array
        t = np.linspace(0, duration, num_samples, False)
        
        # Initialize audio buffer (stereo)
        left_channel = np.zeros(num_samples)
        right_channel = np.zeros(num_samples)
        
        # Generate layers based on track instruments
        for instrument in track.instruments:
            if instrument == "synth_pad":
                self._add_synth_pad(left_channel, right_channel, t, track)
            elif instrument == "ambient_pad":
                self._add_ambient_pad(left_channel, right_channel, t, track)
            elif instrument == "gentle_melody":
                self._add_gentle_melody(left_channel, right_channel, t, track)
            elif instrument == "subtle_ambient":
                self._add_subtle_ambient(left_channel, right_channel, t, track)
        
        # Apply master volume and reverb
        master_vol = PROCEDURAL_CONFIG["master_volume"]
        left_channel *= master_vol
        right_channel *= master_vol
        
        # Apply reverb (simple delay-based)
        reverb_mix = PROCEDURAL_CONFIG["reverb"]["mix"]
        decay = PROCEDURAL_CONFIG["reverb"]["decay_time"]
        left_channel = self._apply_reverb(left_channel, decay, reverb_mix)
        right_channel = self._apply_reverb(right_channel, decay, reverb_mix)
        
        # Normalize to prevent clipping
        max_val = max(np.max(np.abs(left_channel)), 
                     np.max(np.abs(right_channel)), 0.001)
        left_channel = left_channel / max_val * 0.9
        right_channel = right_channel / max_val * 0.9
        
        # Convert to 16-bit integers
        left_int = (left_channel * 32767).astype(np.int16)
        right_int = (right_channel * 32767).astype(np.int16)
        
        # Interleave stereo
        stereo = np.empty((num_samples, 2), dtype=np.int16)
        stereo[:, 0] = left_int
        stereo[:, 1] = right_int
        
        return stereo.tobytes()
    
    def _add_synth_pad(self, left: np.ndarray, right: np.ndarray, 
                       t: np.ndarray, track: MusicTrack):
        """Add a warm synth pad layer."""
        config = PROCEDURAL_CONFIG["ambient_pad"]
        
        # Generate envelope
        attack = 0.5  # Slow attack
        release = 2.0  # Long release
        envelope = self._create_envelope(t, attack, release)
        
        # Add multiple harmonically related frequencies
        base_freq = 130.81  # C3
        for freq_ratio, amp in [(1.0, 0.15), (1.5, 0.1), (2.0, 0.08)]:
            freq = base_freq * freq_ratio
            wave = np.sin(2 * np.pi * freq * t)
            
            # Pan between channels
            pan = np.sin(2 * np.pi * 0.02 * t)  # Slow panning
            left_wave = wave * (0.5 + 0.5 * pan)
            right_wave = wave * (0.5 - 0.5 * pan)
            
            left += left_wave * amp * envelope * config["amplitude"]
            right += right_wave * amp * envelope * config["amplitude"]
    
    def _add_ambient_pad(self, left: np.ndarray, right: np.ndarray,
                         t: np.ndarray, track: MusicTrack):
        """Add a slow ambient pad layer."""
        config = PROCEDURAL_CONFIG["ambient_pad"]
        
        # Very slow undulating pad
        freq = 55.0  # A1
        modulation_freq = 0.5  # Slow modulation
        
        mod = np.sin(2 * np.pi * modulation_freq * t) * 0.3 + 0.7
        
        wave = np.sin(2 * np.pi * freq * t)
        wave *= mod  # Add movement
        
        # Center the pad
        left += wave * 0.1 * config["amplitude"]
        right += wave * 0.1 * config["amplitude"]
    
    def _add_gentle_melody(self, left: np.ndarray, right: np.ndarray,
                          t: np.ndarray, track: MusicTrack):
        """Add a very gentle, not distracting melody."""
        melody_config = PROCEDURAL_CONFIG["melody"]
        
        # Play random notes from scale at slow rhythm
        scale = melody_config["scale"]
        rhythm = melody_config["rhythm"]
        
        note_duration = 60.0 / track.bpm  # Base duration
        current_time = 0.0
        note_index = 0
        
        for i, tk in enumerate(t):
            if tk >= current_time + note_duration * rhythm[note_index % len(rhythm)]:
                note_index += 1
                current_time = tk
            
            # Select note from scale (pentatonic for consonance)
            note_idx = note_index % len(scale)
            freq = scale[note_idx]
            
            # Gentle envelope for each note
            note_time = tk - current_time + note_duration * rhythm[note_index % len(rhythm)]
            attack = 0.1
            decay = 0.3
            note_env = self._create_note_envelope(note_time, attack, decay)
            
            # Play note softly (use scalar tk for single-sample wave)
            wave = np.sin(2 * np.pi * freq * tk) * 0.05 * melody_config["amplitude"]
            left[i] = wave * note_env
            right[i] = wave * note_env * 0.8  # Slightly quieter in right
    
    def _add_subtle_ambient(self, left: np.ndarray, right: np.ndarray,
                           t: np.ndarray, track: MusicTrack):
        """Add very subtle ambient texture."""
        # Use low amplitude pink noise filtered to bass frequencies
        pink_noise = self._generate_pink_noise(len(t))
        
        # Low pass filter (simple averaging)
        window_size = 100
        filtered = np.convolve(pink_noise, np.ones(window_size)/window_size, mode='same')
        
        # Very subtle
        left += filtered * 0.03
        right += filtered * 0.03
    
    def _create_envelope(self, t: np.ndarray, attack: float, 
                         release: float) -> np.ndarray:
        """
        Create_adsr_envelope.
        
        Args:
            t: Time array
            attack: Attack time in seconds
            release: Release time in seconds
            
        Returns:
            Envelope values
        """
        envelope = np.ones_like(t)
        
        # Attack
        if len(t) > 0:
            attack_samples = int(attack * PROCEDURAL_CONFIG["sample_rate"])
            if attack_samples > 0:
                envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        
        return envelope
    
    def _create_note_envelope(self, note_time: float, attack: float,
                              decay: float) -> float:
        """
        Create envelope for a single note.
        
        Args:
            note_time: Time within the note
            attack: Attack time
            decay: Decay time
            
        Returns:
            Envelope value (0.0-1.0)
        """
        if note_time < attack:
            return note_time / attack
        elif note_time < attack + decay:
            return 1.0 - (note_time - attack) / decay * 0.7
        else:
            return 0.3
    
    def _generate_pink_noise(self, size: int) -> np.ndarray:
        """
        Generate pink noise (1/f noise).
        
        Args:
            size: Number of samples
            
        Returns:
            Pink noise array
        """
        # Simple approximation: sum of multiple band-limited noise sources
        white = np.random.uniform(-1, 1, size)
        
        # Apply simple filter to approximate pink noise
        pink = np.zeros(size)
        cumulative = 0.0
        for i in range(size):
            cumulative = 0.99 * cumulative + 0.01 * white[i]
            pink[i] = cumulative
        
        return pink
    
    def _apply_reverb(self, signal: np.ndarray, decay: float,
                     mix: float) -> np.ndarray:
        """
        Apply simple reverb effect.
        
        Args:
            signal: Input signal
            decay: Reverb decay time
            mix: Wet/dry mix (0.0-1.0)
            
        Returns:
            Signal with reverb applied
        """
        # Simple delay-based reverb
        delay_samples = int(decay * PROCEDURAL_CONFIG["sample_rate"] * 0.1)
        if delay_samples <= 0:
            return signal
        
        delayed = np.zeros_like(signal)
        delayed[delay_samples:] = signal[:-delay_samples]
        
        # Apply multiple echoes
        reverb = signal.copy()
        echo_decay = 0.7
        for i in range(5):
            delay = delay_samples * (i + 1)
            if delay < len(signal):
                delayed[delay:] = signal[:-delay] * (echo_decay ** (i + 1))
                reverb += delayed
        
        # Mix dry and wet
        return (1 - mix) * signal + mix * reverb * 0.3


# Global singleton instance
_music_manager: Optional[MusicManager] = None


def get_music_manager() -> MusicManager:
    """
    Get or create the global music manager instance.
    
    Returns:
        MusicManager singleton
    """
    global _music_manager
    if _music_manager is None:
        _music_manager = MusicManager()
    return _music_manager


def reset_music_manager():
    """Reset the global music manager (useful for testing)."""
    global _music_manager
    _music_manager = None


# Convenience functions

def play_music(state: MusicState) -> bool:
    """
    Play music for a game state.
    
    Args:
        state: MusicState to play
    
    Returns:
        True if started successfully
    """
    return get_music_manager().play(state)


def stop_music(fade_ms: int = 500) -> bool:
    """
    Stop music playback.
    
    Args:
        fade_ms: Fade out duration
    
    Returns:
        True if stopped successfully
    """
    return get_music_manager().stop(fade_ms)


def set_music_volume(volume: float) -> bool:
    """
    Set music volume.
    
    Args:
        volume: Volume level 0.0-1.0
    
    Returns:
        True if set successfully
    """
    return get_music_manager().set_volume(volume)


def get_music_volume() -> float:
    """
    Get music volume.
    
    Returns:
        Volume level 0.0-1.0
    """
    return get_music_manager().get_volume()


def toggle_music_mute() -> bool:
    """
    Toggle music mute.
    
    Returns:
        New mute state
    """
    return get_music_manager().toggle_mute()
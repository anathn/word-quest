"""
SFX Generator Module

Procedurally generates sound effects using sine wave synthesis.
Creates high-quality audio without requiring external asset files.
"""

import numpy as np
import wave
import struct
import math
import tempfile
import os
from typing import List, Optional, Tuple
import io


class SFXGenerator:
    """
    Procedural sound effect generator.
    
    Generates high-quality audio using numpy for waveform synthesis.
    Supports multiple frequency layers, fade effects, and various waveforms.
    """
    
    def __init__(self, sample_rate: int = 44100):
        """
        Initialize the SFX generator.
        
        Args:
            sample_rate: Sample rate in Hz (default: 44100)
        """
        self.sample_rate = sample_rate
    
    def generate_tone(
        self,
        frequency: float,
        duration: float,
        amplitude: float = 0.3,
        waveform: str = 'sine',
        fade_duration: float = 0.02
    ) -> bytes:
        """
        Generate a single tone.
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in seconds
            amplitude: Amplitude (0.0 to 1.0)
            waveform: Waveform type ('sine', 'square', 'sawtooth', 'triangle')
            fade_duration: Duration for attack/release fade in seconds
            
        Returns:
            WAV format audio data as bytes
        """
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        
        # Generate waveform
        if waveform == 'sine':
            signal = amplitude * np.sin(2 * np.pi * frequency * t)
        elif waveform == 'square':
            signal = amplitude * np.sign(np.sin(2 * np.pi * frequency * t))
        elif waveform == 'sawtooth':
            signal = amplitude * (2 * (t * frequency - np.floor(t * frequency + 0.5)))
        elif waveform == 'triangle':
            signal = amplitude * (2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1)
        else:
            signal = amplitude * np.sin(2 * np.pi * frequency * t)
        
        # Apply fade in/out
        if fade_duration > 0 and fade_duration < duration:
            fade_samples = int(self.sample_rate * fade_duration)
            
            # Fade in
            fade_in = np.linspace(0, 1, fade_samples)
            signal[:fade_samples] *= fade_in
            
            # Fade out
            fade_out = np.linspace(1, 0, fade_samples)
            signal[-fade_samples:] *= fade_out
        
        # Convert to 16-bit PCM
        signal = np.int16(signal * 32767)
        
        # Return as WAV bytes
        return self._notify_array_to_wav(signal)
    
    def _notify_array_to_wav(self, signal: np.ndarray) -> bytes:
        """Convert numpy array to WAV bytes using io.BytesIO."""
        buffer = io.BytesIO()
        
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            
            # Convert to bytes and write
            wave_data = signal.tobytes()
            wav_file.writeframes(wave_data)
        
        buffer.seek(0)
        return buffer.read()
    
    def generate_chime(
        self,
        frequencies: List[float],
        durations: List[float],
        amplitude: float = 0.3,
        overlap: float = 0.05
    ) -> bytes:
        """
        Generate a sequence of tones (chime).
        
        Args:
            frequencies: List of frequencies in Hz
            durations: List of durations in seconds (must match frequencies length)
            amplitude: Base amplitude (0.0 to 1.0)
            overlap: Overlap between tones in seconds
            
        Returns:
            WAV format audio data as bytes
        """
        if len(frequencies) != len(durations):
            raise ValueError("frequencies and durations must have same length")
        
        # Calculate total duration with overlap
        total_duration = sum(durations) - (overlap * (len(durations) - 1))
        num_samples = int(self.sample_rate * total_duration)
        
        # Initialize signal
        signal = np.zeros(num_samples)
        
        current_offset = 0
        for freq, duration in zip(frequencies, durations):
            fade_duration = min(0.02, overlap)
            tone_data = self._generate_tone_array(
                freq, duration, amplitude, 'sine', fade_duration
            )
            
            # Determine overlap region
            overlap_samples = int(self.sample_rate * overlap)
            tone_samples = len(tone_data)
            
            # Ensure we don't go out of bounds
            end_offset = min(current_offset + tone_samples, num_samples)
            actual_length = end_offset - current_offset
            
            if actual_length > 0:
                # Blend overlapping tones
                if current_offset > 0 and overlap_samples > 0 and current_offset + overlap_samples <= len(signal):
                    # Create crossfade
                    fade_length = min(overlap_samples, len(tone_data), num_samples - current_offset)
                    crossfade = np.linspace(1, 0, fade_length)
                    signal[current_offset:current_offset + fade_length] += tone_data[:fade_length] * crossfade * amplitude
                    if len(tone_data) > fade_length:
                        signal[current_offset + fade_length:end_offset] += tone_data[fade_length:end_offset - current_offset] * amplitude
                else:
                    signal[current_offset:end_offset] += tone_data[:actual_length]
            
            current_offset += int(self.sample_rate * duration) - int(self.sample_rate * overlap)
        
        # Normalize to prevent clipping
        if np.max(np.abs(signal)) > 0:
            signal = signal / np.max(np.abs(signal)) * (amplitude * 0.9)
        
        # Convert to 16-bit PCM
        signal = np.int16(signal * 32767)
        
        return self._notify_array_to_wav(signal)
    
    def _generate_tone_array(
        self,
        frequency: float,
        duration: float,
        amplitude: float,
        waveform: str,
        fade_duration: float
    ) -> np.ndarray:
        """Generate a single tone as numpy array."""
        num_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, num_samples, endpoint=False)
        
        if waveform == 'sine':
            signal = amplitude * np.sin(2 * np.pi * frequency * t)
        elif waveform == 'square':
            signal = amplitude * np.sign(np.sin(2 * np.pi * frequency * t))
        elif waveform == 'sawtooth':
            signal = amplitude * (2 * (t * frequency - np.floor(t * frequency + 0.5)))
        elif waveform == 'triangle':
            signal = amplitude * (2 * np.abs(2 * (t * frequency - np.floor(t * frequency + 0.5))) - 1)
        else:
            signal = amplitude * np.sin(2 * np.pi * frequency * t)
        
        # Apply fade in/out
        if fade_duration > 0 and fade_duration < duration:
            fade_samples = int(self.sample_rate * fade_duration)
            
            if fade_samples > 0 and fade_samples < len(signal):
                fade_in = np.linspace(0, 1, fade_samples)
                signal[:fade_samples] *= fade_in
                
                fade_out = np.linspace(1, 0, fade_samples)
                signal[-fade_samples:] *= fade_out
        
        return signal
    
    def generate_fanfare(
        self,
        frequencies: List[float],
        durations: List[float],
        base_amplitude: float = 0.4,
        build_intensity: bool = True
    ) -> bytes:
        """
        Generate a fanfare sound (progressive intensity sequence).
        
        Args:
            frequencies: List of frequencies in Hz
            durations: List of durations in seconds
            base_amplitude: Base amplitude (0.0 to 1.0)
            build_intensity: Whether to increase amplitude across the fanfare
            
        Returns:
            WAV format audio data as bytes
        """
        if len(frequencies) != len(durations):
            raise ValueError("frequencies and durations must have same length")
        
        # Generate individual tones and concatenate
        all_samples = []
        
        for i, (freq, duration) in enumerate(zip(frequencies, durations)):
            # Build intensity for first half, sustain for second
            if build_intensity and i < len(frequencies) // 2:
                amplitude = base_amplitude * (0.5 + 0.5 * (i / (len(frequencies) // 2)))
            else:
                amplitude = base_amplitude
            
            tone_data = self._generate_tone_array(freq, duration, amplitude, 'sine', 0.02)
            all_samples.append(tone_data)
        
        # Concatenate all tones
        if all_samples:
            signal = np.concatenate(all_samples)
            
            # Normalize to prevent clipping
            if np.max(np.abs(signal)) > 0:
                signal = signal / np.max(np.abs(signal)) * (base_amplitude * 0.9)
            
            signal = np.int16(signal * 32767)
            return self._notify_array_to_wav(signal)
        
        # Return silence if no data
        return self.generate_silence(0.1)
    
    def generate_silence(self, duration: float) -> bytes:
        """
        Generate silence.
        
        Args:
            duration: Duration in seconds
            
        Returns:
            WAV format silence as bytes
        """
        num_samples = int(self.sample_rate * duration)
        signal = np.zeros(num_samples, dtype=np.int16)
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(signal.tobytes())
        
        buffer.seek(0)
        return buffer.read()
    
    def generate_noise_chunk(
        self,
        duration: float,
        amplitude: float = 0.2,
        lowpass_freq: float = 1000.0
    ) -> np.ndarray:
        """
        Generate low-pass filtered noise for whoosh effects.
        
        Args:
            duration: Duration in seconds
            amplitude: Amplitude (0.0 to 1.0)
            lowpass_freq: Low-pass filter cutoff frequency in Hz
            
        Returns:
            Noise as numpy array
        """
        num_samples = int(self.sample_rate * duration)
        noise = np.random.standard_normal(num_samples)
        
        # Simple moving average as low-pass filter
        window_size = int(self.sample_rate / lowpass_freq)
        if window_size < 1:
            window_size = 1
        noise = np.convolve(noise, np.ones(window_size)/window_size, mode='same')
        
        # Apply fade in/out
        fade_samples = int(self.sample_rate * 0.02)
        if fade_samples > 0 and fade_samples < len(noise):
            fade_in = np.linspace(0, 1, fade_samples)
            noise[:fade_samples] *= fade_in
            
            fade_out = np.linspace(1, 0, fade_samples)
            noise[-fade_samples:] *= fade_out
        
        return amplitude * noise
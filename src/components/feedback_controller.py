"""
Feedback Controller Component

Manages visual and audio feedback for correct/incorrect answers.
Provides encouraging responses with appropriate timing and animations.
"""

import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum


class FeedbackType(Enum):
    """Types of feedback that can be shown."""
    SUCCESS = "success"
    RETRY = "retry"
    NONE = "none"


class FeedbackState(Enum):
    """States for the feedback system."""
    IDLE = "idle"
    SHOWING_SUCCESS = "showing_success"
    SHOWING_RETRY = "showing_retry"
    TRANSITIONING = "transitioning"


@dataclass
class FeedbackConfig:
    """Configuration for feedback behavior."""
    # Timing
    success_display_duration: float = 2.0  # seconds
    feedback_transition_time: float = 0.1  # seconds for fade in/out
    
    # Audio
    success_volume: float = 0.7  # 70% volume
    retry_volume: float = 0.5    # 50% volume
    audio_fade_time: float = 1.0  # seconds
    
    # Visual
    success_message: str = "Great job!"
    retry_message: str = "Try again!"
    
    # Auto-advance
    auto_advance_on_success: bool = True


class FeedbackController:
    """
    Controls feedback display for answer validation.
    
    Features:
    - Success celebration with animation and audio
    - Gentle retry feedback for incorrect answers
    - Auto-advance timing management
    - Accessibility fallbacks
    """
    
    def __init__(self, audio_system=None, config: Optional[FeedbackConfig] = None):
        """
        Initialize the feedback controller.
        
        Args:
            audio_system: AudioSystem instance for playing feedback sounds
            config: FeedbackConfig for customization
        """
        self.audio_system = audio_system
        self.config = config or FeedbackConfig()
        
        self.state = FeedbackState.IDLE
        self.current_feedback: Optional[FeedbackType] = None
        self.feedback_start_time: float = 0
        self.auto_advance_timer: Optional[float] = None
        
        # Callbacks
        self.on_feedback_shown: Optional[Callable] = None
        self.on_feedback_complete: Optional[Callable] = None
        self.on_auto_advance: Optional[Callable] = None
        self.on_hint_requested: Optional[Callable] = None
        
        # Animation state
        self.animation_progress: float = 0.0
        self.animation_active: bool = False
    
    def show_feedback(self, is_correct: bool) -> bool:
        """
        Show appropriate feedback for an answer.
        
        Args:
            is_correct: Whether the answer was correct
            
        Returns:
            True if feedback was shown successfully
        """
        feedback_type = FeedbackType.SUCCESS if is_correct else FeedbackType.RETRY
        
        # Record timing
        self.feedback_start_time = time.time()
        self.current_feedback = feedback_type
        self.animation_active = True
        self.animation_progress = 0.0
        
        if is_correct:
            return self._show_success()
        else:
            return self._show_retry()
    
    def _show_success(self) -> bool:
        """Display success feedback."""
        self.state = FeedbackState.SHOWING_SUCCESS
        
        # Play success audio
        if self.audio_system:
            self._play_success_sound()
        
        # Set auto-advance timer
        if self.config.auto_advance_on_success:
            self.auto_advance_timer = self.feedback_start_time + self.config.success_display_duration
        
        # Notify listeners
        if self.on_feedback_shown:
            self.on_feedback_shown(FeedbackType.SUCCESS)
        
        return True
    
    def _show_retry(self) -> bool:
        """Display retry feedback."""
        self.state = FeedbackState.SHOWING_RETRY
        
        # Play retry audio (softer)
        if self.audio_system:
            self._play_retry_sound()
        
        # Request hint escalation
        if self.on_hint_requested:
            self.on_hint_requested()
        
        # Notify listeners
        if self.on_feedback_shown:
            self.on_feedback_shown(FeedbackType.RETRY)
        
        return True
    
    def _play_success_sound(self):
        """Play success chime audio."""
        try:
            # Success chime: ascending C-E-G chord
            def on_complete():
                pass
            
            # Use TTS for success message as fallback
            self.audio_system.speak(
                self.config.success_message,
                on_complete=on_complete
            )
        except Exception as e:
            print(f"Error playing success sound: {e}")
    
    def _play_retry_sound(self):
        """Play retry tone audio."""
        try:
            # Gentle retry message
            def on_complete():
                pass
            
            self.audio_system.speak(
                self.config.retry_message,
                on_complete=on_complete
            )
        except Exception as e:
            print(f"Error playing retry sound: {e}")
    
    def update(self, current_time: float):
        """
        Update feedback state (call each frame).
        
        Args:
            current_time: Current time in seconds
        """
        if not self.animation_active:
            return
        
        # Calculate animation progress
        elapsed = current_time - self.feedback_start_time
        
        if self.state == FeedbackState.SHOWING_SUCCESS:
            # Fade in quickly, then hold
            if elapsed < self.config.feedback_transition_time:
                self.animation_progress = elapsed / self.config.feedback_transition_time
            elif elapsed < self.config.success_display_duration:
                self.animation_progress = 1.0
            else:
                # Fade out
                fade_elapsed = elapsed - self.config.success_display_duration
                self.animation_progress = max(0, 1.0 - (fade_elapsed / self.config.feedback_transition_time))
                
                if self.animation_progress <= 0:
                    self._complete_feedback()
        
        elif self.state == FeedbackState.SHOWING_RETRY:
            # Gentle pulse animation
            import math
            self.animation_progress = 0.7 + 0.3 * math.sin(elapsed * 2)  # Slow pulse
    
    def _complete_feedback(self):
        """Complete the feedback display."""
        self.animation_active = False
        self.state = FeedbackState.IDLE
        self.current_feedback = FeedbackType.NONE
        
        if self.on_feedback_complete:
            self.on_feedback_complete(self.current_feedback)
        
        # Trigger auto-advance for success
        if self.auto_advance_timer and time.time() >= self.auto_advance_timer:
            if self.on_auto_advance:
                self.on_auto_advance()
    
    def force_complete(self):
        """Force feedback to complete (for incorrect answers)."""
        if self.state == FeedbackState.SHOWING_RETRY:
            self._complete_feedback()
    
    def get_feedback_message(self) -> str:
        """Get the current feedback message text."""
        if self.current_feedback == FeedbackType.SUCCESS:
            return self.config.success_message
        elif self.current_feedback == FeedbackType.RETRY:
            return self.config.retry_message
        return ""
    
    def is_feedback_active(self) -> bool:
        """Check if feedback is currently being shown."""
        return self.animation_active
    
    def get_state(self) -> FeedbackState:
        """Get the current feedback state."""
        return self.state
    
    def get_animation_progress(self) -> float:
        """Get the current animation progress (0.0 to 1.0)."""
        return self.animation_progress
    
    def set_audio_system(self, audio_system):
        """Set the audio system for feedback sounds."""
        self.audio_system = audio_system
    
    def reset(self):
        """Reset the feedback controller to idle state."""
        self.state = FeedbackState.IDLE
        self.current_feedback = FeedbackType.NONE
        self.feedback_start_time = 0
        self.auto_advance_timer = None
        self.animation_active = False
        self.animation_progress = 0.0


class CelebrationAnimation:
    """
    Manages celebration animation effects for correct answers.
    
    Features:
    - Particle burst effects
    - Planet sparkle animations
    - Text animation
    """
    
    def __init__(self):
        """Initialize the celebration animation."""
        self.active = False
        self.particles: list = []
        self.start_time = 0
        self.duration = 1.0
    
    def start(self):
        """Start the celebration animation."""
        self.active = True
        self.start_time = time.time()
        self._create_particles()
    
    def _create_particles(self):
        """Create particle effects for celebration."""
        # Simple particle system
        for i in range(20):
            self.particles.append({
                'x': 0,  # Will be set by renderer
                'y': 0,
                'vx': (i - 10) * 2,  # Spread horizontally
                'vy': -10 - (i % 10),  # Upward velocity
                'life': 1.0,
                'color': self._get_particle_color(i)
            })
    
    def _get_particle_color(self, index: int) -> tuple:
        """Get color for a particle."""
        colors = [
            (255, 215, 0),   # Gold
            (255, 255, 255), # White
            (0, 200, 83),    # Green
            (255, 153, 0),   # Orange
        ]
        return colors[index % len(colors)]
    
    def update(self, current_time: float):
        """Update particle positions."""
        if not self.active:
            return
        
        elapsed = current_time - self.start_time
        progress = elapsed / self.duration
        
        for particle in self.particles:
            # Update position
            particle['x'] += particle['vx'] * 0.016  # Assuming 60 FPS
            particle['y'] += particle['vy'] * 0.016
            particle['vy'] += 0.5  # Gravity
            
            # Reduce life
            particle['life'] = max(0, 1.0 - progress)
    
    def is_complete(self) -> bool:
        """Check if animation is complete."""
        if not self.active:
            return True
        return all(p['life'] <= 0 for p in self.particles)
    
    def stop(self):
        """Stop the animation."""
        self.active = False
        self.particles = []


class RetryIndicator:
    """
    Gentle retry indicator for incorrect answers.
    
    Features:
    - Pulse animation on input field
    - No harsh colors (uses orange, not red)
    - Encouraging visual feedback
    """
    
    def __init__(self):
        """Initialize the retry indicator."""
        self.active = False
        self.start_time = 0
        self.pulse_speed = 2.0  # Hz
    
    def start(self):
        """Start the retry indicator."""
        self.active = True
        self.start_time = time.time()
    
    def get_pulse_intensity(self, current_time: float) -> float:
        """
        Get the current pulse intensity (0.0 to 1.0).
        
        Args:
            current_time: Current time in seconds
            
        Returns:
            Pulse intensity for visual effects
        """
        if not self.active:
            return 0.0
        
        import math
        elapsed = current_time - self.start_time
        return 0.7 + 0.3 * math.sin(elapsed * self.pulse_speed * 3.14159 * 2)
    
    def stop(self):
        """Stop the retry indicator."""
        self.active = False


# Factory function
def create_feedback_controller(audio_system=None) -> FeedbackController:
    """
    Create a FeedbackController instance.
    
    Args:
        audio_system: Optional AudioSystem instance
        
    Returns:
        Configured FeedbackController instance
    """
    return FeedbackController(audio_system=audio_system)

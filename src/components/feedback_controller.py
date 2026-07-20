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
    
    # Performance mode
    enable_animations: bool = True  # Disable for performance mode
    enable_particles: bool = True   # Disable particle effects


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
        self._auto_advance_triggered: bool = False  # Track if auto-advance has fired
        
        # Rendering
        self.render_center_x: int = 400  # Default, should be set by screen
        self.render_center_y: int = 300
        
        # Celebration animation with render capability
        self.celebration = CelebrationAnimation(enable_particles=config.enable_particles if config else True)
        self.retry_indicator = RetryIndicator()
    
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
        self._auto_advance_triggered = False  # Reset trigger flag
        
        # Set auto-advance timer only if enabled
        if self.config.auto_advance_on_success:
            self.auto_advance_timer = self.feedback_start_time + self.config.success_display_duration
        
        # Play success audio
        if self.audio_system:
            self._play_success_sound()
        
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
            # Try to play actual chime first
            if self.audio_system and hasattr(self.audio_system, 'play_sfx'):
                if self.audio_system.play_sfx('success_chime', self.config.success_volume):
                    return  # Success, exit early
            
            # Fallback to TTS if SFX unavailable
            def on_complete():
                pass
            
            self.audio_system.speak(
                self.config.success_message,
                on_complete=on_complete
            )
        except Exception as e:
            print(f"Error playing success sound: {e}")
    
    def _play_retry_sound(self):
        """Play retry tone audio."""
        try:
            # Try to play actual tone first
            if self.audio_system and hasattr(self.audio_system, 'play_sfx'):
                if self.audio_system.play_sfx('retry_tone', self.config.retry_volume):
                    return  # Success, exit early
            
            # Fallback to TTS if SFX unavailable
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
            # Check for auto-advance BEFORE fade out
            if elapsed >= self.config.success_display_duration and not self._auto_advance_triggered:
                self._auto_advance_triggered = True
                if self.on_auto_advance:
                    self.on_auto_advance()
            
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
        
        # Note: Auto-advance is triggered separately in update()
        # This method only handles feedback completion
    
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
    
    def set_render_position(self, x: int, y: int):
        """Set the center position for rendering feedback."""
        self.render_center_x = x
        self.render_center_y = y
    
    def render(self, screen):
        """
        Render feedback on screen.
        
        Args:
            screen: Pygame surface to render to
        """
        if not self.config.enable_animations:
            return  # Skip rendering in performance mode
        
        if self.state == FeedbackState.SHOWING_SUCCESS:
            self.celebration.render(screen, self.render_center_x, self.render_center_y)
            
            # Render success message
            if self.animation_progress > 0:
                self._render_message(screen, self.get_feedback_message())
        
        elif self.state == FeedbackState.SHOWING_RETRY:
            # Render retry indicator pulse
            intensity = self.retry_indicator.get_pulse_intensity(
                time.time() - self.feedback_start_time
            )
            self._render_retry_indicator(screen, intensity)
    
    def _render_message(self, screen, message: str):
        """
        Render feedback message text with shape indicator.
        STORY-006-01: Uses both color AND shape for color-blind accessibility.
        """
        import pygame
        
        # Create font (should be configurable)
        font = pygame.font.Font(None, 72)  # 72pt
        
        # Calculate alpha based on animation progress
        alpha = int(255 * self.animation_progress)
        
        # Color-blind safe: Green for success (with checkmark shape)
        # Note: Green is OK here because we also use a visual shape indicator
        success_color = (76, 175, 80)  # Material green
        
        # Render text
        text_surf = font.render(message, True, success_color)
        
        # Apply transparency
        text_surf.set_alpha(alpha)
        
        # Center on screen
        text_rect = text_surf.get_rect(center=(self.render_center_x, self.render_center_y - 50))
        
        screen.blit(text_surf, text_rect)
        
        # STORY-006-01: Draw checkmark shape indicator (visible even without color)
        self._draw_checkmark(screen, self.render_center_x, self.render_center_y + 40, alpha)
    
    def _draw_checkmark(self, screen, x: int, y: int, alpha: int):
        """
        Draw a checkmark shape indicator for success feedback.
        STORY-006-01: Shape-based feedback for color-blind accessibility.
        
        Args:
            screen: Pygame surface
            x: Center X position
            y: Center Y position  
            alpha: Transparency value (0-255)
        """
        import pygame
        
        # Create a circular background
        size = 60
        circle_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        circle_color = (76, 175, 80, alpha)  # Green with alpha
        pygame.draw.circle(circle_surf, circle_color, (size // 2, size // 2), size // 2)
        
        # Draw checkmark shape
        check_width = 35
        points = [
            (size // 2 - check_width, size // 2 + check_width // 2),  # Start (left)
            (size // 2 - check_width // 3, size // 2 - check_width // 2),  # Bottom of V
            (size // 2 + check_width, size // 2 - check_width),  # End (right, up)
        ]
        
        check_color = (255, 255, 255, alpha)  # White checkmark
        pygame.draw.aalines(circle_surf, True, points, width=4)
        # Also draw solid line for visibility
        pygame.draw.lines(circle_surf, check_color, False, points, width=4)
        
        screen.blit(circle_surf, (x - size // 2, y - size // 2))
    
    def _render_retry_indicator(self, screen, intensity: float):
        """
        Render retry indicator with pulse intensity.
        STORY-006-01: Uses both color AND shape for color-blind accessibility.
        
        Args:
            screen: Pygame surface
            intensity: Pulse intensity (0.0 to 1.0)
        """
        import pygame
        
        # Color-blind safe: Blue for retry/incorrect (NOT red)
        retry_color = (33, 150, 243)  # Material blue (not red!)
        
        # Draw pulsing X shape indicator
        pulse_size = 50 + int(10 * intensity)
        
        # Create square background
        square_surf = pygame.Surface((pulse_size, pulse_size), pygame.SRCALPHA)
        square_color = (*retry_color, int(180 * intensity))  # Blue with alpha
        pygame.draw.rect(square_surf, square_color, (0, 0, pulse_size, pulse_size), border_radius=8)
        
        # Draw X shape (visible without color)
        x_color = (255, 255, 255, int(200 * intensity))  # White X
        margin = pulse_size // 5
        points = [
            (margin, margin),           # Top-left
            (pulse_size - margin, pulse_size - margin),  # Bottom-right
            (pulse_size - margin, margin),  # Top-right
            (margin, pulse_size - margin),  # Bottom-left
        ]
        pygame.draw.aalines(square_surf, True, points, width=3)
        pygame.draw.lines(square_surf, x_color, False, points, width=3)
        
        # Center of screen
        center_x = self.render_center_x + 100  # Offset for retry indicator
        center_y = self.render_center_y + 50
        
        screen.blit(square_surf, (center_x - pulse_size // 2, center_y - pulse_size // 2))
    
    def reset(self):
        """Reset the feedback controller to idle state."""
        self.state = FeedbackState.IDLE
        self.current_feedback = FeedbackType.NONE
        self.feedback_start_time = 0
        self.auto_advance_timer = None
        self.animation_active = False
        self.animation_progress = 0.0
        self._auto_advance_triggered = False


# Celebration animation constants - color-blind safe palette
CELEBRATION_PARTICLE_COUNT = 20
CELEBRATION_PARTICLE_COLORS = [
    (255, 215, 0),   # Gold
    (255, 255, 255), # White
    (76, 175, 80),   # Green (success color)
    (255, 152, 0),   # Orange
    (33, 150, 243),  # Blue (retry color - also used in celebration for variety)
]


class CelebrationAnimation:
    """
    Manages celebration animation effects for correct answers.
    
    Features:
    - Particle burst effects
    - Planet sparkle animations
    - Text animation
    """
    
    def __init__(self, enable_particles: bool = True):
        """Initialize the celebration animation.
        
        Args:
            enable_particles: Whether to show particle effects (for performance mode)
        """
        self.active = False
        self.particles: list = []
        self.start_time = 0
        self.duration = 1.0
        self.enable_particles = enable_particles
    
    def start(self):
        """Start the celebration animation."""
        self.active = True
        self.start_time = time.time()
        self._create_particles()
    
    def _create_particles(self):
        """Create particle effects for celebration."""
        if not self.enable_particles:
            return  # Skip particle creation in performance mode
        
        # Simple particle system
        for i in range(CELEBRATION_PARTICLE_COUNT):
            self.particles.append({
                'x': 0,  # Will be set by renderer
                'y': 0,
                'vx': (i - 10) * 2,  # Spread horizontally
                'vy': -10 - (i % 10),  # Upward velocity
                'life': 1.0,
                'color': CELEBRATION_PARTICLE_COLORS[i % len(CELEBRATION_PARTICLE_COLORS)]
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
    
    def render(self, screen, center_x: int, center_y: int):
        """
        Render the celebration animation on screen.
        
        Args:
            screen: Pygame surface to render to
            center_x: X position of animation center
            center_y: Y position of animation center
        """
        if not self.active or not self.enable_particles:
            return
        
        import pygame
        
        for particle in self.particles:
            if particle['life'] > 0:
                # Calculate position relative to center
                x = center_x + particle['x']
                y = center_y + particle['y']
                
                # Calculate alpha based on life
                alpha = int(255 * particle['life'])
                
                # Create particle surface with transparency
                particle_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                color = (*particle['color'], alpha)
                pygame.draw.circle(particle_surf, color, (4, 4), 4)
                
                # Blit to screen
                screen.blit(particle_surf, (x - 4, y - 4))


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

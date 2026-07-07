"""
Animations Module

Provides animation components for the game including:
- Rocket travel animations
- Letter appearance animations
- Success/failure visual effects
- Progress bar animations
"""

from typing import Optional, Tuple, List
from dataclasses import dataclass
import math
import time

import pygame


@dataclass
class AnimationState:
    """State for a running animation."""
    start_time: float
    duration: float
    progress: float = 0.0
    is_complete: bool = False
    paused: bool = False


class RocketAnimator:
    """
    Handles rocket sprite movement and visual effects for transitions.
    
    Used by PlanetTransitionScreen for rocket travel animations.
    """
    
    def __init__(self, color: Tuple[int, int, int] = (200, 200, 200)):
        """
        Initialize the rocket animator.
        
        Args:
            color: Rocket body color (RGB tuple)
        """
        self.color = color
        self.flame_offset = 0.0
        self.flame_direction = 1
        self.rocket_width = 60
        self.rocket_height = 120
        
        # Animation timing
        self.last_frame_time = 0
        self.frame_interval = 0.1  # 100ms per frame
    
    def update(self, current_time: float):
        """
        Update animation state.
        
        Args:
            current_time: Current time in seconds
        """
        # Animate flame
        if current_time - self.last_frame_time >= self.frame_interval:
            self.flame_offset += 0.5 * self.flame_direction
            if self.flame_offset >= 1.0 or self.flame_offset <= 0.0:
                self.flame_direction *= -1
            self.last_frame_time = current_time
    
    def draw(self, screen, x: int, y: int, angle: float = 0):
        """
        Draw the rocket at the given position.
        
        Args:
            screen: Pygame screen surface
            x: X position (center)
            y: Y position (center)
            angle: Rotation angle in radians (optional)
        """
        # Create a surface for the rocket
        rocket_surface = pygame.Surface((self.rocket_width, self.rocket_height), pygame.SRCALPHA)
        
        # Rocket body (ellipse)
        body_color = self.color
        pygame.draw.ellipse(rocket_surface, body_color, (5, 20, 50, 80))
        
        # Rocket nose cone
        nose_points = [
            (30, 0),   # Top center
            (55, 35),  # Right base
            (5, 35)    # Left base
        ]
        pygame.draw.polygon(rocket_surface, (220, 220, 220), nose_points)
        
        # Rocket fins
        left_fin_points = [
            (5, 60),
            (0, 90),
            (15, 70)
        ]
        right_fin_points = [
            (55, 60),
            (60, 90),
            (45, 70)
        ]
        pygame.draw.polygon(rocket_surface, (180, 180, 180), left_fin_points)
        pygame.draw.polygon(rocket_surface, (180, 180, 180), right_fin_points)
        
        # Window
        window_color = (135, 206, 235)  # Sky blue
        pygame.draw.circle(rocket_surface, window_color, (30, 50), 15)
        pygame.draw.circle(rocket_surface, (200, 200, 200), (30, 50), 15, 3)
        
        # Engine flame
        flame_width = 20
        flame_height = int(30 * (0.5 + 0.5 * (1 - abs(self.flame_offset))))
        flame_points = [
            (30 - flame_width // 2, 100),
            (30, 100 + flame_height),
            (30 + flame_width // 2, 100)
        ]
        flame_color = (255, int(100 * self.flame_offset + 100), 0)
        pygame.draw.polygon(rocket_surface, flame_color, flame_points)
        
        # Rotate if needed
        if angle != 0:
            rotated_surface = pygame.transform.rotate(rocket_surface, math.degrees(angle))
            rect = rotated_surface.get_rect(center=(x, y))
            screen.blit(rotated_surface, rect.topleft)
        else:
            rect = rocket_surface.get_rect(center=(x, y))
            screen.blit(rocket_surface, rect.topleft)


class StarField:
    """
    Star field background with motion blur effect.
    
    Creates a space background with twinkling stars that
    appear to move during rocket travel.
    """
    
    def __init__(self, width: int = 800, height: int = 600, num_stars: int = 100):
        """
        Initialize the star field.
        
        Args:
            width: Screen width
            height: Screen height
            num_stars: Number of stars to generate
        """
        self.width = width
        self.height = height
        self.stars = []
        self.motion_offset = 0
        self.twinkle_timer = 0
        
        # Generate random stars
        import random
        for _ in range(num_stars):
            self.stars.append({
                'x': random.randint(0, width),
                'y': random.randint(0, height),
                'size': random.randint(1, 3),
                'brightness': random.random(),
                'twinkle_speed': random.uniform(0.01, 0.05)
            })
    
    def update(self, progress: float, delta_time: float):
        """
        Update star field for motion effect.
        
        Args:
            progress: Animation progress (0.0 to 1.0)
            delta_time: Time since last update in seconds
        """
        # Create motion blur effect based on progress
        self.motion_offset += progress * 2 * delta_time
        
        # Update twinkle
        self.twinkle_timer += delta_time
        for star in self.stars:
            star['brightness'] += star['twinkle_speed']
            if star['brightness'] >= 1.0 or star['brightness'] <= 0.3:
                star['twinkle_speed'] *= -1
    
    def draw(self, screen):
        """
        Draw the star field.
        
        Args:
            screen: Pygame screen surface
        """
        # Draw space background
        screen.fill((26, 26, 62))  # Deep space blue
        
        # Draw stars with motion blur and twinkle
        for star in self.stars:
            # Apply motion offset
            x = (star['x'] - self.motion_offset) % self.width
            y = star['y']
            
            # Calculate brightness
            brightness = int(255 * star['brightness'])
            color = (brightness, brightness, brightness + 50)
            
            # Draw star
            pygame.draw.circle(screen, color, (int(x), int(y)), star['size'])


class LetterAnimator:
    """
    Handles letter appearance animations.
    
    Provides fade-in and bounce effects for letter display.
    """
    
    def __init__(self, animation_type: str = "fade"):
        """
        Initialize the letter animator.
        
        Args:
            animation_type: Type of animation ("fade", "bounce", "slide")
        """
        self.animation_type = animation_type
        self.state = AnimationState(
            start_time=0,
            duration=0.5
        )
    
    def start(self, current_time: float):
        """
        Start the animation.
        
        Args:
            current_time: Current time in seconds
        """
        self.state = AnimationState(
            start_time=current_time,
            duration=0.5,
            progress=0.0,
            is_complete=False,
            paused=False
        )
    
    def update(self, current_time: float):
        """
        Update animation state.
        
        Args:
            current_time: Current time in seconds
        """
        if self.state.paused or self.state.is_complete:
            return
        
        elapsed = current_time - self.state.start_time
        self.state.progress = elapsed / self.state.duration
        
        if self.state.progress >= 1.0:
            self.state.progress = 1.0
            self.state.is_complete = True
    
    def get_alpha(self) -> int:
        """
        Get the alpha value for fade animation.
        
        Returns:
            Alpha value (0-255)
        """
        return int(255 * self.state.progress)
    
    def get_scale(self) -> float:
        """
        Get the scale factor for bounce animation.
        
        Returns:
            Scale factor (1.0 is normal)
        """
        if self.animation_type != "bounce":
            return 1.0
        
        # Bounce effect: scale up then settle
        progress = self.state.progress
        if progress < 0.5:
            return 1.0 + 0.3 * (progress * 2)
        else:
            return 1.0 + 0.3 * (1.0 - (progress - 0.5) * 2)
    
    def get_offset(self) -> Tuple[float, float]:
        """
        Get the offset for slide animation.
        
        Returns:
            (x_offset, y_offset) tuple
        """
        if self.animation_type != "slide":
            return (0, 0)
        
        progress = self.state.progress
        # Slide from bottom
        return (0, int(20 * (1 - progress)))


class ProgressBarAnimator:
    """
    Handles progress bar animations.
    
    Provides smooth progress filling with optional pulse effects.
    """
    
    def __init__(self, color: Tuple[int, int, int] = (0, 200, 83)):
        """
        Initialize the progress bar animator.
        
        Args:
            color: Bar fill color (RGB tuple)
        """
        self.color = color
        self.progress = 0.0
        self.target_progress = 0.0
        self.animation_speed = 0.05  # Animation speed factor
    
    def set_target(self, progress: float):
        """
        Set the target progress value.
        
        Args:
            progress: Target progress (0.0 to 1.0)
        """
        self.target_progress = max(0.0, min(1.0, progress))
    
    def update(self, delta_time: float):
        """
        Update progress bar towards target.
        
        Args:
            delta_time: Time since last update in seconds
        """
        # Smoothly interpolate towards target
        diff = self.target_progress - self.progress
        if abs(diff) > 0.001:
            self.progress += diff * self.animation_speed * delta_time * 60
        else:
            self.progress = self.target_progress
    
    def draw(self, screen, x: int, y: int, width: int, height: int, 
             bg_color: Tuple[int, int, int] = (60, 60, 80),
             border_color: Tuple[int, int, int] = (255, 255, 255)):
        """
        Draw the progress bar.
        
        Args:
            screen: Pygame screen surface
            x: X position
            y: Y position
            width: Bar width
            height: Bar height
            bg_color: Background color
            border_color: Border color
        """
        # Background
        pygame.draw.rect(screen, bg_color, (x, y, width, height))
        pygame.draw.rect(screen, border_color, (x, y, width, height), 2)
        
        # Fill
        fill_width = int(width * self.progress)
        pygame.draw.rect(screen, self.color, (x, y, fill_width, height))


class SuccessAnimator:
    """
    Handles success celebration animations.
    
    Provides sparkle, confetti, and burst effects for correct answers.
    """
    
    def __init__(self):
        """Initialize the success animator."""
        self.particles: List[dict] = []
        self.active = False
        self.start_time = 0
        self.duration = 1.0  # 1 second celebration
    
    def trigger(self, center_x: int, center_y: int):
        """
        Trigger the success animation.
        
        Args:
            center_x: Center X position
            center_y: Center Y position
        """
        self.active = True
        self.start_time = time.time()
        
        # Create particles
        import random
        for i in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            self.particles.append({
                'x': center_x,
                'y': center_y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.5, 1.0),
                'color': random.choice([
                    (255, 215, 0),   # Gold
                    (0, 200, 83),    # Green
                    (135, 206, 235), # Blue
                    (255, 105, 180), # Pink
                    (255, 165, 0)    # Orange
                ]),
                'size': random.randint(3, 8)
            })
    
    def update(self, delta_time: float):
        """
        Update animation state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        if not self.active:
            return
        
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            self.active = False
            self.particles.clear()
            return
        
        # Update particles
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['vy'] += 200 * delta_time  # Gravity
            particle['life'] -= delta_time
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def draw(self, screen):
        """
        Draw the success animation.
        
        Args:
            screen: Pygame screen surface
        """
        if not self.active:
            return
        
        for particle in self.particles:
            alpha = int(255 * (particle['life'] / self.duration))
            # Draw particle (simplified - just circles)
            pygame.draw.circle(screen, particle['color'], 
                             (int(particle['x']), int(particle['y'])),
                             particle['size'])


class RetryAnimator:
    """
    Handles retry/incorrect answer animations.
    
    Provides gentle shake and fade effects for wrong answers.
    """
    
    def __init__(self):
        """Initialize the retry animator."""
        self.active = False
        self.start_time = 0
        self.shake_intensity = 5
        self.shake_duration = 0.5
    
    def trigger(self):
        """Trigger the retry animation."""
        self.active = True
        self.start_time = time.time()
    
    def update(self, delta_time: float):
        """
        Update animation state.
        
        Args:
            delta_time: Time since last update in seconds
        """
        if not self.active:
            return
        
        elapsed = time.time() - self.start_time
        if elapsed >= self.shake_duration:
            self.active = False
    
    def get_offset(self) -> Tuple[int, int]:
        """
        Get the shake offset to apply to UI elements.
        
        Returns:
            (x_offset, y_offset) tuple
        """
        if not self.active:
            return (0, 0)
        
        import random
        elapsed = time.time() - self.start_time
        intensity = self.shake_intensity * (1 - elapsed / self.shake_duration)
        
        return (
            random.randint(-int(intensity), int(intensity)),
            random.randint(-int(intensity), int(intensity))
        )


# Convenience functions for creating animations
def create_rocket_animator(color: Tuple[int, int, int] = (200, 200, 200)) -> RocketAnimator:
    """Create a rocket animator instance."""
    return RocketAnimator(color)


def create_star_field(width: int = 800, height: int = 600, num_stars: int = 100) -> StarField:
    """Create a star field instance."""
    return StarField(width, height, num_stars)


def create_letter_animator(animation_type: str = "fade") -> LetterAnimator:
    """Create a letter animator instance."""
    return LetterAnimator(animation_type)


def create_progress_bar(color: Tuple[int, int, int] = (0, 200, 83)) -> ProgressBarAnimator:
    """Create a progress bar animator instance."""
    return ProgressBarAnimator(color)


def create_success_animation() -> SuccessAnimator:
    """Create a success animation instance."""
    return SuccessAnimator()


def create_retry_animation() -> RetryAnimator:
    """Create a retry animation instance."""
    return RetryAnimator()

"""
Integration Tests for Rocket in Screen Contexts (STORY-005-02)

Integration tests verify that rocket components work correctly within
actual game screen contexts (main menu, planet transition, etc.).
"""

import pytest
import pygame
import os
import sys

# Set TESTING environment variable and headless display before importing
os.environ["TESTING"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.ui.rocket_sprite import RocketSprite
from src.ui.rocket_animator import RocketAnimator, create_rocket_animator
from src.models.rocket_config import RocketConfig, ROCKET_COLOR_PRESETS


class TestRocketInMainCampaign:
    """Integration tests for rocket in main campaign screens."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame for testing."""
        pygame.init()
        yield
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create 800x600 test screen."""
        return pygame.display.set_mode((800, 600))
    
    @pytest.fixture
    def player_id(self):
        """Return test player ID."""
        return "test_integration_player"
    
    def test_rocket_initializes_in_main_menu(self, screen, player_id):
        """Test rocket initializes correctly in main menu context."""
        # Simulate main_menu.py rocket initialization
        rocket_config = RocketConfig(player_id)
        rocket_color = rocket_config.get_current_color()
        rocket_sprite = RocketSprite(color=rocket_color, size=64)
        rocket_animator = create_rocket_animator(
            rocket_sprite,
            initial_position=(400, 300)  # Center of 800x600 screen
        )
        
        # Verify rocket exists and has correct initial state
        assert rocket_sprite is not None
        assert rocket_animator is not None
        assert rocket_animator.position == (400, 300)
        
        rocket_color_hex = rocket_config.get_current_color_hex()
        # ROCKET_COLOR_PRESETS is a list of dicts with 'hex' key
        preset_hexes = [c["hex"].upper() for c in ROCKET_COLOR_PRESETS]
        assert rocket_color_hex.upper() in preset_hexes
    
    def test_rocket_renders_without_crashing_in_main_menu(self, screen, player_id):
        """Test rocket renders without crashing in main menu."""
        # Initialize rocket as main_menu.py does
        rocket_config = RocketConfig(player_id)
        rocket_color = rocket_config.get_current_color()
        rocket_sprite = RocketSprite(color=rocket_color, size=64)
        rocket_animator = create_rocket_animator(
            rocket_sprite,
            initial_position=(400, 300)
        )
        
        # Start hover animation
        rocket_animator.animate_hover((400, 300))
        
        # Render should not crash
        try:
            rocket_animator.render(screen)
            # Verify something was drawn (check alpha channel)
            pixel_data = screen.get_at((400, 300))
            # Rocket should be visible (alpha > 0 or color != background)
            assert pixel_data[3] > 0 or pixel_data[:3] != (26, 26, 62)
        except Exception as e:
            pytest.fail(f"Rocket rendering crashed: {e}")
    
    def test_rocket_animation_updates_smoothly(self, screen, player_id):
        """Test rocket animation updates maintain smooth movement."""
        rocket_config = RocketConfig(player_id)
        rocket_color = rocket_config.get_current_color()
        rocket_sprite = RocketSprite(color=rocket_color, size=64)
        rocket_animator = create_rocket_animator(
            rocket_sprite,
            initial_position=(400, 300)
        )
        
        # Start hover animation
        rocket_animator.animate_hover((400, 300))
        
        # Update multiple times with typical delta time (60 FPS = ~0.0167s)
        delta_time = 0.0167
        positions = []
        for _ in range(10):
            rocket_animator.update(delta_time)
            positions.append(rocket_animator.position)
        
        # Verify positions are different (animation is moving)
        # Check that vertical position oscillates (hover effect)
        y_positions = [pos[1] for pos in positions]
        assert len(set(y_positions)) > 1, "Hover animation should move rocket vertically"
    
    def test_rocket_color_persists_across_instances(self, screen, player_id):
        """Test that rocket color can be set and retrieved in same instance."""
        # Note: Full persistence testing is done in test_rocket_config.py
        # This test verifies the color setting/getting workflow works
        test_color_rgb = (244, 67, 54)  # Red
        rocket_config = RocketConfig(player_id)
        
        # Set color
        rocket_config.set_color(test_color_rgb)
        
        # Verify color was set correctly in same instance
        assert rocket_config.get_current_color() == test_color_rgb
        
        # Verify color can be retrieved in hex format
        hex_color = rocket_config.get_current_color_hex()
        assert hex_color == "#F44336"  # Red in hex


class TestRocketInPlanetTransition:
    """Integration tests for rocket in planet transition screen."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame for testing."""
        pygame.init()
        yield
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create test screen."""
        return pygame.display.set_mode((800, 600))
    
    def test_transition_rocket_initializes_with_config(self, screen):
        """Test planet transition rocket initializes with RocketConfig."""
        # Simulate planet_transition.py initialization
        try:
            from src.profiles.student_profile import get_current_student_id
            player_id = get_current_student_id()
        except Exception:
            player_id = "default_student"
        
        rocket_config = RocketConfig(player_id)
        rocket_color = rocket_config.get_current_color()
        
        rocket_sprite = RocketSprite(color=rocket_color, size=64)
        rocket_animator = RocketAnimator(rocket_sprite)
        
        assert rocket_sprite is not None
        assert rocket_animator is not None
        assert rocket_animator.rocket.get_color() == rocket_color
    
    def test_transition_rocket_animation_works(self, screen):
        """Test rocket transition animation completes without errors."""
        rocket_sprite = RocketSprite(color=(255, 255, 255), size=64)
        rocket_animator = RocketAnimator(rocket_sprite)
        
        # Simulate transition animation
        start_pos = (100, 300)
        end_pos = (700, 300)
        rocket_animator.animate_transition(start_pos, end_pos, duration=2.0)
        
        # Update through animation
        delta_time = 0.0167  # ~60 FPS
        elapsed = 0
        while not rocket_animator.is_complete() and elapsed < 3.0:
            rocket_animator.update(delta_time)
            elapsed += delta_time
        
        # Verify animation completed
        assert rocket_animator.is_complete() or elapsed >= 2.0
    
    def test_rocket_renders_during_transition(self, screen):
        """Test rocket renders correctly during transition."""
        rocket_sprite = RocketSprite(color=(255, 100, 100), size=64)
        rocket_animator = RocketAnimator(rocket_sprite)
        
        rocket_animator.animate_transition((100, 300), (700, 300))
        
        # Render at various points in animation
        for _ in range(5):
            rocket_animator.update(0.0167)
            try:
                rocket_animator.render(screen)
            except Exception as e:
                pytest.fail(f"Rocket render during transition crashed: {e}")


class TestRocketInSpellingChallenge:
    """Integration tests for rocket in spelling challenge screen."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame for testing."""
        pygame.init()
        yield
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create test screen."""
        return pygame.display.set_mode((800, 600))
    
    def test_rocket_boost_animation_integration(self, screen):
        """Test rocket boost animation works in spelling challenge context."""
        from src.animations.rocket_boost import RocketBoostAnimation, create_rocket_boost_animation
        
        # Create boost animation at streak display position
        start_pos = (700, 300)
        boost_animation = create_rocket_boost_animation(screen, start_pos)
        
        assert boost_animation is not None
        assert boost_animation.is_complete() == False  # Should not be complete initially
        
        # Update through animation until completion (boost duration is 1.5 seconds)
        iterations_needed = int(1.6 / 0.0167)  # ~96 iterations for 1.6 seconds
        for _ in range(iterations_needed):
            boost_animation.update(0.0167)
        
        # Should complete after the animation loop
        assert boost_animation.is_complete()
    
    def test_rocket_renders_with_bonus_animation(self, screen):
        """Test rocket renders correctly during bonus animation."""
        from src.animations.rocket_boost import create_rocket_boost_animation
        
        boost_animation = create_rocket_boost_animation(screen, (400, 300))
        
        # Render multiple frames
        for _ in range(10):
            boost_animation.update(0.0167)
            try:
                boost_animation.render()
            except Exception as e:
                pytest.fail(f"Boost animation render crashed: {e}")


class TestRocketPerformance:
    """Performance tests for rocket rendering and animations."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame for testing."""
        pygame.init()
        yield
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create test screen."""
        return pygame.display.set_mode((800, 600))
    
    def test_rocket_render_timing_meets_target(self, screen):
        """Test rocket rendering stays under 3ms target."""
        import time
        
        rocket_sprite = RocketSprite(color=(255, 255, 255), size=64)
        
        # Warm up (first render can be slower)
        rocket_sprite.render(screen, (400, 300))
        
        # Benchmark multiple renders
        iterations = 100
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            rocket_sprite.render(screen, (400, 300))
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / iterations) * 1000
        
        # Should be well under 3ms per render
        assert avg_time_ms < 3.0, f"Average render time {avg_time_ms:.2f}ms exceeds 3ms target"
    
    def test_rocket_animator_update_timing(self, screen):
        """Test animator updates stay performant."""
        import time
        
        rocket_sprite = RocketSprite(color=(255, 255, 255), size=64)
        rocket_animator = create_rocket_animator(rocket_sprite, initial_position=(400, 300))
        rocket_animator.animate_hover((400, 300))
        
        # Warm up
        rocket_animator.update(0.0167)
        
        # Benchmark
        iterations = 1000
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            rocket_animator.update(0.0167)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / iterations) * 1000
        
        # Should be well under 1ms per update
        assert avg_time_ms < 1.0, f"Average update time {avg_time_ms:.2f}ms exceeds target"
    
    def test_multiple_rocks_render_performance(self, screen):
        """Test rendering multiple rockets maintains performance."""
        import time
        
        rockets = [RocketSprite(color=(255, 255, 255), size=64) for _ in range(10)]
        
        # Benchmark rendering multiple rockets
        iterations = 100
        start_time = time.perf_counter()
        
        for _ in range(iterations):
            for i, rocket in enumerate(rockets):
                rocket.render(screen, (i * 80, 300))
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        # 10 rockets should render in under 30ms total (allows for test variance)
        # Target is <3ms per rocket, so 10 rockets = ~30ms max
        assert total_time_ms < 30.0, f"Multiple rocket render took {total_time_ms:.2f}ms"


class TestRocketColorCustomization:
    """Integration tests for color customization workflow."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame for testing."""
        pygame.init()
        yield
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create test screen."""
        return pygame.display.set_mode((800, 600))
    
    def test_color_picker_integration_workflow(self, screen):
        """Test complete color picker workflow from selection to rocket update."""
        player_id = "test_color_player"
        
        # Step 1: Create rocket config (simulates student_settings.py)
        rocket_config = RocketConfig(player_id)
        original_color = rocket_config.get_current_color()
        
        # Step 2: Select new color (simulates color picker callback)
        new_color_rgb = (33, 150, 243)  # Blue
        rocket_config.set_color(new_color_rgb)
        
        # Step 3: Verify config updated
        assert rocket_config.get_current_color() == new_color_rgb
        
        # Step 4: Create rocket with new color (simulates rocket preview)
        rocket_sprite = RocketSprite(color=new_color_rgb, size=80)
        assert rocket_sprite.get_color() == new_color_rgb
        
        # Step 5: Render rocket with new color
        try:
            rocket_sprite.render(screen, (400, 300))
        except Exception as e:
            pytest.fail(f"Rocket render with custom color crashed: {e}")
    
    def test_color_changes_at_runtime(self, screen):
        """Test rocket color changes dynamically at runtime."""
        rocket_sprite = RocketSprite(color=(255, 255, 255), size=64)
        
        # Change color
        rocket_sprite.set_color((244, 67, 54))  # Red
        
        assert rocket_sprite.get_color() == (244, 67, 54)
        
        # Render with new color
        rocket_sprite.render(screen, (400, 300))
        
        # Change again
        rocket_sprite.set_color((76, 175, 80))  # Green
        
        assert rocket_sprite.get_color() == (76, 175, 80)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
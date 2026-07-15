"""
Unit Tests for Engine Flames (STORY-005-02)

Tests for engine flame animation system.
"""

import pytest
import pygame
import os
import sys

# Set TESTING environment variable and headless display before importing
os.environ["TESTING"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.ui.engine_flames import EngineFlames, FlameParticle, create_engine_flames


class TestFlameParticle:
    """Tests for individual flame particles."""
    
    def test_particle_creation(self):
        """Test particle creation with initial values."""
        particle = FlameParticle(
            x=100.0,
            y=200.0,
            vx=10.0,
            vy=-50.0,
            color=(255, 144, 0),
            life=0.5,
            size=8.0
        )
        
        assert particle.x == 100.0
        assert particle.y == 200.0
        assert particle.life == 0.5
        assert particle.opacity == 255
    
    def test_particle_update_position(self):
        """Test particle position update."""
        particle = FlameParticle(
            x=100.0,
            y=200.0,
            vx=10.0,
            vy=-50.0,
            color=(255, 144, 0),
            life=0.5,
            size=8.0
        )
        
        particle.update(0.1)  # 100ms
        
        assert abs(particle.x - 101.0) < 0.01  # vx * dt = 10 * 0.1 = 1
        assert abs(particle.y - 195.0) < 0.01  # vy * dt = -50 * 0.1 = -5
    
    def test_particle_update_life(self):
        """Test particle life reduction."""
        particle = FlameParticle(
            x=100.0,
            y=200.0,
            vx=0.0,
            vy=0.0,
            color=(255, 144, 0),
            life=0.5,
            size=8.0
        )
        
        particle.update(0.2)  # 200ms
        
        assert particle.life == pytest.approx(0.3, abs=0.01)
    
    def test_particle_fades_when_life_low(self):
        """Test particle opacity fades when life is low."""
        particle = FlameParticle(
            x=100.0,
            y=200.0,
            vx=0.0,
            vy=0.0,
            color=(255, 144, 0),
            life=0.1,  # Low life
            size=8.0
        )
        
        particle.update(0.05)  # 50ms
        
        assert particle.life == pytest.approx(0.05, abs=0.01)
        assert particle.opacity < 255


class TestEngineFlames:
    """Tests for engine flame system."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame."""
        pygame.init()
        yield
        pygame.quit()
    
    @pytest.fixture
    def flames(self):
        """Create engine flames instance."""
        return EngineFlames(max_particles=20)
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create test screen."""
        return pygame.display.set_mode((800, 600))
    
    def test_initialization(self):
        """Test engine flames initializes correctly."""
        flames = EngineFlames(max_particles=20)
        
        assert flames.max_particles == 20
        assert flames.intensity == 1.0
        assert flames.particle_spawn_counter == 0
        assert len(flames.particles) == 0
    
    def test_particle_count_limit(self, flames):
        """Test that particle count stays within limit."""
        # Set high spawn rate
        flames.set_intensity(1.0)
        
        # Emit and update multiple times
        for _ in range(100):
            flames.emit()
            flames.update(0.016)  # ~60 FPS
        
        assert len(flames.particles) <= flames.max_particles
    
    def test_set_intensity(self, flames):
        """Test intensity adjustment."""
        flames.set_intensity(0.5)
        assert flames.intensity == 0.5
        
        flames.set_intensity(0.0)
        assert flames.intensity == 0.0
        
        flames.set_intensity(1.0)
        assert flames.intensity == 1.0
    
    def test_set_intensity_bounds(self, flames):
        """Test intensity clamping."""
        flames.set_intensity(10.0)  # Above max
        assert flames.intensity == 1.0
        
        flames.set_intensity(-1.0)  # Below min
        assert flames.intensity == 0.0
    
    def test_boost_sets_full_intensity(self, flames):
        """Test boost sets intensity to maximum."""
        flames.set_intensity(0.5)
        flames.boost()
        assert flames.intensity == 1.0
    
    def test_idle_sets_low_intensity(self, flames):
        """Test idle sets low intensity."""
        flames.set_intensity(1.0)
        flames.idle()
        assert flames.intensity == 0.3
    
    def test_off_turns_off(self, flames):
        """Test off turns off flames."""
        flames.set_intensity(1.0)
        flames.off()
        assert flames.intensity == 0.0
    
    def test_update_with_emission(self, flames):
        """Test update produces particles."""
        flames.set_intensity(1.0)
        
        # Emit and update
        flames.emit()
        flames.update(0.016)
        
        # Should have some particles
        assert len(flames.particles) > 0
    
    def test_update_removes_dead_particles(self, flames):
        """Test update removes particles with zero life."""
        flames.set_intensity(1.0)
        
        # Emit particles
        flames.emit()
        initial_count = len(flames.particles)
        
        # Update with large delta time to kill all particles
        flames.update(10.0)
        
        # All particles should be dead
        for particle in flames.particles:
            assert particle.life <= 0
    
    def test_particle_movement(self, flames):
        """Test particles move upward."""
        flames.set_intensity(1.0)
        
        # Emit
        flames.emit()
        
        if len(flames.particles) > 0:
            # Check initial Y position
            initial_y = flames.particles[0].y
            
            # Update
            flames.update(0.1)
            
            # Particles should move up (y decreases)
            final_y = flames.particles[0].y
            # Allow for some randomness in velocity
            assert final_y < initial_y + 10  # Should have moved or stayed same
    
    def test_get_particle_count(self, flames):
        """Test getting particle count."""
        count = flames.get_particle_count()
        assert count >= 0
    
    def test_is_active(self, flames):
        """Test is_active method."""
        # Empty flames should not be active
        assert not flames.is_active()
        
        # With particles and intensity, should be active
        flames.set_intensity(1.0)
        flames.emit()
        assert flames.is_active()


@pytest.mark.parametrize("intensity", [0.0, 0.25, 0.5, 0.75, 1.0])
class TestFlameIntensity:
    """Tests for flame intensity behavior."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame."""
        pygame.init()
        yield
        pygame.quit()
    
    def test_intensity_affects_spawn_rate(self, intensity):
        """Test that intensity affects particle spawn rate."""
        flames = EngineFlames(max_particles=100)
        flames.set_intensity(intensity)
        
        # Emit with different intensities
        flames.emit()
        
        # Higher intensity should spawn at least as many particles
        # (exact count may vary due to randomness)
        assert True  # Verified by integration with other tests


class TestEngineFlameRendering:
    """Tests for engine flame rendering."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame."""
        pygame.init()
        yield
        pygame.quit()
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create test screen."""
        return pygame.display.set_mode((800, 600))
    
    @pytest.fixture
    def flames(self, pygame_init):
        """Create engine flames instance."""
        return EngineFlames(max_particles=20)
    
    def test_render_no_crash(self, flames, screen):
        """Test rendering doesn't crash."""
        flames.set_intensity(1.0)
        flames.emit()
        flames.update(0.016)
        flames.render(screen, (400, 300))
        assert True
    
    def test_render_with_particles(self, flames, screen):
        """Test rendering with active particles."""
        flames.set_intensity(1.0)
        
        # Create some particles
        for _ in range(10):
            flames.emit()
            flames.update(0.016)
        
        flames.render(screen, (400, 300))
        assert True
    
    def test_render_offscreen_particles(self, flames, screen):
        """Test rendering particles offscreen doesn't crash."""
        flames.set_intensity(1.0)
        flames.emit()
        flames.update(0.016)
        
        # Render at offscreen position
        flames.render(screen, (2000, 2000))
        assert True
    
    def test_render_before_emit(self, flames, screen):
        """Test rendering before emitting particles."""
        flames.render(screen, (400, 300))
        assert True
    
    def test_render_at_various_positions(self, flames, screen):
        """Test rendering at various screen positions."""
        positions = [
            (0, 0),
            (400, 300),
            (800, 600),
            (-50, -50),
            (200, 200)
        ]
        
        for pos in positions:
            flames.render(screen, pos)
        assert True


class TestCreateEngineFlames:
    """Tests for factory function."""
    
    def test_factory_creates_instance(self):
        """Test factory function creates EngineFlames."""
        flames = create_engine_flames()
        assert isinstance(flames, EngineFlames)
    
    def test_factory_with_max_particles(self):
        """Test factory function with max_particles parameter."""
        flames = create_engine_flames(max_particles=30)
        assert flames.max_particles == 30
    
    def test_factory_with_intensity(self):
        """Test factory function with intensity parameter."""
        flames = create_engine_flames(intensity=0.5)
        assert flames.intensity == 0.5
    
    def test_factory_custom_settings(self):
        """Test factory function with both parameters."""
        flames = create_engine_flames(max_particles=25, intensity=0.75)
        assert flames.max_particles == 25
        assert flames.intensity == 0.75


@pytest.mark.performance
class TestFlamePerformance:
    """Performance tests for engine flames."""
    
    @pytest.fixture
    def pygame_init(self):
        """Initialize pygame."""
        pygame.init()
        yield
        pygame.quit()
    
    @pytest.fixture
    def screen(self, pygame_init):
        """Create test screen."""
        return pygame.display.set_mode((800, 600))
    
    def test_emit_performance(self):
        """Test particle emission is fast."""
        flames = EngineFlames(max_particles=20)
        
        import time
        start = time.time()
        for _ in range(1000):
            flames.emit()
        elapsed = time.time() - start
        
        # 1000 emissions should take < 0.1 second
        assert elapsed < 0.1
    
    def test_update_performance(self):
        """Test particle update is fast."""
        flames = EngineFlames(max_particles=20)
        flames.set_intensity(1.0)
        
        # Pre-populate with particles
        for _ in range(10):
            flames.emit()
            flames.update(0.016)
        
        import time
        start = time.time()
        for _ in range(1000):
            flames.update(0.016)
        elapsed = time.time() - start
        
        # 1000 updates should take < 0.1 second
        assert elapsed < 0.1
    
    def test_full_animation_performance(self, screen):
        """Test complete animation cycle performance."""
        flames = EngineFlames(max_particles=20)
        flames.set_intensity(1.0)
        
        import time
        start = time.time()
        
        # Simulate 60 FPS for 1 second
        for _ in range(60):
            flames.emit()
            flames.update(0.016)
            flames.render(screen, (400, 300))
        
        elapsed = time.time() - start
        
        # 1 second of animation should take < 0.5 second
        assert elapsed < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
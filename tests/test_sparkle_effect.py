"""
Simple unit tests for sparkle effect system.
"""

import pytest

import sys
sys.path.insert(0, '/home/nathan/repo/word-quest')

from src.ui.sparkle_effect import Particle, SparkleEffect, create_sparkle_effect


class TestParticle:
    """Tests for individual particle."""
    
    def test_particle_initialization(self):
        """Test particle initializes with expected values."""
        particle = Particle(x=400, y=300, color=(255, 255, 255), size=3)
        
        assert particle.x == 400
        assert particle.y == 300
        assert particle.color == (255, 255, 255)
        assert particle.size == 3
    
    def test_particle_update(self):
        """Test particle updates position and life."""
        particle = Particle(x=400, y=300, size=3)
        initial_life = particle.life
        
        particle.update(0.1)
        
        assert particle.life < initial_life
    
    def test_particle_death(self):
        """Test particle dies after lifetime expires."""
        particle = Particle(x=400, y=300, size=3)
        
        # Update past lifetime
        particle.update(particle.total_life + 0.1)
        
        assert particle.is_dead()


class TestSparkleEffect:
    """Tests for sparkle effect system."""
    
    def test_initialization(self):
        """Test sparkle effect initializes correctly."""
        sparkle = SparkleEffect(center=(400, 300), max_particles=100)
        
        assert sparkle.center == (400, 300)
        assert sparkle.max_particles == 100
        assert len(sparkle.particles) == 0
        assert sparkle.active == False
    
    def test_start_activates(self):
        """Test start sets active flag."""
        sparkle = SparkleEffect(center=(400, 300))
        sparkle.start()
        
        assert sparkle.active == True
    
    def test_stop_deactivates(self):
        """Test stop clears particles and deactivates."""
        sparkle = SparkleEffect(center=(400, 300))
        sparkle.start()
        sparkle.emit(count=5)
        
        sparkle.stop()
        
        assert sparkle.active == False
        assert len(sparkle.particles) == 0
    
    def test_emit_adds_particles(self):
        """Test that emitting adds particles."""
        sparkle = SparkleEffect(center=(400, 300))
        sparkle.start()
        
        sparkle.emit(count=5)
        
        assert len(sparkle.particles) == 5
    
    def test_emit_respects_max_particles(self):
        """Test that emission respects max particle limit."""
        sparkle = SparkleEffect(center=(400, 300), max_particles=10)
        sparkle.start()
        
        sparkle.emit(count=20)
        
        assert len(sparkle.particles) <= 10
    
    def test_get_particle_count(self):
        """Test particle count query."""
        sparkle = SparkleEffect(center=(400, 300))
        
        assert sparkle.get_particle_count() == 0
        
        sparkle.start()
        sparkle.emit(count=10)  # Note: MAX_EMIT_COUNT limits to 5
        
        # Should have emitted some particles (capped at MAX_EMIT_COUNT=5)
        assert sparkle.get_particle_count() > 0
        assert sparkle.get_particle_count() <= 5
    
    def test_set_center(self):
        """Test setting new center position."""
        sparkle = SparkleEffect(center=(400, 300))
        
        sparkle.set_center((500, 400))
        
        assert sparkle.center == (500, 400)


class TestCreateSparkleEffect:
    """Tests for factory function."""
    
    def test_create_with_defaults(self):
        """Test factory with default parameters."""
        sparkle = create_sparkle_effect(center=(400, 300))
        
        assert sparkle.center == (400, 300)
        assert sparkle.max_particles == 100
    
    def test_create_with_custom_max(self):
        """Test factory with custom max particles."""
        sparkle = create_sparkle_effect(center=(400, 300), max_particles=50)
        
        assert sparkle.max_particles == 50


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
"""
Simple unit tests for planet bloom animation.
"""

import pytest
from unittest.mock import MagicMock

import sys
sys.path.insert(0, '/home/nathan/repo/word-quest')

from src.ui.planet_bloom import PlanetBloom, BloomState, create_planet_bloom


class TestPlanetBloom:
    """Tests for planet bloom animation."""
    
    def test_initialization(self):
        """Test bloom initializes in idle state."""
        planet_mock = MagicMock()
        bloom = PlanetBloom(planet_mock, planet_number=1)
        
        assert bloom.state == BloomState.IDLE
        assert bloom.progress == 0.0
        assert bloom.planet_number == 1
    
    def test_start_bloom(self):
        """Test start_bloom sets starting state."""
        planet_mock = MagicMock()
        bloom = PlanetBloom(planet_mock, planet_number=1)
        
        bloom.start_bloom()
        
        assert bloom.state == BloomState.STARTING
    
    def test_update_transitions_to_blooming(self):
        """Test update transitions from starting to blooming."""
        planet_mock = MagicMock()
        bloom = PlanetBloom(planet_mock, planet_number=1)
        
        bloom.start_bloom()
        bloom.update(0.1)
        
        assert bloom.state == BloomState.BLOOMING
    
    def test_bloom_progresses(self):
        """Test bloom progress increases."""
        planet_mock = MagicMock()
        bloom = PlanetBloom(planet_mock, planet_number=1)
        bloom.start_bloom()
        bloom.update(0.1)  # Transition to BLOOMING
        
        initial_progress = bloom.progress
        bloom.update(1.0)
        
        assert bloom.progress > initial_progress
    
    def test_bloom_reaches_holding(self):
        """Test bloom eventually reaches holding state."""
        planet_mock = MagicMock()
        bloom = PlanetBloom(planet_mock, planet_number=1)
        bloom.start_bloom()
        
        # Simulate 2.5 seconds (25 updates of 0.1s) to ensure we reach holding
        for _ in range(25):
            bloom.update(0.1)
        
        assert bloom.state == BloomState.HOLDING
        assert bloom.progress == 1.0
    
    def test_holding_transitions_to_fade(self):
        """Test holding state transitions to fade out."""
        planet_mock = MagicMock()
        bloom = PlanetBloom(planet_mock, planet_number=1)
        bloom.start_bloom()
        
        # Reach holding (25 updates to be safe)
        for _ in range(25):
            bloom.update(0.1)
        
        assert bloom.state == BloomState.HOLDING
        
        # Update past hold duration (0.5s = 5 updates of 0.1s, use 10 to be safe)
        for _ in range(10):
            bloom.update(0.1)
        
        assert bloom.state == BloomState.FADE_OUT
    
    def test_fade_returns_to_idle(self):
        """Test fade out returns to idle."""
        planet_mock = MagicMock()
        bloom = PlanetBloom(planet_mock, planet_number=1)
        bloom.start_bloom()
        
        # Complete full cycle (3.5s total, use 40 updates to be safe)
        for _ in range(40):
            bloom.update(0.1)
        
        assert bloom.state == BloomState.IDLE
    
    def test_is_active(self):
        """Test active state detection."""
        planet_mock = MagicMock()
        bloom = PlanetBloom(planet_mock, planet_number=1)
        
        assert bloom.is_active() == False
        
        bloom.start_bloom()
        assert bloom.is_active() == True
        
        # Complete cycle (40 updates to be safe)
        for _ in range(40):
            bloom.update(0.1)
        
        assert bloom.is_active() == False
    
    def test_is_complete(self):
        """Test completion detection."""
        planet_mock = MagicMock()
        bloom = PlanetBloom(planet_mock, planet_number=1)
        
        assert bloom.is_complete() == True
        
        bloom.start_bloom()
        assert bloom.is_complete() == False
        
        # Complete cycle (40 updates to be safe)
        for _ in range(40):
            bloom.update(0.1)
        
        assert bloom.is_complete() == True
    
    def test_get_intensity(self):
        """Test intensity calculation."""
        planet_mock = MagicMock()
        bloom = PlanetBloom(planet_mock, planet_number=1)
        
        # Idle intensity is 0
        assert bloom._get_intensity() == 0.0
        
        bloom.start_bloom()
        for _ in range(25):  # Reach holding (use 25 to be safe)
            bloom.update(0.1)
        
        # Holding intensity is 1.0
        assert bloom._get_intensity() == 1.0
    
    def test_planet_colors(self):
        """Test different planet numbers have colors."""
        planet_mock = MagicMock()
        
        for planet_num in [1, 2, 3, 4, 5]:
            bloom = PlanetBloom(planet_mock, planet_number=planet_num)
            assert bloom.colors is not None


class TestCreatePlanetBloom:
    """Tests for factory function."""
    
    def test_create_with_defaults(self):
        """Test factory with default parameters."""
        planet_mock = MagicMock()
        bloom = create_planet_bloom(planet_mock)
        
        assert bloom.planet_number == 1
    
    def test_create_with_planet_number(self):
        """Test factory with specific planet number."""
        planet_mock = MagicMock()
        bloom = create_planet_bloom(planet_mock, planet_number=3)
        
        assert bloom.planet_number == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
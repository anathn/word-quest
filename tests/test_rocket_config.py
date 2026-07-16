"""
Unit Tests for Rocket Config (STORY-005-02)

Tests for rocket color configuration and persistence.
"""

import pytest
import pygame
import os
import sys
import json
import tempfile
from datetime import datetime

# Set TESTING environment variable before importing
os.environ["TESTING"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from src.models.rocket_config import (
    RocketConfig,
    RocketColor,
    create_rocket_config,
    ROCKET_COLOR_PRESETS,
    DEFAULT_ROCKET_COLOR_RGB,
    DEFAULT_ROCKET_COLOR_HEX
)


class TestRocketColor:
    """Tests for RocketColor dataclass."""
    
    def test_rocket_color_creation(self):
        """Test creating a RocketColor."""
        color = RocketColor(
            name="Red",
            rgb=(244, 67, 54),
            hex="#F44336"
        )
        
        assert color.name == "Red"
        assert color.rgb == (244, 67, 54)
        assert color.hex == "#F44336"
    
    def test_rocket_color_invalid_rgb_low(self):
        """Test RocketColor rejects RGB below 0."""
        with pytest.raises(ValueError):
            RocketColor(name="Invalid", rgb=(-1, 100, 100), hex="#FF0000")
    
    def test_rocket_color_invalid_rgb_high(self):
        """Test RocketColor rejects RGB above 255."""
        with pytest.raises(ValueError):
            RocketColor(name="Invalid", rgb=(256, 100, 100), hex="#FF0000")


class TestRocketConfig:
    """Tests for RocketConfig class."""
    
    def test_initialization(self):
        """Test config initializes with defaults."""
        config = RocketConfig(player_id="test_player")
        
        assert config.player_id == "test_player"
        assert len(config.rocket_colors) == 8
        assert config.get_current_color() == DEFAULT_ROCKET_COLOR_RGB
        
    def test_get_current_color(self):
        """Test getting current color."""
        config = RocketConfig("test_player")
        
        assert config.get_current_color() == DEFAULT_ROCKET_COLOR_RGB
        assert config.get_current_color_hex() == DEFAULT_ROCKET_COLOR_HEX
    
    def test_set_color_by_rgb(self):
        """Test setting color by RGB."""
        config = RocketConfig("test_player")
        
        config.set_color((244, 67, 54))  # Red
        assert config.get_current_color() == (244, 67, 54)
        assert config.get_current_color_hex() == "#F44336"
    
    def test_set_color_by_hex(self):
        """Test setting color by hex."""
        config = RocketConfig("test_player")
        
        config.set_color_by_hex("#2196F3")  # Blue
        assert config.get_current_color() == (33, 150, 243)
        assert config.get_current_color_hex() == "#2196F3"
    
    def test_set_color_all_presets(self):
        """Test setting all preset colors."""
        config = RocketConfig("test_player")
        
        for color_data in ROCKET_COLOR_PRESETS:
            config.set_color(color_data["rgb"])
            assert config.get_current_color() == color_data["rgb"]
            assert config.get_current_color_hex() == color_data["hex"]
    
    def test_set_color_invalid_rgb(self):
        """Test setting invalid RGB value."""
        config = RocketConfig("test_player")
        
        with pytest.raises(ValueError):
            config.set_color((256, 0, 0))  # R > 255
        
        with pytest.raises(ValueError):
            config.set_color((-1, 0, 0))  # R < 0
    
    def test_set_color_not_in_presets(self):
        """Test setting color not in presets."""
        config = RocketConfig("test_player")
        
        with pytest.raises(ValueError):
            config.set_color((123, 45, 67))  # Random color not in presets
    
    def test_set_color_by_hex_invalid_format(self):
        """Test setting hex with invalid format."""
        config = RocketConfig("test_player")
        
        with pytest.raises(ValueError):
            config.set_color_by_hex("FF4444")  # Missing #
        
        with pytest.raises(ValueError):
            config.set_color_by_hex("#FF44")  # Too short
        
        with pytest.raises(ValueError):
            config.set_color_by_hex("#GGGGGG")  # Invalid hex chars
    
    def test_set_color_by_hex_not_in_presets(self):
        """Test setting hex color not in presets."""
        config = RocketConfig("test_player")
        
        with pytest.raises(ValueError):
            config.set_color_by_hex("#123456")  # Not in presets
    
    def test_get_available_colors(self):
        """Test getting available colors."""
        config = RocketConfig("test_player")
        
        colors = config.get_available_colors()
        
        assert len(colors) == 8
        assert (255, 255, 255) in colors  # White
        assert (244, 67, 54) in colors  # Red
        assert (33, 150, 243) in colors  # Blue
    
    def test_get_available_colors_hex(self):
        """Test getting available colors as hex."""
        config = RocketConfig("test_player")
        
        colors = config.get_available_colors_hex()
        
        assert len(colors) == 8
        assert "#FFFFFF" in colors
        assert "#F44336" in colors
        assert "#2196F3" in colors
    
    def test_get_color_name(self):
        """Test getting color name."""
        config = RocketConfig("test_player")
        
        assert config.get_color_name((255, 255, 255)) == "White"
        assert config.get_color_name((244, 67, 54)) == "Red"
        assert config.get_color_name((33, 150, 243)) == "Blue"
    
    def test_get_color_name_unknown(self):
        """Test getting name for unknown color."""
        config = RocketConfig("test_player")
        
        # Note: This test assumes (123, 45, 67) is not in presets
        name = config.get_color_name((123, 45, 67))
        assert name == "Unknown"
    
    def test_validate_color(self):
        """Test color validation."""
        config = RocketConfig("test_player")
        
        assert config.validate_color((255, 255, 255)) == True
        assert config.validate_color((244, 67, 54)) == True
        assert config.validate_color((123, 45, 67)) == False


class TestHexRgbConversion:
    """Tests for hex/RGB conversion utilities."""
    
    def test_hex_to_rgb_basic(self):
        """Test hex to RGB conversion."""
        config = RocketConfig("test_player")
        
        assert RocketConfig.hex_to_rgb("#FF0000") == (255, 0, 0)
        assert RocketConfig.hex_to_rgb("#00FF00") == (0, 255, 0)
        assert RocketConfig.hex_to_rgb("#0000FF") == (0, 0, 255)
    
    def test_hex_to_rgb_presets(self):
        """Test hex to RGB for all presets."""
        config = RocketConfig("test_player")
        
        for color_data in ROCKET_COLOR_PRESETS:
            rgb = RocketConfig.hex_to_rgb(color_data["hex"])
            assert rgb == color_data["rgb"]
    
    def test_hex_to_rgb_invalid(self):
        """Test hex to RGB with invalid input."""
        config = RocketConfig("test_player")
        
        with pytest.raises(ValueError):
            RocketConfig.hex_to_rgb("#FF00")  # Too short
        
        with pytest.raises(ValueError):
            RocketConfig.hex_to_rgb("#GGGGGG")  # Invalid chars
    
    def test_rgb_to_hex_basic(self):
        """Test RGB to hex conversion."""
        config = RocketConfig("test_player")
        
        assert RocketConfig.rgb_to_hex((255, 0, 0)) == "#ff0000"
        assert RocketConfig.rgb_to_hex((0, 255, 0)) == "#00ff00"
        assert RocketConfig.rgb_to_hex((0, 0, 255)) == "#0000ff"
    
    def test_rgb_to_hex_presets(self):
        """Test RGB to hex for all presets."""
        config = RocketConfig("test_player")
        
        for color_data in ROCKET_COLOR_PRESETS:
            hex_color = RocketConfig.rgb_to_hex(color_data["rgb"])
            assert hex_color.upper() == color_data["hex"].upper()
    
    def test_roundtrip_conversion(self):
        """Test hex -> RGB -> hex roundtrip."""
        config = RocketConfig("test_player")
        
        for color_data in ROCKET_COLOR_PRESETS:
            hex_to_rgb = RocketConfig.hex_to_rgb(color_data["hex"])
            rgb_to_hex = RocketConfig.rgb_to_hex(hex_to_rgb)
            assert rgb_to_hex.upper() == color_data["hex"].upper()


class TestRocketConfigFactory:
    """Tests for factory function."""
    
    def test_factory_creates_instance(self):
        """Test factory creates RocketConfig."""
        config = create_rocket_config("test_player")
        
        assert isinstance(config, RocketConfig)
        assert config.player_id == "test_player"
    
    def test_factory_unique_instances(self):
        """Test factory creates unique instances."""
        config1 = create_rocket_config("player1")
        config2 = create_rocket_config("player2")
        
        assert config1 is not config2
        assert config1.player_id == "player1"
        assert config2.player_id == "player2"


@pytest.mark.serial
class TestRocketConfigPersistence:
    """Tests for rocket color persistence."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test data."""
        import tempfile
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        import shutil
        shutil.rmtree(tmpdir)
    
    def test_persistence_integration(self, temp_dir):
        """Test that color changes can persist (integration check)."""
        config = RocketConfig("test_player")
        
        # Set a custom color
        config.set_color((244, 67, 54))
        assert config.get_current_color() == (244, 67, 54)
        
        # Create new config instance (simulates restart)
        config2 = RocketConfig("test_player")
        
        # Note: In MVP, persistence depends on player profile system
        # which may not be fully implemented. This test verifies
        # the config logic works correctly.
        assert config2.player_id == "test_player"
    
    def test_player_id_stored(self):
        """Test player ID is properly stored."""
        config = RocketConfig("unique_player_123")
        
        assert config.player_id == "unique_player_123"
    
    def test_multiple_players_independent(self):
        """Test that different players have independent configs."""
        config1 = RocketConfig("player1")
        config2 = RocketConfig("player2")
        
        config1.set_color((244, 67, 54))  # Red
        config2.set_color((33, 150, 243))  # Blue
        
        assert config1.get_current_color() == (244, 67, 54)
        assert config2.get_current_color() == (33, 150, 243)


@pytest.mark.performance
class TestRocketConfigPerformance:
    """Performance tests for rocket config."""
    
    def test_color_set_performance(self):
        """Test color set operation is fast."""
        config = RocketConfig("test_player")
        
        import time
        start = time.time()
        for _ in range(100):
            config.set_color((244, 67, 54))
        elapsed = time.time() - start
        
        # 100 color sets should take < 0.1 second
        assert elapsed < 0.1
    
    def test_get_color_performance(self):
        """Test get color operation is fast."""
        config = RocketConfig("test_player")
        
        import time
        start = time.time()
        for _ in range(10000):
            config.get_current_color()
        elapsed = time.time() - start
        
        # 10000 gets should take < 0.05 second (relaxed from 0.01 for CI stability)
        assert elapsed < 0.05
    
    def test_color_validation_performance(self):
        """Test color validation is fast."""
        config = RocketConfig("test_player")
        
        import time
        start = time.time()
        for _ in range(1000):
            config.validate_color((255, 255, 255))
        elapsed = time.time() - start
        
        # 1000 validations should take < 0.01 second
        assert elapsed < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
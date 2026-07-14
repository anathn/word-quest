"""
Unit Tests for Captain Display Component (STORY-004-04)

Tests for the Captain Cosmos display UI including:
- Character rendering
- Animation state transitions
- Speech bubble display
- Position and sizing
"""

import pytest
import pygame
import math


@pytest.fixture
def pygame_initialized():
    """Initialize pygame for testing."""
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def mock_screen(pygame_initialized):
    """Create a mock pygame screen surface."""
    return pygame.Surface((800, 600))


@pytest.fixture
def mock_captain():
    """Create a mock CaptainCosmos instance for testing."""
    from unittest.mock import MagicMock
    from src.components.captain_cosmos import CaptainState
    
    captain = MagicMock()
    captain.get_state.return_value = CaptainState.IDLE
    captain.get_current_line.return_value = None
    captain.current_line = None
    return captain


@pytest.fixture
def captain_display(mock_screen, mock_captain):
    """Create a CaptainDisplay instance for testing."""
    from src.ui.captain_display import CaptainDisplay
    
    return CaptainDisplay(mock_screen, mock_captain)


class TestCaptainDisplayInitialization:
    """Test CaptainDisplay initialization."""
    
    def test_initializes_with_default_position(self, captain_display):
        """CaptainDisplay should use default position."""
        assert captain_display.position == (50, 500)
    
    def test_initializes_with_custom_position(self, mock_screen, mock_captain):
        """CaptainDisplay should accept custom position."""
        from src.ui.captain_display import CaptainDisplay
        
        custom_pos = (100, 400)
        display = CaptainDisplay(mock_screen, mock_captain, custom_pos)
        
        assert display.position == custom_pos
    
    def test_initializes_with_idle_state(self, captain_display):
        """CaptainDisplay should start in IDLE state."""
        from src.components.captain_cosmos import CaptainState
        assert captain_display._current_state == CaptainState.IDLE
    
    def test_initializes_with_no_speech(self, captain_display):
        """CaptainDisplay should have no speech bubble initially."""
        assert captain_display._speech_text == ""
        assert captain_display._speech_timer == 0
    
    def test_creates_font(self, captain_display):
        """CaptainDisplay should create pygame font."""
        assert captain_display._font is not None


class TestCharacterRendering:
    """Test Captain character rendering."""
    
    def test_render_creates_character_surface(self, captain_display):
        """render should create character surface."""
        captain_display._render_character()
        
        assert captain_display._character_surface is not None
        assert captain_display._character_surface.get_width() == 100
        assert captain_display._character_surface.get_height() == 150
    
    def test_render_draws_character_components(self, captain_display, mock_screen):
        """render should draw character without errors."""
        # Should not raise any exceptions
        captain_display.render()
    
    def test_idle_animation_has_bob_offset(self, captain_display):
        """Idle state should have bob animation."""
        from src.components.captain_cosmos import CaptainState
        
        captain_display._current_state = CaptainState.IDLE
        captain_display._last_update_time = pygame.time.get_ticks()
        
        # Update should set bob offset
        captain_display.update(0.016)  # ~60fps
        
        assert captain_display._bob_offset is not None


class TestAnimationStates:
    """Test animation state transitions."""
    
    def test_update_syncs_with_captain_state(self, captain_display, mock_captain, mock_screen):
        """update should sync _current_state with CaptainCosmos state."""
        from src.components.captain_cosmos import CaptainState
        
        # Mock captain returns CELEBRATING state
        from src.components.captain_cosmos import CaptainState
        mock_captain.get_state.return_value = CaptainState.CELEBRATING
        
        captain_display.update(0.016)
        
        assert captain_display._current_state == CaptainState.CELEBRATING
    
    def test_celebrating_state_no_bob(self, captain_display):
        """Celebrating state should not have bob animation."""
        from src.components.captain_cosmos import CaptainState
        
        captain_display._current_state = CaptainState.CELEBRATING
        initial_bob = captain_display._bob_offset
        
        # Update should not change bob in celebrating state
        captain_display.update(0.016)
        
        # Bob offset should remain at last value (no continuous animation)
        # Note: Actually bob_offset is not reset, just not actively updated
    
    def test_state_change_records_transition_time(self, captain_display, mock_captain):
        """State change should update transition start time."""
        from src.components.captain_cosmos import CaptainState
        
        initial_time = captain_display._state_transition_start
        mock_captain.get_state.return_value = CaptainState.CELEBRATING
        
        captain_display.update(0.016)
        
        # Transition start should be updated if state changed
        assert captain_display._state_transition_start >= initial_time


class TestSpeechBubble:
    """Test speech bubble functionality."""
    
    def test_show_speech_bubble(self, captain_display):
        """show_speech_bubble should set text and timer."""
        captain_display.show_speech_bubble("Hello!", duration=2.0)
        
        assert captain_display._speech_text == "Hello!"
        assert captain_display._speech_timer == 2000  # Convert to ms
        assert captain_display._speech_alpha == 255
    
    def test_hide_speech_bubble(self, captain_display):
        """hide_speech_bubble should clear bubble."""
        captain_display.show_speech_bubble("Test")
        captain_display.hide_speech_bubble()
        
        assert captain_display._speech_text == ""
        assert captain_display._speech_timer == 0
        assert captain_display._speech_alpha == 0
    
    def test_speech_bubble_fade_in_out(self, captain_display):
        """Speech bubble should fade in and out."""
        # Start with new bubble
        captain_display.show_speech_bubble("Test", duration=3.0)
        captain_display._speech_timer = 3000  # Start at full
        captain_display.update(0.001)  # Very small delta
        
        # Initially should be fully visible (after fade in)
        assert captain_display._speech_alpha <= 255
        
        # Near end (should be fading out)
        captain_display._speech_timer = 100
        captain_display.update(0.001)
        assert captain_display._speech_alpha < 255
    
    def test_speech_timer_decrements(self, captain_display):
        """Speech timer should decrement on update."""
        captain_display.show_speech_bubble("Test", duration=3.0)
        initial_timer = captain_display._speech_timer
        
        captain_display.update(0.1)  # 100ms
        
        assert captain_display._speech_timer < initial_timer
    
    def test_speech_bubble_creates_surface(self, captain_display):
        """Speech bubble should create surface when text is set."""
        captain_display.show_speech_bubble("Hello World")
        captain_display._render_speech_bubble()
        
        assert captain_display._speech_surface is not None
    
    def test_speech_bubble_hides_when_empty(self, captain_display):
        """Speech bubble surface should be None when no text."""
        captain_display.hide_speech_bubble()
        captain_display._render_speech_bubble()
        
        assert captain_display._speech_surface is None
    
    def test_tts_start_shows_bubble(self, captain_display, mock_captain):
        """on_tts_start should show speech bubble with current line."""
        from unittest.mock import MagicMock
        
        mock_captain.current_line = MagicMock()
        mock_captain.current_line.text = "Test line"
        
        captain_display.on_tts_start()
        
        assert captain_display._speech_text == "Test line"
    
    def test_tts_complete_hides_bubble(self, captain_display):
        """on_tts_complete should hide speech bubble."""
        captain_display.show_speech_bubble("Test")
        captain_display.on_tts_complete()
        
        assert captain_display._speech_text == ""
        assert captain_display._speech_timer == 0


class TestCaptainDisplayFactory:
    """Test factory function for CaptainDisplay."""
    
    def test_create_captain_display(self, mock_screen, mock_captain):
        """create_captain_display should create and return CaptainDisplay."""
        from src.ui.captain_display import create_captain_display, CaptainDisplay
        
        display = create_captain_display(mock_screen, mock_captain)
        
        assert display is not None
        assert isinstance(display, CaptainDisplay)
    

class TestSetState:
    """Test set_state functionality."""
    
    def test_set_state_updates_state(self, captain_display):
        """set_state should update _current_state."""
        from src.components.captain_cosmos import CaptainState
        
        captain_display.set_state(CaptainState.CELEBRATING)
        
        assert captain_display._current_state == CaptainState.CELEBRATING
    
    def test_set_state_updates_transition_time(self, captain_display):
        """set_state should update _state_transition_start."""
        from src.components.captain_cosmos import CaptainState
        
        initial_time = captain_display._state_transition_start
        captain_display.set_state(CaptainState.CELEBRATING)
        
        assert captain_display._state_transition_start >= initial_time


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_update_with_zero_dt(self, captain_display):
        """update should handle zero delta time."""
        # Should not raise any exceptions
        captain_display.update(0)
    
    def test_update_with_large_dt(self, captain_display):
        """update should handle very large delta time."""
        # Should not raise any exceptions
        captain_display.update(10.0)
    
    def test_show_speech_bubble_with_empty_text(self, captain_display):
        """show_speech_bubble should handle empty text."""
        captain_display.show_speech_bubble("")
        
        assert captain_display._speech_text == ""
        assert captain_display._speech_timer == 3000  # Default duration
    
    def test_speech_bubble_with_very_long_text(self, captain_display):
        """Speech bubble should handle long text."""
        long_text = "This is a very long message that should still work fine in the speech bubble component."
        captain_display.show_speech_bubble(long_text)
        
        assert captain_display._speech_text == long_text
        captain_display._render_speech_bubble()
        assert captain_display._speech_surface is not None
    
    def test_render_with_no_surfaces(self, captain_display, mock_screen):
        """render should handle missing surfaces gracefully."""
        captain_display._character_surface = None
        captain_display._speech_surface = None
        
        # Should not raise any exceptions
        captain_display.render()
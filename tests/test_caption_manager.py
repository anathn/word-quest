"""
Unit Tests for Caption Manager Component (STORY-006-03)

Tests for caption queuing, display timing, and state management.
"""

import pytest
import time
import os
import json
from unittest.mock import Mock, MagicMock, patch
from collections import deque

from src.components.caption_manager import (
    CaptionManager, Caption, CaptionIntensity
)


class TestCaption:
    """Tests for Caption dataclass."""
    
    def test_caption_creation(self):
        """Test basic caption creation."""
        caption = Caption(
            text="Hello",
            duration=3.0,
            speaker="Captain Cosmos",
            caption_id="test_001"
        )
        
        assert caption.text == "Hello"
        assert caption.duration == 3.0
        assert caption.speaker == "Captain Cosmos"
        assert caption.caption_id == "test_001"
        assert caption.is_sfx == False
        assert caption.intensity_required == CaptionIntensity.FULL
    
    def test_caption_to_dict(self):
        """Test caption serialization."""
        caption = Caption(
            text="Test",
            duration=4.0,
            speaker="System",
            caption_id="sys_001",
            is_sfx=True
        )
        
        result = caption.to_dict()
        
        assert result['text'] == "Test"
        assert result['duration'] == 4.0
        assert result['speaker'] == "System"
        assert result['caption_id'] == "sys_001"
        assert result['is_sfx'] == True
    
    def test_caption_default_values(self):
        """Test caption default values."""
        caption = Caption(text="Simple")
        
        assert caption.duration == 3.0
        assert caption.speaker is None
        assert caption.caption_id == ""
        assert caption.is_sfx == False


class TestCaptionManager:
    """Tests for CaptionManager component."""
    
    @pytest.fixture
    def mock_display(self):
        """Create a mock caption display."""
        return Mock()
    
    @pytest.fixture
    def temp_data_dir(self, tmp_path):
        """Create a temporary data directory."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create minimal captions.json with proper structure
        captions = {
            "captions": {
                "captain_cosmos": {
                    "welcome": "Welcome aboard!",
                    "good_job": "Excellent spelling!"
                },
                "system": {
                    "level_complete": "Planet Complete!"
                },
                "sfx_descriptions": {}
            }
        }
        
        captions_file = data_dir / "captions.json"
        with open(captions_file, 'w') as f:
            json.dump(captions, f)
        
        return str(data_dir)
    
    def test_manager_initialization(self, mock_display):
        """Test basic manager initialization."""
        manager = CaptionManager(caption_display=mock_display)
        
        assert manager.enabled == True
        assert len(manager.caption_queue) == 0
        assert manager.current_caption is None
        assert manager.display == mock_display
    
    def test_show_caption_immediate(self, mock_display):
        """Test showing caption immediately."""
        manager = CaptionManager(caption_display=mock_display)
        
        manager.show_caption("Hello World", speaker="Test")
        
        assert manager.current_caption is not None
        assert manager.current_caption.text == "Hello World"
        assert manager.current_caption.speaker == "Test"
        mock_display.show_caption.assert_called_once()
    
    def test_show_caption_disabled(self, mock_display):
        """Test that captions don't show when disabled."""
        manager = CaptionManager(caption_display=mock_display)
        manager.set_enabled(False)
        
        manager.show_caption("Should not appear")
        
        assert manager.current_caption is None
        mock_display.show_caption.assert_not_called()
    
    def test_show_caption_empty_text(self, mock_display):
        """Test that empty text doesn't show caption."""
        manager = CaptionManager(caption_display=mock_display)
        
        manager.show_caption("")
        
        assert manager.current_caption is None
    
    def test_queue_caption(self, mock_display):
        """Test queuing captions."""
        manager = CaptionManager(caption_display=mock_display)
        
        caption = Caption(text="Queued", duration=3.0)
        manager.queue_caption(caption)
        
        assert len(manager.caption_queue) == 1
        assert manager.caption_queue[0].text == "Queued"
    
    def test_queue_multiple_captions(self, mock_display):
        """Test queuing multiple captions."""
        manager = CaptionManager(caption_display=mock_display)
        
        manager.queue_caption(Caption(text="First"))
        manager.queue_caption(Caption(text="Second"))
        manager.queue_caption(Caption(text="Third"))
        
        assert len(manager.caption_queue) == 3
    
    def test_update_displays_queued(self, mock_display, monkeypatch):
        """Test that update() displays queued captions."""
        manager = CaptionManager(caption_display=mock_display)
        
        # Queue a caption
        caption = Caption(text="Next", duration=3.0)
        manager.queue_caption(caption)
        
        # Mock time to avoid expiration
        monkeypatch.setattr(time, 'time', lambda: 0)
        manager.expires_at = float('inf')  # Never expire
        
        # Update should show queued caption
        manager.update(0.016)
        
        assert manager.current_caption is not None
        assert manager.current_caption.text == "Next"
    
    def test_update_expires_caption(self, mock_display):
        """Test that update() expires old captions."""
        manager = CaptionManager(caption_display=mock_display)
        
        # Set current caption with immediate expiration
        manager.current_caption = Caption(text="Current")
        manager.expires_at = time.time() - 1  # Already expired
        
        manager.update(0.016)
        
        assert manager.current_caption is None
        mock_display.hide_caption.assert_called()
    
    def test_clear_removes_all(self, mock_display):
        """Test that clear() removes all captions."""
        manager = CaptionManager(caption_display=mock_display)
        
        manager.queue_caption(Caption(text="First"))
        manager.queue_caption(Caption(text="Second"))
        manager.current_caption = Caption(text="Current")
        
        manager.clear()
        
        assert len(manager.caption_queue) == 0
        assert manager.current_caption is None
        mock_display.hide_caption.assert_called()
    
    def test_set_enabled_false_clears(self, mock_display):
        """Test that disabling clears captions."""
        manager = CaptionManager(caption_display=mock_display)
        
        manager.current_caption = Caption(text="Current")
        manager.queue_caption(Caption(text="Queued"))
        
        manager.set_enabled(False)
        
        assert not manager.enabled
        assert manager.current_caption is None
        assert len(manager.caption_queue) == 0
    
    def test_set_intensity_mode_full(self, mock_display):
        """Test setting intensity mode to full."""
        manager = CaptionManager(caption_display=mock_display)
        
        manager.set_intensity_mode(CaptionIntensity.FULL)
        
        assert manager.get_intensity_mode() == CaptionIntensity.FULL
    
    def test_set_intensity_mode_reduced(self, mock_display):
        """Test setting intensity mode to reduced."""
        manager = CaptionManager(caption_display=mock_display)
        
        manager.set_intensity_mode(CaptionIntensity.REDUCED)
        
        assert manager.get_intensity_mode() == CaptionIntensity.REDUCED
    
    def test_set_intensity_mode_off_disables(self, mock_display):
        """Test that off intensity disables captions."""
        manager = CaptionManager(caption_display=mock_display)
        
        manager.set_intensity_mode(CaptionIntensity.OFF)
        
        assert not manager.enabled
        assert manager.get_intensity_mode() == CaptionIntensity.OFF
    
    def test_get_caption_history(self, mock_display):
        """Test getting caption history."""
        manager = CaptionManager(caption_display=mock_display)
        
        manager.show_caption("First")
        manager.show_caption("Second")
        manager.show_caption("Third")
        
        history = manager.get_caption_history(limit=2)
        
        assert len(history) == 2
        assert history[0].text == "Third"
        assert history[1].text == "Second"
    
    def test_skip_celebration(self, mock_display):
        """Test skipping celebration captions."""
        manager = CaptionManager(caption_display=mock_display)
        
        # Queue some celebration captions
        manager.queue_caption(Caption(text="Celebration 1"))
        manager.queue_caption(Caption(text="Celebration 2"))
        
        manager.skip_celebration()
        
        assert len(manager.caption_queue) == 0
    
    def test_get_caption_from_db(self, temp_data_dir):
        """Test getting caption from database."""
        manager = CaptionManager(data_dir=temp_data_dir)
        
        text = manager.get_caption("captain_cosmos", "welcome")
        
        assert text == "Welcome aboard!"
    
    def test_get_capton_with_formatting(self, temp_data_dir):
        """Test getting formatted caption from database."""
        manager = CaptionManager(data_dir=temp_data_dir)
        
        # Add a formatted caption to test
        manager._captions_db['test'] = {'formatted': "Word has {count} letters"}
        
        text = manager.get_caption("test", "formatted", count=7)
        
        assert text == "Word has 7 letters"
    
    def test_get_caption_missing_key(self, temp_data_dir):
        """Test getting non-existent caption returns None."""
        manager = CaptionManager(data_dir=temp_data_dir)
        
        text = manager.get_caption("captain_cosmos", "nonexistent")
        
        assert text is None
    
    def test_show_caption_by_id(self, temp_data_dir, mock_display):
        """Test showing caption from database by ID."""
        manager = CaptionManager(
            caption_display=mock_display,
            data_dir=temp_data_dir
        )
        
        manager.show_caption_by_id("captain_cosmos", "welcome")
        
        assert manager.current_caption is not None
        assert "Welcome aboard" in manager.current_caption.text
    
    def test_queue_caption_by_id(self, temp_data_dir, mock_display):
        """Test queuing caption from database by ID."""
        manager = CaptionManager(
            caption_display=mock_display,
            data_dir=temp_data_dir
        )
        
        manager.queue_caption_by_id("captain_cosmos", "good_job")
        
        assert len(manager.caption_queue) == 1
        assert "Excellent spelling" in manager.caption_queue[0].text
    
    def test_sfx_captions_reduced_intensity(self, mock_display):
        """Test SFX captions not shown in reduced mode."""
        manager = CaptionManager(caption_display=mock_display)
        manager.set_intensity_mode(CaptionIntensity.REDUCED)
        
        manager.show_caption("[SOUND]", is_sfx=True)
        
        assert manager.current_caption is None
    
    def test_normal_captions_in_reduced_mode(self, mock_display):
        """Test normal captions still shown in reduced mode."""
        manager = CaptionManager(caption_display=mock_display)
        manager.set_intensity_mode(CaptionIntensity.REDUCED)
        
        manager.show_caption("Normal text", is_sfx=False)
        
        assert manager.current_caption is not None
        assert not manager.current_caption.is_sfx


class TestCaptionManagerIntegration:
    """Integration tests for caption manager."""
    
    @pytest.fixture  
    def temp_data_dir(self, tmp_path):
        """Create a temporary data directory with full captions."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        captions = {
            "captions": {
                "captain_cosmos": {
                    "welcome": "Welcome aboard, Space Speller!",
                    "good_job": "Excellent spelling!"
                },
                "system": {},
                "sfx_descriptions": {
                    "chime": "[SUCCESSFUL CHIME]"
                }
            }
        }
        
        captions_file = data_dir / "captions.json"
        with open(captions_file, 'w') as f:
            json.dump(captions, f)
        
        return str(data_dir)
    
    def test_caption_queue_processing(self, temp_data_dir):
        """Test complete caption queue processing."""
        manager = CaptionManager(data_dir=temp_data_dir)
        
        # Queue multiple captions
        manager.queue_caption(Caption(text="First", duration=2.0))
        manager.queue_caption(Caption(text="Second", duration=2.0))
        
        # Simulate time passing
        initial_time = time.time()
        
        # Show first caption
        manager.show_caption("Current", duration=2.0)
        
        # Update 1 - within duration
        manager.update(0.016)
        assert manager.current_caption.text == "Current"
        
        # Mock time to advance past duration
        class TimeMock:
            count = 0
            def __call__(self):
                self.count += 1
                return initial_time + self.count * 3  # 3 seconds per call
        
        time_mock = TimeMock()
        with patch('time.time', time_mock):
            # Update 2 - past duration, should show first queued
            manager.update(0.016)
            assert manager.current_caption.text == "First"
            
            # Update 3 - past duration, should show second queued
            manager.update(0.016)
            assert manager.current_caption.text == "Second"
    
    def test_history_tracking(self, temp_data_dir):
        """Test caption history accuracy."""
        manager = CaptionManager(data_dir=temp_data_dir)
        
        manager.show_caption("Caption 1")
        manager.show_caption("Caption 2")
        manager.clear()
        manager.show_caption("Caption 3")
        
        history = manager.get_caption_history(limit=10)
        
        # Should have 3 captions in history
        assert len(history) >= 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
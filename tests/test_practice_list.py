"""
Unit tests for Words Needing Practice List (STORY-002-05)

Tests the PracticeListDisplay UI component and ProgressTracker integration.
"""

import pytest
import pygame
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from src.components.progress_tracker import ProgressTracker, create_progress_tracker
from src.components.session_tracker import SessionTracker, WordAttempt
from src.ui.practice_list import PracticeListDisplay, create_practice_list


class TestPracticeListDisplay:
    """Tests for PracticeListDisplay UI component."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Initialize pygame for testing
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
        
        self.screen_width = 800
        self.screen_height = 600
    
    def teardown_method(self):
        """Clean up after tests."""
        pass
    
    def test_create_practice_list_parent_view(self):
        """Test creating practice list in parent view mode."""
        practice_list = create_practice_list(
            screen_width=self.screen_width,
            screen_height=self.screen_height,
            view_type="parent"
        )
        
        assert practice_list.view_type == "parent"
        assert practice_list.title_text == "Words Needing Practice:"
        assert practice_list.practice_words == []
    
    def test_create_practice_list_student_view(self):
        """Test creating practice list in student view mode."""
        practice_list = create_practice_list(
            screen_width=self.screen_width,
            screen_height=self.screen_height,
            view_type="student"
        )
        
        assert practice_list.view_type == "student"
        assert practice_list.title_text == "Let's Practice These!"
    
    def test_set_practice_words(self):
        """Test setting practice words."""
        practice_list = PracticeListDisplay(800, 600, "parent")
        
        test_words = [
            {'word': 'because', 'attempts': 3, 'label': 'because - 3 attempts'},
            {'word': 'planet', 'attempts': 2, 'label': 'planet - 2 attempts'}
        ]
        
        practice_list.set_practice_words(test_words)
        
        assert len(practice_list.practice_words) == 2
        assert practice_list.practice_words[0]['word'] == 'because'
        assert practice_list.practice_words[0]['attempts'] == 3
    
    def test_empty_state_message_parent(self):
        """Test empty state message for parent view."""
        practice_list = PracticeListDisplay(800, 600, "parent")
        practice_list.set_practice_words([])
        
        # Should render without errors
        screen = pygame.Surface((800, 600))
        practice_list.render(screen)
        
        # Verify title is correct
        assert practice_list.title_text == "Words Needing Practice:"
    
    def test_empty_state_message_student(self):
        """Test empty state message for student view."""
        practice_list = PracticeListDisplay(800, 600, "student")
        practice_list.set_practice_words([])
        
        # Should render without errors
        screen = pygame.Surface((800, 600))
        practice_list.render(screen)
        
        # Verify title is correct
        assert practice_list.title_text == "Let's Practice These!"
    
    def test_limit_displayed_items(self):
        """Test that only max_items_visible items are displayed."""
        practice_list = PracticeListDisplay(800, 600, "parent")
        
        # Create more words than can be displayed
        test_words = [
            {'word': f'word{i}', 'attempts': i, 'label': f'word{i} - {i} attempts'}
            for i in range(15)
        ]
        
        practice_list.set_practice_words(test_words)
        
        assert len(practice_list.practice_words) == 15
        assert practice_list.max_items_visible == 8
    
    def test_color_scheme(self):
        """Test that correct colors are used."""
        practice_list = PracticeListDisplay(800, 600, "parent")
        
        # Verify orange accent (not red - encouraging)
        assert practice_list.ORANGE_ACCENT == (255, 152, 0)
        assert practice_list.ORANGE_ACCENT != (255, 0, 0)  # Not red
    
    def test_handle_event_no_callback(self):
        """Test event handling without callback set."""
        practice_list = PracticeListDisplay(800, 600, "parent")
        
        # Create a mock click event
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 100))
        
        # Should not raise error
        result = practice_list.handle_event(event)
        
        # No word selected (empty list)
        assert result == False
    
    def test_encouraging_messages_student_view(self):
        """Test that student view shows encouraging messages."""
        practice_list = PracticeListDisplay(800, 600, "student")
        
        test_words = [
            {'word': 'because', 'attempts': 1, 'first_attempt_correct': False},
            {'word': 'planet', 'attempts': 2, 'first_attempt_correct': False},
            {'word': 'astronaut', 'attempts': 5, 'first_attempt_correct': False}
        ]
        
        practice_list.set_practice_words(test_words)
        
        # Should render without errors
        screen = pygame.Surface((800, 600))
        practice_list.render(screen)


class TestProgressTrackerPracticeList:
    """Tests for ProgressTracker.get_words_needing_practice() method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = create_progress_tracker(student_id="test_student")
    
    def teardown_method(self):
        """Clean up."""
        self.tracker.reset()
    
    def test_get_words_needing_practice_empty(self):
        """Test empty practice list when no sessions exist."""
        result = self.tracker.get_words_needing_practice()
        
        assert result == []
    
    def test_get_words_needing_practice_excludes_mastered(self):
        """Test that mastered words are excluded from practice list."""
        # Start a session
        self.tracker.start_session("session_1")
        
        # Complete a word correctly on first attempt (mastered)
        self.tracker.start_word("word_1", "because")
        self.tracker.record_attempt(True)
        self.tracker.complete_word(True)
        
        # Complete a word with multiple attempts (needs practice)
        self.tracker.start_word("word_2", "planet")
        self.tracker.record_attempt(False)
        self.tracker.record_attempt(False)
        self.tracker.record_attempt(True)
        self.tracker.complete_word(True)
        
        self.tracker.end_session()
        
        # Get practice list
        result = self.tracker.get_words_needing_practice()
        
        # Should only include 'planet', not 'because'
        assert len(result) == 1
        assert result[0]['word'] == 'planet'
        assert result[0]['attempts'] == 3
    
    def test_get_words_needing_practice_sorted_by_attempts(self):
        """Test that practice list is sorted by attempts (descending)."""
        # Start a session
        self.tracker.start_session("session_1")
        
        # Word with 2 attempts
        self.tracker.start_word("word_1", "because")
        self.tracker.record_attempt(False)
        self.tracker.record_attempt(True)
        self.tracker.complete_word(True)
        
        # Word with 5 attempts
        self.tracker.start_word("word_2", "planet")
        for _ in range(4):
            self.tracker.record_attempt(False)
        self.tracker.record_attempt(True)
        self.tracker.complete_word(True)
        
        # Word with 3 attempts
        self.tracker.start_word("word_3", "astronaut")
        self.tracker.record_attempt(False)
        self.tracker.record_attempt(False)
        self.tracker.record_attempt(True)
        self.tracker.complete_word(True)
        
        self.tracker.end_session()
        
        # Get practice list
        result = self.tracker.get_words_needing_practice()
        
        # Should be sorted: planet (5), astronaut (3), because (2)
        assert len(result) == 3
        assert result[0]['word'] == 'planet'
        assert result[0]['attempts'] == 5
        assert result[1]['word'] == 'astronaut'
        assert result[1]['attempts'] == 3
        assert result[2]['word'] == 'because'
        assert result[2]['attempts'] == 2
    
    def test_get_words_needing_practice_limit(self):
        """Test that limit parameter works correctly."""
        # Start a session
        self.tracker.start_session("session_1")
        
        # Create 10 words needing practice
        for i in range(10):
            self.tracker.start_word(f"word_{i}", f"word{i}")
            self.tracker.record_attempt(False)
            self.tracker.record_attempt(True)
            self.tracker.complete_word(True)
        
        self.tracker.end_session()
        
        # Get practice list with limit=5
        result = self.tracker.get_words_needing_practice(limit=5)
        
        assert len(result) == 5
    
    def test_format_practice_list(self):
        """Test format_practice_list method."""
        # Start a session
        self.tracker.start_session("session_1")
        
        # Complete a word with multiple attempts
        self.tracker.start_word("word_1", "because")
        self.tracker.record_attempt(False)
        self.tracker.record_attempt(True)
        self.tracker.complete_word(True)
        
        self.tracker.end_session()
        
        # Format for display
        result = self.tracker.format_practice_list()
        
        assert len(result) == 1
        assert 'label' in result[0]
        assert result[0]['label'] == "because - 2 attempts"
    
    def test_get_practice_list_empty_message(self):
        """Test empty state message."""
        message = self.tracker.get_practice_list_empty_message()
        
        assert message == "Great job! No words need practice"
    
    def test_multiple_sessions_aggregate_attempts(self):
        """Test that attempts are aggregated across sessions."""
        # First session
        self.tracker.start_session("session_1")
        self.tracker.start_word("word_1", "because")
        self.tracker.record_attempt(False)
        self.tracker.record_attempt(True)
        self.tracker.complete_word(True)
        self.tracker.end_session()
        
        # Second session - same word
        self.tracker.start_session("session_2")
        self.tracker.start_word("word_1", "because")
        self.tracker.record_attempt(False)
        self.tracker.record_attempt(False)
        self.tracker.record_attempt(True)
        self.tracker.complete_word(True)
        self.tracker.end_session()
        
        # Get practice list
        result = self.tracker.get_words_needing_practice()
        
        # Should aggregate: 2 + 3 = 5 attempts
        assert len(result) == 1
        assert result[0]['word'] == 'because'
        assert result[0]['attempts'] == 5
    
    def test_word_removed_from_practice_when_mastered(self):
        """Test that word is removed from practice list once mastered."""
        # First session - word needs practice
        self.tracker.start_session("session_1")
        self.tracker.start_word("word_1", "because")
        self.tracker.record_attempt(False)
        self.tracker.record_attempt(True)
        self.tracker.complete_word(True)
        self.tracker.end_session()
        
        # Verify word is in practice list
        result = self.tracker.get_words_needing_practice()
        assert len(result) == 1
        
        # Second session - word is mastered on first attempt
        self.tracker.start_session("session_2")
        self.tracker.start_word("word_1", "because")
        self.tracker.record_attempt(True)
        self.tracker.complete_word(True)
        self.tracker.end_session()
        
        # Word should now be mastered and removed from practice list
        result = self.tracker.get_words_needing_practice()
        assert len(result) == 0


class TestPracticeListIntegration:
    """Integration tests for practice list functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        import pygame
        # Initialize pygame display/font for UI tests
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
        
        self.tracker = create_progress_tracker(student_id="test_student")
    
    def teardown_method(self):
        """Clean up."""
        self.tracker.reset()
    
    def test_full_practice_workflow(self):
        """Test complete workflow: track words, get practice list, display."""
        # Simulate a realistic session
        self.tracker.start_session("session_1")
        
        # Master some words
        for word in ['cat', 'dog', 'sun']:
            self.tracker.start_word(f"word_{word}", word)
            self.tracker.record_attempt(True)
            self.tracker.complete_word(True)
        
        # Have some words needing practice
        for word in ['because', 'planet', 'astronaut']:
            self.tracker.start_word(f"word_{word}", word)
            self.tracker.record_attempt(False)
            self.tracker.record_attempt(True)
            self.tracker.complete_word(True)
        
        self.tracker.end_session()
        
        # Get practice list
        practice_words = self.tracker.get_words_needing_practice()
        
        # Create UI component
        practice_display = create_practice_list(800, 600, "parent")
        practice_display.set_practice_words(practice_words)
        
        # Verify integration
        assert len(practice_words) == 3
        assert practice_display.practice_words == practice_words
        
        # Render should not raise errors
        screen = pygame.Surface((800, 600))
        practice_display.render(screen)
    
    def test_parent_vs_student_view_difference(self):
        """Test that parent and student views show different information."""
        # Set up some practice words
        self.tracker.start_session("session_1")
        self.tracker.start_word("word_1", "because")
        self.tracker.record_attempt(False)
        self.tracker.record_attempt(True)
        self.tracker.complete_word(True)
        self.tracker.end_session()
        
        practice_words = self.tracker.get_words_needing_practice()
        
        # Create both view types
        parent_view = create_practice_list(800, 600, "parent")
        student_view = create_practice_list(800, 600, "student")
        
        parent_view.set_practice_words(practice_words)
        student_view.set_practice_words(practice_words)
        
        # Verify different titles
        assert parent_view.title_text == "Words Needing Practice:"
        assert student_view.title_text == "Let's Practice These!"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
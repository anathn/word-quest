"""
Badge System Tests (STORY-004-03)

Unit tests for the achievement badge system.
Tests badge unlock conditions, progress tracking, and persistence.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime
import time
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.components.badge_system import (
    Badge, BadgeManager, BadgeProgress, BadgeTracker,
    Rarity, create_badge_manager
)


class TestBadge:
    """Tests for Badge dataclass."""
    
    def test_badge_creation(self):
        """Test Badge can be created from dict."""
        badge_data = {
            'id': 'speed_speller',
            'name': 'Speed Speller',
            'description': 'Complete 10 words in under 5 minutes',
            'icon_path': 'assets/badges/speed_speller.png',
            'rarity': 'common',
            'unlock_condition': '10_words_in_5_minutes',
            'color_scheme': 'yellow_blue'
        }
        
        badge = Badge.from_dict(badge_data)
        
        assert badge.id == 'speed_speller'
        assert badge.name == 'Speed Speller'
        assert badge.rarity == Rarity.COMMON
        assert badge.unlocked_at is None
    
    def test_badge_to_dict(self):
        """Test Badge serialization."""
        badge_data = {
            'id': 'speed_speller',
            'name': 'Speed Speller',
            'description': 'Complete 10 words in under 5 minutes',
            'icon_path': 'assets/badges/speed_speller.png',
            'rarity': 'common',
            'unlock_condition': '10_words_in_5_minutes',
            'color_scheme': 'yellow_blue'
        }
        
        badge = Badge.from_dict(badge_data)
        badge.unlocked_at = datetime(2026, 7, 12, 10, 30, 0)
        
        data = badge.to_dict()
        
        assert data['id'] == 'speed_speller'
        assert data['unlocked_at'] == '2026-07-12T10:30:00'
        assert data['rarity'] == 'common'


class TestBadgeProgress:
    """Tests for BadgeProgress dataclass."""
    
    def test_progress_calculation(self):
        """Test progress percentage calculation."""
        progress = BadgeProgress('test', 5, 10, False)
        
        assert progress.current == 5
        assert progress.target == 10
        assert progress.progress_percent() == 0.5
        assert progress.get_progress_text() == '5/10'
    
    def test_progress_complete(self):
        """Test progress when complete."""
        progress = BadgeProgress('test', 10, 10, True)
        
        assert progress.progress_percent() == 1.0
        assert progress.is_complete is True
    
    def test_progress_zero_target(self):
        """Test progress with zero target."""
        progress = BadgeProgress('test', 0, 0, False)
        
        # Zero target should return 0% if not complete
        assert progress.progress_percent() == 0.0


class TestBadgeManager:
    """Tests for BadgeManager class."""
    
    @pytest.fixture
    def badge_manager(self, tmp_path):
        """Create a BadgeManager for testing."""
        # Set up a temporary badge definitions file
        badge_defs = {
            'badges': [
                {
                    'id': 'speed_speller',
                    'name': 'Speed Speller',
                    'description': 'Complete 10 words in under 5 minutes',
                    'icon_path': 'assets/badges/speed_speller.png',
                    'rarity': 'common',
                    'unlock_condition': '10_words_in_5_minutes',
                    'color_scheme': 'yellow_blue'
                },
                {
                    'id': 'perseverance',
                    'name': 'Perseverance Award',
                    'description': 'Master a word after 5+ attempts',
                    'icon_path': 'assets/badges/perseverance.png',
                    'rarity': 'uncommon',
                    'unlock_condition': 'master_after_5_attempts',
                    'color_scheme': 'brown_green'
                },
                {
                    'id': 'perfect_planet',
                    'name': 'Perfect Planet',
                    'description': 'Get 5/5 correct on first attempt',
                    'icon_path': 'assets/badges/perfect_planet.png',
                    'rarity': 'rare',
                    'unlock_condition': 'perfect_planet',
                    'color_scheme': 'gold_purple'
                },
                {
                    'id': 'streak_master',
                    'name': 'Streak Master',
                    'description': 'Achieve a 10-word streak',
                    'icon_path': 'assets/badges/streak_master.png',
                    'rarity': 'rare',
                    'unlock_condition': '10_word_streak',
                    'color_scheme': 'orange_red'
                },
                {
                    'id': 'word_warrior',
                    'name': 'Word Warrior',
                    'description': 'Master 25 words total',
                    'icon_path': 'assets/badges/word_warrior.png',
                    'rarity': 'legendary',
                    'unlock_condition': '25_words_mastered',
                    'color_scheme': 'blue_silver'
                },
                {
                    'id': 'comeback_kid',
                    'name': 'Comeback Kid',
                    'description': 'Correct answer after 3+ incorrect attempts',
                    'icon_path': 'assets/badges/comeback_kid.png',
                    'rarity': 'uncommon',
                    'unlock_condition': 'correct_after_3_wrong',
                    'color_scheme': 'green_yellow'
                }
            ]
        }
        
        import json
        defs_path = os.path.join(tmp_path, 'badge_definitions.json')
        with open(defs_path, 'w') as f:
            json.dump(badge_defs, f)
        
        # Create manager
        manager = create_badge_manager(student_id='student_1')
        # Force reload definitions from tmp_path
        manager.BADGE_DEFS_PATH = defs_path
        manager._load_badge_definitions()
        
        return manager
    
    def test_badge_manager_creation(self, badge_manager):
        """Test BadgeManager initializes correctly."""
        assert badge_manager is not None
        assert len(badge_manager.badges) == 6
        assert len(badge_manager.progress) == 6
        assert badge_manager.get_unlocked_count() == 0
    
    def test_get_all_badges(self, badge_manager):
        """Test retrieving all badges."""
        badges = badge_manager.get_all_badges()
        
        assert len(badges) == 6
        badge_ids = [b.id for b in badges]
        assert 'speed_speller' in badge_ids
        assert 'perseverance' in badge_ids
        assert 'perfect_planet' in badge_ids
        assert 'streak_master' in badge_ids
        assert 'word_warrior' in badge_ids
        assert 'comeback_kid' in badge_ids
    
    def test_get_badge_by_id(self, badge_manager):
        """Test retrieving badge by ID."""
        badge = badge_manager.get_badge_by_id('speed_speller')
        
        assert badge is not None
        assert badge.name == 'Speed Speller'
        assert badge.rarity == Rarity.COMMON
    
    def test_speed_speller_unlock(self, badge_manager):
        """Test Speed Speller badge unlocks correctly."""
        badge_manager.start_session()
        
        # Simulate completing 10 words quickly
        import time
        for i in range(10):
            badge_manager.on_word_started()
            badge_manager.on_word_completed(
                attempts=1, hints_used=0, is_first_attempt_correct=True,
                completion_time=20.0  # 20 seconds per word = 3 min 20 sec total
            )
        
        # Check badge is unlocked
        assert badge_manager.is_badge_unlocked('speed_speller')
    
    def test_permalink_unlock_after_5_attempts(self, badge_manager):
        """Test Perseverance badge unlocks after 5+ attempts."""
        badge_manager.start_session()
        
        # Simulate mastering a word after 6 attempts
        badge_manager.on_word_started()
        for _ in range(5):
            badge_manager.on_incorrect_answer()
        badge_manager.on_word_completed(
            attempts=6, hints_used=2, is_first_attempt_correct=False,
            completion_time=120.0
        )
        
        # Check badge is unlocked
        assert badge_manager.is_badge_unlocked('perseverance')
    
    def test_perfect_planet_unlock(self, badge_manager):
        """Test Perfect Planet badge unlocks on perfect planet."""
        badge_manager.start_session()
        
        # Simulate perfect planet completion
        badge_manager.on_planet_completed(perfect=True)
        
        # Check badge is unlocked
        assert badge_manager.is_badge_unlocked('perfect_planet')
    
    def test_streak_master_unlock(self, badge_manager):
        """Test Streak Master badge unlocks at 10 streak."""
        badge_manager.start_session()
        
        # Simulate 10-word streak
        for i in range(10):
            badge_manager.on_correct_answer(streak=i + 1)
        
        # Check badge is unlocked
        assert badge_manager.is_badge_unlocked('streak_master')
    
    def test_word_warrior_unlock(self, badge_manager):
        """Test Word Warrior badge unlocks at 25 mastered words."""
        badge_manager.start_session()
        
        # Simulate mastering 25 words
        for i in range(25):
            badge_manager.on_word_mastered()
        
        # Check badge is unlocked
        assert badge_manager.is_badge_unlocked('word_warrior')
    
    def test_comeback_kid_unlock(self, badge_manager):
        """Test Comeback Kid badge unlocks after 3+ incorrect then correct."""
        badge_manager.start_session()
        
        # Simulate word with 3+ incorrect then correct
        badge_manager.on_word_started()
        badge_manager.on_incorrect_answer()
        badge_manager.on_incorrect_answer()
        badge_manager.on_incorrect_answer()
        # Now correct - should unlock
        badge_manager.on_incorrect_answer()  # 4th incorrect
        badge_manager.on_word_completed(
            attempts=5, hints_used=0, is_first_attempt_correct=False,
            completion_time=90.0
        )
        
        # Check badge is unlocked
        assert badge_manager.is_badge_unlocked('comeback_kid')
    
    def test_badge_not_re_unlocked(self, badge_manager):
        """Test that badges cannot be re-unlocked."""
        badge_manager.start_session()
        
        # Unlock badge once
        badge_manager.on_planet_completed(perfect=True)
        assert badge_manager.is_badge_unlocked('perfect_planet')
        
        # Try to unlock again
        badge_manager.on_planet_completed(perfect=True)
        
        # Should still be unlocked (not double-unlocked)
        assert badge_manager.get_unlocked_count() == 1
    
    def test_get_progress(self, badge_manager):
        """Test getting badge progress."""
        badge_manager.start_session()
        
        # Get progress for streak master
        progress = badge_manager.get_progress('streak_master')
        
        assert progress is not None
        assert progress.badge_id == 'streak_master'
        assert progress.target == 10
        assert progress.current == 0
    
    def test_session_start_resets_tracking(self, badge_manager):
        """Test that session start resets session-specific tracking."""
        badge_manager.start_session()
        
        # Do some tracking
        badge_manager.on_word_started()
        badge_manager.on_incorrect_answer()
        
        # Start new session
        badge_manager.start_session()
        
        # Progress tracker should be reset for session-specific badges
        assert badge_manager.tracker.speed_speller_start_time is not None
    
    def test_get_unlocked_badges(self, badge_manager):
        """Test getting only unlocked badges."""
        badge_manager.start_session()
        
        # Unlock one badge
        badge_manager.on_planet_completed(perfect=True)
        
        # Get unlocked badges
        unlocked = badge_manager.get_unlocked_badges()
        
        assert len(unlocked) == 1
        assert unlocked[0].id == 'perfect_planet'
    
    def test_get_locked_badges(self, badge_manager):
        """Test getting only locked badges."""
        badge_manager.start_session()
        
        # Unlock one badge
        badge_manager.on_planet_completed(perfect=True)
        
        # Get locked badges
        locked = badge_manager.get_locked_badges()
        
        assert len(locked) == 5  # 6 total - 1 unlocked = 5 locked
    
    def test_progress_summary(self, badge_manager):
        """Test getting progress summary for all badges."""
        badge_manager.start_session()
        
        # Unlock one and make progress on another
        badge_manager.on_planet_completed(perfect=True)
        for i in range(5):
            badge_manager.on_correct_answer(streak=i + 1)
        
        summary = badge_manager.get_progress_summary()
        
        assert 'perfect_planet' in summary
        assert summary['perfect_planet']['complete'] is True
        assert 'streak_master' in summary
        assert summary['streak_master']['current'] == 5
        assert summary['streak_master']['target'] == 10


class TestBadgeTracker:
    """Tests for BadgeTracker class."""
    
    def test_tracker_initialization(self):
        """Test BadgeTracker initializes correctly."""
        tracker = BadgeTracker()
        
        assert tracker.speed_speller_words == 0
        assert tracker.speed_speller_start_time is None
        assert tracker.current_word_attempts == 0
        assert tracker.max_word_attempts == 0
        assert tracker.perfect_planets_earned == 0
        assert tracker.total_words_mastered == 0
        assert tracker.current_word_incorrect == 0
        assert tracker.had_3plus_incorrect is False
    
    def test_speed_speller_tracking(self):
        """Test speed speller word counting."""
        tracker = BadgeTracker()
        tracker.speed_speller_start_time = time.time()
        
        tracker.speed_speller_words += 1
        tracker.speed_speller_words += 1
        
        assert tracker.speed_speller_words == 2
    
    def test_had_3plus_incorrect_flag(self):
        """Test had_3plus_incorrect flag."""
        tracker = BadgeTracker()
        
        assert tracker.had_3plus_incorrect is False
        
        tracker.current_word_incorrect = 3
        assert tracker.had_3plus_incorrect is False  # Not set yet
        
        tracker.had_3plus_incorrect = True
        assert tracker.had_3plus_incorrect is True


class TestFactoryFunction:
    """Tests for factory function."""
    
    def test_create_badge_manager(self):
        """Test factory function creates manager correctly."""
        manager = create_badge_manager(student_id='test_student')
        
        assert manager is not None
        assert manager.student_id == 'test_student'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
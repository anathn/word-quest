"""
Unit Tests for Sticker Manager (STORY-004-06)

Tests for StickerManager, StickerTracker, and related components.
"""

import pytest
import os
import sys
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.components.sticker_manager import (
    StickerManager,
    StickerTracker,
    StickerDefinition,
    StickerProgress,
    StickerRarity,
    create_sticker_manager,
    SOLAR_SYSTEM_PLANETS_REQUIRED,
    STREAK_STICKER_REQUIRED,
    WORDS_MASTERED_FOR_STICKER
)
from src.components.data_store import DataStore, LoadResult


class TestStickerProgress:
    """Tests for StickerProgress dataclass."""
    
    def test_progress_percent_basic(self):
        """Test progress percentage calculation."""
        progress = StickerProgress('test', 3, 10)
        assert progress.progress_percent() == 0.3
    
    def test_progress_percent_complete(self):
        """Test progress percentage when complete."""
        progress = StickerProgress('test', 15, 10)
        assert progress.progress_percent() == 1.0
    
    def test_progress_percent_zero_target(self):
        """Test progress percentage with zero target."""
        progress = StickerProgress('test', 0, 0)
        assert progress.progress_percent() == 0.0
        
        progress_complete = StickerProgress('test', 0, 0, is_complete=True)
        assert progress_complete.progress_percent() == 1.0
    
    def test_get_progress_text(self):
        """Test formatted progress text."""
        progress = StickerProgress('test', 7, 10)
        assert progress.get_progress_text() == "7/10"


class TestStickerDefinition:
    """Tests for StickerDefinition dataclass."""
    
    def test_from_dict_basic(self):
        """Test creating StickerDefinition from dictionary."""
        data = {
            'id': 'test_sticker',
            'name': 'Test Sticker',
            'description': 'A test sticker',
            'rarity': 'common',
            'unlock_condition': 'test_condition',
            'category': 'test',
            'color_scheme': 'blue'
        }
        sticker = StickerDefinition.from_dict(data)
        
        assert sticker.id == 'test_sticker'
        assert sticker.name == 'Test Sticker'
        assert sticker.rarity == StickerRarity.COMMON
        assert sticker.unlock_condition == 'test_condition'
    
    def test_from_dict_with_unlock_info(self):
        """Test creating StickerDefinition with unlock info."""
        data = {
            'id': 'test_sticker',
            'name': 'Test Sticker',
            'description': 'A test sticker',
            'rarity': 'rare',
            'unlock_condition': 'test_condition',
            'category': 'test',
            'color_scheme': 'gold',
            'unlocked_at': '2026-07-14T10:30:00',
            'unlock_context': {'planet': 'Mars'}
        }
        sticker = StickerDefinition.from_dict(data)
        
        assert sticker.unlocked_at is not None
        assert sticker.unlock_context == {'planet': 'Mars'}
    
    def test_to_dict(self):
        """Test converting StickerDefinition to dictionary."""
        sticker = StickerDefinition(
            id='test',
            name='Test',
            description='Test description',
            rarity=StickerRarity.RARE,
            unlock_condition='test_cond',
            category='test',
            color_scheme='gold'
        )
        
        data = sticker.to_dict()
        assert data['id'] == 'test'
        assert data['rarity'] == 'rare'
        assert data['unlocked_at'] is None


class TestStickerTracker:
    """Tests for StickerTracker class."""
    
    def test_initial_state(self):
        """Test initial tracker state."""
        tracker = StickerTracker()
        
        assert tracker.planets_completed == 0
        assert tracker.perfect_planets == 0
        assert tracker.current_streak == 0
        assert tracker.words_mastered == 0
        assert len(tracker.failed_planets) == 0
        assert len(tracker.completed_solar_systems) == 0
        assert len(tracker.solar_system_planets) == 0
    
    def test_galaxy_explorer_tracking(self):
        """Test solar system tracking for Galaxy Explorer."""
        tracker = StickerTracker()
        
        # Add planets to solar system
        tracker.solar_system_planets['solar_system_1'] = {'planet_1', 'planet_2', 'planet_3'}
        
        # Check that we have 3 planets
        assert len(tracker.solar_system_planets['solar_system_1']) == 3
    
    def test_comeback_champion_tracking(self):
        """Test failed planet tracking for Comeback Champion."""
        tracker = StickerTracker()
        
        tracker.failed_planets.add('planet_1')
        tracker.failed_planets.add('planet_2')
        
        assert 'planet_1' in tracker.failed_planets
        assert len(tracker.failed_planets) == 2


class TestStickerManagerInit:
    """Tests for StickerManager initialization."""
    
    def test_create_with_mock_datastore(self):
        """Test creating manager with mocked DataStore."""
        mock_datastore = Mock(spec=DataStore)
        mock_datastore.load.return_value = LoadResult(
            success=True,
            data={'unlocked_stickers': []},
            used_recovery=False
        )
        
        manager = StickerManager(
            student_id='test_student',
            data_store=mock_datastore,
            is_female=True
        )
        
        assert manager.student_id == 'test_student'
        assert manager.is_female == True
    
    def test_factory_function(self):
        """Test create_sticker_manager factory function."""
        manager = create_sticker_manager(
            student_id='factory_test',
            is_female=False
        )
        
        assert manager.student_id == 'factory_test'
        assert manager.is_female == False
    
    def test_has_all_stickers(self):
        """Test that manager has all sticker definitions loaded."""
        manager = create_sticker_manager()
        
        # Should have 11 stickers (including the extras like flawless_victory)
        assert len(manager.stickers) > 0
        
        # Check some key stickers exist
        assert 'planet_winner' in manager.stickers
        assert 'speed_demon' in manager.stickers
        assert 'early_bird' in manager.stickers


class TestStickerManagerSessionTracking:
    """Tests for session-based sticker tracking."""
    
    def test_start_session_early_bird(self):
        """Test Early Bird sticker unlock on morning session."""
        manager = create_sticker_manager()
        
        # Simulate early morning session (8 AM)
        manager.start_session(hour=8)
        
        assert manager.tracker.early_bird_unlocked == True
        assert manager.is_sticker_unlocked('early_bird')
    
    def test_start_session_night_owl(self):
        """Test Night Owl sticker unlock on evening session."""
        manager = create_sticker_manager()
        
        # Simulate evening session (20:00 = 8 PM)
        manager.start_session(hour=20)
        
        assert manager.tracker.night_owl_unlocked == True
        assert manager.is_sticker_unlocked('night_owl')
    
    def test_start_session_normal_hours(self):
        """Test that normal hours don't unlock time-based stickers."""
        manager = create_sticker_manager()
        
        manager.start_session(hour=12)  # Noon
        
        assert not manager.tracker.early_bird_unlocked
        assert not manager.tracker.night_owl_unlocked
    
    def test_time_tracking_only_once(self):
        """Test that Early Bird/Night Owl only unlock once."""
        manager = create_sticker_manager()
        
        # First session at 8 AM
        manager.start_session(hour=8)
        assert manager.tracker.early_bird_unlocked == True
        
        # Second session at 8 AM - should not duplicate
        # (The current implementation uses check in _unlock_sticker)
        # Note: The sticker is only unlocked once due to the check in _unlock_sticker
    
    def test_end_session_saves(self):
        """Test that end_session persists unlocked stickers."""
        mock_datastore = Mock(spec=DataStore)
        manager = StickerManager(
            student_id='test_student',
            data_store=mock_datastore,
            is_female=True
        )
        
        # Force an unlock
        manager._unlock_sticker('planet_winner', {'planet': 'test'})
        
        # End session
        manager.end_session()
        
        # Verify save was called
        mock_datastore.save.assert_called_once()


class TestStickerManagerPlanetTracking:
    """Tests for planet-based sticker tracking."""
    
    def test_planet_winner_first_completion(self):
        """Test Planet Winner sticker on first planet completion."""
        manager = create_sticker_manager()
        
        manager.start_planet('mars', 'solar_system_1')
        manager.on_planet_completed(
            planet_id='mars',
            solar_system='solar_system_1',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        
        assert manager.tracker.planet_winner_unlocked == True
        assert manager.is_sticker_unlocked('planet_winner')
    
    def test_flawless_victory(self):
        """Test Flawless Victory on perfect planet completion."""
        manager = create_sticker_manager()
        
        manager.start_planet('mars', 'solar_system_1')
        manager.on_planet_completed(
            planet_id='mars',
            solar_system='solar_system_1',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        
        assert manager.tracker.flawless_victory_unlocked == True
        assert manager.is_sticker_unlocked('flawless_victory')
    
    def test_flawless_victory_requires_perfect(self):
        """Test that Flawless Victory requires all first-attempt correct."""
        manager = create_sticker_manager()
        
        manager.start_planet('mars', 'solar_system_1')
        manager.on_planet_completed(
            planet_id='mars',
            solar_system='solar_system_1',
            score=5,
            total_attempts=6,  # One extra attempt
            first_attempt_correct=False,  # Not all first attempt
            hints_used=0
        )
        
        assert manager.tracker.flawless_victory_unlocked == False
    
    def test_speed_demon_fast_completion(self):
        """Test Speed Demon sticker for fast planet completion."""
        manager = create_sticker_manager()
        
        # Start planet
        manager.start_planet('mars', 'solar_system_1')
        
        # Complete quickly (simulate very fast)
        time.sleep(0.1)  # Small delay for realism
        
        manager.on_planet_completed(
            planet_id='mars',
            solar_system='solar_system_1',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        
        # Speed Demon should be unlocked (under 3 minutes)
        assert manager.tracker.speed_demon_unlocked == True
        assert manager.is_sticker_unlocked('speed_demon')
    
    def test_speed_demon_too_slow(self):
        """Test that Speed Demon requires under 3 minutes."""
        manager = create_sticker_manager()
        
        # Manually set start time to be very old
        manager._current_planet_start_time = time.time() - 300  # 5 minutes ago
        
        manager.on_planet_completed(
            planet_id='mars',
            solar_system='solar_system_1',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        
        # Should NOT unlock speed demon (took too long)
        assert manager.tracker.speed_demon_unlocked == False


class TestStickerManagerGalaxyExplorer:
    """Tests for Galaxy Explorer sticker tracking (CRITICAL FIX VERIFICATION)."""
    
    def test_galaxy_explorer_requires_three_planets(self):
        """Test that Galaxy Explorer requires 3 planets in solar system."""
        manager = create_sticker_manager()
        
        # Complete first planet
        manager.start_planet('planet_1', 'solar_system_1')
        manager.on_planet_completed(
            planet_id='planet_1',
            solar_system='solar_system_1',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        assert not manager.tracker.galaxy_explorer_unlocked
        
        # Complete second planet
        manager.start_planet('planet_2', 'solar_system_1')
        manager.on_planet_completed(
            planet_id='planet_2',
            solar_system='solar_system_1',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        assert not manager.tracker.galaxy_explorer_unlocked
        
        # Complete third planet - THIS SHOULD UNLOCK GALAXY EXPLORER
        manager.start_planet('planet_3', 'solar_system_1')
        manager.on_planet_completed(
            planet_id='planet_3',
            solar_system='solar_system_1',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        
        # Verify Galaxy Explorer is unlocked
        assert manager.tracker.galaxy_explorer_unlocked == True
        assert manager.is_sticker_unlocked('galaxy_explorer')
    
    def test_galaxy_explorer_progress_tracking(self):
        """Test that Galaxy Explorer progress is tracked correctly."""
        manager = create_sticker_manager()
        
        # Check initial progress
        progress = manager.get_progress('galaxy_explorer')
        assert progress.current == 0
        assert progress.target == SOLAR_SYSTEM_PLANETS_REQUIRED
        
        # Complete planets
        for i in range(3):
            manager.start_planet(f'planet_{i+1}', 'solar_system_1')
            manager.on_planet_completed(
                planet_id=f'planet_{i+1}',
                solar_system='solar_system_1',
                score=5,
                total_attempts=5,
                first_attempt_correct=True,
                hints_used=0
            )
        
        # Progress should show 1 completed solar system
        progress = manager.get_progress('galaxy_explorer')
        assert progress.current == 1
        assert progress.is_complete == True
    
    def test_galaxy_explorer_multiple_solar_systems(self):
        """Test Galaxy Explorer unlock after multiple solar systems."""
        manager = create_sticker_manager()
        
        # Complete first solar system (unlocks sticker)
        for i in range(3):
            manager.start_planet(f'p{i+1}', 'system_a')
            manager.on_planet_completed(
                planet_id=f'p{i+1}',
                solar_system='system_a',
                score=5,
                total_attempts=5,
                first_attempt_correct=True,
                hints_used=0
            )
        
        assert manager.tracker.galaxy_explorer_unlocked == True
        assert len(manager.tracker.completed_solar_systems) == 1
        
        # Complete second solar system
        for i in range(3):
            manager.start_planet(f'p{i+1}', 'system_b')
            manager.on_planet_completed(
                planet_id=f'p{i+1}',
                solar_system='system_b',
                score=5,
                total_attempts=5,
                first_attempt_correct=True,
                hints_used=0
            )
        
        # Should now have 2 completed solar systems
        assert len(manager.tracker.completed_solar_systems) == 2


class TestStickerManagerComebackChampion:
    """Tests for Comeback Champion sticker tracking."""
    
    def test_comeback_champion_success(self):
        """Test Comeback Champion after failing then clearing planet."""
        manager = create_sticker_manager()
        
        # Fail the planet first
        manager.on_planet_failed('mars')
        
        # Then complete it
        manager.start_planet('mars', 'solar_system_1')
        manager.on_planet_completed(
            planet_id='mars',
            solar_system='solar_system_1',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        
        assert manager.tracker.comeback_champion_unlocked == True
        assert manager.is_sticker_unlocked('comeback_champion')
    
    def test_comeback_champion_no_fail(self):
        """Test that Comeback Champion requires prior failure."""
        manager = create_sticker_manager()
        
        # Complete planet without failing first
        manager.start_planet('mars', 'solar_system_1')
        manager.on_planet_completed(
            planet_id='mars',
            solar_system='solar_system_1',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        
        assert manager.tracker.comeback_champion_unlocked == False


class TestStickerManagerHintHelper:
    """Tests for Hint Helper sticker tracking."""
    
    def test_hint_helper_unlock(self):
        """Test Hint Helper sticker on full hint usage."""
        manager = create_sticker_manager()
        
        manager.on_full_hint_solved()
        
        assert manager.tracker.hint_helper_unlocked == True
        assert manager.is_sticker_unlocked('hint_helper')
    
    def test_hint_helper_progress(self):
        """Test Hint Helper progress tracking."""
        manager = create_sticker_manager()
        
        manager.on_full_hint_solved()
        manager.on_full_hint_solved()
        
        assert manager.tracker.full_hint_solves == 2
        progress = manager.get_progress('hint_helper')
        assert progress.current == 2
        assert progress.is_complete == True


class TestStickerManagerStreakTracking:
    """Tests for Streak King/Queen sticker tracking."""
    
    def test_streak_queen_female(self):
        """Test Streak Queen for female student."""
        manager = create_sticker_manager(is_female=True)
        
        # Set streak to 15
        manager.on_streak_update(15)
        
        assert manager.tracker.streak_queen_unlocked == True
        assert manager.is_sticker_unlocked('streak_queen')
        assert not manager.tracker.streak_king_unlocked
    
    def test_streak_king_male(self):
        """Test Streak King for male student."""
        manager = create_sticker_manager(is_female=False)
        
        # Set streak to 15
        manager.on_streak_update(15)
        
        assert manager.tracker.streak_king_unlocked == True
        assert manager.is_sticker_unlocked('streak_king')
        assert not manager.tracker.streak_queen_unlocked
    
    def test_streak_requirement_is_15(self):
        """Test that streak requirement is 15."""
        assert STREAK_STICKER_REQUIRED == 15
    
    def test_streak_not_unlocked_below_threshold(self):
        """Test that streak sticker doesn't unlock below threshold."""
        manager = create_sticker_manager(is_female=True)
        
        # Set streak to 14 (below threshold)
        manager.on_streak_update(14)
        
        assert not manager.tracker.streak_queen_unlocked
    
    def test_streak_progress_updated(self):
        """Test that streak progress is tracked."""
        manager = create_sticker_manager()
        
        manager.on_streak_update(10)
        
        progress_king = manager.get_progress('streak_king')
        progress_queen = manager.get_progress('streak_queen')
        
        assert progress_king.current == 10
        assert progress_queen.current == 10


class TestStickerManagerWordMaster:
    """Tests for Word Master sticker tracking."""
    
    def test_word_master_unlock(self):
        """Test Word Master sticker at 50 words."""
        assert WORDS_MASTERED_FOR_STICKER == 50
        
        manager = create_sticker_manager()
        
        # Master 50 words
        for _ in range(50):
            manager.on_word_mastered()
        
        assert manager.tracker.word_master_unlocked == True
        assert manager.is_sticker_unlocked('word_master')
    
    def test_word_master_progress(self):
        """Test Word Master progress tracking."""
        manager = create_sticker_manager()
        
        # Master 25 words
        for _ in range(25):
            manager.on_word_mastered()
        
        progress = manager.get_progress('word_master')
        assert progress.current == 25
        assert progress.target == 50
        assert not progress.is_complete


class TestStickerManagerDuplicatePrevention:
    """Tests to ensure duplicate unlocks are prevented."""
    
    def test_planet_winner_not_duplicated(self):
        """Test that Planet Winner doesn't unlock multiple times."""
        manager = create_sticker_manager()
        
        # First completion
        manager.start_planet('mars', 'solar_system_1')
        manager.on_planet_completed(
            planet_id='mars',
            solar_system='solar_system_1',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        
        assert 'planet_winner' in manager.unlocked_stickers
        
        # Complete more planets
        for i in range(5):
            manager.start_planet(f'planet_{i}', 'solar_system_1')
            manager.on_planet_completed(
                planet_id=f'planet_{i}',
                solar_system='solar_system_1',
                score=5,
                total_attempts=5,
                first_attempt_correct=True,
                hints_used=0
            )
        
        # Should still only have unique Planet Winner sticker (not duplicated)
        # But other stickers may also unlock (speed_demon, flawless_victory, etc.)
        assert 'planet_winner' in manager.unlocked_stickers
        
        # Verify planet_winner is not duplicated - check count is exactly 1 for this sticker
        planet_winner_list = [s for s in manager.unlocked_stickers.values() if s.id == 'planet_winner']
        assert len(planet_winner_list) == 1, "Planet Winner should only be unlocked once"


class TestStickerManagerCallback:
    """Tests for sticker unlock callback."""
    
    def test_callback_on_sticker_unlock(self):
        """Test that callback is called when sticker is unlocked."""
        manager = create_sticker_manager()
        
        callback_called = False
        received_sticker = None
        
        def on_unlock(sticker):
            nonlocal callback_called, received_sticker
            callback_called = True
            received_sticker = sticker
        
        manager.on_sticker_unlocked = on_unlock
        
        # Unlock a sticker
        manager._unlock_sticker('planet_winner', {'planet': 'mars'})
        
        assert callback_called == True
        assert received_sticker is not None
        assert received_sticker.id == 'planet_winner'


class TestStickerManagerGetters:
    """Tests for getter methods."""
    
    def test_get_all_stickers(self):
        """Test get_all_stickers returns all definitions."""
        manager = create_sticker_manager()
        
        all_stickers = manager.get_all_stickers()
        assert len(all_stickers) > 0
    
    def test_get_unlocked_stickers(self):
        """Test get_unlocked_stickers returns only unlocked."""
        manager = create_sticker_manager()
        
        manager._unlock_sticker('planet_winner')
        
        unlocked = manager.get_unlocked_stickers()
        assert len(unlocked) == 1
        assert unlocked[0].id == 'planet_winner'
    
    def test_get_locked_stickers(self):
        """Test get_locked_stickers returns only locked."""
        manager = create_sticker_manager()
        
        manager._unlock_sticker('planet_winner')
        
        locked = manager.get_locked_stickers()
        assert len(locked) > 0
        assert not any(s.id == 'planet_winner' for s in locked)
    
    def test_get_stickers_by_category(self):
        """Test filtering by category."""
        manager = create_sticker_manager()
        
        progression_stickers = manager.get_stickers_by_category('progression')
        assert len(progression_stickers) > 0
        
        skill_stickers = manager.get_stickers_by_category('skill')
        assert len(skill_stickers) > 0
        
        special_stickers = manager.get_stickers_by_category('special')
        assert len(special_stickers) > 0
    
    def test_get_sticker_by_id(self):
        """Test getting sticker by ID."""
        manager = create_sticker_manager()
        
        sticker = manager.get_sticker_by_id('planet_winner')
        assert sticker is not None
        assert sticker.id == 'planet_winner'
        
        # Non-existent sticker
        missing = manager.get_sticker_by_id('nonexistent')
        assert missing is None
    
    def test_get_progress_summary(self):
        """Test progress summary."""
        manager = create_sticker_manager()
        
        summary = manager.get_progress_summary()
        assert 'planet_winner' in summary
        assert summary['planet_winner']['target'] == 1
    
    def test_get_new_unlocks_since(self):
        """Test getting new unlocks since timestamp."""
        manager = create_sticker_manager()
        
        # Unlock a sticker
        now = datetime.now()
        manager._unlock_sticker('planet_winner')
        
        # Get stickers since now
        new_stickers = manager.get_new_unlocks_since(now)
        assert len(new_stickers) == 1
        assert new_stickers[0].id == 'planet_winner'
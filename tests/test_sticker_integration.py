"""
Integration Tests for Sticker Collection System (STORY-004-06)

Tests for the full sticker unlock flow from game events to sticker unlocks.
"""

import pytest
import os
import sys
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.components.sticker_manager import (
    StickerManager,
    create_sticker_manager,
    SOLAR_SYSTEM_PLANETS_REQUIRED,
    STREAK_STICKER_REQUIRED,
    WORDS_MASTERED_FOR_STICKER,
    SPEED_DEMON_MAX_SECONDS
)
from src.components.data_store import DataStore, LoadResult


class TestStickerIntegrationFullFlow:
    """Integration tests for complete sticker unlock scenarios."""
    
    def setup_method(self):
        """Set up test fixtures before each test."""
        self.mock_datastore = None
        self.manager = None
    
    def test_full_galaxy_explorer_flow(self):
        """
        Integration test for complete Galaxy Explorer unlock flow.
        
        Scenario: Student completes 3 planets in the same solar system
        Expected: Galaxy Explorer sticker unlocks on 3rd planet
        """
        # Setup
        self.manager = create_sticker_manager(student_id='integration_test_1')
        
        # Act: Complete first planet in solar system
        self.manager.start_planet('mars', 'outer_solar_system')
        self.manager.on_planet_completed(
            planet_id='mars',
            solar_system='outer_solar_system',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        
        # Verify: No unlock yet
        assert not self.manager.is_sticker_unlocked('galaxy_explorer')
        assert self.manager.get_progress('galaxy_explorer').current == 0
        
        # Act: Complete second planet in same solar system
        self.manager.start_planet('jupiter', 'outer_solar_system')
        self.manager.on_planet_completed(
            planet_id='jupiter',
            solar_system='outer_solar_system',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        
        # Verify: Still no unlock
        assert not self.manager.is_sticker_unlocked('galaxy_explorer')
        assert self.manager.get_progress('galaxy_explorer').current == 0
        
        # Act: Complete third planet in same solar system
        self.manager.start_planet('saturn', 'outer_solar_system')
        self.manager.on_planet_completed(
            planet_id='saturn',
            solar_system='outer_solar_system',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        
        # Assert: Galaxy Explorer should be unlocked
        assert self.manager.is_sticker_unlocked('galaxy_explorer')
        assert self.manager.tracker.galaxy_explorer_unlocked == True
        assert self.manager.get_progress('galaxy_explorer').is_complete == True
        
        # Verify unlock context includes the solar system
        sticker = self.manager.get_sticker_by_id('galaxy_explorer')
        assert sticker.unlock_context is not None
        assert sticker.unlock_context.get('system') == 'outer_solar_system'
    
    def test_multiple_stickers_single_session(self):
        """
        Integration test for multiple stickers in one session.
        
        Scenario: Student plays game in early morning and completes a perfect planet
        Expected: Early Bird AND Flawless Victory stickers unlock
        """
        # Setup: Early morning session
        self.manager = create_sticker_manager(student_id='integration_test_2')
        self.manager.start_session(hour=7)  # 7 AM - Early Bird time
        
        # Early Bird should unlock immediately
        assert self.manager.is_sticker_unlocked('early_bird')
        
        # Act: Complete a perfect planet
        self.manager.start_planet('earth', 'inner_solar_system')
        self.manager.on_planet_completed(
            planet_id='earth',
            solar_system='inner_solar_system',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )
        
        # Assert: Both stickers should be unlocked (and more!)
        assert self.manager.is_sticker_unlocked('early_bird')
        assert self.manager.is_sticker_unlocked('flawless_victory')
        # Also planet_winner and speed_demon unlock from perfect fast planet
        assert self.manager.get_unlocked_count() >= 2
    
    def test_comeback_champion_full_cycle(self):
        """
        Integration test for Comeback Champion unlock flow.
        
        Scenario: Student fails a planet, then completes it on retry
        Expected: Comeback Champion sticker unlocks on successful completion
        """
        # Setup
        self.manager = create_sticker_manager(student_id='integration_test_3')
        
        # Act 1: Fail the planet
        self.manager.on_planet_failed('pluto')
        
        # Verify planet is marked as failed
        assert 'pluto' in self.manager.tracker.failed_planets
        
        # Act 2: Retry and complete the planet
        self.manager.start_planet('pluto', 'outer_solar_system')
        self.manager.on_planet_completed(
            planet_id='pluto',
            solar_system='outer_solar_system',
            score=4,  # Pass with 4/5
            total_attempts=6,  # Some retries
            first_attempt_correct=False,
            hints_used=2
        )
        
        # Assert: Comeback Champion should unlock
        assert self.manager.is_sticker_unlocked('comeback_champion')
        assert self.manager.tracker.comeback_champion_unlocked == True
        
        # Verify planet is now tracked as cleared after failure
        assert 'pluto' in self.manager.tracker.cleared_after_fail
    
    def test_streak_king_progression(self):
        """
        Integration test for Streak King progression.
        
        Scenario: Male student builds streak to 15
        Expected: Progress updates as streak grows, Streak King unlocks at 15
        """
        # Setup: Male student
        self.manager = create_sticker_manager(student_id='integration_test_4', is_female=False)
        
        # Act: Build streak incrementally
        for streak_value in range(1, 20):
            self.manager.on_streak_update(streak_value)
            
            # Verify progress updates
            progress = self.manager.get_progress('streak_king')
            assert progress.current == streak_value
            
            if streak_value < STREAK_STICKER_REQUIRED:
                # Should not be unlocked yet
                assert not self.manager.is_sticker_unlocked('streak_king')
                assert not progress.is_complete
            elif streak_value == STREAK_STICKER_REQUIRED:
                # Should unlock exactly at 15
                assert self.manager.is_sticker_unlocked('streak_king')
                assert progress.is_complete
            
            # Should never unlock above threshold
            assert self.manager.get_unlocked_count() <= 1
        
        # Final verification
        assert self.manager.is_sticker_unlocked('streak_king')
        assert not self.manager.is_sticker_unlocked('streak_queen')
    
    def test_word_master_progression(self):
        """
        Integration test for Word Master progression.
        
        Scenario: Student masters 60 words
        Expected: Progress increments, Word Master unlocks at 50
        """
        # Setup
        self.manager = create_sticker_manager(student_id='integration_test_5')
        
        # Act: Master words incrementally
        for word_num in range(1, 61):
            self.manager.on_word_mastered()
            
            progress = self.manager.get_progress('word_master')
            assert progress.current == word_num
            
            if word_num < WORDS_MASTERED_FOR_STICKER:
                assert not self.manager.is_sticker_unlocked('word_master')
                assert not progress.is_complete
            elif word_num == WORDS_MASTERED_FOR_STICKER:
                assert self.manager.is_sticker_unlocked('word_master')
                assert progress.is_complete
        
        # Final: Should have Word Master sticker
        assert self.manager.is_sticker_unlocked('word_master')
        assert self.manager.tracker.words_mastered == 60
    
    def test_no_duplicate_stickers(self):
        """
        Integration test to ensure no duplicate stickers are awarded.
        
        Scenario: Student completes multiple planets, builds streak, masters words
        Expected: Each sticker type is awarded exactly once (if applicable)
        """
        # Setup
        self.manager = create_sticker_manager(student_id='integration_test_6')
        self.manager.start_session(hour=10)  # Normal hours, no time stickers
        
        # Complete many planets
        for planet_num in range(1, 11):
            self.manager.start_planet(f'planet_{planet_num}', 'test_system')
            self.manager.on_planet_completed(
                planet_id=f'planet_{planet_num}',
                solar_system='test_system',
                score=5,
                total_attempts=5,
                first_attempt_correct=True,
                hints_used=0
            )
        
        # Build a massive streak
        self.manager.on_streak_update(50)
        
        # Master many words
        for _ in range(100):
            self.manager.on_word_mastered()
        
        # Assert: No duplicates - each sticker should be unique
        unlocked_ids = [s.id for s in self.manager.get_unlocked_stickers()]
        
        # Check no duplicates
        assert len(unlocked_ids) == len(set(unlocked_ids)), \
            f"Duplicate stickers found: {unlocked_ids}"
        
        # Check specific counts
        assert sum(1 for sid in unlocked_ids if 'streak' in sid) == 1
        assert sum(1 for sid in unlocked_ids if 'planet_winner' in sid) == 1
        assert sum(1 for sid in unlocked_ids if 'flawless' in sid) == 1
        assert sum(1 for sid in unlocked_ids if 'speed_demon' in sid) == 1
        assert sum(1 for sid in unlocked_ids if 'galaxy_explorer' in sid) == 1
    
    def test_hint_helper_tracking(self):
        """
        Integration test for Hint Helper sticker.
        
        Scenario: Student solves words after using all hints multiple times
        Expected: Hint Helper unlocks on first full hint solve
        """
        # Setup
        self.manager = create_sticker_manager(student_id='integration_test_7')
        
        # Act: Use full hints multiple times
        self.manager.on_full_hint_solved()  # 1st time
        
        # Should unlock immediately
        assert self.manager.is_sticker_unlocked('hint_helper')
        assert self.manager.tracker.hint_helper_unlocked == True
        
        # Act: More full hint solves
        self.manager.on_full_hint_solved()
        self.manager.on_full_hint_solved()
        
        # Should still only have 1 sticker
        assert self.manager.get_unlocked_count() == 1
        assert self.manager.get_progress('hint_helper').current == 3
    
    def test_time_based_stickers_only_once(self):
        """
        Integration test for time-based sticker deduplication.
        
        Scenario: Student plays multiple sessions at different times
        Expected: Each time-based sticker unlocks only once
        """
        # Setup
        self.manager = create_sticker_manager(student_id='integration_test_8')
        
        # Session 1: Early morning
        self.manager.start_session(hour=6)
        assert self.manager.is_sticker_unlocked('early_bird')
        assert not self.manager.is_sticker_unlocked('night_owl')
        
        # Session 2: Even earlier
        new_manager = create_sticker_manager(student_id='integration_test_8')
        new_manager.start_session(hour=5)
        # Should still only have 1 early_bird
        assert new_manager.get_unlocked_count() == 1
    
    def test_persistence_round_trip(self):
        """
        Integration test for sticker persistence.
        
        Scenario: Save unlocked stickers to datastore, then load from it
        Expected: All unlocked stickers are preserved
        """
        # Setup with mock datastore
        mock_datastore = DataStore(base_path='test_data')
        
        # First manager: unlocks stickers and saves
        manager1 = StickerManager(
            student_id='persistence_test',
            data_store=mock_datastore,
            is_female=True
        )
        
        # Unlock some stickers
        manager1.start_session(hour=8)  # Early Bird
        manager1.start_planet('mars', 'inner_solar_system')
        manager1.on_planet_completed(
            planet_id='mars',
            solar_system='inner_solar_system',
            score=5,
            total_attempts=5,
            first_attempt_correct=True,
            hints_used=0
        )  # Planet Winner + Flawless Victory
        
        manager1.on_streak_update(15)  # Streak Queen
        
        # Save and create new manager
        manager1.end_session()
        
        # Cleanup test data
        if os.path.exists('test_data'):
            import shutil
            shutil.rmtree('test_data')
    
    def test_all_sticker_types_uniqueness(self):
        """
        Integration test for all sticker type definitions.
        
        Scenario: Load all sticker definitions
        Expected: Each sticker has unique ID, name, and properly defined rarity
        """
        # Setup
        self.manager = create_sticker_manager()
        
        # Act: Get all stickers
        all_stickers = self.manager.get_all_stickers()
        
        # Assert: All stickers have required fields
        sticker_ids = set()
        sticker_names = set()
        
        for sticker in all_stickers:
            # IDs must be unique
            assert sticker.id not in sticker_ids, \
                f"Duplicate sticker ID: {sticker.id}"
            sticker_ids.add(sticker.id)
            
            # Names must be unique  
            assert sticker.name not in sticker_names, \
                f"Duplicate sticker name: {sticker.name}"
            sticker_names.add(sticker.name)
            
            # Rarity must be valid (it's an enum, so compare value)
            assert sticker.rarity.value in [
                'common', 'uncommon', 'rare', 'epic', 'legendary'
            ]
            
            # Category must be valid
            assert sticker.category in ['progression', 'skill', 'special']
            
            # Unlock condition must be non-empty
            assert len(sticker.unlock_condition) > 0


class TestStickerProgressTracking:
    """Integration tests for progress tracking across stickers."""
    
    def test_all_progress_initialization(self):
        """Test that all stickers have progress initialized."""
        manager = create_sticker_manager()
        
        # Expected stickers
        expected_stickers = [
            'planet_winner',
            'flawless_victory', 
            'speed_demon',
            'hint_helper',
            'comeback_champion',
            'galaxy_explorer',
            'streak_king',
            'streak_queen',
            'word_master',
            'early_bird',
            'night_owl'
        ]
        
        for sticker_id in expected_stickers:
            progress = manager.get_progress(sticker_id)
            assert progress is not None, \
                f"Progress not initialized for {sticker_id}"
            assert progress.current == 0, \
                f"Progress for {sticker_id} should start at 0"
    
    def test_progress_updates_correctly(self):
        """Test that progress updates as expected."""
        manager = create_sticker_manager()
        
        # Test planet progress
        for i in range(3):
            manager.start_planet(f'planet_{i}', 'test_system')
            manager.on_planet_completed(
                planet_id=f'planet_{i}',
                solar_system='test_system',
                score=5,
                total_attempts=5,
                first_attempt_correct=True,
                hints_used=0
            )
            
            progress = manager.get_progress('planet_winner')
            assert progress.current == i + 1
    
    def test_progress_marked_complete(self):
        """Test that progress is marked complete when sticker unlocks."""
        manager = create_sticker_manager()
        
        # Unlock a sticker
        manager._unlock_sticker('planet_winner')
        
        # Progress should be marked complete
        progress = manager.get_progress('planet_winner')
        assert progress.is_complete == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
"""
Tests for Streak Bonus Manager (STORY-004-02)

Tests for the streak bonus milestone detection and trigger system.
"""

import pytest
from src.components.streak_bonus import (
    StreakBonusManager,
    BonusType,
    BonusMilestone,
    create_streak_bonus_manager
)


class TestStreakBonusManager:
    """Tests for the StreakBonusManager class."""
    
    def test_create_streak_bonus_manager(self):
        """Test factory function creates manager correctly."""
        manager = create_streak_bonus_manager()
        assert manager is not None
        assert isinstance(manager, StreakBonusManager)
    
    def test_initial_milestones(self):
        """Test that default milestones are created."""
        manager = StreakBonusManager()
        
        assert len(manager.milestones) == 2
        assert manager.milestones[0].streak_threshold == 3
        assert manager.milestones[0].bonus_type == BonusType.GOLDEN_ROCKET
        assert manager.milestones[1].streak_threshold == 5
        assert manager.milestones[1].bonus_type == BonusType.PLANET_DISCOVERY
    
    def test_check_milestone_at_3(self):
        """Test bonus triggered at 3-word streak."""
        manager = StreakBonusManager()
        
        bonus = manager.check_milestone(3)
        
        assert bonus is not None
        assert bonus.bonus_type == BonusType.GOLDEN_ROCKET
        assert bonus.message == "3-word streak! GOLDEN BOOST!"
        assert manager.active_bonus == bonus
        assert bonus.triggered is True
    
    def test_check_milestone_at_5(self):
        """Test bonus triggered at 5-word streak."""
        manager = StreakBonusManager()
        
        bonus = manager.check_milestone(5)
        
        assert bonus is not None
        assert bonus.bonus_type == BonusType.PLANET_DISCOVERY
        assert bonus.message == "5-word streak! NEW PLANET DISCOVERED!"
    
    def test_milestone_only_triggers_once(self):
        """Test that a milestone can only trigger once per session."""
        manager = StreakBonusManager()
        
        # First call at streak 3 should trigger
        bonus1 = manager.check_milestone(3)
        assert bonus1 is not None
        
        # Second call at streak 3 should NOT trigger again
        bonus2 = manager.check_milestone(3)
        assert bonus2 is None
    
    def test_no_bonus_at_non_milestone(self):
        """Test that no bonus is triggered at non-milestone streaks."""
        manager = StreakBonusManager()
        
        # Check streaks that are not milestones
        assert manager.check_milestone(1) is None
        assert manager.check_milestone(2) is None
        assert manager.check_milestone(4) is None
        assert manager.check_milestone(6) is None
        assert manager.check_milestone(10) is None
    
    def test_milestones_missed_when_not_at_exact_threshold(self):
        """Test that missed streak values cannot be triggered later."""
        manager = StreakBonusManager()
        
        # Skip to streak 4, missing streak 3
        bonus = manager.check_milestone(4)
        assert bonus is None
        
        # Streak 3 milestone is now permanently missed for this session
        bonus = manager.check_milestone(3)  # Won't trigger - already past it
        assert bonus is None
    
    def test_reset_session_resets_milestones(self):
        """Test that reset_session allows milestones to trigger again."""
        manager = StreakBonusManager()
        
        # Trigger milestone
        bonus1 = manager.check_milestone(3)
        assert bonus1 is not None
        
        # Should not trigger again
        bonus2 = manager.check_milestone(3)
        assert bonus2 is None
        
        # Reset session
        manager.reset_session()
        
        # Should trigger again after reset
        bonus3 = manager.check_milestone(3)
        assert bonus3 is not None
        assert bonus3.triggered is True
    
    def test_on_bonus_triggered_callback(self):
        """Test callback is called when bonus is triggered."""
        manager = StreakBonusManager()
        
        callback_called = False
        triggered_bonus = None
        
        def on_bonus_triggered(bonus):
            nonlocal callback_called, triggered_bonus
            callback_called = True
            triggered_bonus = bonus
        
        manager.on_bonus_triggered = on_bonus_triggered
        
        # Trigger bonus
        bonus = manager.check_milestone(3)
        
        assert callback_called is True
        assert triggered_bonus == bonus
    
    def test_clear_active_bonus(self):
        """Test clearing active bonus after animation."""
        manager = StreakBonusManager()
        
        # Trigger bonus
        bonus = manager.check_milestone(3)
        assert manager.active_bonus == bonus
        
        # Clear active bonus
        manager.clear_active_bonus()
        assert manager.active_bonus is None
    
    def test_get_triggered_milestones(self):
        """Test getting list of triggered milestones."""
        manager = StreakBonusManager()
        
        # Initially none triggered
        assert len(manager.get_triggered_milestones()) == 0
        
        # Trigger one milestone
        manager.check_milestone(3)
        triggered = manager.get_triggered_milestones()
        assert len(triggered) == 1
        assert triggered[0].bonus_type == BonusType.GOLDEN_ROCKET
        
        # Trigger second milestone
        manager.check_milestone(5)
        triggered = manager.get_triggered_milestones()
        assert len(triggered) == 2
    
    def test_is_bonus_available(self):
        """Test checking if bonus is available for streak."""
        manager = StreakBonusManager()
        
        # All bonuses available initially
        assert manager.is_bonus_available(3) is True
        assert manager.is_bonus_available(5) is True
        
        # Trigger one
        manager.check_milestone(3)
        
        # 3 no longer available, 5 still is
        assert manager.is_bonus_available(3) is False
        assert manager.is_bonus_available(5) is True


class TestBonusMilestone:
    """Tests for the BonusMilestone dataclass."""
    
    def test_milestone_creation(self):
        """Test creating a bonus milestone."""
        milestone = BonusMilestone(
            streak_threshold=3,
            bonus_type=BonusType.GOLDEN_ROCKET,
            message="Test message"
        )
        
        assert milestone.streak_threshold == 3
        assert milestone.bonus_type == BonusType.GOLDEN_ROCKET
        assert milestone.message == "Test message"
        assert milestone.triggered is False
    
    def test_milestone_triggered_flag(self):
        """Test triggered flag."""
        milestone = BonusMilestone(3, BonusType.GOLDEN_ROCKET, "Test")
        
        assert milestone.triggered is False
        milestone.triggered = True
        assert milestone.triggered is True


@pytest.fixture
def sample_manager():
    """Fixture providing a configured StreakBonusManager."""
    return create_streak_bonus_manager()


class TestStreakBonusIntegration:
    """Integration tests for streak bonus system."""
    
    def test_typical_3_word_streak(self, sample_manager):
        """Test typical gameplay reaching 3-word streak."""
        # Simulate reaching streak milestones
        assert sample_manager.check_milestone(1) is None
        assert sample_manager.check_milestone(2) is None
        
        # This should trigger
        bonus = sample_manager.check_milestone(3)
        assert bonus is not None
        assert bonus.bonus_type == BonusType.GOLDEN_ROCKET
    
    def test_typical_5_word_streak(self, sample_manager):
        """Test typical gameplay reaching 5-word streak."""
        # Reach 3-word streak
        bonus1 = sample_manager.check_milestone(3)
        assert bonus1 is not None
        
        # Reach 5-word streak
        bonus2 = sample_manager.check_milestone(5)
        assert bonus2 is not None
        assert bonus2.bonus_type == BonusType.PLANET_DISCOVERY
    
    def test_both_bonuses_in_session(self, sample_manager):
        """Test both bonuses can be triggered in one session."""
        sample_manager.check_milestone(3)
        sample_manager.check_milestone(5)
        
        triggered = sample_manager.get_triggered_milestones()
        assert len(triggered) == 2
        assert any(b.bonus_type == BonusType.GOLDEN_ROCKET for b in triggered)
        assert any(b.bonus_type == BonusType.PLANET_DISCOVERY for b in triggered)
    
    def test_session_reset_between_games(self, sample_manager):
        """Test that new game session resets bonuses."""
        # First game
        sample_manager.check_milestone(3)
        sample_manager.check_milestone(5)
        
        # Second game - should be able to trigger again
        sample_manager.reset_session()
        
        bonus = sample_manager.check_milestone(3)
        assert bonus is not None
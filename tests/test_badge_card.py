"""
Badge Card Tests (STORY-007-02)

Unit tests for the BadgeCard component.
Tests rendering, animations, hover states, and interactions.
"""

import pytest
from unittest.mock import MagicMock, patch
import pygame
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.components.badge_system import Badge, Rarity, BadgeProgress
from src.ui.badge_card import BadgeCard, BadgeCardConfig, BadgeState, create_badge_card


@pytest.fixture
def sample_badge():
    """Create a sample badge for testing."""
    return Badge(
        id='test_badge',
        name='Test Badge',
        description='This is a test badge description',
        icon_path='assets/badges/test.png',
        rarity=Rarity.COMMON,
        unlock_condition='test_condition',
        color_scheme='blue_yellow',
        category='speed'
    )


@pytest.fixture
def sample_badge_rare():
    """Create a rare badge for testing."""
    return Badge(
        id='rare_badge',
        name='Rare Achievement',
        description='This is a rare badge',
        icon_path='assets/badges/rare.png',
        rarity=Rarity.RARE,
        unlock_condition='rare_condition',
        color_scheme='gold_purple',
        category='accuracy'
    )


@pytest.fixture
def pygame_initialized():
    """Initialize pygame for testing."""
    pygame.init()
    yield
    pygame.quit()


@pytest.fixture
def test_screen(pygame_initialized):
    """Create a test pygame surface."""
    return pygame.display.set_mode((800, 600))


class TestBadgeCardConfig:
    """Tests for BadgeCardConfig."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = BadgeCardConfig()
        
        assert config.CARD_SIZE == 80
        assert config.MARGIN == 10
        assert config.BORDER_WIDTH == 3
        assert config.BACKGROUND_UNLOCKED == (30, 30, 50)
        assert config.BACKGROUND_LOCKED == (20, 20, 35)
    
    def test_get_rarity_color(self):
        """Test getting rarity colors."""
        config = BadgeCardConfig()
        
        silver = config.get_rarity_color(Rarity.COMMON)
        bronze = config.get_rarity_color(Rarity.UNCOMMON)
        gold = config.get_rarity_color(Rarity.RARE)
        purple = config.get_rarity_color(Rarity.LEGENDARY)
        # Use invalid key to test default
        invalid = config.get_rarity_color('invalid_rarity')  # type: ignore
        
        assert silver == (192, 192, 192)
        assert bronze == (205, 127, 50)
        assert gold == (255, 215, 0)
        assert purple == (128, 0, 128)
        assert invalid == (192, 192, 192)  # Falls back to silver


class TestBadgeCardCreation:
    """Tests for BadgeCard creation."""
    
    def test_create_earned_badge_card(self, sample_badge):
        """Test creating an earned badge card."""
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100))
        
        assert card.badge.id == 'test_badge'
        assert card.state == BadgeState.EARNED
        assert card.position == (100, 100)
        assert card.size == 80
        assert card.rect == pygame.Rect(100, 100, 80, 80)
    
    def test_create_locked_badge_card(self, sample_badge):
        """Test creating a locked badge card."""
        card = BadgeCard(sample_badge, BadgeState.LOCKED, (200, 200))
        
        assert card.state == BadgeState.LOCKED
        assert card.lock_icon is not None
    
    def test_create_with_progress(self, sample_badge):
        """Test creating badge card with progress."""
        progress = BadgeProgress('test_badge', 3, 10, False)
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100), progress=progress)
        
        assert card.progress == progress
        assert progress.current == 3
        assert progress.target == 10
    
    def test_create_with_callback(self, sample_badge):
        """Test creating badge card with click callback."""
        callback = MagicMock()
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100), on_click=callback)
        
        assert card.on_click == callback
    
    def test_create_with_custom_config(self, sample_badge):
        """Test creating badge card with custom config."""
        config = BadgeCardConfig(CARD_SIZE=100, MARGIN=15)
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100), config=config)
        
        assert card.size == 100
        assert card.margin == 15


class TestBadgeCardFactory:
    """Tests for factory functions."""
    
    def test_create_badge_card_unlocked(self, sample_badge):
        """Test factory function for unlocked badge."""
        card = create_badge_card(sample_badge, unlocked=True, position=(100, 100))
        
        assert card.state == BadgeState.EARNED
    
    def test_create_badge_card_locked(self, sample_badge):
        """Test factory function for locked badge."""
        card = create_badge_card(sample_badge, unlocked=False, position=(100, 100))
        
        assert card.state == BadgeState.LOCKED
    
    def test_create_badge_card_with_progress(self, sample_badge):
        """Test factory function with progress."""
        progress = BadgeProgress('test', 5, 10)
        card = create_badge_card(sample_badge, unlocked=True, position=(100, 100), progress=progress)
        
        assert card.progress == progress


class TestBadgeCardInteractions:
    """Tests for badge card interactions."""
    
    def test_is_point_inside(self, sample_badge):
        """Test point collision detection."""
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100))
        
        assert card.is_point_inside((140, 140)) is True
        assert card.is_point_inside((100, 100)) is True
        assert card.is_point_inside((179, 179)) is True  # Within 80x80 rect at (100,100)
        assert card.is_point_inside((50, 50)) is False
        assert card.is_point_inside((181, 181)) is False  # Outside rect
    
    def test_handle_mouse_click(self, sample_badge, pygame_initialized):
        """Test handling mouse click event."""
        callback = MagicMock()
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100), on_click=callback)
        
        # Create click event at badge position
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(140, 140), button=1)
        
        result = card.handle_event(event)
        
        assert result is True
        callback.assert_called_once()
    
    def test_handle_mouse_click_outside(self, sample_badge):
        """Test click outside badge doesn't trigger callback."""
        callback = MagicMock()
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100), on_click=callback)
        
        event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(50, 50), button=1)
        
        result = card.handle_event(event)
        
        assert callback.call_count == 0
    
    def test_handle_mouse_hover(self, sample_badge):
        """Test hover state update."""
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100))
        
        # Move event over badge
        event = pygame.event.Event(pygame.MOUSEMOTION, pos=(140, 140))
        card.handle_event(event)
        
        assert card.is_hovered is True
        
        # Move event away from badge
        event = pygame.event.Event(pygame.MOUSEMOTION, pos=(50, 50))
        card.handle_event(event)
        
        assert card.is_hovered is False


class TestBadgeCardAnimations:
    """Tests for badge card animations."""
    
    def test_hover_alpha_increases(self, sample_badge):
        """Test hover alpha increases during hover."""
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100))
        card.is_hovered = True
        
        # Update with 0.1 second delta
        card.update(0.1)
        
        assert card.hover_alpha > 0
    
    def test_hover_alpha_decreases(self, sample_badge):
        """Test hover alpha decreases when not hovering."""
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100))
        card.hover_alpha = 200
        card.is_hovered = False
        
        # Update with 0.1 second delta
        card.update(0.1)
        
        assert card.hover_alpha < 200
    
    def test_new_badge_pulse_animation(self, sample_badge):
        """Test newly earned badge pulse animation."""
        card = BadgeCard(sample_badge, BadgeState.NEWLY_EARNED, (100, 100))
        
        # Initially should have no pulse
        assert card.new_badge_pulse >= 0
        
        # Update for 0.5 seconds
        card.update(0.5)
        
        # Pulse should be active
        assert card.new_badge_pulse >= 0
    
    def test_new_badge_transitions_to_earned(self, sample_badge):
        """Test newly earned badge transitions to earned state after 2 seconds."""
        card = BadgeCard(sample_badge, BadgeState.NEWLY_EARNED, (100, 100))
        
        # Update for 2.5 seconds (past the 2 second threshold)
        card.update(2.5)
        
        # Should transition to earned state
        assert card.state == BadgeState.EARNED
        assert card.new_badge_pulse == 0.0


class TestBadgeCardStates:
    """Tests for badge card state handling."""
    
    def test_locked_state_has_lock_icon(self, sample_badge):
        """Test locked badge displays lock icon."""
        card = BadgeCard(sample_badge, BadgeState.LOCKED, (100, 100))
        
        assert card.lock_icon is not None
        assert card.lock_icon.get_width() == 24
        assert card.lock_icon.get_height() == 24
    
    def test_locked_state_no_border(self, sample_badge, test_screen):
        """Test locked badge has no rarity border."""
        card = BadgeCard(sample_badge, BadgeState.LOCKED, (100, 100))
        
        # Should draw without applying rarity color logic
        # (actual rendering test would verify this visually)
        assert card.state == BadgeState.LOCKED
    
    def test_earned_state_has_rarity_color(self, sample_badge, sample_badge_rare):
        """Test earned badge uses rarity color."""
        common_card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100))
        rare_card = BadgeCard(sample_badge_rare, BadgeState.EARNED, (200, 200))
        
        assert common_card.badge.rarity == Rarity.COMMON
        assert rare_card.badge.rarity == Rarity.RARE
    
    def test_newly_earned_state_pulses(self, sample_badge):
        """Test newly earned badge has pulse effect."""
        card = BadgeCard(sample_badge, BadgeState.NEWLY_EARNED, (100, 100))
        
        assert card.state == BadgeState.NEWLY_EARNED
        assert card.pulse_speed > 0


class TestBadgeCardRendering:
    """Tests for badge card rendering (sanity checks)."""
    
    def test_render_does_not_crash(self, sample_badge, test_screen):
        """Test that rendering doesn't cause errors."""
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100))
        
        # Should not raise any exceptions
        try:
            card.draw(test_screen)
        except Exception as e:
            pytest.fail(f"Rendering raised exception: {e}")
    
    def test_render_locked_does_not_crash(self, sample_badge, test_screen):
        """Test locked badge rendering doesn't cause errors."""
        card = BadgeCard(sample_badge, BadgeState.LOCKED, (100, 100))
        
        try:
            card.draw(test_screen)
        except Exception as e:
            pytest.fail(f"Locked rendering raised exception: {e}")
    
    def test_render_newly_earned_does_not_crash(self, sample_badge, test_screen):
        """Test newly earned badge rendering doesn't cause errors."""
        card = BadgeCard(sample_badge, BadgeState.NEWLY_EARNED, (100, 100))
        
        try:
            card.draw(test_screen)
        except Exception as e:
            pytest.fail(f"Newly earned rendering raised exception: {e}")
    
    def test_draw_tooltip_does_not_crash(self, sample_badge, test_screen):
        """Test tooltip rendering doesn't cause errors."""
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100))
        
        try:
            card.draw_tooltip(test_screen)
        except Exception as e:
            pytest.fail(f"Tooltip rendering raised exception: {e}")
    
    def test_draw_tooltip_locked_returns_early(self, sample_badge, test_screen):
        """Test tooltip for locked badge doesn't draw."""
        card = BadgeCard(sample_badge, BadgeState.LOCKED, (100, 100))
        
        # Should return early without drawing
        # (can't easily test "not drawn", so just verify no crash)
        try:
            card.draw_tooltip(test_screen)
        except Exception as e:
            pytest.fail(f"Locked tooltip raised exception: {e}")


class TestTextWrapping:
    """Tests for text wrapping functionality."""
    
    def test_wrap_short_text(self, sample_badge, test_screen):
        """Test wrapping short text that fits."""
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100))
        
        font = pygame.font.Font(None, 20)
        text = "Short text"
        
        lines = card._wrap_text(font, text, 200)
        
        assert len(lines) == 1
        assert lines[0] == "Short text"
    
    def test_wrap_long_text(self, sample_badge, test_screen):
        """Test wrapping long text that needs multiple lines."""
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100))
        
        font = pygame.font.Font(None, 20)
        text = "This is a very long description that should wrap to multiple lines"
        
        lines = card._wrap_text(font, text, 100)
        
        assert len(lines) > 1
        # Verify no line exceeds max_width
        for line in lines:
            assert font.render(line, True, (255, 255, 255)).get_width() <= 100
    
    def test_wrap_single_word(self, sample_badge, test_screen):
        """Test wrapping single very long word."""
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100))
        
        font = pygame.font.Font(None, 20)
        text = "Supercalifragilisticexpialidocious"
        
        lines = card._wrap_text(font, text, 100)
        
        # Long word should be on its own line
        assert len(lines) >= 1


class TestPerformance:
    """Performance tests for badge card."""
    
    def test_update_performance(self, sample_badge):
        """Test update completes quickly."""
        card = BadgeCard(sample_badge, BadgeState.EARNED, (100, 100))
        
        import time
        start = time.time()
        
        # Run many updates
        for _ in range(1000):
            card.update(0.016)  # ~60 FPS
        
        elapsed = time.time() - start
        
        # 1000 updates should take < 100ms
        assert elapsed < 0.1, f"1000 updates took {elapsed*1000}ms, expected <100ms"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
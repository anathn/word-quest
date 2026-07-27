"""
Badge State Module (STORY-007-02)

Provides badge state tracking and management.

Note: This module re-exports badge state functionality from badge_system.py
for API compatibility with the story specification. The actual implementation
is centralized in badge_system.py to avoid duplication and maintain a single
source of truth for badge state management.

Classes:
    BadgeState: Enum representing badge display states (LOCKED, EARNED, NEWLY_EARNED)
    BadgeProgress: Tracks progress toward unlocking a badge
    
All state logic is handled by BadgeManager in badge_system.py.
"""

# Re-export badge state components from badge_system for API compatibility
from src.components.badge_system import Badge, Rarity, BadgeProgress

# Import BadgeState from badge_card since it's UI-specific
# This maintains the separation: badge_system has Badge enum, badge_card has BadgeState
try:
    from src.ui.badge_card import BadgeState
except ImportError:
    # Fallback if badge_card not yet loaded - define inline
    from enum import Enum
    
    class BadgeState(Enum):
        """Badge display state."""
        LOCKED = "locked"
        EARNED = "earned"
        NEWLY_EARNED = "newly_earned"


__all__ = ['BadgeState', 'Badge', 'BadgeProgress', 'Rarity']


# Deprecated aliases for backward compatibility (will be removed in future version)
BadgeStateEnum = BadgeState
"""Deprecated: Use BadgeState instead."""
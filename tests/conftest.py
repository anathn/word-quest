"""
Pytest configuration for pygame testing.

Provides fixtures and setup for pygame-based tests.
"""

import pytest


@pytest.fixture
def test_screen():
    """Create a test pygame display surface."""
    import pygame
    return pygame.display.set_mode((800, 600))
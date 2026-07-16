"""
Pytest configuration for headless pygame testing.

Sets SDL environment variables and provides fixtures for test isolation.
"""

import os
import sys

# CRITICAL: Set environment variables IMMEDIATELY, before ANY pygame import
# This MUST be at the very top, before any other imports
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.pop('DISPLAY', None)  # Remove DISPLAY to ensure headless mode

# CRITICAL: Initialize pygame IMMEDIATELY at module load time
# This happens WHENEVER conftest.py is imported (including in xdist workers)
# By initializing here, we ensure pygame is ready before any test file imports pygame
try:
    import pygame
    # Only initialize if not already done (safe for xdist workers)
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()
    if not pygame.font.get_init():
        pygame.font.init()
except Exception as e:
    # If pygame init fails, log but continue (tests will fail with better errors)
    print(f"Warning: pygame initialization in conftest: {e}", file=sys.stderr)

import pytest


@pytest.fixture
def test_screen():
    """Create a test pygame display surface."""
    import pygame
    return pygame.display.set_mode((800, 600))
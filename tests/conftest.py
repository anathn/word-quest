"""
Pytest configuration for headless pygame testing.

Sets SDL environment variables and provides fixtures for test isolation.

CRITICAL: This file sets environment variables and initializes pygame
at MODULE LOAD TIME, which happens when each pytest-xdist worker imports conftest.py.
This is BEFORE any test files are loaded, ensuring pygame is ready for all tests.
"""

import os
import sys

# CRITICAL: Set environment variables IMMEDIATELY, before ANY pygame import
# These must be set before any module (including src modules) imports pygame
_os_env_set = {'SDL_VIDEODRIVER': 'dummy', 'SDL_AUDIODRIVER': 'dummy'}
for key, value in _os_env_set.items():
    if os.environ.get(key) != value:
        os.environ[key] = value

# Remove DISPLAY to ensure headless mode
os.environ.pop('DISPLAY', None)

# CRITICAL: Initialize pygame IMMEDIATELY at module load time
# This code runs when conftest.py is imported by each xdist worker
# It happens BEFORE test files are loaded by that worker
try:
    import pygame
    # Safe initialization: only init components that aren't already initialized
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()
    if not pygame.font.get_init():
        pygame.font.init()
except Exception as e:
    # If init fails at this stage, log but continue - tests will fail with clearer errors
    print(f"Warning in conftest.py pygame init: {e}", file=sys.stderr)

import pytest


@pytest.fixture
def test_screen():
    """Create a test pygame display surface."""
    import pygame
    return pygame.display.set_mode((800, 600))
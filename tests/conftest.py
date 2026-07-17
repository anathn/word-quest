"""
Pytest configuration for headless pygame testing with xdist.

This file ensures pygame is properly initialized for all pytest-xdist workers
by setting environment variables and initializing pygame at module load time,
which happens when each worker imports conftest.py (before any test files).
"""

import os
import sys

# CRITICAL: Set headless environment variables FIRST (before ANY pygame import)
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
if 'DISPLAY' in os.environ:
    del os.environ['DISPLAY']

# CRITICAL: Initialize pygame IMMEDIATELY at module load time
# This code runs when each xdist worker imports conftest.py, BEFORE test collection
# We use a try/except to handle any initialization failures gracefully
if not os.environ.get('PYGAME_ALREADY_INITIALIZED'):
    try:
        import pygame
        # Only initialize if not already done (idempotent for safety)
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
        os.environ['PYGAME_ALREADY_INITIALIZED'] = '1'
    except Exception as e:
        print(f"Warning: pygame initialization in conftest failed: {e}", file=sys.stderr)

import pytest


def pytest_configure(config):
    """
    Hook that runs early in pytest startup, ensuring pygame is initialized.
    This is a backup to the module-level initialization.
    """
    # Ensure environment variables are set (double-check)
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
    
    # Force initialization if not already done
    try:
        import pygame
        if not pygame.get_init():
            pygame.init()
        if not pygame.display.get_init():
            pygame.display.init()
        if not pygame.font.get_init():
            pygame.font.init()
    except Exception as e:
        print(f"Warning: pygame init in pytest_configure: {e}", file=sys.stderr)


@pytest.fixture
def test_screen():
    """Create a test pygame display surface."""
    import pygame
    return pygame.display.set_mode((800, 600))
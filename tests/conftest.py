"""
Pytest configuration for headless pygame testing with xdist.

This file ensures pygame is properly initialized for all pytest-xdist workers
by running initialization code at module load time, which happens when each
worker imports conftest.py (before any test files).
"""

import os
import sys

# Set headless environment variables (must be before pygame import)
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.pop('DISPLAY', None)

# Force pygame initialization at conftest load time
# This runs when each xdist worker imports this file, BEFORE test collection
if not os.environ.get('PYGAME_INITIALIZED'):
    try:
        import pygame
        pygame.init()
        pygame.display.init()
        pygame.font.init()
        os.environ['PYGAME_INITIALIZED'] = '1'
    except Exception as e:
        print(f"Warning: pygame init in conftest: {e}", file=sys.stderr)

import pytest


@pytest.fixture
def test_screen():
    """Create a test pygame display surface."""
    import pygame
    return pygame.display.set_mode((800, 600))
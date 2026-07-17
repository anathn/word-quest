"""
Pytest configuration for headless pygame testing with xdist.

CRITICAL: This file MUST initialize pygame BEFORE any test files are imported.
"""

import os
import sys

# Step 1: Set environment variables FIRST (before ANY pygame import anywhere)
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
if 'DISPLAY' in os.environ:
    del os.environ['DISPLAY']

# Step 2: Initialize pygame IMMEDIATELY, before importing pytest
# This ensures pygame is fully initialized before any test module collection
if not os.environ.get('PYGAME_INITIALIZED_BY_CONFTEST'):
    import pygame
    pygame.init()
    pygame.display.init()
    pygame.font.init()
    os.environ['PYGAME_INITIALIZED_BY_CONFTEST'] = '1'

# Step 3: Now it's safe to import pytest (which will collect test modules)
import pytest


def pytest_configure(config):
    """Double-check pygame is initialized (run early in pytest startup)."""
    # Environment variables should already be set, but double-check
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')


@pytest.fixture
def test_screen():
    """Create a test pygame display surface."""
    return pygame.display.set_mode((800, 600))
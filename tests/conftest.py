"""
Pytest configuration for headless pygame testing.

Sets SDL environment variables and provides fixtures for proper test isolation
to prevent pygame state accumulation and segfaults during serial test execution.
"""

import os

# CRITICAL: Set SDL video/audio drivers to dummy BEFORE any pygame import
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ.setdefault('DISPLAY', '')

# CRITICAL: Initialize pygame at conftest load time, BEFORE any test files are imported
# This prevents circular import errors in pytest-xdist parallel execution
import pygame
pygame.init()
pygame.display.init()
pygame.font.init()

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Configure pytest with pygame already initialized."""
    pass  # pygame is already initialized above


@pytest.fixture(scope="function", autouse=True)
def ensure_pygame():
    """Autouse fixture keeping pygame initialized for each test."""
    # pygame is already initialized above, ensure it stays that way
    import pygame
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_init():
        pygame.display.init()
    if not pygame.font.get_init():
        pygame.font.init()
    yield


@pytest.fixture(scope="function")
def test_screen():
    """Create a test screen surface."""
    import pygame
    return pygame.display.set_mode((800, 600))

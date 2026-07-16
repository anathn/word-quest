"""
Pytest configuration for headless pygame testing.

Sets SDL environment variables and provides fixtures for proper pygame initialization
in headless CI environments.
"""

import os
import pytest

# CRITICAL: Set SDL video/audio drivers to dummy BEFORE any pygame import
# These MUST be set before any module imports pygame
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
# Clear DISPLAY to ensure headless mode
if 'DISPLAY' in os.environ:
    del os.environ['DISPLAY']


def pytest_configure(config):
    """
    Configure pytest for headless testing.
    
    This hook runs early in pytest startup, before test collection.
    """
    # Ensure env vars are set (already set above, but double-check)
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'


@pytest.fixture(scope="session", autouse=True)
def setup_pygame_headless():
    """
    Session-scoped autouse fixture that initializes pygame once per pytest-xdist worker.
    
    This ensures pygame is initialized in headless mode for all tests.
    Place at session scope to avoid re-initialization overhead and race conditions.
    """
    import pygame
    
    # Initialize pygame components needed for tests
    # Only initialize if not already initialized (handles test files that init early)
    if not pygame.get_init():
        pygame.init()
    
    # Ensure display is initialized
    if not pygame.display.get_init():
        pygame.display.init()
    
    # Ensure font is initialized (critical for UI tests)
    if not pygame.font.get_init():
        pygame.font.init()
    
    yield
    
    # Cleanup: quit display to free resources (but don't quit pygame entirely)
    try:
        if pygame.display.get_init():
            pygame.display.quit()
    except:
        pass


@pytest.fixture
def test_screen(setup_pygame_headless):
    """
    Create a test pygame display surface.
    
    Note: In headless mode with SDL dummy driver, this creates a surface
    that can be rendered to but has no visible display.
    """
    import pygame
    return pygame.display.set_mode((800, 600))
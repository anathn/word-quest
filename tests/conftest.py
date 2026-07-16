"""
Pytest configuration for headless pygame testing.

Sets SDL environment variables and provides fixtures for proper test isolation
to prevent pygame state accumulation and segfaults during serial test execution.
"""

import os

# CRITICAL: Set SDL video/audio drivers to dummy BEFORE any pygame import
# This must happen at module load time, before pytest collects tests
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ.setdefault('DISPLAY', '')

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Configure pytest with headless settings."""
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'


@pytest.fixture(scope="function")
def pygame_setup():
    """
    Fixture to properly initialize pygame for each test.
    
    This ensures pygame display and font modules are initialized before tests
    that use pygame.display, pygame.mouse, or pygame.font.
    
    Usage:
        def test_something(pygame_setup):
            # pygame is now properly initialized
            screen = pygame.display.set_mode((800, 600))
    """
    import pygame
    
    # Initialize pygame if not already initialized
    if not pygame.get_init():
        pygame.init()
    
    # Ensure display is initialized for tests that need it
    if not pygame.display.get_init():
        pygame.display.init()
    
    # Ensure font is initialized for tests that need it
    if not pygame.font.get_init():
        pygame.font.init()
    
    yield
    
    # Cleanup: quit display after test to free resources
    # This helps prevent resource leaks between tests
    try:
        if pygame.display.get_init():
            pygame.display.quit()
    except (RuntimeError, AttributeError):
        # pygame may already be quit
        pass


@pytest.fixture(scope="function")
def test_screen(pygame_setup):
    """
    Fixture that creates a test screen with proper pygame initialization.
    
    Usage:
        def test_something(test_screen):
            # test_screen is a valid pygame display surface
            test_screen.fill((0, 0, 0))
    """
    import pygame
    return pygame.display.set_mode((800, 600))
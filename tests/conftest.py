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


@pytest.fixture(autouse=True)
def pygame_cleanup():
    """
    Clean up pygame state between tests to prevent accumulation and segfaults.
    
    This runs before and after each test to ensure clean pygame state.
    Only calls pygame.quit() if pygame is actually loaded.
    """
    # Check if pygame is already loaded
    pygame_loaded = False
    try:
        import pygame
        pygame_loaded = pygame.get_init()
    except (ImportError, AttributeError):
        pass
    
    yield
    
    # After test: only quit pygame if it was loaded during the test
    # and only if we detect it might cause issues
    if pygame_loaded:
        try:
            import pygame
            # Only quit display/mixer, not the whole pygame
            if pygame.display.get_init():
                pygame.display.quit()
        except (ImportError, RuntimeError, AttributeError):
            pass

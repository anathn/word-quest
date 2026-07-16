"""
Pytest configuration for headless pygame testing.

Sets SDL environment variables before pygame is imported to ensure
all tests run without displaying windows (headless mode).
"""

import os

# CRITICAL: Set SDL video/audio drivers to dummy BEFORE any pygame import
# This must happen at module load time, before pytest collects tests
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

# Also set DISPLAY to empty to prevent X11 connections
os.environ.setdefault('DISPLAY', '')

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Configure pytest with headless settings."""
    # Double-check environment variables
    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    os.environ['SDL_AUDIODRIVER'] = 'dummy'
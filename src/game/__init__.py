"""
Game package - contains the main Game class and related utilities.

This package provides the core game loop and initialization logic.
"""

from .game import Game, create_display, initialize_pygame, cleanup_pygame

__all__ = ['Game', 'create_display', 'initialize_pygame', 'cleanup_pygame']
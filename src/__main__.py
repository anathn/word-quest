"""
Word Quest Entry Point

Main entry point for launching the Word Quest game.
Runs when executing: python -m src

Usage:
    python -m src          # Normal launch
    HEADLESS=1 python -m src    # Headless mode (testing)
    TESTING=1 python -m src     # Test mode
"""

import sys
import os

# Setup logging before importing game modules
from src.logging_config import setup_logging
setup_logging()

import logging
logger = logging.getLogger(__name__)


def main() -> int:
    """
    Main entry point for the game.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    logger.info("=" * 60)
    logger.info("Word Quest: Spelling Adventure")
    logger.info("=" * 60)
    
    try:
        # Import pygame first to allow driver override for headless mode
        if os.environ.get('HEADLESS', '0') == '1':
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
            os.environ['SDL_AUDIODRIVER'] = 'dummy'
            setup_logging()  # Re-configure for headless output
            logger.info("Running in headless mode")
            
        import pygame
        
        # Initialize pygame
        logger.info("Initializing Pygame...")
        if not pygame.init():
            logger.error("Failed to initialize Pygame")
            return 1
            
        logger.info("Initializing Pygame mixer...")
        try:
            pygame.mixer.init()
            logger.info("Audio system ready")
        except Exception as e:
            logger.warning(f"Audio initialization failed: {e}")
            logger.info("Continuing without sound")
            
        # Import game module after pygame initialization
        from src.config import WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, FPS, DEFAULT_WINDOWED
        from src.game import Game
        
        # Create display
        logger.info(f"Creating display: {WINDOW_WIDTH}x{WINDOW_HEIGHT}...")
        flags = pygame.RESIZABLE if DEFAULT_WINDOWED else 0
        screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        pygame.display.set_caption(WINDOW_TITLE)
        logger.info("Display created successfully")
        
        # Create and run game
        logger.info("Creating Game instance...")
        game = Game(screen)
        
        logger.info("Starting game loop...")
        game.run()
        
        logger.info("Game exited normally")
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nGame interrupted by user")
        return 0
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure all dependencies are installed:")
        logger.error("  pip install -r requirements.txt")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    finally:
        # Clean up pygame
        try:
            pygame.quit()
        except:
            pass
        logger.info("Cleanup complete")


if __name__ == "__main__":
    sys.exit(main())

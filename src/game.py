"""
Word Quest Game

Main game class that manages the game loop, initialization, and core systems.
This is the central controller for the entire game application.
"""

import pygame
import sys
import os
import logging
from typing import Optional
from pathlib import Path

from src.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, FPS,
    COLOR_BACKGROUND, DEFAULT_WINDOWED, is_headless, is_testing
)
from src.ui.screen_manager import ScreenManager, Screen
from src.screens.main_menu import MainMenuScreen
from src.audio.music_manager import MusicManager
from src.audio.sfx_generator import SFXGenerator
from src.components.data_store import DataStore
from src.settings.player_preferences import PlayerPreferencesManager
from src.components.audio_system import AudioSystem
from src.components.caption_manager import CaptionManager
from src.components.caption_settings import CaptionSettingsManager, CaptionSettings
from src.ui.caption_display import CaptionDisplay
from src.screens.authenticated_parent_dashboard import AuthenticatedParentDashboard

logger = logging.getLogger(__name__)


class Game:
    """
    Main game controller and application loop.
    
    Responsibilities:
    - Initialize pygame and all subsystems
    - Manage the game loop
    - Handle global events (escape, quit)
    - Coordinate between systems (audio, input, etc.)
    - Manage screen transitions
    """
    
    def __init__(self, screen: pygame.Surface):
        """
        Initialize the game.
        
        Args:
            screen: The main pygame display surface
        """
        self.screen = screen
        self.clock = pygame.time.Clock()
        self._running = True
        self._paused = False
        
        # Initialize managers
        self.screen_manager = ScreenManager(screen)
        self.data_store = DataStore()
        self.player_preferences_manager: Optional[PlayerPreferencesManager] = None
        
        # Audio managers (lazy loaded for performance)
        self._music_manager: Optional[MusicManager] = None
        self._sfx_generator: Optional[SFXGenerator] = None
        
        # Caption system
        self.caption_manager: Optional[CaptionManager] = None
        self.caption_settings: Optional[CaptionSettings] = None
        self.caption_display: Optional[CaptionDisplay] = None
        
        # Initialize caption system
        try:
            self.caption_settings_mgr = CaptionSettingsManager()
            self.caption_settings = self.caption_settings_mgr.get_settings()
            self.caption_display = CaptionDisplay(self.screen, self.caption_settings)
            self.caption_manager = CaptionManager(self.caption_display)
            
            # Pass caption_manager to AudioSystem
            self.audio_system = AudioSystem(caption_manager=self.caption_manager)
            
            logger.info("Caption system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize caption system: {e}")
            self.caption_manager = None
        
        # Setup initial screen
        self._setup_initial_screen()
        
        logger.info("Game initialized successfully")
        
    @property
    def music_manager(self) -> Optional[MusicManager]:
        """Get music manager (lazy loaded)."""
        if self._music_manager is None:
            try:
                self._music_manager = MusicManager()
            except Exception as e:
                logger.warning(f"Failed to initialize MusicManager: {e}")
                self._music_manager = None
        return self._music_manager
    
    @property
    def sfx_generator(self) -> Optional[SFXGenerator]:
        """Get SFX generator (lazy loaded)."""
        if self._sfx_generator is None:
            try:
                self._sfx_generator = SFXGenerator()
            except Exception as e:
                logger.warning(f"Failed to initialize SFXGenerator: {e}")
                self._sfx_generator = None
        return self._sfx_generator
    
    @property
    def player_preferences(self) -> PlayerPreferencesManager:
        """Get player preferences manager (lazy loaded)."""
        if self.player_preferences_manager is None:
            self.player_preferences_manager = PlayerPreferencesManager()
        return self.player_preferences_manager
        
    def _setup_initial_screen(self) -> None:
        """
        Setup the initial screen based on game state.
        
        Checks if this is a first run and sets up appropriate screen.
        """
        # Check if this is first run
        is_first_run = not self.data_store.has_profiles()
        
        if is_first_run:
            logger.info("First run detected - setup wizard to be shown")
            # TODO: Show setup wizard screen instead of main menu
            # initial_screen = SetupWizardScreen(...)
        
        try:
            initial_screen = MainMenuScreen(self.screen)
            
            # Wire up callbacks
            initial_screen.on_parent_dashboard = self._show_parent_dashboard
            initial_screen.on_start_game = self._start_game
            
            self.screen_manager.push_screen(initial_screen)
        except ImportError as e:
            logger.error(f"Failed to load main menu: {e}")
            logger.error("Make sure src/screens/main_menu.py exists and has no errors")
            raise RuntimeError("Main menu screen not available") from e
        except Exception as e:
            logger.error(f"Failed to initialize main menu: {e}")
            raise
        
        logger.info("Initial screen setup complete")
        
    def run(self) -> None:
        """
        Main game loop.
        
        Processes events, updates game state, and renders at target FPS.
        """
        logger.info(f"Starting game loop at {FPS} FPS")
        
        while self._running and self.screen_manager.is_running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._handle_escape()
                    elif event.key == pygame.K_p and is_testing():
                        # Pause toggle (debug only)
                        self._paused = not self._paused
                        
                # Pass all events to current screen
                self.screen_manager.handle_event(event)
                
            if not self._paused:
                # Update current screen
                self.screen_manager.update()
                
                # Update captions (call every frame)
                if self.caption_manager:
                    self.caption_manager.update(1.0 / FPS)
                
                # Clear screen with background color
                self.screen.fill(COLOR_BACKGROUND)
                
                # Draw current screen
                self.screen_manager.draw()
                
                # Render captions (after screen draw so they appear on top)
                if self.caption_display:
                    self.caption_display.render()
                
                # Update display
                pygame.display.flip()
                
            # Cap frame rate
            self.clock.tick(FPS)
            
        logger.info("Game loop ended")
        
    def _show_parent_dashboard(self) -> None:
        """Show the parent dashboard after authentication."""
        try:
            # Create authenticated parent dashboard with caption manager
            parent_dashboard = AuthenticatedParentDashboard(
                sessions=[],  # Empty sessions - analytics would be loaded here
                screen_width=self.screen.get_width(),
                screen_height=self.screen.get_height(),
                caption_manager=self.caption_manager
            )
            
            # Create a wrapper screen for the authenticated dashboard
            # For now, we'll push it directly as a custom screen wrapper
            # In a full implementation, this would be a Screen subclass
            from src.ui.screen_manager import Screen
            
            class ParentDashboardWrapper(Screen):
                def __init__(self, dashboard):
                    super().__init__()
                    self.dashboard = dashboard
                    
                def handle_event(self, event):
                    return self.dashboard.handle_event(event)
                
                def draw(self, screen):
                    self.dashboard.render(screen)
                
                def update(self):
                    pass
            
            wrapper = ParentDashboardWrapper(parent_dashboard)
            parent_dashboard.activate()
            self.screen_manager.push_screen(wrapper)
            
            logger.info("Parent dashboard activated")
        except Exception as e:
            logger.error(f"Failed to show parent dashboard: {e}")
    
    def _start_game(self) -> None:
        """Start the spelling game (placeholder for game screen)."""
        logger.info("Start game clicked - game screen to be implemented")
        # TODO: Push game screen
    
    def _handle_escape(self) -> None:
        """
        Handle Escape key press.
        
        Behavior:
        - If on a sub-screen, return to previous screen
        - If on main menu, quit the game
        """
        current_screen = self.screen_manager.current_screen
        
        if current_screen:
            # Try screen-specific escape handling
            if hasattr(current_screen, 'on_escape'):
                current_screen.on_escape()
                
            # Check if escape requested exit
            if current_screen.should_exit:
                self.quit()
            elif current_screen.next_screen is not None:
                # Let screen manager handle the transition
                pass
            else:
                # Default: try to pop screen, or quit if at main menu
                if len(self.screen_manager.screen_stack) > 1:
                    self.screen_manager.pop_screen()
                else:
                    self.quit()
                    
    def quit(self) -> None:
        """
        Clean shutdown of the game.
        
        Performs cleanup of all systems before exiting.
        """
        logger.info("Game shutdown initiated")
        
        # Stop music
        try:
            if self._music_manager is not None:
                self._music_manager.stop_music()
        except Exception as e:
            logger.warning(f"Error stopping music: {e}")
            
        # Save all data
        try:
            self.data_store.save_all()
            if self.player_preferences_manager:
                self.player_preferences_manager.save_settings()
        except Exception as e:
            logger.error(f"Error saving data: {e}")
            
        # Stop screen manager
        self.screen_manager._running = False
        
        # Flag game as not running
        self._running = False
        
        logger.info("Game shutdown complete")


def create_display(width: int = WINDOW_WIDTH, 
                   height: int = WINDOW_HEIGHT) -> pygame.Surface:
    """
    Create the game display window.
    
    Args:
        width: Window width in pixels
        height: Window height in pixels
        
    Returns:
        The pygame display surface
    """
    flags = pygame.RESIZABLE if DEFAULT_WINDOWED else 0
    
    # For headless testing, use dummy video driver
    if is_headless():
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
        
    screen = pygame.display.set_mode((width, height), flags)
    pygame.display.set_caption(WINDOW_TITLE)
    
    logger.info(f"Display created: {width}x{height}")
    
    return screen


def initialize_pygame() -> bool:
    """
    Initialize Pygame and all required subsystems.
    
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        pygame.init()
        pygame.mixer.init()
        logger.info("Pygame initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Pygame initialization failed: {e}")
        return False


def cleanup_pygame() -> None:
    """Clean up Pygame resources."""
    pygame.mixer.quit()
    pygame.quit()
    logger.info("Pygame cleaned up")

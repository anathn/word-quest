"""
Word Quest Configuration

Game configuration constants and settings.
All configurable game parameters are defined here.
"""

import os
from pathlib import Path

# ============================================================================
# WINDOW SETTINGS
# ============================================================================

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
WINDOW_TITLE = "Word Quest: Spelling Adventure"
FPS = 60
DEFAULT_WINDOWED = True  # False for fullscreen

# ============================================================================
# PATHS
# ============================================================================

# Get the base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Assets directory
ASSETS_DIR = BASE_DIR / "assets"
FONTS_DIR = ASSETS_DIR / "fonts"
SOUNDS_DIR = ASSETS_DIR / "sounds"  # Match story specification
IMAGES_DIR = ASSETS_DIR / "images"

# Data directory
DATA_DIR = BASE_DIR / "data"
PROGRESS_DIR = DATA_DIR / "progress"
WORD_LISTS_DIR = DATA_DIR / "word_lists"
BADGES_DIR = DATA_DIR / "badges"

# Ensure directories exist
for dir_path in [ASSETS_DIR, DATA_DIR, FONTS_DIR, SOUNDS_DIR, IMAGES_DIR,
                 PROGRESS_DIR, WORD_LISTS_DIR, BADGES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Data files
PROFILES_FILE = DATA_DIR / "profiles.json"
THEME_CONFIG_FILE = DATA_DIR / "theme_config.json"
BADGE_DEFINITIONS_FILE = DATA_DIR / "badge_definitions.json"
STICKER_DEFINITIONS_FILE = DATA_DIR / "sticker_definitions.json"
VOICE_LINES_FILE = DATA_DIR / "voice_lines.json"
EMAIL_CONFIG_FILE = DATA_DIR / "email_config.json"

# ============================================================================
# COLORS
# ============================================================================

# Space theme colors (from STORY-005-01)
COLOR_BACKGROUND = (26, 26, 62)  # #1a1a3e - Deep space blue
COLOR_WHITE = (255, 255, 255)
COLOR_GOLD = (255, 215, 0)
COLOR_SPACE_BLUE = (26, 26, 62)
COLOR_STAR_WHITE = (255, 255, 255)

# UI element colors
COLOR_BUTTON_PRIMARY = (76, 175, 80)  # Green
COLOR_BUTTON_HOVER = (100, 189, 100)
COLOR_BUTTON_SECONDARY = (33, 150, 243)  # Blue
COLOR_TEXT_DARK = (33, 33, 33)
COLOR_TEXT_LIGHT = (255, 255, 255)

# Feedback colors
COLOR_CORRECT = (76, 175, 80)  # Green
COLOR_INCORRECT = (244, 67, 54)  # Red
COLOR_HINT = (255, 152, 0)  # Orange
COLOR_SUCCESS = (102, 187, 106)

# ============================================================================
# AUDIO SETTINGS
# ============================================================================

DEFAULT_MUSIC_VOLUME = 0.3  # 30% volume by default
DEFAULT_SFX_VOLUME = 0.7    # 70% volume by default
MUSIC_FADE_TIME = 500       # 500ms fade transitions

# ============================================================================
# GAMEPLAY SETTINGS
# ============================================================================

# Words per planet
WORDS_PER_PLANET = 5

# Mastery threshold (correct answers needed to unlock next planet)
MASTERY_THRESHOLD = 4  # 4/5 correct

# Hint system
MAX_HINTS_BEFORE_REVEAL = 3
HINT_DELAY_MS = 500  # Delay between hint escalations

# Streak bonuses
STREAK_BONUS_3 = 3   # First bonus at 3 correct
STREAK_BONUS_5 = 5   # Second bonus at 5 correct

# ============================================================================
# PERFORMANCE
# ============================================================================

MAX_MEMORY_POOL_SIZE = 100  # Maximum objects in object pools
STAR_COUNT = 200           # Number of stars in background
MAX_PARTICLES = 100        # Maximum particles for effects

# ============================================================================
# ACCESSIBILITY
# ============================================================================

ANIMATION_ENABLED = True
ANIMATION_INTENSITY = "normal"  # "minimal", "normal", "full"
TEXT_SCALE = 1.0               # Base text size multiplier
SHOW_TEXT_WRAPPER = True       # Show text-to-speech wrapper

# ============================================================================
# TIMEOUTS
# ============================================================================

SESSION_TIMEOUT_MINUTES = 10  # Parent dashboard session timeout
LOCKOUT_DURATION_MINUTES = 15  # Lockout after failed login attempts
MAX_LOGIN_ATTEMPTS = 5       # Max failed attempts before lockout

# ============================================================================
# FILE FORMATS
# ============================================================================

SUPPORTED_VIDEO_FORMATS = ['.mp4', '.webm', '.mov', '.avi']
SUPPORTED_AUDIO_FORMATS = ['.wav', '.mp3', '.ogg']
SUPPORTED_IMAGE_FORMATS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp']

# ============================================================================
# DEFAULT VALUES
# ============================================================================

DEFAULT_AVATAR = "astronaut"
DEFAULT_USERNAME = "Student"
DEFAULT_DIFFICULTY = "beginner"  # "beginner", "intermediate", "advanced"

# ============================================================================
# HELPERS
# ============================================================================

def get_data_path(filename: str) -> Path:
    """Get full path for a data file."""
    return DATA_DIR / filename

def get_assets_path(filename: str) -> Path:
    """Get full path for an asset file."""
    return ASSETS_DIR / filename

def get_font_path(filename: str) -> Path:
    """Get full path for a font file."""
    return FONTS_DIR / filename

def is_testing() -> bool:
    """Check if running in testing mode."""
    return os.environ.get('TESTING', '0') == '1'

def is_headless() -> bool:
    """Check if running in headless mode (no display)."""
    return os.environ.get('HEADLESS', '0') == '1'

def get_default_window_flags() -> int:
    """Get default pygame window flags."""
    import pygame
    if DEFAULT_WINDOWED:
        return pygame.RESIZABLE
    return 0
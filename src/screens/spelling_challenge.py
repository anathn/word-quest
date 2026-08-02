"""
Spelling Challenge Screen

Main game screen for presenting spelling words with audio and visual hints.
This is the core gameplay screen where students see words, hear them pronounced,
and begin typing with starter letter hints.
"""

import pygame
from typing import Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)

from src.ui.screen_manager import Screen
from src.components.input_handler import InputHandler, InputDisplay, InputState
from src.components.feedback_controller import (
    FeedbackController,
    FeedbackType,
    FeedbackState as FeedbackScreenState,
    create_feedback_controller
)
from src.components.hint_manager import HintManager, create_hint_manager
from src.components.planet_manager import PlanetManager, create_planet_manager
from src.components.streak_bonus import StreakBonusManager, create_streak_bonus_manager
from src.ui.hint_display import HintDisplay, create_hint_display
from src.ui.progress_display import ProgressDisplay, create_progress_display
from src.ui.streak_display import StreakDisplay, create_streak_display
from src.ui.bonus_message import BonusMessage, create_golden_boost_message, create_planet_discovery_message
from src.animations.rocket_boost import RocketBoostAnimation, create_rocket_boost_animation
from src.animations.planet_discovery import PlanetDiscoveryAnimation, create_planet_discovery_animation
from src.utils.validators import InputValidator, AnswerValidator
from src.components.captain_cosmos import CaptainCosmos, get_captain_cosmos
from src.components.audio_system import get_audio_system
from src.ui.star_field import StarField
from src.ui.theme import get_theme, SPACE_BLUE
from src.audio.music_manager import get_music_manager, MusicState
from src.ui.animated_word_display import AnimatedWordDisplay, create_animated_word_display
from src.components.tts_manager import TTSManager

# Performance threshold constants
WORD_PRESENTATION_TIMEOUT_MS = 200  # Maximum allowed time for word presentation


class ChallengeState(Enum):
    """States for the spelling challenge."""
    IDLE = "idle"
    PRESENTING = "presenting"
    READY_FOR_INPUT = "ready"
    AWAITING_RESPONSE = "awaiting_response"
    SHOWING_FEEDBACK = "showing_feedback"


@dataclass
class WordPresentation:
    """Data for presenting a word to the student."""
    word_text: str
    definition: str
    context_sentence: str
    starter_letters: str
    difficulty: int
    audio_replayable: bool = True


class SpellingChallengeScreen(Screen):
    """
    Main game screen for spelling word presentation.
    
    Features:
    - Display word with audio pronunciation
    - Show starter letter hints based on difficulty
    - Display definition and context sentence
    - Audio replay capability
    - Real-time letter display with animation
    - Planet completion tracking (STORY-001-05)
    """
    
    def __init__(self, screen, word_manager, audio_system, typography, progress_tracker=None):
        """
        Initialize the spelling challenge screen.
        
        Args:
            screen: The pygame display surface
            word_manager: WordManager instance for word data
            audio_system: AudioSystem instance for TTS
            typography: Typography instance for text rendering
            progress_tracker: ProgressTracker instance for tracking progress
        """
        # Initialize base Screen class (required for ScreenManager compatibility)
        super().__init__(screen)
        
        self.word_manager = word_manager
        self.audio_system = audio_system
        self.typography = typography
        self.progress_tracker = progress_tracker
        
        self.state = ChallengeState.IDLE
        self.current_word = None
        self.presentation: Optional[WordPresentation] = None
        self.starter_letters: List[str] = []    # Pre-displayed hints
        self.presentation_start_time = 0
        
        # Planet tracking (STORY-001-05)
        self.current_planet_id: Optional[str] = None
        self.current_planet_name: Optional[str] = None
        self.planet_manager: Optional[PlanetManager] = None
        
        # Input handling
        self.input_handler: Optional[InputHandler] = None
        self.input_display: Optional[InputDisplay] = None
        self.answer_validator: Optional[AnswerValidator] = None
        
        # Feedback system
        self.feedback_controller: Optional[FeedbackController] = None
        
        # Hint system
        self.hint_manager: Optional[HintManager] = None
        self.hint_display: Optional[HintDisplay] = None
        
        # Progress display (STORY-002-03)
        self.progress_display: Optional[ProgressDisplay] = None
        self.streak_display: Optional[StreakDisplay] = None
        self._last_mastered_count: int = 0
        
        # Streak bonus system (STORY-004-02)
        self.streak_bonus_manager: Optional[StreakBonusManager] = None
        self.active_bonus_animation = None
        self.active_bonus_message: Optional[BonusMessage] = None
        
        # Callbacks for state changes
        self.on_word_presented: Optional[Callable] = None
        self.on_input_changed: Optional[Callable] = None
        self.on_submit: Optional[Callable] = None
        self.on_invalid_input: Optional[Callable] = None
        self.on_feedback_shown: Optional[Callable] = None
        self.on_word_complete: Optional[Callable] = None
        self.on_hint_used: Optional[Callable] = None  # For analytics tracking
        self.on_planet_complete: Optional[Callable] = None  # STORY-001-05
        
        # Performance tracking
        self.render_times: List[float] = []
        
        # Captain Cosmos integration (STORY-004-04)
        # Get singleton instance with audio_system for TTS integration
        self.captain = get_captain_cosmos(audio_system=self.audio_system)
        
        # Initialize TTS manager for visual indicator (STORY-006-02)
        self.tts_manager = TTSManager()
        
        # Space theme integration (STORY-005-01)
        self.theme = get_theme()
        self.star_field: Optional[StarField] = None
        
        # Music manager (STORY-005-04)
        self.music_manager = get_music_manager()
        
        # Animated word display (STORY-005-05)
        self.animated_word_display: Optional[AnimatedWordDisplay] = None
        
        # TTS Manager for visual indicator (STORY-006-02)
        self.tts_manager: Optional[TTSManager] = None
    
    def on_enter(self):
        """Called when screen becomes active - start gameplay music and initialize UI."""
        try:
            self.music_manager.initialize()
            self.music_manager.play(MusicState.GAMEPLAY)
        except Exception as e:
            # Music initialization failed - continue without music
            logger.warning(f"Could not initialize music in spelling challenge: {e}")
        
        # Initialize UI components that need screen dimensions
        self._initialize_ui_components()
        
        # Start presenting the first word
        try:
            self.start_new_word()
        except Exception as e:
            logger.error(f"Failed to start first word: {e}")
            # Screen still renders, just with no word presented
    
    def _initialize_ui_components(self):
        """Initialize basic UI components."""
        # Star field always needs to be initialized
        if self.star_field is None:
            self.star_field = StarField(self.screen_rect.width, self.screen_rect.height)
        
        # Progress display (optional)
        if self.progress_display is None and self.progress_tracker:
            self.progress_display = create_progress_display(self.progress_tracker)
        
        # Feedback controller
        if self.feedback_controller is None:
            self.feedback_controller = create_feedback_controller()
        
        # Note: input_handler, input_display, hint_manager, hint_display, streak_display, planet_manager
        # will be initialized when a word is presented
        
        # Initialize planet manager (done when word is presented)
        # self.planet_manager = None
    
    def start_new_word(self):
        """Start presenting a new word to spell."""
        # Get the next word from word manager
        if not self.word_manager:
            logger.warning("Word manager not available")
            return
        
        logger.info(f"Starting new word - word_manager has {len(self.word_manager.all_words)} words")
        
        # Get a random word for the challenge
        word = self.word_manager.get_random_word() if self.word_manager else None
        if not word:
            logger.warning("No words available")
            return
        
        logger.info(f"Selected word: {word.text} (id={word.id}, difficulty={word.difficulty})")
        logger.info(f"Starter letters: {list(word.get_starter_letters())}")
        logger.info(f"Remaining letters to type: {len(word.text) - len(word.get_starter_letters())}")
        
        # Present the word with screen dimensions for star field
        screen_width = self.screen_rect.width if self.screen_rect else 800
        screen_height = self.screen_rect.height if self.screen_rect else 600
        self.present_word(word, planet_id="planet-1", planet_name="Mercury", 
                         screen_width=screen_width, screen_height=screen_height)
    
    def present_word(self, word, planet_id: Optional[str] = None, planet_name: Optional[str] = None, screen_width: int = 800, screen_height: int = 600):
        """
        Present a word with audio and starter hints.
        
        Args:
            word: SpellingWord object to present
            planet_id: Planet identifier for tracking
            planet_name: Planet name for tracking  
            screen_width: Screen width for star field initialization
            screen_height: Screen height for star field initialization
            
        Returns:
            True if presentation started successfully
        """
        logger.info(f"present_word called: word={word.text}, planet_id={planet_id}, planet_name={planet_name}")
        logger.info(f"Screen dimensions: {screen_width}x{screen_height}")
        
        # Initialize star field if not already created (STORY-005-01)
        if not self.star_field:
            logger.info("Creating star field")
            self.star_field = StarField(screen_width, screen_height)
        
        start_time = time.time()
        
        self.current_word = word
        self.presentation_start_time = start_time
        
        # Initialize planet manager if new planet
        if planet_id and (not self.planet_manager or self.current_planet_id != planet_id):
            self.current_planet_id = planet_id
            self.current_planet_name = planet_name or planet_id
            # Get all words for this planet from word_manager
            planet_words = self.word_manager.get_words_for_planet(planet_id)
            self.planet_manager = create_planet_manager(planet_id, self.current_planet_name, planet_words)
            
            # Set up planet completion callback
            self.planet_manager.on_planet_complete = self._on_planet_complete
        
        # Extract starter letters based on difficulty
        self.starter_letters = list(word.get_starter_letters())
        
        # Calculate remaining letters to type
        remaining_length = len(word.text) - len(self.starter_letters)
        
        # Initialize input handler for remaining letters
        self.input_handler = InputHandler(max_length=remaining_length)
        self.input_display = InputDisplay(max_length=remaining_length)
        self.answer_validator = AnswerValidator(word.text, ''.join(self.starter_letters))
        
        # Initialize feedback controller (only if not already created)
        if not self.feedback_controller:
            self.feedback_controller = create_feedback_controller(self.audio_system)
        # Set callbacks (always set them, in case controller was recreated)
        self.feedback_controller.on_feedback_shown = self._on_feedback_shown
        self.feedback_controller.on_auto_advance = self._on_auto_advance
        self.feedback_controller.on_hint_requested = self._on_hint_requested
        self.feedback_controller.on_feedback_complete = self._on_feedback_complete
        
        # Initialize hint system
        self.hint_manager = create_hint_manager(word.text)
        self.hint_manager.on_hint_shown = self._on_hint_shown
        
        self.hint_display = create_hint_display(self.typography, hint_manager=self.hint_manager)
        self.hint_display.set_word(word.text)
        self.hint_display.on_help_clicked = self._request_hint
        
        # Update progress tracker with planet info (STORY-001-05)
        if self.progress_tracker and planet_id:
            self.progress_tracker.start_planet(planet_id, self.current_planet_name)
            
            # Update word total from word manager
            total_words = self.word_manager.get_total_word_count()
            self.progress_tracker.set_total_words(total_words)
            
            # Initialize progress display (STORY-002-03)
            if not self.progress_display:
                self.progress_display = create_progress_display(self.progress_tracker)
            
            # Initialize streak display (STORY-004-01)
            if not self.streak_display:
                # Dynamic position based on screen size for responsiveness
                screen_width = self.screen.get_width()
                self.streak_display = create_streak_display(
                    screen=self.screen,
                    streak_tracker=self.progress_tracker.streak_tracker,
                    position=(screen_width - 100, 20)  # Right-aligned, 100px from edge
                )
            
            # Initialize streak bonus manager (STORY-004-02)
            if not self.streak_bonus_manager:
                self.streak_bonus_manager = create_streak_bonus_manager()
                self.streak_bonus_manager.on_bonus_triggered = self._on_bonus_triggered
        
        # Initialize streak display (STORY-004-01) - outside progress_tracker check
        if not self.streak_display:
            try:
                # Dynamic position based on screen size for responsiveness
                screen_width = self.screen.get_width()
                # Only initialize if progress_tracker is available (streak_tracker is needed)
                if self.progress_tracker:
                    self.streak_display = create_streak_display(
                        screen=self.screen,
                        streak_tracker=self.progress_tracker.streak_tracker,
                        position=(screen_width - 100, 20)  # Right-aligned, 100px from edge
                    )
                else:
                    logger.info("Skipping streak_display initialization (progress_tracker not available)")
            except Exception as e:
                logger.warning(f"Could not initialize streak_display: {e}")
        
        # Initialize animated word display (STORY-005-05) - outside progress_tracker check
        if not self.animated_word_display:
            logger.info(f"Creating animated_word_display with typography={self.typography is not None}")
            self.animated_word_display = create_animated_word_display(
                typography=self.typography,
                font_size=48,
                letter_spacing=20,
                starter_count=len(self.starter_letters)
            )
            logger.info("animated_word_display created successfully")
        else:
            logger.info("Using existing animated_word_display")
        
        # Set the word and show starter letters
        logger.info(f"Setting word: {word.text}, starter_count: {len(self.starter_letters)}")
        self.animated_word_display.set_word(word.text, starter_count=len(self.starter_letters))
        self.animated_word_display.show_starter_letters()
        self.animated_word_display.start_animation()
        logger.info(f"animated_word_display initialized: {self.animated_word_display is not None}")
        
        # Check if progress_tracker is available
        logger.info(f"progress_tracker available: {self.progress_tracker is not None}")
        logger.info(f"planet_id passed: {planet_id}")
        
        # Initialize hint system
        self.hint_manager = create_hint_manager(word.text)
        self.hint_manager.on_hint_shown = self._on_hint_shown
        
        self.hint_display = create_hint_display(self.typography, hint_manager=self.hint_manager)
        self.hint_display.set_word(word.text)
        self.hint_display.on_help_clicked = self._request_hint
        
        logger.info(f"hint_display created: {self.hint_display is not None}")
        
        # Set up input handler and display for typing
        remaining_length = len(word.text) - len(self.starter_letters)
        self.input_handler = InputHandler(max_length=remaining_length)
        self.input_display = InputDisplay(max_length=remaining_length)
        self.answer_validator = AnswerValidator(word.text, ''.join(self.starter_letters))
        
        logger.info(f"input_handler and input_display created for {remaining_length} letters")
        
        # Start tracking the word (STORY-002-01)
        if self.progress_tracker:
            self.progress_tracker.start_word(word.id, word.text)
        
        # Set up callbacks
        self.input_handler.on_input_changed = self._on_input_changed
        self.input_handler.on_invalid_input = self._on_invalid_input
        self.input_handler.on_submit = self._on_submit
        self.input_handler.on_complete = self._on_input_complete
        
        # Create presentation data
        self.presentation = WordPresentation(
            word_text=word.text,
            definition=word.definition,
            context_sentence=word.context_sentence,
            starter_letters=word.get_starter_letters(),
            difficulty=word.difficulty
        )
        
        # Speak the word
        def on_speech_complete():
            self.state = ChallengeState.READY_FOR_INPUT
            if self.on_word_presented:
                self.on_word_presented(self.presentation)
        
        self.state = ChallengeState.PRESENTING
        self.audio_system.speak(word.text, on_complete=on_speech_complete)
        
        # Track performance
        render_time = (time.time() - start_time) * 1000  # Convert to ms
        self.render_times.append(render_time)
        
        # Performance check: should be under WORD_PRESENTATION_TIMEOUT_MS
        if render_time > WORD_PRESENTATION_TIMEOUT_MS:
            print(f"Warning: Word presentation took {render_time:.0f}ms (target: <{WORD_PRESENTATION_TIMEOUT_MS}ms)")
        
        return True
    
    def replay_audio(self):
        """Replay the word audio on demand."""
        if self.current_word and self.presentation:
            def on_complete():
                pass  # No state change needed
            return self.audio_system.speak(self.current_word.text, on_complete=on_complete)
        return False
    
    def _on_input_changed(self, input_text: str):
        """Handle input change event."""
        # Update input display with animation
        if self.input_display:
            letters = list(input_text)
            self.input_display.set_letters(letters)
        
        if self.on_input_changed:
            self.on_input_changed(input_text)
    
    def _on_invalid_input(self, reason):
        """Handle invalid input event."""
        # Trigger shake animation for visual feedback
        if self.input_display:
            self.input_display.trigger_shake()
        
        if self.on_invalid_input:
            self.on_invalid_input(reason)
    
    def _on_input_complete(self, input_text: str):
        """Handle input completion (max length reached)."""
        # Auto-submit when word is fully typed
        is_correct, full_answer = self.submit_answer()
        
        if self.on_submit:
            self.on_submit(is_correct, full_answer)
    
    def _on_submit(self, input_text: str):
        """Handle submit event from input handler."""
        is_correct, full_answer = self.submit_answer()
        
        if self.on_submit:
            self.on_submit(is_correct, full_answer)
    
    def _on_feedback_shown(self, feedback_type: FeedbackType):
        """Handle feedback being shown."""
        import time
        logger.info(f"_on_feedback_shown called with {feedback_type}")
        
        # Record incorrect attempt when retry feedback shown (STORY-002-01)
        if feedback_type == FeedbackType.RETRY and self.progress_tracker:
            self.progress_tracker.record_attempt(False)
            # Reset streak on incorrect answer (STORY-004-01)
            self.progress_tracker.record_incorrect_answer()
            # Update streak display to hide it
            if self.streak_display:
                self.streak_display.update_streak(0)
            
            # Force complete retry feedback after 1 second to clear input
            import time as time_module
            self._retry_force_complete_time = time_module.time() + 1.0
            logger.info(f"Retry force complete time set to {self._retry_force_complete_time}")
        
        if self.on_feedback_shown:
            self.on_feedback_shown(feedback_type)
    
    def _on_feedback_complete(self, feedback_type: FeedbackType):
        """Handle feedback being completed."""
        logger.info(f"_on_feedback_complete called with {feedback_type}")
        # For retry feedback, clear input and reset state to allow another try
        if feedback_type == FeedbackType.RETRY:
            # Clear the input
            if self.input_handler:
                logger.info("Clearing input after retry")
                self.input_handler.clear()
            
            # Reset state to allow user to try again
            self.state = ChallengeState.READY_FOR_INPUT
            logger.info(f"State reset to {self.state}")
            
            # Trigger shake animation on input display to indicate error
            if self.input_display:
                self.input_display.trigger_shake()
    
    def _on_auto_advance(self):
        """Handle auto-advance after correct answer."""
        logger.info("_on_auto_advance called!")
        
        # Record word result for planet tracking (STORY-001-05)
        if self.planet_manager and self.current_word:
            # Get attempts from input handler
            attempts = 1  # Default to 1, will be updated if hints were used
            if self.hint_manager:
                hint_analytics = self.hint_manager.get_analytics()
                attempts = hint_analytics.get('hints_used', 0) + 1  # hints + original attempt
            
            self.planet_manager.record_word_result(
                word_id=self.current_word.id,
                word_text=self.current_word.text,
                correct=True,
                attempts=attempts
            )
        
        # Complete word tracking (STORY-002-01)
        just_mastered = False
        if self.progress_tracker:
            # Check if word was just mastered BEFORE completing (to capture the transition)
            if self.progress_display:
                self._last_mastered_count = self.progress_tracker.get_mastered_count()
            
            self.progress_tracker.complete_word(True)
            
            # Trigger completion flash if a new word was completed
            if self.progress_display:
                current_count = self.progress_tracker.get_mastered_count()
                if current_count > self._last_mastered_count:
                    self.progress_display.trigger_completion_flash()
            
            # Record correct answer for streak tracking (STORY-004-01)
            new_streak = self.progress_tracker.record_correct_answer()
            
            # Update streak display
            if self.streak_display:
                self.streak_display.update_streak(new_streak)
            
            # Check for bonus milestones (STORY-004-02)
            if self.streak_bonus_manager:
                bonus = self.streak_bonus_manager.check_milestone(new_streak)
                if bonus:
                    self._start_bonus_animation(bonus, new_streak)
        
        # Captain Cosmos feedback (STORY-004-04)
        if self.captain:
            # Trigger Captain response for correct answer
            self.captain.on_correct_answer()
            
            # Check for streak milestones
            if new_streak in [3, 5, 10]:
                self.captain.on_streak_milestone(new_streak)
        
        if self.on_word_complete:
            self.on_word_complete(True)  # True = success
        
        # Start the next word
        self.start_new_word()
    
    def _on_hint_requested(self):
        """Handle hint request after incorrect answer."""
        # Enable the help button for student-requested hints
        if self.hint_display:
            self.hint_display.enable_help_button()
    
    def _on_hint_shown(self, hint_data):
        """Handle hint being shown (for analytics).
        
        Note: Hint usage is recorded in _request_hint() to avoid double-counting.
        This callback is only triggered for hints shown via _request_hint().
        """
        if self.on_hint_used:
            self.on_hint_used(hint_data)
        
        # Update hint display
        if self.hint_display and self.hint_manager:
            # Get encouragement message for enhanced user experience
            encouragement = self.hint_manager.get_encouragement_message()
            
            self.hint_display.show_hint(
                hint_data.message,
                hint_data.revealed_indices,
                encouragement_message=encouragement
            )
            # Also update the animated word display with revealed letters
            self._update_animated_word_display_with_hints(hint_data.revealed_indices)
    
    def _on_bonus_triggered(self, bonus):
        """Handle bonus milestone triggered event.
        
        Args:
            bonus: BonusMilestone that was triggered
        """
        # The actual animation is started by _start_bonus_animation
        # This callback is just for logging/analytics if needed
        pass
    
    def _start_bonus_animation(self, bonus, streak: int):
        """Start the appropriate bonus animation.
        
        Args:
            bonus: BonusMilestone that was triggered
            streak: Current streak value
        """
        screen = self.screen
        
        # Create bonus message
        if bonus.bonus_type.name == 'GOLDEN_ROCKET':
            self.active_bonus_message = create_golden_boost_message(
                screen,
                bonus.message
            )
            # Create rocket boost animation at streak display position with fallback
            # Use default position as fallback to prevent crash if streak_display is missing
            rocket_pos = (screen.get_width() - 100, screen.get_height() // 2)
            if self.streak_display and hasattr(self.streak_display, 'position'):
                rocket_pos = self.streak_display.position
            self.active_bonus_animation = create_rocket_boost_animation(screen, rocket_pos)
        elif bonus.bonus_type.name == 'PLANET_DISCOVERY':
            self.active_bonus_message = create_planet_discovery_message(
                screen,
                bonus.message
            )
            # Create planet discovery animation - planet appears to the right of screen
            planet_pos = (screen.get_width() - 100, screen.get_height() // 2)
            rocket_start = self.streak_display.position if self.streak_display else (screen.get_width() // 2, screen.get_height() // 2)
            self.active_bonus_animation = create_planet_discovery_animation(screen, rocket_start, planet_pos)
    
    def render_bonus_animation(self, screen):
        """Render active bonus animations.
        
        Args:
            screen: Pygame surface to render on
        """
        # Render planet discovery animation (behind other UI)
        if self.active_bonus_animation:
            self.active_bonus_animation.render()
        
        # Render bonus message (overlay)
        if self.active_bonus_message:
            self.active_bonus_message.render()
    
    def update_bonus_animation(self, dt: float):
        """Update bonus animation state.
        
        Args:
            dt: Time delta in seconds
        """
        try:
            # Update bonus message
            if self.active_bonus_message:
                self.active_bonus_message.update(dt)
                if self.active_bonus_message.is_complete():
                    self.active_bonus_message = None
            
            # Update bonus animation
            if self.active_bonus_animation:
                self.active_bonus_animation.update(dt)
                if self.active_bonus_animation.is_complete():
                    # Clear animation but keep message if needed
                    self.active_bonus_animation = None
                    # Clear any streak bonus entity that might reference it
                    if self.streak_bonus_manager:
                        self.streak_bonus_manager.clear_active_bonus()
        except Exception as e:
            # Log error and clear animations to prevent crash
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating bonus animation: {e}")
            self.active_bonus_animation = None
            self.active_bonus_message = None
    
    def render_background(self, screen):
        """
        Render the space theme background (STORY-005-01).
        
        This fills the screen with deep space blue and renders the star field.
        Call this BEFORE rendering other UI elements.
        
        Args:
            screen: Pygame surface to render on
        """
        # Fill with deep space blue background
        screen.fill(self.theme.get_color("space_blue"))
        
        # Render star field
        if self.star_field:
            self.star_field.render(screen)
    
    def render_progress_display(self, screen):
        """
        Render the words mastered counter on the screen (STORY-002-03).
        
        Args:
            screen: Pygame surface to render on
        """
        if self.progress_display and self.progress_tracker:
            self.progress_display.render(screen)
    
    def render_streak_display(self, screen):
        """
        Render the streak counter on the screen (STORY-004-01).
        
        Args:
            screen: Pygame surface to render on
        """
        if self.streak_display:
            self.streak_display.render(screen)
    
    def render_tts_indicator(self, screen):
        """
        Render TTS active indicator (STORY-006-02).
        
        Args:
            screen: Pygame surface to render on
        """
        if self.tts_manager and self.tts_manager.is_enabled:
            self._render_tts_indicator(screen)
    
    def _render_tts_indicator(self, screen):
        """Render TTS active indicator."""
        font = pygame.font.Font(None, 24)
        
        # Show TTS status
        tts_text = "🔊 TTS Active" if self.tts_manager.is_speaking() else "🔊 TTS Ready"
        tts_surf = font.render(tts_text, True, (33, 150, 243))  # Blue color
        screen.blit(tts_surf, (20, 20))  # Top-left position
    
    def _on_planet_complete(self, planet_result):
        """
        Handle planet completion event.
        
        Args:
            planet_result: PlanetResult from PlanetManager
        """
        # Also record in progress tracker
        if self.progress_tracker and self.current_planet_id:
            for word_result in planet_result.word_results:
                self.progress_tracker.record_planet_word_result(
                    word_id=word_result.word_id,
                    word_text=word_result.word_text,
                    correct=word_result.correct,
                    attempts=word_result.attempts
                )
        
        # Notify callback
        if self.on_planet_complete:
            self.on_planet_complete(planet_result)
    
    def _request_hint(self):
        """Handle student clicking the 'Need Help?' button."""
        if self.hint_manager:
            hint = self.hint_manager.get_next_hint()
            if hint and self.hint_display:
                # Record hint usage in progress tracker (STORY-002-01)
                # This is the canonical place to record hint usage to avoid double-counting
                if self.progress_tracker:
                    self.progress_tracker.record_hint_usage()
                
                # Get encouragement message for enhanced user experience
                encouragement = self.hint_manager.get_encouragement_message()
                
                self.hint_display.show_hint(
                    hint.message,
                    hint.revealed_indices,
                    encouragement_message=encouragement
                )
                # Update animated word display with revealed hint letters
                if self.animated_word_display:
                    for index in hint.revealed_indices:
                        self.animated_word_display.reveal_letter(index)
                # Disable button after use until next incorrect answer
                self.hint_display.disable_help_button()
    
    def _update_animated_word_display_with_hints(self, revealed_indices):
        """Update the animated word display to show revealed hint letters.
        
        Args:
            revealed_indices: Set or list of indices revealed by hints
        """
        if not self.animated_word_display or not self.current_word:
            return
        
        # Mark revealed letters as hints in the animated display
        for index in revealed_indices:
            if index >= len(self.starter_letters):  # Only hint-revealed, not starters
                self.animated_word_display.set_letter_as_hint(index)
    
    def _update_word_display_with_hints(self):
        """Update the input display (typed letters) to show revealed hint letters."""
        if not self.hint_manager or not self.input_display or not self.current_word:
            return
        
        # Get revealed indices from hint manager
        revealed_indices = self.hint_manager.get_revealed_indices()
        
        # Build the full display list merging starter letters with revealed hint letters
        full_display = []
        for i, letter in enumerate(self.current_word.text):
            if i < len(self.starter_letters):
                # Starter letter
                full_display.append(('starter', letter))
            elif i in revealed_indices:
                # Hint-revealed letter
                full_display.append(('hint', letter))
            else:
                # Hidden letter
                full_display.append(('hidden', '_'))
        
        # Actually update the display with the full state
        self.input_display.set_full_display(full_display)
    
    def handle_key_input(self, key: str, unicode_char: Optional[str] = None):
        """
        Handle a key press from the student.
        
        Args:
            key: The pygame key constant name (e.g., 'K_a', 'K_BACKSPACE')
            unicode_char: The actual character from event.unicode
        """
        if self.state != ChallengeState.READY_FOR_INPUT or not self.input_handler:
            return
        
        self.input_handler.handle_keydown(key, unicode_char)
    
    def handle_virtual_key(self, character: str):
        if self.state != ChallengeState.READY_FOR_INPUT or not self.input_handler:
            return
        
        self.input_handler.handle_virtual_key(character)
    
    def handle_backspace(self):
        """Handle backspace key press."""
        if self.state != ChallengeState.READY_FOR_INPUT or not self.input_handler:
            return
        
        self.input_handler.handle_keydown('K_BACKSPACE')
    
    def submit_answer(self):
        """
        Submit the current answer for validation.
        
        Returns:
            Tuple of (is_correct, full_answer)
        """
        logger.info(f"submit_answer called, state={self.state}, feedback_controller={self.feedback_controller is not None}")
        
        # Allow submission during PRESENTING or READY_FOR_INPUT state
        if self.state not in [ChallengeState.PRESENTING, ChallengeState.READY_FOR_INPUT]:
            logger.warning(f"Cannot submit: state={self.state}")
            return False, ""
        
        if not self.input_handler or not self.answer_validator:
            logger.warning("Cannot submit: input_handler or answer_validator is None")
            return False, ""
        
        # Get current input
        current_input = self.input_handler.get_input()
        logger.info(f"Current input to validate: '{current_input}'")
        
        # Validate using AnswerValidator
        result = self.answer_validator.validate(current_input)
        logger.info(f"Validation result: is_correct={result.is_correct}")
        
        # Show feedback immediately (within 100ms target)
        if self.feedback_controller:
            logger.info("Calling feedback_controller.show_feedback()")
            self.feedback_controller.show_feedback(result.is_correct)
        else:
            logger.error("feedback_controller is None!")
        
        self.state = ChallengeState.AWAITING_RESPONSE
        
        if self.on_submit:
            self.on_submit(result.is_correct, result.full_answer)
        
        return result.is_correct, result.full_answer
    
    def get_current_input(self) -> str:
        """Get the letters currently typed by the student (excluding starters)."""
        if self.input_handler:
            return self.input_handler.get_input()
        return ""
    
    def get_full_answer(self) -> str:
        """Get the complete answer including starter letters."""
        current = self.get_current_input()
        return ''.join(self.starter_letters) + current
    
    def get_word_text(self) -> str:
        """Get the target word text."""
        return self.current_word.text if self.current_word else ""
    
    def get_starter_display(self) -> str:
        """Get the starter letters as a string for display."""
        return ''.join(self.starter_letters)
    
    def get_definition(self) -> str:
        """Get the word definition."""
        return self.presentation.definition if self.presentation else ""
    
    def get_context_sentence(self) -> str:
        """Get the context sentence."""
        return self.presentation.context_sentence if self.presentation else ""
    
    def is_audio_available(self) -> bool:
        """Check if audio/TTS is available."""
        return self.audio_system.is_audio_available()
    
    def get_performance_stats(self) -> dict:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with render time stats
        """
        if not self.render_times:
            return {"avg_ms": 0, "max_ms": 0, "min_ms": 0}
        
        return {
            "avg_ms": sum(self.render_times) / len(self.render_times),
            "max_ms": max(self.render_times),
            "min_ms": min(self.render_times),
            "sample_count": len(self.render_times)
        }
    
    def get_feedback_message(self) -> str:
        """
        Get the current feedback message.
        
        Returns:
            Feedback message text or empty string
        """
        if self.feedback_controller:
            return self.feedback_controller.get_feedback_message()
        return ""
    
    def is_feedback_active(self) -> bool:
        """
        Check if feedback is currently being shown.
        
        Returns:
            True if feedback is active
        """
        if self.feedback_controller:
            return self.feedback_controller.is_feedback_active()
        return False
    
    def get_feedback_state(self) -> FeedbackScreenState:
        """
        Get the current feedback state.
        
        Returns:
            Current FeedbackState
        """
        if self.feedback_controller:
            return self.feedback_controller.get_state()
        return FeedbackScreenState.IDLE
    
    def reset(self):
        """Reset the screen to idle state."""
        self.state = ChallengeState.IDLE
        self.current_word = None
        self.presentation = None
        self.starter_letters = []
        self.input_handler = None
        self.input_display = None
        self.answer_validator = None
        if self.feedback_controller:
            self.feedback_controller.reset()
        if self.hint_manager:
            self.hint_manager.reset()
        if self.hint_display:
            self.hint_display.reset()
        # Reset planet tracking (STORY-001-05)
        if self.planet_manager:
            self.planet_manager.reset()
        self.current_planet_id = None
        self.current_planet_name = None
        self.cursor_visible = True
        
        # Reset progress display tracking (STORY-002-03)
        self._last_mastered_count = 0
        
        # Reset streak display (STORY-004-01)
        if getattr(self, 'streak_display', None):
            self.streak_display.update_streak(0)
        
        # Reset bonus animations (STORY-004-02)
        self.active_bonus_animation = None
        self.active_bonus_message = None
        if self.streak_bonus_manager:
            self.streak_bonus_manager.reset_session()
        
        # Reset animated word display (STORY-005-05)
        if self.animated_word_display:
            self.animated_word_display.reset()
        
        # Reset star field (STORY-005-01)
        if self.star_field:
            # Keep star field but reset doesn't need to regenerate stars
            pass
    
    def get_hint_analytics(self) -> dict:
        """
        Get hint usage analytics for progress tracking.
        
        Returns:
            Dictionary with hint usage statistics
        """
        if self.hint_manager:
            return self.hint_manager.get_analytics()
        return {}

    def handle_event(self, event: pygame.event.Event) -> None:
        """
        Handle pygame events.
        
        Args:
            event: Pygame event
        """
        # Let input handler handle keyboard events
        if self.input_handler:
            self.input_handler.handle_event(event)
        
        # Handle mouse clicks for hint button
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                self.handle_mouse_click(event.pos[0], event.pos[1])
        
        # Handle back navigation
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Return to main menu
                from src.screens.main_menu import MainMenuScreen
                self.next_screen = MainMenuScreen
    
    def update(self) -> None:
        """
        Update screen state.
        """
        import time
        current_time = time.time()  # Get current time in seconds
        
        # Update star field animation
        if self.star_field:
            self.star_field.update(1.0 / 60.0)
        
        # Update feedback animations
        if self.feedback_controller:
            try:
                self.feedback_controller.update(current_time)
                # Log feedback state for debugging
                if self.feedback_controller.get_state() != FeedbackScreenState.IDLE:
                    pass  # Debug: feedback is active
            except Exception as e:
                logger.error(f"Error updating feedback controller: {e}")
            
            # Force complete retry feedback after delay to allow another attempt
            if hasattr(self, '_retry_force_complete_time') and self._retry_force_complete_time:
                if current_time >= self._retry_force_complete_time:
                    logger.info(f"Forcing retry feedback complete at {current_time}")
                    self.feedback_controller.force_complete()
                    self._retry_force_complete_time = None
        
        # Update hint display (if exists and initialized)
        if hasattr(self, 'hint_display') and self.hint_display:
            try:
                self.hint_display.update(current_time)
            except:
                pass  # Hint display may not be fully initialized
        
        # Update input display (cursor blink, shake animation)
        if self.input_display:
            try:
                self.input_display.update(current_time)
            except:
                pass  # Input display may not be fully initialized
    
    def draw(self) -> None:
        """
        Draw the spelling challenge screen to the display.
        """
        # Clear screen with space blue background
        self.screen.fill(SPACE_BLUE)
        
        # Draw star field background
        if self.star_field:
            self.star_field.render(self.screen)
        
        # Draw planets (if planet manager exists)
        if hasattr(self, 'planet_manager') and self.planet_manager:
            try:
                self.planet_manager.render_planet(self.screen)
            except:
                pass
        
        # Draw progress display (top-right corner)
        if self.progress_display:
            try:
                self.progress_display.render(self.screen)
            except:
                pass
        
        # Draw title/text area (only if we have a current word)
        if self.typography and self.current_word and self.presentation:
            try:
                # Word title
                title_style = self.typography.style_word_display
                title_surface = self.typography.render_text(self.get_word_text(), title_style)
                self.screen.blit(title_surface, (40, 60))
                
                # Definition (with more vertical spacing since word display is large)
                if self.get_definition():
                    def_style = self.typography.style_definition
                    def_surface = self.typography.render_text(f"Definition: {self.get_definition()}", def_style)
                    self.screen.blit(def_surface, (40, 125))
            except:
                pass  # Skip text rendering if styles not available
        
        # Draw animated word display (the word letters)
        if self.animated_word_display:
            try:
                self.animated_word_display.render(self.screen, (self.screen_rect.centerx, 200))
            except:
                pass  # Skip rendering if there's an issue
        
        # Draw input/answer area (center)
        if self.input_display:
            try:
                self.input_display.render(self.screen)
            except:
                pass
        
        # Draw starter hints overlay
        if hasattr(self, 'hint_display') and self.hint_display:
            try:
                self.hint_display.render(self.screen)
            except:
                pass
        
        # Draw feedback (correct/incorrect)
        if self.feedback_controller and self.feedback_controller.get_state() != FeedbackScreenState.IDLE:
            try:
                # Set render position to screen center
                self.feedback_controller.set_render_position(
                    self.screen.get_width() // 2,
                    self.screen.get_height() // 2
                )
                self.feedback_controller.render(self.screen)
            except:
                pass
        
        # Draw hint button (bottom)
        if hasattr(self, 'hint_display') and self.hint_display:
            try:
                self.hint_display.render_hint_button(self.screen)
            except:
                pass
    
    def handle_mouse_click(self, x: int, y: int) -> bool:
        """
        Handle mouse click for hint button.
        
        Args:
            x: Mouse X position
            y: Mouse Y position
            
        Returns:
            True if hint button was clicked
        """
        if self.hint_display:
            return self.hint_display.check_button_click(x, y)
        return False


class HintRenderer:
    """
    Renders starter letter hints with distinct styling.
    
    This component handles the visual distinction between
    starter hints and student-typed letters.
    """
    
    def __init__(self, typography):
        """
        Initialize the hint renderer.
        
        Args:
            typography: Typography instance for text rendering
        """
        self.typography = typography
    
    def render_starter_hint(
        self, 
        letter: str, 
        position: tuple,
        is_revealed: bool = True
    ):
        """
        Render a single starter letter hint.
        
        Args:
            letter: The letter to render
            position: (x, y) position
            is_revealed: Whether the hint is currently visible
        """
        if not is_revealed:
            return None  # Hidden hint
        
        style = self.typography.style_starter_letters
        return self.typography.render_text(letter.upper(), style)
    
    def render_starter_hints(
        self, 
        starter_letters: str,
        base_position: tuple,
        letter_spacing: int = 10
    ) -> List[tuple]:
        """
        Render all starter hints in a row.
        
        Args:
            starter_letters: String of starter letters
            base_position: Starting (x, y) position
            letter_spacing: Additional spacing between letters
            
        Returns:
            List of (surface, position) tuples for blitting
        """
        rendered = []
        x, y = base_position
        
        for letter in starter_letters:
            surface = self.render_starter_hint(letter, (x, y))
            if surface:
                rendered.append((surface, (x, y)))
                x += surface.get_width() + letter_spacing
        
        return rendered


# Factory function for creating the screen
def create_spelling_challenge_screen(
    screen,
    word_manager=None,
    audio_system=None,
    typography=None,
    progress_tracker=None
):
    """
    Create a SpellingChallengeScreen with dependencies.
    
    Args:
        screen: The pygame display surface
        word_manager: Optional WordManager instance
        audio_system: Optional AudioSystem instance
        typography: Optional Typography instance
        progress_tracker: Optional ProgressTracker instance
        
    Returns:
        Configured SpellingChallengeScreen instance
    """
    from src.components.word_manager import get_word_manager
    from src.components.audio_system import get_audio_system
    from src.ui.typography import get_typography
    
    return SpellingChallengeScreen(
        screen=screen,
        word_manager=word_manager or get_word_manager(),
        audio_system=audio_system or get_audio_system(),
        typography=typography or get_typography(),
        progress_tracker=progress_tracker
    )

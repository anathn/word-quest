"""
Planet Results Screen

Displays planet completion results and determines next actions based on
mastery threshold (4/5 correct unlocks next planet, 2-3/5 retries, 0-1/5 needs help).
"""

from typing import Optional, Callable, List, Dict
from dataclasses import dataclass
from enum import Enum
import logging
import time
import pygame

from src.components.planet_manager import PlanetManager, PlanetStatus, PlanetResult
from src.components.audio_system import AudioSystem
from src.ui.typography import Typography
from src.ui.screen_manager import Screen
from src.audio.music_manager import get_music_manager, MusicState

logger = logging.getLogger(__name__)


class ResultsState(Enum):
    """State of the results screen."""
    IDLE = "idle"
    SHOWING_RESULTS = "showing_results"
    CELEBRATING = "celebrating"
    AWAITING_ACTION = "awaiting_action"


@dataclass
class WordResultDisplay:
    """Display data for a single word result."""
    word_text: str
    is_correct: bool
    attempts: int
    is_mastered: bool  # First-attempt correct


class PlanetResultsScreen(Screen):
    """
    Screen for displaying planet completion results.
    """

    def __init__(
        self,
        typography: Typography,
        audio_system: AudioSystem,
        screen: Optional[pygame.Surface] = None,
    ):
        """
        Initialize the planet results screen.

        Args:
            typography: Typography instance for text rendering
            audio_system: AudioSystem instance for audio feedback
            screen: Optional pygame surface (required for live gameplay)
        """
        if screen is None:
            # Unit tests construct without a display surface.
            if not pygame.get_init():
                pygame.init()
            screen = pygame.Surface((800, 600))
        super().__init__(screen)

        self.typography = typography
        self.audio_system = audio_system

        self.state = ResultsState.IDLE
        self.planet_result: Optional[PlanetResult] = None
        self.word_displays: List[WordResultDisplay] = []
        self.results_start_time = 0

        self.current_planet_number: int = 0
        self.total_planets: int = 12

        self.on_continue: Optional[Callable[[], None]] = None
        self.on_retry: Optional[Callable[[], None]] = None
        self.on_practice: Optional[Callable[[], None]] = None
        self.on_transition_to_next_planet: Optional[Callable] = None
        self.on_back_to_menu: Optional[Callable[[], None]] = None

        self.title_position = (400, 100)
        self.results_position = (400, 250)
        self.button_position = (400, 500)
        self._button_rect = pygame.Rect(0, 0, 320, 56)
        self._button_hover = False
        self._button_pressed = False
        self._action_consumed = False

        self.planet_sprite = None
        self.planet_bloom = None
        self.sparkles = None
        self.celebration = None
        self.bloom_planet_number = 1
        self.bloom_triggered = False

        self.music_manager = get_music_manager()

    def on_enter(self):
        """Called when screen becomes active."""
        try:
            self.music_manager.initialize()
            self.music_manager.play(MusicState.CELEBRATION)
        except Exception as e:
            logger.warning(f"Could not initialize music in planet results: {e}")

        if self.planet_result is None:
            # Allow construction-then-show_results before push.
            return

    def show_results(self, planet_result: PlanetResult):
        """Display planet results."""
        self.planet_result = planet_result
        self.state = ResultsState.SHOWING_RESULTS
        self.results_start_time = time.time()

        self.word_displays = [
            WordResultDisplay(
                word_text=wr.word_text,
                is_correct=wr.correct,
                attempts=wr.attempts,
                is_mastered=wr.first_attempt
            )
            for wr in (planet_result.word_results or [])
        ]

        self._play_result_audio()

        if planet_result.status == PlanetStatus.COMPLETED:
            try:
                self._trigger_bloom_celebration()
            except Exception as e:
                logger.warning(f"Bloom celebration skipped: {e}")

        self.state = ResultsState.AWAITING_ACTION
        self._layout_button()

    def _layout_button(self):
        cx, cy = self.button_position
        self._button_rect = pygame.Rect(0, 0, 360, 56)
        self._button_rect.center = (self.screen_rect.centerx, cy)

    def _trigger_bloom_celebration(self):
        """Optional celebration; never required for progress."""
        from src.ui.planet_sprite import PlanetSprite
        from src.ui.planet_bloom import create_planet_bloom
        from src.ui.sparkle_effect import create_sparkle_effect
        from src.ui.celebration_renderer import create_celebration_renderer

        planet_name = self.planet_result.planet_name if self.planet_result else "Planet 1"
        planet_num_str = planet_name.replace("Planet", "").strip() if planet_name else "1"
        try:
            self.bloom_planet_number = int(planet_num_str)
        except ValueError:
            self.bloom_planet_number = 1

        self.planet_sprite = PlanetSprite(self.bloom_planet_number, 120)
        self.planet_bloom = create_planet_bloom(self.planet_sprite, self.bloom_planet_number)
        self.sparkles = create_sparkle_effect((self.screen_rect.centerx, 350))
        self.celebration = create_celebration_renderer(
            planet_bloom=self.planet_bloom,
            sparkles=self.sparkles,
            rocket=None
        )
        self.celebration.start_celebration((self.screen_rect.centerx, 350))
        self.bloom_triggered = True

    def _play_result_audio(self):
        """Play audio feedback based on planet result."""
        if not self.planet_result or not self.audio_system:
            return

        status = self.planet_result.status
        try:
            # Clear any leftover gameplay speech so encouragement is immediate.
            self.audio_system.stop()
            if status == PlanetStatus.COMPLETED:
                fanfare = getattr(self.audio_system, "play_victory_fanfare", None)
                if callable(fanfare):
                    fanfare()
                else:
                    self.audio_system.play_sfx("transition")
                self.audio_system.speak("Planet complete! Great job!")
            elif status == PlanetStatus.RETRY:
                tone = getattr(self.audio_system, "play_encouraging_tone", None)
                if callable(tone):
                    tone()
                self.audio_system.speak(
                    f"Good effort! {self.planet_result.first_attempt_correct} out of 5 words mastered."
                )
            else:
                tone = getattr(self.audio_system, "play_gentle_tone", None)
                if callable(tone):
                    tone()
                self.audio_system.speak(
                    f"Let's practice more. {self.planet_result.first_attempt_correct} out of 5 words mastered."
                )
        except Exception as e:
            logger.warning(f"Result audio failed: {e}")

    def get_title_text(self) -> str:
        if not self.planet_result:
            return ""
        status = self.planet_result.status
        if status == PlanetStatus.COMPLETED:
            return "Planet Complete!"
        if status == PlanetStatus.RETRY:
            return "Good Effort!"
        return "Let's Practice More"

    def get_summary_text(self) -> str:
        if not self.planet_result:
            return ""
        status = self.planet_result.status
        correct = self.planet_result.first_attempt_correct
        total = self.planet_result.total_words
        if status == PlanetStatus.COMPLETED:
            return f"You mastered {correct} out of {total} words on the first try!"
        if status == PlanetStatus.RETRY:
            return f"You mastered {correct} out of {total} words. Let's try again!"
        return f"You mastered {correct} out of {total} words. Let's practice more!"

    def get_action_button_text(self) -> str:
        if not self.planet_result:
            return "Continue"
        status = self.planet_result.status
        if status == PlanetStatus.COMPLETED:
            return "Continue to Next Planet"
        if status == PlanetStatus.RETRY:
            return "Try Again"
        return "Practice More"

    def get_action_button_color(self) -> tuple:
        if not self.planet_result:
            return (255, 255, 255)
        status = self.planet_result.status
        if status == PlanetStatus.COMPLETED:
            return (34, 139, 34)
        if status == PlanetStatus.RETRY:
            return (255, 140, 0)
        return (30, 144, 255)

    def handle_action_button_click(self):
        if not self.planet_result or self._action_consumed:
            return
        self._action_consumed = True
        self._button_pressed = True

        # Stop encouragement immediately so Continue feels instant.
        if self.audio_system:
            try:
                self.audio_system.stop()
            except Exception:
                pass

        status = self.planet_result.status
        if status == PlanetStatus.COMPLETED:
            if self.on_transition_to_next_planet and self.planet_result.unlock_next:
                from_planet_num = self.current_planet_number
                to_planet_num = from_planet_num + 1
                progress = to_planet_num / max(self.total_planets, 1)
                self.on_transition_to_next_planet(
                    self.planet_result.planet_name,
                    f"Planet {to_planet_num}",
                    from_planet_num,
                    to_planet_num,
                    progress,
                )
            elif self.on_continue:
                self.on_continue()
        elif status == PlanetStatus.RETRY:
            if self.on_retry:
                self.on_retry()
        else:
            if self.on_practice:
                self.on_practice()

    def get_word_results_display(self) -> List[WordResultDisplay]:
        return self.word_displays.copy()

    def is_mastered(self) -> bool:
        return self.planet_result is not None and self.planet_result.status == PlanetStatus.COMPLETED

    def needs_retry(self) -> bool:
        return self.planet_result is not None and self.planet_result.status == PlanetStatus.RETRY

    def needs_help(self) -> bool:
        return self.planet_result is not None and self.planet_result.status == PlanetStatus.NEEDS_HELP

    def should_unlock_next(self) -> bool:
        return self.planet_result is not None and self.planet_result.unlock_next

    def should_notify_parent(self) -> bool:
        return self.planet_result is not None and self.planet_result.notify_parent

    def get_progress_percent(self) -> float:
        if not self.planet_result or self.planet_result.total_words == 0:
            return 0.0
        return self.planet_result.first_attempt_correct / self.planet_result.total_words

    def set_planet_info(self, planet_number: int, total_planets: int):
        self.current_planet_number = planet_number
        self.total_planets = total_planets

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEMOTION:
            self._button_hover = self._button_rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.handle_action_button_click()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.on_back_to_menu:
                self.on_back_to_menu()
            elif self.on_continue:
                self.on_continue()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._button_rect.collidepoint(event.pos):
                self._button_pressed = True
                self.handle_action_button_click()
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._button_pressed = False

    def update(self, current_time: float = None) -> None:
        """ScreenManager calls update() with no args; tests may pass a timestamp."""
        if self.state == ResultsState.CELEBRATING and self.celebration:
            try:
                self.celebration.update(1 / 60.0)
                if self.celebration.is_complete():
                    self.state = ResultsState.AWAITING_ACTION
            except Exception:
                self.state = ResultsState.AWAITING_ACTION

    def get_performance_ms(self) -> float:
        if self.results_start_time == 0:
            return 0.0
        return (time.time() - self.results_start_time) * 1000

    def reset(self):
        self.state = ResultsState.IDLE
        self.planet_result = None
        self.word_displays.clear()
        self.results_start_time = 0
        self.planet_sprite = None
        self.planet_bloom = None
        self.sparkles = None
        self.celebration = None
        self.bloom_triggered = False

    def draw(self) -> None:
        self.screen.fill((26, 26, 62))
        if not self.planet_result:
            return

        font = pygame.font.Font(None, 48)
        small = pygame.font.Font(None, 32)

        title = font.render(self.get_title_text(), True, (255, 255, 255))
        self.screen.blit(title, title.get_rect(center=(self.screen_rect.centerx, 100)))

        summary = small.render(self.get_summary_text(), True, (220, 220, 220))
        self.screen.blit(summary, summary.get_rect(center=(self.screen_rect.centerx, 160)))

        y = 220
        for word_result in self.word_displays:
            color = (76, 175, 80) if word_result.is_correct else (244, 67, 54)
            label = small.render(word_result.word_text, True, color)
            self.screen.blit(label, label.get_rect(center=(self.screen_rect.centerx, y)))
            y += 36

        self._layout_button()
        color = self.get_action_button_color()
        if self._button_pressed:
            color = tuple(max(0, c - 40) for c in color)
        elif self._button_hover:
            color = tuple(min(255, c + 30) for c in color)
        pygame.draw.rect(self.screen, color, self._button_rect, border_radius=8)
        # Simple pressed inset so the click is obvious even if transition is brief.
        if self._button_pressed:
            inset = self._button_rect.inflate(-6, -6)
            pygame.draw.rect(self.screen, tuple(max(0, c - 60) for c in color), inset, border_radius=6)
        btn = small.render(self.get_action_button_text(), True, (255, 255, 255))
        self.screen.blit(btn, btn.get_rect(center=self._button_rect.center))

    # Back-compat alias used by older call sites / tests
    def render(self, screen: pygame.Surface):
        previous = self.screen
        self.screen = screen
        self.screen_rect = screen.get_rect()
        try:
            self.draw()
        finally:
            self.screen = previous
            self.screen_rect = previous.get_rect()

def create_planet_results_screen(
    typography: Typography,
    audio_system: AudioSystem,
    screen: Optional[pygame.Surface] = None,
) -> PlanetResultsScreen:
    """Factory for PlanetResultsScreen."""
    return PlanetResultsScreen(typography, audio_system, screen=screen)


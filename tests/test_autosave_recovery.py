"""Tests for per-word auto-save and crash recovery."""

from src.components.data_store import DataStore
from src.components.planet_manager import PlanetManager
from src.components.progress_tracker import ProgressTracker
from src.components.word_manager import SpellingWord


def make_words():
    return [
        SpellingWord(
            id=f"w{i}",
            text=f"word{i}",
            definition=f"definition {i}",
            context_sentence=f"Use word{i} in a sentence.",
            difficulty=1,
            starter_letters=2
        )
        for i in range(5)
    ]


def complete_word(tracker, word, attempts=1):
    tracker.start_word(word.id, word.text)
    for attempt in range(attempts):
        tracker.record_attempt(attempt == attempts - 1)
    tracker.complete_word(True)
    tracker.record_planet_word_result(
        word.id, word.text, correct=True, attempts=attempts
    )


def create_active_tracker(tmp_path):
    store = DataStore(base_path=str(tmp_path))
    tracker = ProgressTracker(student_id="student", data_store=store)
    words = make_words()
    tracker.start_session("session-1")
    tracker.set_total_planets(12)
    tracker.start_planet("planet-1", "Mercury")
    tracker.set_planet_word_order([word.id for word in words])
    return store, tracker, words


def test_checkpoint_written_after_each_completed_word(tmp_path):
    store, tracker, words = create_active_tracker(tmp_path)

    complete_word(tracker, words[0])

    progress = store.load("student").data
    checkpoint = progress["active_checkpoint"]
    assert checkpoint["planet_id"] == "planet-1"
    assert checkpoint["next_word_index"] == 1
    assert checkpoint["word_ids"] == [word.id for word in words]
    assert checkpoint["word_results"][0]["word_id"] == words[0].id
    assert checkpoint["session"]["words"][0]["word_id"] == words[0].id


def test_new_tracker_restores_unfinished_session_and_planet(tmp_path):
    store, tracker, words = create_active_tracker(tmp_path)
    complete_word(tracker, words[0])
    complete_word(tracker, words[1], attempts=2)

    restored = ProgressTracker(student_id="student", data_store=store)
    checkpoint = restored.get_active_checkpoint()

    assert restored.current_session.session_id == "session-1"
    assert restored.current_planet_id == "planet-1"
    assert [result["word_id"] for result in restored.planet_word_results] == [
        words[0].id,
        words[1].id
    ]
    assert len(restored.session_tracker.current_session.words) == 2
    assert checkpoint["next_word_index"] == 2


def test_planet_manager_resumes_at_next_unfinished_word(tmp_path):
    _, tracker, words = create_active_tracker(tmp_path)
    complete_word(tracker, words[0])
    complete_word(tracker, words[1])
    checkpoint = tracker.get_active_checkpoint()

    manager = PlanetManager("planet-1", "Mercury", words)
    manager.restore_progress(
        checkpoint["word_results"], checkpoint["next_word_index"]
    )

    assert manager.get_word_index() == 2
    assert manager.get_current_word().id == words[2].id
    assert len(manager.get_word_results()) == 2


def test_planet_completion_clears_checkpoint_and_saves_session(tmp_path):
    store, tracker, words = create_active_tracker(tmp_path)

    for word in words:
        complete_word(tracker, word)

    progress = store.load("student").data
    assert "active_checkpoint" not in progress
    assert len(progress["sessions"]) == 1
    assert progress["sessions"][0]["planet_completed"] == "planet-1"
    assert len(progress["sessions"][0]["words"]) == 5
    assert progress["galaxy_progress"]["completed_planets"] == 1
    assert progress["galaxy_progress"]["current_planet_number"] == 2

    restored = ProgressTracker(student_id="student", data_store=store)
    assert restored.get_current_planet_number() == 2


def test_summary_updates_preserve_existing_progress_document(tmp_path):
    store = DataStore(base_path=str(tmp_path))
    progress = store.load("student").data
    progress["sessions"] = [{"session_id": "existing"}]
    assert store.save("student", progress).success

    tracker = ProgressTracker(student_id="student", data_store=store)
    tracker.set_total_words(60)

    reloaded = store.load("student").data
    assert reloaded["sessions"] == [{"session_id": "existing"}]
    assert reloaded["total_words_in_list"] == 60

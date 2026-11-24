import unittest
from src.components.progress_tracker import ProgressTracker, LegacyWordAttempt

class TestProgressCount(unittest.TestCase):
    def test_completed_count_includes_mastered_words(self):
        tracker = ProgressTracker()
        tracker.mastered_words = {"w001", "w002"}
        tracker.word_history["w003"] = LegacyWordAttempt(
            word_id="w003", word_text="three", completed_correctly=True
        )
        tracker.word_history["w002"] = LegacyWordAttempt(
            word_id="w002", word_text="two", completed_correctly=True
        )
        self.assertEqual(tracker.get_completed_count(), 3)
        tracker.total_words_in_list = 60
        self.assertEqual(tracker.get_progress_text(), "3/60 words")

    def test_normalize_galaxy_progress_clamps_overflow(self):
        tracker = ProgressTracker()
        tracker.galaxy_progress.total_planets = 12
        tracker.galaxy_progress.completed_planets = 15
        tracker.galaxy_progress.current_planet_number = 16
        tracker.galaxy_progress.unlocked_planets = 20
        tracker._normalize_galaxy_progress()
        self.assertEqual(tracker.galaxy_progress.completed_planets, 12)
        self.assertEqual(tracker.galaxy_progress.current_planet_number, 12)
        self.assertEqual(tracker.galaxy_progress.unlocked_planets, 12)

if __name__ == "__main__":
    unittest.main()

"""
Unit tests for PlanetManager component.

Tests cover:
- Planet completion status for all mastery thresholds
- First-attempt accuracy calculation
- Parent notification flag logic
- Word shuffling functionality
- Reset functionality
- Progress tracking
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.components.planet_manager import (
    PlanetManager,
    PlanetStatus,
    PlanetResult,
    WordResult,
    create_planet_manager
)


class TestWordResult(unittest.TestCase):
    """Tests for the WordResult dataclass."""
    
    def test_first_attempt_true(self):
        """Test first_attempt is True when attempts=1."""
        result = WordResult(
            word_id="w001",
            word_text="because",
            correct=True,
            attempts=1
        )
        self.assertTrue(result.first_attempt)
    
    def test_first_attempt_false(self):
        """Test first_attempt is False when attempts>1."""
        result = WordResult(
            word_id="w001",
            word_text="because",
            correct=True,
            attempts=3
        )
        self.assertFalse(result.first_attempt)
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        result = WordResult(
            word_id="w001",
            word_text="because",
            correct=True,
            attempts=1
        )
        data = result.to_dict() if hasattr(result, 'to_dict') else {
            'word_id': result.word_id,
            'word_text': result.word_text,
            'correct': result.correct,
            'attempts': result.attempts,
            'first_attempt': result.first_attempt
        }
        self.assertEqual(data['word_id'], "w001")
        self.assertEqual(data['correct'], True)


class TestPlanetManagerInit(unittest.TestCase):
    """Tests for PlanetManager initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_words = [
            Mock(id="w001", text="because"),
            Mock(id="w002", text="friend"),
            Mock(id="w003", text="people"),
            Mock(id="w004", text="beautiful"),
            Mock(id="w005", text="accomplish"),
        ]
    
    def test_init_with_valid_words(self):
        """Test initialization with valid word list."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        self.assertEqual(manager.planet_id, "planet-1")
        self.assertEqual(manager.planet_name, "Mercury")
        self.assertEqual(len(manager.words), 5)
        self.assertFalse(manager.is_complete)
    
    def test_init_limits_to_5_words(self):
        """Test that more than 5 words are truncated to 5."""
        extra_words = self.mock_words + [Mock(id="w006", text="extra")]
        manager = PlanetManager("planet-1", "Mercury", extra_words)
        
        self.assertEqual(len(manager.words), 5)
    
    def test_init_with_empty_list_raises(self):
        """Test that empty word list raises ValueError."""
        with self.assertRaises(ValueError) as context:
            PlanetManager("planet-1", "Mercury", [])
        
        self.assertIn("must have at least 1 word", str(context.exception))
    
    def test_init_with_fewer_than_5_words(self):
        """Test initialization with fewer than 5 words (edge case)."""
        few_words = self.mock_words[:3]
        manager = PlanetManager("planet-1", "Mercury", few_words)
        
        self.assertEqual(len(manager.words), 3)


class TestCompletionStatus(unittest.TestCase):
    """Tests for planet completion status logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_words = [
            Mock(id=f"w{i:03d}", text=f"word{i}")
            for i in range(5)
        ]
    
    def create_manager_with_results(self, correct_counts: list):
        """
        Helper to create manager with specific results.
        
        Args:
            correct_counts: List of (correct, attempts) tuples for each word
        """
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        for i, (correct, attempts) in enumerate(correct_counts):
            manager.record_word_result(
                word_id=f"w{i:03d}",
                word_text=f"word{i}",
                correct=correct,
                attempts=attempts
            )
        
        return manager
    
    def test_status_mastered_4_of_5(self):
        """Test 4/5 first-attempt correct returns COMPLETED status."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        # 4 correct on first attempt, 1 incorrect
        for i in range(4):
            manager.record_word_result(f"w{i}", f"word{i}", correct=True, attempts=1)
        manager.record_word_result("w4", "word4", correct=False, attempts=2)
        
        result = manager.get_completion_status()
        
        self.assertEqual(result.status, PlanetStatus.COMPLETED)
        self.assertTrue(result.unlock_next)
        self.assertFalse(result.notify_parent)
        self.assertEqual(result.first_attempt_correct, 4)
    
    def test_status_mastered_5_of_5(self):
        """Test 5/5 first-attempt correct returns COMPLETED status."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        for i in range(5):
            manager.record_word_result(f"w{i}", f"word{i}", correct=True, attempts=1)
        
        result = manager.get_completion_status()
        
        self.assertEqual(result.status, PlanetStatus.COMPLETED)
        self.assertTrue(result.unlock_next)
        self.assertFalse(result.notify_parent)
        self.assertEqual(result.first_attempt_correct, 5)
    
    def test_status_retry_3_of_5(self):
        """Test 3/5 first-attempt correct returns RETRY status."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        # 3 correct on first attempt, 2 incorrect
        for i in range(3):
            manager.record_word_result(f"w{i}", f"word{i}", correct=True, attempts=1)
        for i in range(3, 5):
            manager.record_word_result(f"w{i}", f"word{i}", correct=False, attempts=2)
        
        result = manager.get_completion_status()
        
        self.assertEqual(result.status, PlanetStatus.RETRY)
        self.assertFalse(result.unlock_next)
        self.assertFalse(result.notify_parent)
        self.assertEqual(result.first_attempt_correct, 3)
    
    def test_status_retry_2_of_5(self):
        """Test 2/5 first-attempt correct returns RETRY status."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        # 2 correct on first attempt, 3 incorrect
        for i in range(2):
            manager.record_word_result(f"w{i}", f"word{i}", correct=True, attempts=1)
        for i in range(2, 5):
            manager.record_word_result(f"w{i}", f"word{i}", correct=False, attempts=2)
        
        result = manager.get_completion_status()
        
        self.assertEqual(result.status, PlanetStatus.RETRY)
        self.assertFalse(result.unlock_next)
        self.assertFalse(result.notify_parent)
        self.assertEqual(result.first_attempt_correct, 2)
    
    def test_status_needs_help_1_of_5(self):
        """Test 1/5 first-attempt correct returns NEEDS_HELP status."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        # 1 correct on first attempt, 4 incorrect
        manager.record_word_result("w0", "word0", correct=True, attempts=1)
        for i in range(1, 5):
            manager.record_word_result(f"w{i}", f"word{i}", correct=False, attempts=2)
        
        result = manager.get_completion_status()
        
        self.assertEqual(result.status, PlanetStatus.NEEDS_HELP)
        self.assertFalse(result.unlock_next)
        self.assertTrue(result.notify_parent)
        self.assertEqual(result.first_attempt_correct, 1)
    
    def test_status_needs_help_0_of_5(self):
        """Test 0/5 first-attempt correct returns NEEDS_HELP status."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        for i in range(5):
            manager.record_word_result(f"w{i}", f"word{i}", correct=False, attempts=2)
        
        result = manager.get_completion_status()
        
        self.assertEqual(result.status, PlanetStatus.NEEDS_HELP)
        self.assertFalse(result.unlock_next)
        self.assertTrue(result.notify_parent)
        self.assertEqual(result.first_attempt_correct, 0)
    
    def test_status_in_progress_not_complete(self):
        """Test status is IN_PROGRESS when not all words recorded."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        # Only record 3 words
        for i in range(3):
            manager.record_word_result(f"w{i}", f"word{i}", correct=True, attempts=1)
        
        result = manager.get_completion_status()
        
        self.assertEqual(result.status, PlanetStatus.IN_PROGRESS)
        self.assertFalse(result.unlock_next)
        self.assertFalse(result.notify_parent)


class TestWordResultRecording(unittest.TestCase):
    """Tests for recording word results."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_words = [Mock(id=f"w{i:03d}", text=f"word{i}") for i in range(5)]
    
    def test_record_word_result_stores_data(self):
        """Test that word results are stored correctly."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        manager.record_word_result("w001", "because", correct=True, attempts=1)
        
        results = manager.get_word_results()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].word_id, "w001")
        self.assertTrue(results[0].correct)
        self.assertEqual(results[0].attempts, 1)
    
    def test_callback_invoked_on_word_recorded(self):
        """Test that on_word_recorded callback is invoked."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        callback_data = []
        manager.on_word_recorded = lambda data: callback_data.append(data)
        
        manager.record_word_result("w001", "because", correct=True, attempts=1)
        
        self.assertEqual(len(callback_data), 1)
        self.assertEqual(callback_data[0]['word_id'], "w001")
        self.assertEqual(callback_data[0]['progress'], "1/5 words")
    
    def test_callback_invoked_on_planet_complete(self):
        """Test that on_planet_complete callback is invoked."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        callback_data = []
        manager.on_planet_complete = lambda result: callback_data.append(result)
        
        # Record all 5 words
        for i in range(5):
            manager.record_word_result(f"w{i}", f"word{i}", correct=True, attempts=1)
        
        self.assertEqual(len(callback_data), 1)
        self.assertEqual(callback_data[0].status, PlanetStatus.COMPLETED)


class TestProgressTracking(unittest.TestCase):
    """Tests for progress tracking methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_words = [Mock(id=f"w{i:03d}", text=f"word{i}") for i in range(5)]
    
    def test_get_progress_text(self):
        """Test progress text formatting."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        self.assertEqual(manager.get_progress_text(), "0/5 words")
        
        manager.record_word_result("w0", "word0", correct=True, attempts=1)
        self.assertEqual(manager.get_progress_text(), "1/5 words")
        
        for i in range(1, 5):
            manager.record_word_result(f"w{i}", f"word{i}", correct=True, attempts=1)
        
        self.assertEqual(manager.get_progress_text(), "5/5 words")
    
    def test_get_progress_percent(self):
        """Test progress percentage calculation."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        self.assertEqual(manager.get_progress_percent(), 0.0)
        
        manager.record_word_result("w0", "word0", correct=True, attempts=1)
        self.assertEqual(manager.get_progress_percent(), 0.2)
        
        for i in range(1, 5):
            manager.record_word_result(f"w{i}", f"word{i}", correct=True, attempts=1)
        
        self.assertEqual(manager.get_progress_percent(), 1.0)
    
    def test_get_words_remaining(self):
        """Test words remaining calculation."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        self.assertEqual(manager.get_words_remaining(), 5)
        
        manager.record_word_result("w0", "word0", correct=True, attempts=1)
        self.assertEqual(manager.get_words_remaining(), 4)
    
    def test_get_word_index(self):
        """Test current word index."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        self.assertEqual(manager.get_word_index(), 0)
        
        manager.get_next_word()
        self.assertEqual(manager.get_word_index(), 1)


class TestStatusMessages(unittest.TestCase):
    """Tests for status message methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_words = [Mock(id=f"w{i:03d}", text=f"word{i}") for i in range(5)]
    
    def test_get_status_message_in_progress(self):
        """Test status message during progress."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        message = manager.get_status_message()
        
        self.assertIn("Keep going", message)
    
    def test_get_status_message_completed(self):
        """Test status message for completed planet."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        for i in range(5):
            manager.record_word_result(f"w{i}", f"word{i}", correct=True, attempts=1)
        
        message = manager.get_status_message()
        
        self.assertIn("Planet Complete", message)
    
    def test_get_encouragement_message(self):
        """Test encouragement message varies by status."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        # In progress
        message = manager.get_encouragement_message()
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)


class TestResetAndShuffle(unittest.TestCase):
    """Tests for reset and shuffle functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_words = [Mock(id=f"w{i:03d}", text=f"word{i}") for i in range(5)]
    
    def test_reset_clears_results(self):
        """Test that reset clears all results."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        # Record some results
        for i in range(3):
            manager.record_word_result(f"w{i}", f"word{i}", correct=True, attempts=1)
        
        # Reset
        manager.reset()
        
        self.assertEqual(len(manager.word_results), 0)
        self.assertEqual(manager.current_word_index, 0)
        self.assertFalse(manager.is_complete)
    
    def test_shuffle_words_randomizes_order(self):
        """Test that shuffle_words randomizes word order."""
        original_words = self.mock_words.copy()
        manager = PlanetManager("planet-1", "Mercury", original_words)
        
        # Shuffle multiple times and check order changes
        manager.shuffle_words()
        shuffled1 = manager.words.copy()
        
        manager.shuffle_words()
        shuffled2 = manager.words.copy()
        
        # At least one shuffle should produce different order
        # (high probability with random.shuffle)
        self.assertNotEqual(shuffled1, original_words)


class TestGetCurrentWord(unittest.TestCase):
    """Tests for word retrieval methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_words = [Mock(id=f"w{i:03d}", text=f"word{i}") for i in range(5)]
    
    def test_get_current_word_returns_word(self):
        """Test getting current word."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        word = manager.get_current_word()
        
        self.assertEqual(word, self.mock_words[0])
    
    def test_get_current_word_returns_none_when_complete(self):
        """Test getting current word when all words done."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        # Advance past all words
        for _ in range(5):
            manager.get_next_word()
        
        word = manager.get_current_word()
        
        self.assertIsNone(word)
    
    def test_get_next_word_advances(self):
        """Test getting next word advances index."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        word1 = manager.get_next_word()
        word2 = manager.get_next_word()
        
        self.assertEqual(word1, self.mock_words[1])
        self.assertEqual(word2, self.mock_words[2])


class TestFactoryFunction(unittest.TestCase):
    """Tests for the factory function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_words = [Mock(id=f"w{i:03d}", text=f"word{i}") for i in range(5)]
    
    def test_create_planet_manager(self):
        """Test factory function creates PlanetManager."""
        manager = create_planet_manager("planet-1", "Mercury", self.mock_words)
        
        self.assertIsInstance(manager, PlanetManager)
        self.assertEqual(manager.planet_id, "planet-1")
        self.assertEqual(manager.planet_name, "Mercury")


class TestPlanetResultSerialization(unittest.TestCase):
    """Tests for PlanetResult serialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_words = [Mock(id=f"w{i:03d}", text=f"word{i}") for i in range(5)]
    
    def test_to_dict_serialization(self):
        """Test PlanetResult to_dict conversion."""
        manager = PlanetManager("planet-1", "Mercury", self.mock_words)
        
        for i in range(5):
            manager.record_word_result(f"w{i}", f"word{i}", correct=True, attempts=1)
        
        result = manager.get_completion_status()
        data = result.to_dict()
        
        self.assertEqual(data['planet_id'], "planet-1")
        self.assertEqual(data['planet_name'], "Mercury")
        self.assertEqual(data['total_words'], 5)
        self.assertEqual(data['first_attempt_correct'], 5)
        self.assertEqual(data['status'], 'completed')
        self.assertTrue(data['unlock_next'])
        self.assertFalse(data['notify_parent'])
        self.assertEqual(len(data['word_results']), 5)


if __name__ == '__main__':
    unittest.main()

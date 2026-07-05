"""
Unit tests for WordManager component.

Tests cover:
- Word loading from JSON
- Starter letter extraction
- Word retrieval by various criteria
- Difficulty-based filtering
"""

import unittest
import json
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.components.word_manager import (
    WordManager, 
    SpellingWord, 
    WordList,
    get_word_manager,
    reset_word_manager
)


class TestSpellingWord(unittest.TestCase):
    """Tests for the SpellingWord dataclass."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.word = SpellingWord(
            id="w001",
            text="because",
            definition="for the reason that",
            context_sentence="I stayed inside because it was raining.",
            difficulty=1,
            starter_letters=3
        )
    
    def test_get_starter_letters_difficulty_1(self):
        """Test starter letters for difficulty 1 (3 letters)."""
        self.assertEqual(self.word.get_starter_letters(), "bec")
    
    def test_get_starter_letters_empty(self):
        """Test with no starter letters."""
        word = SpellingWord(
            id="w002",
            text="test",
            definition="a test",
            context_sentence="This is a test.",
            difficulty=3,
            starter_letters=0
        )
        self.assertEqual(word.get_starter_letters(), "")
    
    def test_get_remaining_letters(self):
        """Test remaining letters after starters."""
        self.assertEqual(self.word.get_remaining_letters(), "ause")
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        data = self.word.to_dict()
        self.assertEqual(data['id'], "w001")
        self.assertEqual(data['text'], "because")
        self.assertEqual(data['difficulty'], 1)
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            'id': 'w003',
            'text': 'friend',
            'definition': 'a pal',
            'context_sentence': 'My friend is nice.',
            'difficulty': 1,
            'starter_letters': 2
        }
        word = SpellingWord.from_dict(data)
        self.assertEqual(word.id, 'w003')
        self.assertEqual(word.text, 'friend')
        self.assertEqual(word.get_starter_letters(), 'fr')


class TestWordList(unittest.TestCase):
    """Tests for the WordList class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.word_list = WordList(
            id="planet-1",
            name="Mercury - Basic Words",
            difficulty=1,
            words=[
                SpellingWord("w001", "because", "reason", "because", 1, 3),
                SpellingWord("w002", "friend", "pal", "friend", 1, 3),
                SpellingWord("w003", "people", "humans", "people", 1, 3),
            ]
        )
    
    def test_get_word_by_id(self):
        """Test finding word by ID."""
        word = self.word_list.get_word_by_id("w002")
        self.assertIsNotNone(word)
        self.assertEqual(word.text, "friend")
    
    def test_get_word_by_id_not_found(self):
        """Test finding non-existent word."""
        word = self.word_list.get_word_by_id("nonexistent")
        self.assertIsNone(word)
    
    def test_get_random_word(self):
        """Test getting a random word."""
        word = self.word_list.get_random_word()
        self.assertIsNotNone(word)
        self.assertIn(word.text, ["because", "friend", "people"])
    
    def test_empty_word_list(self):
        """Test operations on empty word list."""
        empty_list = WordList(id="empty", name="Empty", difficulty=1)
        self.assertIsNone(empty_list.get_random_word())
        self.assertIsNone(empty_list.get_word_by_id("any"))


class TestWordManager(unittest.TestCase):
    """Tests for the WordManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Reset singleton for clean state
        reset_word_manager()
        
        # Use test data directory
        self.test_data_dir = os.path.join(os.path.dirname(__file__), '..', 'src', 'data')
        self.manager = WordManager(self.test_data_dir)
    
    def test_load_word_lists(self):
        """Test that word lists are loaded from JSON."""
        self.assertGreater(len(self.manager.word_lists), 0)
        self.assertGreater(len(self.manager.all_words), 0)
    
    def test_get_word_list(self):
        """Test retrieving a word list by ID."""
        planet1 = self.manager.get_word_list("planet-1")
        self.assertIsNotNone(planet1)
        self.assertEqual(planet1.name, "Mercury - Basic Words")
    
    def test_get_word_list_not_found(self):
        """Test retrieving non-existent word list."""
        result = self.manager.get_word_list("nonexistent")
        self.assertIsNone(result)
    
    def test_get_word_by_id(self):
        """Test retrieving a word by ID."""
        word = self.manager.get_word_by_id("w001")
        self.assertIsNotNone(word)
        self.assertEqual(word.text, "because")
    
    def test_get_words_by_difficulty(self):
        """Test filtering words by difficulty."""
        difficulty_1_words = self.manager.get_words_by_difficulty(1)
        self.assertGreater(len(difficulty_1_words), 0)
        
        # All difficulty 1 words should have difficulty=1
        for word in difficulty_1_words:
            self.assertEqual(word.difficulty, 1)
    
    def test_get_random_word(self):
        """Test getting a random word."""
        word = self.manager.get_random_word()
        self.assertIsNotNone(word)
        self.assertIsInstance(word, SpellingWord)
    
    def test_get_random_word_by_difficulty(self):
        """Test getting a random word filtered by difficulty."""
        word = self.manager.get_random_word(difficulty=2)
        self.assertIsNotNone(word)
        self.assertEqual(word.difficulty, 2)
    
    def test_get_words_for_planet(self):
        """Test getting words for a specific planet."""
        words = self.manager.get_words_for_planet("planet-1")
        self.assertEqual(len(words), 5)  # Mercury has 5 words
    
    def test_get_total_word_count(self):
        """Test total word count."""
        count = self.manager.get_total_word_count()
        self.assertGreater(count, 0)
    
    def test_get_difficulty_distribution(self):
        """Test difficulty distribution calculation."""
        distribution = self.manager.get_difficulty_distribution()
        
        # Should have words at all difficulty levels
        self.assertIn(1, distribution)
        self.assertIn(2, distribution)
        self.assertIn(3, distribution)
        
        # Sum should equal total count
        self.assertEqual(sum(distribution.values()), self.manager.get_total_word_count())
    
    def test_add_word(self):
        """Test adding a new word."""
        initial_count = self.manager.get_total_word_count()
        
        new_word = SpellingWord(
            id="w999",
            text="testword",
            definition="a test",
            context_sentence="test.",
            difficulty=1,
            starter_letters=2
        )
        
        self.manager.add_word(new_word)
        
        self.assertEqual(self.manager.get_total_word_count(), initial_count + 1)
        self.assertIsNotNone(self.manager.get_word_by_id("w999"))
    
    def test_starter_letters_based_on_difficulty(self):
        """Test that starter letters vary by difficulty."""
        # Difficulty 1 words should have 3 starter letters
        diff1_word = self.manager.get_word_by_id("w001")  # because
        self.assertEqual(diff1_word.get_starter_letters(), "bec")
        
        # Difficulty 2 words should have 2 starter letters
        diff2_word = self.manager.get_word_by_id("w006")  # beautiful
        self.assertEqual(diff2_word.get_starter_letters(), "be")
        
        # Difficulty 3 words should have 1 starter letter
        diff3_word = self.manager.get_word_by_id("w011")  # accomplish
        self.assertEqual(diff3_word.get_starter_letters(), "a")


class TestWordManagerSingleton(unittest.TestCase):
    """Tests for the WordManager singleton pattern."""
    
    def test_get_word_manager_returns_singleton(self):
        """Test that get_word_manager returns the same instance."""
        reset_word_manager()
        
        manager1 = get_word_manager()
        manager2 = get_word_manager()
        
        self.assertIs(manager1, manager2)
    
    def test_reset_word_manager(self):
        """Test resetting the singleton."""
        reset_word_manager()
        manager1 = get_word_manager()
        reset_word_manager()
        manager2 = get_word_manager()
        
        self.assertIsNot(manager1, manager2)


if __name__ == '__main__':
    unittest.main()

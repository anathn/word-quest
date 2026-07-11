"""Unit tests for WordListManager."""
import pytest
import os
import sys
import json
import shutil
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.word_entry import Difficulty
from src.words.word_list_manager import WordListManager


class TestWordListManager:
    """Tests for WordListManager CRUD operations."""
    
    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_data_dir):
        """Create a WordListManager instance with temp directory."""
        return WordListManager(temp_data_dir)
    
    def test_add_word(self, manager):
        """Test adding a word to a word list."""
        word = manager.add_word("test_profile", "APPLE", "A red fruit", Difficulty.BEGINNER)
        
        assert word.spelling == "APPLE"
        assert word.definition == "A red fruit"
        assert word.difficulty == Difficulty.BEGINNER
        assert word.id is not None
    
    def test_get_words(self, manager):
        """Test retrieving words from a list."""
        manager.add_word("test_profile", "APPLE", "A red fruit")
        manager.add_word("test_profile", "BANANA", "A yellow fruit")
        
        words = manager.get_words("test_profile")
        
        assert len(words) == 2
        assert words[0].spelling == "APPLE"
        assert words[1].spelling == "BANANA"
    
    def test_get_words_by_difficulty(self, manager):
        """Test filtering words by difficulty."""
        manager.add_word("test_profile", "APPLE", "Easy word", Difficulty.BEGINNER)
        manager.add_word("test_profile", "BANANA", "Medium word", Difficulty.MEDIUM)
        manager.add_word("test_profile", "كالCULASH", "Hard word", Difficulty.ADVANCED)
        
        beginner_words = manager.get_words("test_profile", difficulty=Difficulty.BEGINNER)
        assert len(beginner_words) == 1
        assert beginner_words[0].spelling == "APPLE"
    
    def test_get_words_search(self, manager):
        """Test searching words."""
        manager.add_word("test_profile", "APPLE", "A red fruit")
        manager.add_word("test_profile", "BANANA", "A yellow fruit")
        manager.add_word("test_profile", "ORANGE", "A citrus fruit")
        
        # Search by spelling
        apple_words = manager.get_words("test_profile", search_terms="apple")
        assert len(apple_words) == 1
        assert apple_words[0].spelling == "APPLE"
        
        # Search by definition
        red_words = manager.get_words("test_profile", search_terms="red")
        assert len(red_words) == 1
        assert red_words[0].spelling == "APPLE"
        
        # Multiple search terms (OR logic - matches any term)
        yellow_fruit_words = manager.get_words("test_profile", search_terms="yellow fruit")
        # Finds words containing 'yellow' OR 'fruit' (all 3 words contain 'fruit')
        assert len(yellow_fruit_words) == 3
        
        # Search that matches one specific word
        citrus_words = manager.get_words("test_profile", search_terms="citrus")
        assert len(citrus_words) == 1
        assert citrus_words[0].spelling == "ORANGE"
    
    def test_update_word(self, manager):
        """Test updating a word."""
        # Add a word
        word = manager.add_word("test_profile", "APPLE", "A red fruit")
        
        # Update it
        updated = manager.update_word(
            "test_profile",
            word.id,
            definition="A delicious red fruit",
            difficulty=Difficulty.ADVANCED
        )
        
        assert updated.spelling == "APPLE"
        assert updated.definition == "A delicious red fruit"
        assert updated.difficulty == Difficulty.ADVANCED
    
    def test_update_word_not_found(self, manager):
        """Test updating a non-existent word raises error."""
        with pytest.raises(ValueError, match="Word not found"):
            manager.update_word("test_profile", "non-existent-id")
    
    def test_delete_word(self, manager):
        """Test deleting a word."""
        word = manager.add_word("test_profile", "APPLE")
        
        result = manager.delete_word("test_profile", word.id)
        
        assert result is True
        
        # Verify word is gone
        words = manager.get_words("test_profile")
        assert len(words) == 0
    
    def test_delete_word_not_found(self, manager):
        """Test deleting a non-existent word returns False."""
        result = manager.delete_word("test_profile", "non-existent-id")
        assert result is False
    
    def test_delete_word_gives_correct_result(self, manager):
        """Test add and delete flow."""
        # Add first
        word1 = manager.add_word("test_profile", "APPLE")
        word2 = manager.add_word("test_profile", "BANANA")
        
        # Delete one
        result = manager.delete_word("test_profile", word1.id)
        assert result is True
        
        # Verify only one remains
        words = manager.get_words("test_profile")
        assert len(words) == 1
        assert words[0].spelling == "BANANA"
    
    def test_bulk_import(self, manager):
        """Test bulk word import."""
        text = """APPLE A red fruit
BANANA A yellow fruit
CHERRY A small red fruit"""
        
        added, failed, words = manager.add_bulk_words("test_profile", text)
        
        assert added == 3
        assert failed == 0
        assert len(words) == 3
        assert words[0].spelling == "APPLE"
        assert words[1].spelling == "BANANA"
        assert words[2].spelling == "CHERRY"
    
    def test_bulk_import_with_invalid(self, manager):
        """Test bulk import with some invalid words."""
        text = """APPLE A red fruit
123INVALID Invalid number word
BANANA A yellow fruit"""
        
        added, failed, words = manager.add_bulk_words("test_profile", text)
        
        assert added == 2
        assert failed == 1
    
    def test_get_word_count(self, manager):
        """Test word count statistics."""
        manager.add_word("test_profile", "APPLE", difficulty=Difficulty.BEGINNER)
        manager.add_word("test_profile", "BANANA", difficulty=Difficulty.BEGINNER)
        manager.add_word("test_profile", "CALCULUS", difficulty=Difficulty.ADVANCED)
        
        counts = manager.get_word_count("test_profile")
        
        assert counts["total"] == 3
        assert counts["beginner"] == 2
        assert counts["medium"] == 0
        assert counts["advanced"] == 1
    
    def test_duplicate_word_rejected(self, manager):
        """Test that duplicate words are rejected."""
        manager.add_word("test_profile", "APPLE")
        
        with pytest.raises(ValueError, match="already exists"):
            manager.add_word("test_profile", "apple")  # Same word, different case
    
    def test_invalid_spelling_rejected(self, manager):
        """Test that invalid spellings are rejected."""
        with pytest.raises(ValueError):
            manager.add_word("test_profile", "123")  # Numbers
        
        with pytest.raises(ValueError):
            manager.add_word("test_profile", "")  # Empty
    
    def test_persistence(self, manager):
        """Test that words persist after reloading manager."""
        # Add a word
        manager.add_word("test_profile", "APPLE", "A red fruit")
        
        # Create a new manager instance (simulating restart)
        new_manager = WordListManager(manager.data_dir)
        
        # Verify word is still there
        words = new_manager.get_words("test_profile")
        assert len(words) == 1
        assert words[0].spelling == "APPLE"
    
    def test_empty_list(self, manager):
        """Test operations on empty word list."""
        words = manager.get_words("non_existent_profile")
        assert len(words) == 0
        
        counts = manager.get_word_count("non_existent_profile")
        assert counts["total"] == 0
    
    def test_case_normalization(self, manager):
        """Test that word spellings are normalized to uppercase."""
        word = manager.add_word("test_profile", "SQuIrReL")
        assert word.spelling == "SQUIRREL"
    
    def test_definition_truncation(self, manager):
        """Test that long definitions are truncated."""
        long_definition = "a" * 300
        word = manager.add_word("test_profile", "APPLE", long_definition)
        
        assert len(word.definition) <= 255
    
    def test_clear_word_list(self, manager):
        """Test clearing all words."""
        manager.add_word("test_profile", "APPLE")
        manager.add_word("test_profile", "BANANA")
        
        count = manager.clear_word_list("test_profile")
        
        assert count == 2
        
        words = manager.get_words("test_profile")
        assert len(words) == 0
    
    def test_word_sorting(self, manager):
        """Test that words are returned in alphabetical order."""
        manager.add_word("test_profile", "ZEBRA")
        manager.add_word("test_profile", "APPLE")
        manager.add_word("test_profile", "MANGO")
        
        words = manager.get_words("test_profile")
        
        assert words[0].spelling == "APPLE"
        assert words[1].spelling == "MANGO"
        assert words[2].spelling == "ZEBRA"
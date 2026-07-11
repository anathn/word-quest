"""Unit tests for word entry data model."""
import pytest
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.word_entry import WordEntry, Difficulty
from datetime import datetime


class TestWordEntry:
    """Tests for WordEntry dataclass."""
    
    def test_create_basic_word(self):
        """Test creating a word with just spelling."""
        word = WordEntry(spelling="apple")
        assert word.spelling == "APPLE"  # Should be uppercase
        assert word.definition == ""
        assert word.difficulty == Difficulty.MEDIUM
        assert word.id is not None
        assert word.created_date is not None
        assert word.last_modified is not None
    
    def test_create_word_with_all_fields(self):
        """Test creating a word with all fields set."""
        word = WordEntry(
            spelling="banana",
            definition="A yellow fruit",
            difficulty=Difficulty.BEGINNER
        )
        assert word.spelling == "BANANA"
        assert word.definition == "A yellow fruit"
        assert word.difficulty == Difficulty.BEGINNER
    
    def test_difficulty_from_string(self):
        """Test creating Difficulty from string."""
        assert Difficulty.from_string("beginner") == Difficulty.BEGINNER
        assert Difficulty.from_string("BEGINNER") == Difficulty.BEGINNER
        assert Difficulty.from_string("medium") == Difficulty.MEDIUM
        assert Difficulty.from_string("advanced") == Difficulty.ADVANCED
        assert Difficulty.from_string("invalid") == Difficulty.MEDIUM  # Default
    
    def test_word_validate_valid(self):
        """Test validation of valid words."""
        assert WordEntry(spelling="apple").validate() is True
        assert WordEntry(spelling="apricot").validate() is True
        assert WordEntry(spelling="self-check").validate() is True  # Hyphen allowed
    
    def test_word_validate_empty(self):
        """Test validation rejects empty spelling."""
        assert WordEntry(spelling="").validate() is False
        assert WordEntry(spelling="   ").validate() is False
    
    def test_word_validate_too_short(self):
        """Test validation rejects words that are too short."""
        assert WordEntry(spelling="a").validate() is False
    
    def test_word_validate_too_long(self):
        """Test validation rejects words that are too long."""
        assert WordEntry(spelling="abcdefghijklmnopqrstuvwxyz").validate() is False
    
    def test_word_validate_numbers_rejected(self):
        """Test validation rejects words with numbers."""
        assert WordEntry(spelling="apple123").validate() is False
    
    def test_to_dict(self):
        """Test converting WordEntry to dictionary."""
        word = WordEntry(
            spelling="apple",
            definition="A red fruit",
            difficulty=Difficulty.BEGINNER
        )
        data = word.to_dict()
        
        assert data["spelling"] == "APPLE"
        assert data["definition"] == "A red fruit"
        assert data["difficulty"] == "beginner"
        assert "id" in data
        assert "created_date" in data
        assert "last_modified" in data
    
    def test_from_dict(self):
        """Test creating WordEntry from dictionary."""
        data = {
            "id": "test-id-123",
            "spelling": "APPLE",
            "definition": "A red fruit",
            "difficulty": "beginner",
            "created_date": "2026-07-01T10:00:00",
            "last_modified": "2026-07-01T10:00:00"
        }
        
        word = WordEntry.from_dict(data)
        
        assert word.id == "test-id-123"
        assert word.spelling == "APPLE"
        assert word.definition == "A red fruit"
        assert word.difficulty == Difficulty.BEGINNER


class TestWordEntryPersistence:
    """Tests for WordEntry serialization."""
    
    def test_roundtrip_serialization(self):
        """Test that to_dict/from_dict preserves all data."""
        original = WordEntry(
            spelling="cherry",
            definition="A small red fruit",
            difficulty=Difficulty.ADVANCED
        )
        
        data = original.to_dict()
        restored = WordEntry.from_dict(data)
        
        assert original.id == restored.id
        assert original.spelling == restored.spelling
        assert original.definition == restored.definition
        assert original.difficulty == restored.difficulty
        assert original.created_date.isoformat() == restored.created_date.isoformat()
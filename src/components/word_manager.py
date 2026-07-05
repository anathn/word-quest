"""
Word Manager Component

Manages word data, loading word lists, and providing word presentation
methods including starter letter extraction based on difficulty.
"""

import json
import os
import random
import threading
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class SpellingWord:
    """Represents a single spelling word with metadata."""
    id: str
    text: str
    definition: str
    context_sentence: str
    difficulty: int
    starter_letters: int
    planet_id: Optional[str] = None
    
    def get_starter_letters(self) -> str:
        """
        Get the starter hint letters based on difficulty.
        
        Returns:
            The first N letters of the word as hints
        """
        count = self.starter_letters
        return self.text[:count] if count > 0 else ""
    
    def get_remaining_letters(self) -> str:
        """
        Get the letters that need to be typed by the student.
        
        Returns:
            The remaining letters after starter hints
        """
        count = self.starter_letters
        return self.text[count:] if count < len(self.text) else ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert word to dictionary representation."""
        return {
            'id': self.id,
            'text': self.text,
            'definition': self.definition,
            'context_sentence': self.context_sentence,
            'difficulty': self.difficulty,
            'starter_letters': self.starter_letters,
            'planet_id': self.planet_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpellingWord':
        """Create a SpellingWord from a dictionary."""
        return cls(
            id=data['id'],
            text=data['text'],
            definition=data['definition'],
            context_sentence=data['context_sentence'],
            difficulty=data['difficulty'],
            starter_letters=data.get('starter_letters', 2),
            planet_id=data.get('planet_id')
        )


@dataclass
class WordList:
    """Represents a collection of words for a planet/level."""
    id: str
    name: str
    difficulty: int
    words: List[SpellingWord] = field(default_factory=list)
    
    def get_word_by_id(self, word_id: str) -> Optional[SpellingWord]:
        """Find a word by its ID."""
        for word in self.words:
            if word.id == word_id:
                return word
        return None
    
    def get_random_word(self) -> Optional[SpellingWord]:
        """Get a random word from the list."""
        if not self.words:
            return None
        return random.choice(self.words)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert word list to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'difficulty': self.difficulty,
            'words': [w.to_dict() for w in self.words]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WordList':
        """Create a WordList from a dictionary."""
        words = [SpellingWord.from_dict(w) for w in data.get('words', [])]
        return cls(
            id=data['id'],
            name=data['name'],
            difficulty=data['difficulty'],
            words=words
        )


class WordManager:
    """
    Manages word data loading, storage, and retrieval.
    
    Features:
    - Load word lists from JSON files
    - Get words by difficulty/planet
    - Provide word presentation data
    - Support for custom word lists
    """
    
    def __init__(self, data_dir: str = "src/data"):
        """
        Initialize the word manager.
        
        Args:
            data_dir: Directory containing word list JSON files
        """
        self.data_dir = data_dir
        self.word_lists: Dict[str, WordList] = {}
        self.all_words: List[SpellingWord] = []
        self._load_word_lists()
    
    def _load_word_lists(self):
        """Load all word lists from the data directory."""
        word_list_path = os.path.join(self.data_dir, "word_lists.json")
        
        if not os.path.exists(word_list_path):
            print(f"Warning: Word list file not found at {word_list_path}")
            return
        
        try:
            with open(word_list_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for list_data in data.get('word_lists', []):
                word_list = WordList.from_dict(list_data)
                self.word_lists[word_list.id] = word_list
                
                # Add words to the master list with planet reference
                for word in word_list.words:
                    word.planet_id = word_list.id
                    self.all_words.append(word)
            
            print(f"Loaded {len(self.word_lists)} word lists with {len(self.all_words)} total words")
            
        except Exception as e:
            print(f"Error loading word lists: {e}")
    
    def get_word_list(self, list_id: str) -> Optional[WordList]:
        """
        Get a word list by its ID.
        
        Args:
            list_id: The ID of the word list (e.g., 'planet-1')
            
        Returns:
            The WordList or None if not found
        """
        return self.word_lists.get(list_id)
    
    def get_word_by_id(self, word_id: str) -> Optional[SpellingWord]:
        """
        Get a word by its ID.
        
        Args:
            word_id: The unique identifier of the word
            
        Returns:
            The SpellingWord or None if not found
        """
        for word in self.all_words:
            if word.id == word_id:
                return word
        return None
    
    def get_words_by_difficulty(self, difficulty: int) -> List[SpellingWord]:
        """
        Get all words of a specific difficulty level.
        
        Args:
            difficulty: The difficulty level (1-3)
            
        Returns:
            List of SpellingWord objects
        """
        return [w for w in self.all_words if w.difficulty == difficulty]
    
    def get_random_word(self, difficulty: Optional[int] = None) -> Optional[SpellingWord]:
        """
        Get a random word, optionally filtered by difficulty.
        
        Args:
            difficulty: Optional difficulty filter
            
        Returns:
            A random SpellingWord or None
        """
        if difficulty is not None:
            words = self.get_words_by_difficulty(difficulty)
        else:
            words = self.all_words
        
        if not words:
            return None
        return random.choice(words)
    
    def get_words_for_planet(self, planet_id: str) -> List[SpellingWord]:
        """
        Get all words for a specific planet.
        
        Args:
            planet_id: The planet identifier (e.g., 'planet-1')
            
        Returns:
            List of SpellingWord objects for that planet
        """
        word_list = self.get_word_list(planet_id)
        return word_list.words if word_list else []
    
    def add_word(self, word: SpellingWord, planet_id: Optional[str] = None):
        """
        Add a new word to the manager.
        
        Args:
            word: The SpellingWord to add
            planet_id: Optional planet assignment
        """
        word.planet_id = planet_id
        self.all_words.append(word)
        
        # Also add to appropriate word list if planet specified
        if planet_id and planet_id in self.word_lists:
            self.word_lists[planet_id].words.append(word)
    
    def get_total_word_count(self) -> int:
        """Get the total number of words available."""
        return len(self.all_words)
    
    def get_difficulty_distribution(self) -> Dict[int, int]:
        """
        Get the count of words at each difficulty level.
        
        Returns:
            Dictionary mapping difficulty to word count
        """
        distribution = {}
        for word in self.all_words:
            diff = word.difficulty
            distribution[diff] = distribution.get(diff, 0) + 1
        return distribution
    
    def save_word_lists(self, output_path: Optional[str] = None):
        """
        Save all word lists to a JSON file.
        
        Args:
            output_path: Optional custom output path
        """
        if output_path is None:
            output_path = os.path.join(self.data_dir, "word_lists.json")
        
        data = {
            'version': '1.0',
            'last_updated': '2026-07-04',
            'word_lists': [wl.to_dict() for wl in self.word_lists.values()]
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# Singleton instance for global access
_word_manager: Optional[WordManager] = None
_word_manager_lock = threading.Lock()


def get_word_manager(data_dir: str = "src/data") -> WordManager:
    """
    Get or create the global word manager instance.
    
    Args:
        data_dir: Directory containing word list files
        
    Returns:
        The WordManager singleton instance
    """
    global _word_manager
    if _word_manager is None:
        with _word_manager_lock:
            if _word_manager is None:
                _word_manager = WordManager(data_dir)
    return _word_manager


def reset_word_manager():
    """Reset the global word manager (useful for testing)."""
    global _word_manager
    with _word_manager_lock:
        _word_manager = None

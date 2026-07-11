"""CRUD operations for custom word lists."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from src.models.word_entry import WordEntry, Difficulty


class WordListManager:
    """Manages word lists for student profiles with CRUD operations."""
    
    DATA_DIR = "data/word_lists"
    
    def __init__(self, data_dir: Optional[str] = None):
        """Initialize the word list manager.
        
        Args:
            data_dir: Directory for storing word list JSON files. Defaults to data/word_lists.
        """
        self.data_dir = data_dir or self.DATA_DIR
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_profile_path(self, profile_id: str) -> Path:
        """Get the file path for a student's word list.
        
        Args:
            profile_id: Student profile identifier (alphanumeric + underscore).
            
        Returns:
            Path to the profile's word list JSON file.
            
        Raises:
            ValueError: If profile_id is empty or contains invalid characters.
        """
        # Validate profile_id to prevent path traversal
        if not profile_id or not str(profile_id).replace('_', '').isalnum():
            raise ValueError("Invalid profile ID")
        # Ensure no path traversal attempts
        profile_id = str(profile_id).replace('/', '').replace('\\', '')
        return Path(self.data_dir) / f"{profile_id}.json"
    
    def _load_data(self, profile_id: str) -> dict:
        """Load word list data from file.
        
        Args:
            profile_id: Student profile identifier.
            
        Returns:
            Dictionary with 'words' and 'meta' keys.
        """
        path = self._get_profile_path(profile_id)
        if not path.exists():
            return {"words": [], "meta": {"created": None, "updated": None}}
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Return empty data if file is corrupt
            return {"words": [], "meta": {"created": None, "updated": None}}
    
    def _save_data(self, profile_id: str, data: dict) -> None:
        """Save word list data to file atomically.
        
        Args:
            profile_id: Student profile identifier.
            data: Dictionary containing words and metadata.
        """
        path = self._get_profile_path(profile_id)
        data["meta"]["updated"] = datetime.now().isoformat()
        
        # Atomic write using temp file + rename
        temp_path = path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_path.replace(path)
        except IOError as e:
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            raise e
    
    def _generate_id(self) -> str:
        """Generate a unique word ID."""
        import uuid
        return str(uuid.uuid4())
    
    def add_word(
        self, 
        profile_id: str, 
        spelling: str, 
        definition: str = "", 
        difficulty: Difficulty = Difficulty.MEDIUM
    ) -> WordEntry:
        """Add a new word to the student's list.
        
        Args:
            profile_id: Student profile identifier.
            spelling: The word spelling.
            definition: Optional definition or context.
            difficulty: Word difficulty level.
            
        Returns:
            The created WordEntry.
            
        Raises:
            ValueError: If spelling is invalid or word is duplicate.
        """
        # Validate spelling
        if not spelling or not spelling.strip():
            raise ValueError("Spelling cannot be empty")
        if len(spelling.strip()) < 2 or len(spelling.strip()) > 25:
            raise ValueError("Word must be 2-25 characters")
        if not spelling.strip().replace("-", "").isalpha():
            raise ValueError("Word must contain only letters and hyphens")
        
        # Check for duplicates
        existing_words = self.get_words(profile_id)
        normalized_spelling = spelling.strip().upper()
        for word in existing_words:
            if word.spelling == normalized_spelling:
                raise ValueError(f"Word '{normalized_spelling}' already exists")
        
        word = WordEntry(
            id=self._generate_id(),
            spelling=normalized_spelling,
            definition=definition.strip()[:255],  # Limit definition length
            difficulty=difficulty,
            created_date=datetime.now(),
            last_modified=datetime.now()
        )
        
        data = self._load_data(profile_id)
        if data["meta"]["created"] is None:
            data["meta"]["created"] = datetime.now().isoformat()
        data["words"].append(word.to_dict())
        self._save_data(profile_id, data)
        
        return word
    
    def get_words(
        self, 
        profile_id: str,
        difficulty: Optional[Difficulty] = None,
        search_terms: Optional[str] = None
    ) -> List[WordEntry]:
        """Get words from a student's list with optional filtering.
        
        Args:
            profile_id: Student profile identifier.
            difficulty: Optional difficulty filter.
            search_terms: Optional search terms (spaces separate terms).
            
        Returns:
            List of matching WordEntry objects.
        """
        data = self._load_data(profile_id)
        words = [WordEntry.from_dict(w) for w in data["words"]]
        
        # Apply difficulty filter
        if difficulty:
            words = [w for w in words if w.difficulty == difficulty]
        
        # Apply search filter
        if search_terms:
            terms = search_terms.lower().split()
            words = [w for w in words if 
                    any(term in w.spelling.lower() or term in w.definition.lower() 
                      for term in terms if term)]
        
        # Sort alphabetically by spelling
        words.sort(key=lambda w: w.spelling)
        
        return words
    
    def get_word(self, profile_id: str, word_id: str) -> Optional[WordEntry]:
        """Get a specific word by ID.
        
        Args:
            profile_id: Student profile identifier.
            word_id: The word's unique ID.
            
        Returns:
            The WordEntry if found, None otherwise.
        """
        words = self.get_words(profile_id)
        for word in words:
            if word.id == word_id:
                return word
        return None
    
    def update_word(
        self, 
        profile_id: str, 
        word_id: str,
        spelling: Optional[str] = None, 
        definition: Optional[str] = None,
        difficulty: Optional[Difficulty] = None
    ) -> WordEntry:
        """Update an existing word.
        
        Args:
            profile_id: Student profile identifier.
            word_id: The word's unique ID.
            spelling: New spelling (optional).
            definition: New definition (optional).
            difficulty: New difficulty (optional).
            
        Returns:
            The updated WordEntry.
            
        Raises:
            ValueError: If word not found or new spelling is invalid/duplicate.
        """
        data = self._load_data(profile_id)
        
        # Find the word
        word_index = None
        for i, w in enumerate(data["words"]):
            if w["id"] == word_id:
                word_index = i
                break
        
        if word_index is None:
            raise ValueError("Word not found")
        
        # Get current values
        updated_spelling = data["words"][word_index]["spelling"]
        updated_definition = data["words"][word_index]["definition"]
        updated_difficulty = Difficulty.from_string(data["words"][word_index]["difficulty"])
        
        # Apply updates
        if spelling is not None:
            # Validate new spelling
            if not spelling.strip():
                raise ValueError("Spelling cannot be empty")
            if len(spelling.strip()) < 2 or len(spelling.strip()) > 25:
                raise ValueError("Word must be 2-25 characters")
            if not spelling.strip().replace("-", "").isalpha():
                raise ValueError("Word must contain only letters and hyphens")
            
            # Check for duplicates (excluding current word)
            new_spelling_normalized = spelling.strip().upper()
            for i, w in enumerate(data["words"]):
                if i != word_index and w["spelling"] == new_spelling_normalized:
                    raise ValueError(f"Word '{new_spelling_normalized}' already exists")
            
            updated_spelling = new_spelling_normalized
        
        if definition is not None:
            updated_definition = definition.strip()[:255]
        
        if difficulty is not None:
            updated_difficulty = difficulty
        
        # Update the word
        data["words"][word_index] = {
            "id": word_id,
            "spelling": updated_spelling,
            "definition": updated_definition,
            "difficulty": updated_difficulty.value,
            "created_date": data["words"][word_index]["created_date"],
            "last_modified": datetime.now().isoformat()
        }
        
        self._save_data(profile_id, data)
        return WordEntry.from_dict(data["words"][word_index])
    
    def delete_word(self, profile_id: str, word_id: str) -> bool:
        """Delete a word from the student's list.
        
        Args:
            profile_id: Student profile identifier.
            word_id: The word's unique ID.
            
        Returns:
            True if word was deleted, False if not found.
        """
        data = self._load_data(profile_id)
        initial_len = len(data["words"])
        data["words"] = [w for w in data["words"] if w["id"] != word_id]
        
        if len(data["words"]) < initial_len:
            self._save_data(profile_id, data)
            return True
        return False
    
    def add_bulk_words(
        self, 
        profile_id: str, 
        text: str, 
        difficulty: Difficulty = Difficulty.MEDIUM
    ) -> tuple:
        """Add multiple words from newline-separated text.
        
        Format: One word per line, optionally followed by definition after space/tab.
        Example:
            APPLE A red fruit
            BANANA A yellow fruit
        
        Args:
            profile_id: Student profile identifier.
            text: Newline-separated words.
            difficulty: Difficulty for all words.
            
        Returns:
            Tuple of (successful_count, failed_count, added_words).
        """
        added = []
        failed = 0
        
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            
            # Parse word and definition
            parts = line.split(maxsplit=1)
            spelling = parts[0]
            definition = parts[1] if len(parts) > 1 else ""
            
            try:
                word = self.add_word(profile_id, spelling, definition, difficulty)
                added.append(word)
            except ValueError:
                failed += 1
                continue
        
        return len(added), failed, added
    
    def get_word_count(self, profile_id: str) -> dict:
        """Get word count statistics by difficulty.
        
        Args:
            profile_id: Student profile identifier.
            
        Returns:
            Dictionary with word counts by difficulty level.
        """
        words = self.get_words(profile_id)
        return {
            "total": len(words),
            "beginner": len([w for w in words if w.difficulty == Difficulty.BEGINNER]),
            "medium": len([w for w in words if w.difficulty == Difficulty.MEDIUM]),
            "advanced": len([w for w in words if w.difficulty == Difficulty.ADVANCED])
        }
    
    def get_all_difficulties(self) -> List[Difficulty]:
        """Get all available difficulty levels."""
        return [Difficulty.BEGINNER, Difficulty.MEDIUM, Difficulty.ADVANCED]
    
    def clear_word_list(self, profile_id: str) -> int:
        """Remove all words from a student's list.
        
        Args:
            profile_id: Student profile identifier.
            
        Returns:
            Number of words deleted.
        """
        data = self._load_data(profile_id)
        count = len(data["words"])
        data["words"] = []
        self._save_data(profile_id, data)
        return count
"""
Student Profile Model (STORY-003-02)

Data model for student profiles with name, avatar, and metadata.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import re


@dataclass
class StudentProfile:
    """
    Represents a student profile with personal information and settings.
    
    Attributes:
        id: Unique identifier (UUID or timestamp-based)
        name: Student's name (1-30 characters)
        avatar_id: Identifier for selected avatar image
        created_date: When the profile was created
        last_played: Last time the student played (optional)
        difficulty_level: Skill level (beginner, medium, advanced)
    """
    
    id: str
    name: str
    avatar_id: str
    created_date: datetime
    last_played: Optional[datetime] = None
    difficulty_level: str = "medium"
    
    # Class-level constants
    MIN_NAME_LENGTH = 1
    MAX_NAME_LENGTH = 30
    VALID_DIFFICULTY_LEVELS = {"beginner", "medium", "advanced"}
    
    # Simple blocklist for inappropriate names (MVP)
    NAME_BLOCKLIST = {
        "admin", "root", "system", "test", "guest", "null", "none"
    }
    
    def __post_init__(self):
        """Validate profile data after initialization."""
        self._validate_name()
        self._validate_avatar_id()
        self._validate_difficulty_level()
    
    def _validate_name(self):
        """Validate the student name."""
        if not self.name or len(self.name.strip()) < self.MIN_NAME_LENGTH:
            raise ValueError("Name must be at least 1 character")
        if len(self.name.strip()) > self.MAX_NAME_LENGTH:
            raise ValueError(f"Name must be at most {self.MAX_NAME_LENGTH} characters")
        if self.name.strip().lower() in self.NAME_BLOCKLIST:
            raise ValueError("Name not allowed")
    
    def _validate_avatar_id(self):
        """Validate the avatar ID."""
        if not self.avatar_id:
            raise ValueError("Avatar ID cannot be empty")
    
    def _validate_difficulty_level(self):
        """Validate the difficulty level."""
        if self.difficulty_level not in self.VALID_DIFFICULTY_LEVELS:
            raise ValueError(
                f"Invalid difficulty level: {self.difficulty_level}. "
                f"Must be one of: {', '.join(self.VALID_DIFFICULTY_LEVELS)}"
            )
    
    @property
    def sanitized_name(self) -> str:
        """Get the name with whitespace trimmed."""
        return self.name.strip()
    
    def to_dict(self) -> dict:
        """
        Serialize the profile to a dictionary.
        
        Returns:
            Dictionary representation of the profile
        """
        return {
            "id": self.id,
            "name": self.name,
            "avatar_id": self.avatar_id,
            "created_date": self.created_date.isoformat(),
            "last_played": self.last_played.isoformat() if self.last_played else None,
            "difficulty_level": self.difficulty_level
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "StudentProfile":
        """
        Create a StudentProfile from a dictionary.
        
        Args:
            data: Dictionary containing profile data
            
        Returns:
            StudentProfile instance
        """
        return cls(
            id=data["id"],
            name=data["name"],
            avatar_id=data["avatar_id"],
            created_date=datetime.fromisoformat(data["created_date"]),
            last_played=datetime.fromisoformat(data["last_played"]) if data.get("last_played") else None,
            difficulty_level=data.get("difficulty_level", "medium")
        )
    
    def update_last_played(self):
        """Update the last_played timestamp to the current time."""
        self.last_played = datetime.now()
    
    def has_progress(self) -> bool:
        """
        Check if the profile has any progress data.
        
        Note: This only checks the last_played field. Actual progress
        checking should be done by the ProfileManager which has access
        to the progress data.
        
        Returns:
            True if the profile has been played at least once
        """
        return self.last_played is not None
    
    def __str__(self) -> str:
        """Return a string representation of the profile."""
        return f"StudentProfile({self.name}, {self.avatar_id})"
    
    def __eq__(self, other) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, StudentProfile):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)
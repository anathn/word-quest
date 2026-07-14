"""Word entry data model for custom spelling words."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class Difficulty(Enum):
    """Difficulty levels for custom words."""
    BEGINNER = "beginner"
    MEDIUM = "medium"
    ADVANCED = "advanced"

    @classmethod
    def from_string(cls, value: str) -> "Difficulty":
        """Create Difficulty from string representation."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.MEDIUM


@dataclass
class WordEntry:
    """Data model for a custom spelling word entry."""
    spelling: str
    definition: str = ""
    difficulty: Difficulty = Difficulty.MEDIUM
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_date: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "spelling": self.spelling,
            "definition": self.definition,
            "difficulty": self.difficulty.value,
            "created_date": self.created_date.isoformat(),
            "last_modified": self.last_modified.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WordEntry":
        """Create WordEntry from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            spelling=data["spelling"],
            definition=data.get("definition", ""),
            difficulty=Difficulty.from_string(data.get("difficulty", "medium")),
            created_date=datetime.fromisoformat(data["created_date"]),
            last_modified=datetime.fromisoformat(data["last_modified"])
        )

    def validate(self) -> bool:
        """Validate the word entry."""
        if not self.spelling or not self.spelling.strip():
            return False
        if len(self.spelling.strip()) < 2 or len(self.spelling.strip()) > 25:
            return False
        # Allow letters and hyphens only
        cleaned = self.spelling.strip().replace("-", "")
        if not cleaned.isalpha():
            return False
        return True

    def __post_init__(self):
        """Validate after initialization."""
        if self.spelling:
            self.spelling = self.spelling.upper().strip()
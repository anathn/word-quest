"""
Unit Tests for StudentProfile (STORY-003-02)

Tests for the StudentProfile data model.
"""

import pytest
from datetime import datetime
from src.models.student_profile import StudentProfile


class TestStudentProfileCreation:
    """Tests for StudentProfile creation and validation."""
    
    def test_create_valid_profile(self):
        """Test creating a valid student profile."""
        profile = StudentProfile(
            id="test-id-123",
            name="Alex",
            avatar_id="astronaut",
            created_date=datetime(2026, 7, 10)
        )
        
        assert profile.id == "test-id-123"
        assert profile.name == "Alex"
        assert profile.avatar_id == "astronaut"
        assert profile.difficulty_level == "medium"
        assert profile.last_played is None
    
    def test_create_profile_with_difficulty(self):
        """Test creating a profile with custom difficulty."""
        profile = StudentProfile(
            id="test-id",
            name="Sam",
            avatar_id="alien",
            created_date=datetime.now(),
            difficulty_level="beginner"
        )
        
        assert profile.difficulty_level == "beginner"
    
    def test_create_profile_with_last_played(self):
        """Test creating a profile with last_played date."""
        last_played = datetime(2026, 7, 9, 14, 30)
        profile = StudentProfile(
            id="test-id",
            name="Jordan",
            avatar_id="rocket",
            created_date=datetime(2026, 7, 1),
            last_played=last_played
        )
        
        assert profile.last_played == last_played
        assert profile.has_progress() is True
    
    def test_name_too_short(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="Name must be at least 1 character"):
            StudentProfile(
                id="test-id",
                name="",
                avatar_id="astronaut",
                created_date=datetime.now()
            )
    
    def test_name_whitespace_only(self):
        """Test that whitespace-only name raises ValueError."""
        with pytest.raises(ValueError, match="Name must be at least 1 character"):
            StudentProfile(
                id="test-id",
                name="   ",
                avatar_id="astronaut",
                created_date=datetime.now()
            )
    
    def test_name_too_long(self):
        """Test that name over 30 characters raises ValueError."""
        long_name = "A" * 31
        
        with pytest.raises(ValueError, match="Name must be at most 30 characters"):
            StudentProfile(
                id="test-id",
                name=long_name,
                avatar_id="astronaut",
                created_date=datetime.now()
            )
    
    def test_name_at_max_length(self):
        """Test that name of exactly 30 characters is valid."""
        profile = StudentProfile(
            id="test-id",
            name="A" * 30,
            avatar_id="astronaut",
            created_date=datetime.now()
        )
        
        assert len(profile.name) == 30
    
    def test_invalid_avatar_id(self):
        """Test that empty avatar_id raises ValueError."""
        with pytest.raises(ValueError, match="Avatar ID cannot be empty"):
            StudentProfile(
                id="test-id",
                name="Alex",
                avatar_id="",
                created_date=datetime.now()
            )
    
    def test_invalid_difficulty_level(self):
        """Test that invalid difficulty level raises ValueError."""
        with pytest.raises(ValueError, match="Invalid difficulty level"):
            StudentProfile(
                id="test-id",
                name="Alex",
                avatar_id="astronaut",
                created_date=datetime.now(),
                difficulty_level="expert"
            )
    
    def test_blocked_name(self):
        """Test that blocked names raise ValueError."""
        for blocked_name in ["admin", "root", "system", "test"]:
            with pytest.raises(ValueError, match="Name not allowed"):
                StudentProfile(
                    id="test-id",
                    name=blocked_name,
                    avatar_id="astronaut",
                    created_date=datetime.now()
                )


class TestStudentProfileSerialization:
    """Tests for StudentProfile serialization."""
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        created = datetime(2026, 7, 1, 10, 0)
        last_played = datetime(2026, 7, 9, 14, 30)
        
        profile = StudentProfile(
            id="test-id-123",
            name="Alex",
            avatar_id="astronaut",
            created_date=created,
            last_played=last_played,
            difficulty_level="advanced"
        )
        
        data = profile.to_dict()
        
        assert data["id"] == "test-id-123"
        assert data["name"] == "Alex"
        assert data["avatar_id"] == "astronaut"
        assert data["created_date"] == "2026-07-01T10:00:00"
        assert data["last_played"] == "2026-07-09T14:30:00"
        assert data["difficulty_level"] == "advanced"
    
    def test_to_dict_without_last_played(self):
        """Test serialization without last_played."""
        profile = StudentProfile(
            id="test-id",
            name="Alex",
            avatar_id="astronaut",
            created_date=datetime.now()
        )
        
        data = profile.to_dict()
        
        assert data["last_played"] is None
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "id": "test-id-123",
            "name": "Alex",
            "avatar_id": "astronaut",
            "created_date": "2026-07-01T10:00:00",
            "last_played": "2026-07-09T14:30:00",
            "difficulty_level": "beginner"
        }
        
        profile = StudentProfile.from_dict(data)
        
        assert profile.id == "test-id-123"
        assert profile.name == "Alex"
        assert profile.avatar_id == "astronaut"
        assert profile.created_date == datetime(2026, 7, 1, 10, 0)
        assert profile.last_played == datetime(2026, 7, 9, 14, 30)
        assert profile.difficulty_level == "beginner"
    
    def test_from_dict_without_last_played(self):
        """Test deserialization without last_played."""
        data = {
            "id": "test-id",
            "name": "Alex",
            "avatar_id": "astronaut",
            "created_date": "2026-07-01T10:00:00",
            "last_played": None,
            "difficulty_level": "medium"
        }
        
        profile = StudentProfile.from_dict(data)
        
        assert profile.last_played is None
    
    def test_from_dict_default_difficulty(self):
        """Test deserialization defaults difficulty to medium."""
        data = {
            "id": "test-id",
            "name": "Alex",
            "avatar_id": "astronaut",
            "created_date": "2026-07-01T10:00:00",
            "last_played": None
        }
        
        profile = StudentProfile.from_dict(data)
        
        assert profile.difficulty_level == "medium"


class TestStudentProfileMethods:
    """Tests for StudentProfile methods."""
    
    def test_update_last_played(self):
        """Test updating last_played timestamp."""
        profile = StudentProfile(
            id="test-id",
            name="Alex",
            avatar_id="astronaut",
            created_date=datetime.now()
        )
        
        assert profile.last_played is None
        
        profile.update_last_played()
        
        assert profile.last_played is not None
        assert profile.has_progress() is True
    
    def test_sanitized_name(self):
        """Test sanitized_name property trims whitespace."""
        profile = StudentProfile(
            id="test-id",
            name="  Alex  ",
            avatar_id="astronaut",
            created_date=datetime.now()
        )
        
        assert profile.sanitized_name == "Alex"
    
    def test_equality_by_id(self):
        """Test that equality is based on ID."""
        profile1 = StudentProfile(
            id="test-id",
            name="Alex",
            avatar_id="astronaut",
            created_date=datetime.now()
        )
        
        profile2 = StudentProfile(
            id="test-id",
            name="Alexandra",
            avatar_id="alien",
            created_date=datetime.now()
        )
        
        profile3 = StudentProfile(
            id="different-id",
            name="Alex",
            avatar_id="astronaut",
            created_date=datetime.now()
        )
        
        assert profile1 == profile2  # Same ID
        assert profile1 != profile3  # Different ID
    
    def test_hash_by_id(self):
        """Test that hashing is based on ID."""
        profile1 = StudentProfile(
            id="test-id",
            name="Alex",
            avatar_id="astronaut",
            created_date=datetime.now()
        )
        
        profile2 = StudentProfile(
            id="test-id",
            name="Alexandra",
            avatar_id="alien",
            created_date=datetime.now()
        )
        
        assert hash(profile1) == hash(profile2)
    
    def test_str_representation(self):
        """Test string representation."""
        profile = StudentProfile(
            id="test-id",
            name="Alex",
            avatar_id="astronaut",
            created_date=datetime.now()
        )
        
        str_repr = str(profile)
        
        assert "Alex" in str_repr
        assert "astronaut" in str_repr


class TestStudentProfileProgress:
    """Tests for progress-related functionality."""
    
    def test_has_progress_false(self):
        """Test has_progress returns False when last_played is None."""
        profile = StudentProfile(
            id="test-id",
            name="Alex",
            avatar_id="astronaut",
            created_date=datetime.now()
        )
        
        assert profile.has_progress() is False
    
    def test_has_progress_true(self):
        """Test has_progress returns True when last_played is set."""
        profile = StudentProfile(
            id="test-id",
            name="Alex",
            avatar_id="astronaut",
            created_date=datetime.now(),
            last_played=datetime.now()
        )
        
        assert profile.has_progress() is True
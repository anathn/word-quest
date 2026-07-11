"""
Unit Tests for ProfileManager (STORY-003-02)

Tests for the ProfileManager CRUD operations and persistence.
"""

import pytest
import os
import json
import tempfile
from datetime import datetime
from src.profiles.profile_manager import ProfileManager
from src.models.student_profile import StudentProfile


@pytest.fixture
def temp_profile_file():
    """Create a temporary file for profile storage."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    # Initialize with empty JSON structure
    with open(path, 'w') as f:
        json.dump({"profiles": []}, f)
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def profile_manager(temp_profile_file):
    """Create a ProfileManager with a temporary file."""
    return ProfileManager(data_path=temp_profile_file)


@pytest.fixture
def populated_manager(temp_profile_file):
    """Create a ProfileManager with some existing profiles."""
    manager = ProfileManager(data_path=temp_profile_file)
    manager.create_profile("Alice", "astronaut")
    manager.create_profile("Bob", "alien")
    return manager


class TestProfileManagerInitialization:
    """Tests for ProfileManager initialization."""
    
    def test_create_with_default_path(self):
        """Test creation with default data path."""
        # Clean up if exists
        default_path = "data/profiles.json"
        if os.path.exists(default_path):
            os.remove(default_path)
        
        try:
            manager = ProfileManager()
            assert os.path.exists(default_path)
        finally:
            if os.path.exists(default_path):
                os.remove(default_path)
    
    def test_create_default_file_empty(self, temp_profile_file):
        """Test that default file is created with empty profiles."""
        manager = ProfileManager(data_path=temp_profile_file)
        
        with open(temp_profile_file, 'r') as f:
            data = json.load(f)
        
        assert data["profiles"] == []
    
    def test_get_avatar_options(self, profile_manager):
        """Test that avatar options are accessible."""
        options = profile_manager.get_avatar_options()
        
        assert len(options) == 8
        assert "astronaut" in options
        assert "alien" in options
        assert "rocket" in options


class TestCreateProfile:
    """Tests for profile creation."""
    
    def test_create_valid_profile(self, profile_manager):
        """Test creating a valid profile."""
        profile = profile_manager.create_profile("Charlie", "rocket")
        
        assert profile.name == "Charlie"
        assert profile.avatar_id == "rocket"
        assert profile.difficulty_level == "medium"
        assert profile.id is not None
        assert profile.created_date is not None
    
    def test_create_profile_with_difficulty(self, profile_manager):
        """Test creating a profile with custom difficulty."""
        profile = profile_manager.create_profile("Diana", "star", difficulty_level="advanced")
        
        assert profile.difficulty_level == "advanced"
    
    def test_create_rejects_empty_name(self, profile_manager):
        """Test that empty name is rejected."""
        with pytest.raises(ValueError, match="Name must be at least 1 character"):
            profile_manager.create_profile("", "astronaut")
    
    def test_create_rejects_duplicate_name(self, populated_manager):
        """Test that duplicate names are rejected."""
        with pytest.raises(ValueError, match="already exists"):
            populated_manager.create_profile("Alice", "rocket")
    
    def test_create_case_insensitive_duplicate(self, populated_manager):
        """Test that duplicate check is case-insensitive."""
        with pytest.raises(ValueError, match="already exists"):
            populated_manager.create_profile("alice", "rocket")
    
    def test_create_rejects_invalid_avatar(self, profile_manager):
        """Test that invalid avatar_id is rejected."""
        with pytest.raises(KeyError, match="Invalid avatar selection"):
            profile_manager.create_profile("Test", "invalid_avatar")
    
    def test_create_enforces_max_profiles(self, temp_profile_file):
        """Test that maximum profiles limit is enforced."""
        manager = ProfileManager(data_path=temp_profile_file)
        
        # Create max number of profiles
        for i in range(10):
            manager.create_profile(f"User{i}", "astronaut")
        
        # Try to create one more
        with pytest.raises(ValueError, match="Maximum number of profiles"):
            manager.create_profile("User10", "astronaut")


class TestGetProfile:
    """Tests for profile retrieval."""
    
    def test_get_existing_profile(self, populated_manager):
        """Test retrieving an existing profile."""
        profiles = populated_manager.get_all_profiles()
        profile_id = profiles[0].id
        
        profile = populated_manager.get_profile(profile_id)
        
        assert profile is not None
        assert profile.name in ["Alice", "Bob"]
    
    def test_get_nonexistent_profile(self, profile_manager):
        """Test retrieving a non-existent profile."""
        profile = profile_manager.get_profile("nonexistent-id")
        
        assert profile is None
    
    def test_get_profile_by_name(self, populated_manager):
        """Test retrieving profile by name."""
        profile = populated_manager.get_profile_by_name("Alice")
        
        assert profile is not None
        assert profile.name == "Alice"
    
    def test_get_profile_by_name_case_insensitive(self, populated_manager):
        """Test that name lookup is case-insensitive."""
        profile = populated_manager.get_profile_by_name("alice")
        
        assert profile is not None
        assert profile.name == "Alice"
    
    def test_get_profile_by_name_not_found(self, profile_manager):
        """Test that non-existent name returns None."""
        profile = profile_manager.get_profile_by_name("NonExistent")
        
        assert profile is None
    
    def test_get_all_profiles(self, populated_manager):
        """Test retrieving all profiles."""
        profiles = populated_manager.get_all_profiles()
        
        assert len(profiles) == 2
        names = [p.name for p in profiles]
        assert "Alice" in names
        assert "Bob" in names
    
    def test_get_all_profiles_sorted(self, temp_profile_file):
        """Test that profiles are sorted by creation date."""
        manager = ProfileManager(data_path=temp_profile_file)
        
        # Create profiles with time gaps
        import time
        profile1 = manager.create_profile("First", "astronaut")
        time.sleep(0.1)
        profile2 = manager.create_profile("Second", "alien")
        time.sleep(0.1)
        profile3 = manager.create_profile("Third", "rocket")
        
        profiles = manager.get_all_profiles()
        
        assert len(profiles) == 3
        assert profiles[0].name == "First"
        assert profiles[1].name == "Second"
        assert profiles[2].name == "Third"


class TestUpdateProfile:
    """Tests for profile updates."""
    
    def test_update_name(self, populated_manager):
        """Test updating profile name."""
        profiles = populated_manager.get_all_profiles()
        profile_id = profiles[0].id
        
        updated = populated_manager.update_profile(profile_id, name="AliceUpdated")
        
        assert updated.name == "AliceUpdated"
    
    def test_update_avatar(self, populated_manager):
        """Test updating profile avatar."""
        profiles = populated_manager.get_all_profiles()
        profile_id = profiles[0].id
        
        updated = populated_manager.update_profile(profile_id, avatar_id="rocket")
        
        assert updated.avatar_id == "rocket"
    
    def test_update_difficulty(self, populated_manager):
        """Test updating profile difficulty level."""
        profiles = populated_manager.get_all_profiles()
        profile_id = profiles[0].id
        
        updated = populated_manager.update_profile(profile_id, difficulty_level="beginner")
        
        assert updated.difficulty_level == "beginner"
    
    def test_update_partial(self, populated_manager):
        """Test updating only some fields."""
        profiles = populated_manager.get_all_profiles()
        profile_id = profiles[0].id
        original_avatar = profiles[0].avatar_id
        
        updated = populated_manager.update_profile(profile_id, name="NewName")
        
        assert updated.name == "NewName"
        assert updated.avatar_id == original_avatar  # Unchanged
    
    def test_update_rejects_duplicate_name(self, populated_manager):
        """Test that name update rejects duplicates."""
        profiles = populated_manager.get_all_profiles()
        alice_id = profiles[0].id
        bob_id = profiles[1].id
        
        # Try to change Bob's name to Alice (which already exists)
        with pytest.raises(ValueError, match="already exists"):
            populated_manager.update_profile(bob_id, name="Alice")
    
    def test_update_nonexistent_profile(self, profile_manager):
        """Test that updating non-existent profile raises error."""
        with pytest.raises(ValueError, match="not found"):
            profile_manager.update_profile("nonexistent-id", name="NewName")
    
    def test_update_invalid_avatar(self, populated_manager):
        """Test that invalid avatar_id is rejected."""
        profiles = populated_manager.get_all_profiles()
        profile_id = profiles[0].id
        
        with pytest.raises(KeyError, match="Invalid avatar selection"):
            populated_manager.update_profile(profile_id, avatar_id="invalid")


class TestDeleteProfile:
    """Tests for profile deletion."""
    
    def test_delete_existing_profile(self, populated_manager):
        """Test deleting an existing profile."""
        profiles = populated_manager.get_all_profiles()
        profile_id = profiles[0].id
        
        result = populated_manager.delete_profile(profile_id, confirmation=True)
        
        assert result is True
        assert populated_manager.get_profile(profile_id) is None
    
    def test_delete_rejects_has_progress(self, temp_profile_file):
        """Test that deletion is rejected if profile has progress."""
        manager = ProfileManager(data_path=temp_profile_file)
        profile = manager.create_profile("TestUser", "astronaut")
        
        # Manually add progress
        data = manager._load_data()
        for p in data["profiles"]:
            if p["id"] == profile.id:
                p["last_played"] = datetime.now().isoformat()
        manager._save_data(data)
        
        # Try to delete without confirmation
        with pytest.raises(ValueError, match="Cannot delete profile with progress"):
            manager.delete_profile(profile.id, confirmation=False)
    
    def test_delete_confirms_with_progress(self, temp_profile_file):
        """Test that deletion succeeds with confirmation when has progress."""
        manager = ProfileManager(data_path=temp_profile_file)
        profile = manager.create_profile("TestUser", "astronaut")
        
        # Manually add progress
        data = manager._load_data()
        for p in data["profiles"]:
            if p["id"] == profile.id:
                p["last_played"] = datetime.now().isoformat()
        manager._save_data(data)
        
        # Delete with confirmation
        result = manager.delete_profile(profile.id, confirmation=True)
        
        assert result is True
    
    def test_delete_nonexistent_profile(self, profile_manager):
        """Test that deleting non-existent profile raises error."""
        with pytest.raises(ValueError, match="not found"):
            profile_manager.delete_profile("nonexistent-id")


class TestPersistence:
    """Tests for data persistence."""
    
    def test_profile_persists_across_instances(self, temp_profile_file):
        """Test that profiles persist across ProfileManager instances."""
        # Create first manager and add profile
        manager1 = ProfileManager(data_path=temp_profile_file)
        manager1.create_profile("Persistent", "astronaut")
        
        # Create new manager instance
        manager2 = ProfileManager(data_path=temp_profile_file)
        
        # Verify profile exists
        profiles = manager2.get_all_profiles()
        assert len(profiles) == 1
        assert profiles[0].name == "Persistent"
    
    def test_update_persists(self, temp_profile_file):
        """Test that updates persist."""
        manager1 = ProfileManager(data_path=temp_profile_file)
        profile = manager1.create_profile("PersistenceTest", "astronaut")
        manager1.update_profile(profile.id, name="Updated", avatar_id="rocket")
        
        # Load fresh instance
        manager2 = ProfileManager(data_path=temp_profile_file)
        updated = manager2.get_profile(profile.id)
        
        assert updated.name == "Updated"
        assert updated.avatar_id == "rocket"
    
    def test_delete_persists(self, temp_profile_file):
        """Test that deletions persist."""
        manager1 = ProfileManager(data_path=temp_profile_file)
        profile = manager1.create_profile("To Delete", "astronaut")
        manager1.delete_profile(profile.id, confirmation=True)
        
        # Load fresh instance
        manager2 = ProfileManager(data_path=temp_profile_file)
        
        assert manager2.get_profile_count() == 0


class TestProfileExists:
    """Tests for profile existence checks."""
    
    def test_profile_exists_true(self, populated_manager):
        """Test profile_exists returns True for existing profile."""
        profiles = populated_manager.get_all_profiles()
        
        assert populated_manager.profile_exists(profiles[0].id) is True
    
    def test_profile_exists_false(self, profile_manager):
        """Test profile_exists returns False for non-existing profile."""
        assert profile_manager.profile_exists("nonexistent-id") is False


class TestProfileCount:
    """Tests for profile counting."""
    
    def test_get_profile_count_empty(self, profile_manager):
        """Test getting count of empty profile list."""
        assert profile_manager.get_profile_count() == 0
    
    def test_get_profile_count_populated(self, populated_manager):
        """Test getting count of populated profile list."""
        assert populated_manager.get_profile_count() == 2
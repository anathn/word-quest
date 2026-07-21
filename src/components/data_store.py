"""
Data Store Component

JSON-based data persistence layer for saving and loading student progress.
Implements auto-save functionality with backup and corruption handling.

This component implements STORY-002-02: Data Persistence (JSON)
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from src.utils.file_utils import (
    BackupManager,
    DataValidator,
    FileUtils,
    create_backup_manager,
    create_validator
)


@dataclass
class SaveResult:
    """Result of a save operation."""
    success: bool
    file_path: str
    timestamp: datetime
    error_message: Optional[str] = None
    backup_created: Optional[str] = None


@dataclass
class LoadResult:
    """Result of a load operation."""
    success: bool
    data: Optional[Dict]
    used_recovery: bool
    error_message: Optional[str] = None


class DataStore:
    """
    Manages JSON file operations for student progress data.
    
    Features:
    - Auto-save functionality
    - Backup creation before each save
    - Corruption detection and recovery
    - Graceful handling of missing files
    - Schema validation
    
    Performance:
    - Save operation completes in < 500ms (target)
    """
    
    def __init__(self, base_path: str = "data/progress"):
        """
        Initialize the data store.
        
        Args:
            base_path: Base directory for progress files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize utility components
        self.backup_manager = create_backup_manager(str(self.base_path))
        self.validator = create_validator()
        

        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _get_file_path(self, student_id: str) -> Path:
        """
        Get the file path for a student's progress file.
        
        Args:
            student_id: Unique student identifier
            
        Returns:
            Path to the student's progress file
        """
        # Sanitize student_id to prevent path traversal
        safe_id = "".join(c for c in student_id if c.isalnum() or c in '_-')
        return self.base_path / f"{safe_id}_progress.json"
    
    def save(self, student_id: str, data: dict) -> SaveResult:
        """
        Save student progress data with backup.
        
        Args:
            student_id: Unique student identifier
            data: Progress data dictionary to save
            
        Returns:
            SaveResult with operation status
        """
        file_path = self._get_file_path(student_id)
        
        try:
            # Create backup first if file exists
            backup_path = None
            if file_path.exists():
                backup_path = self.backup_manager.create_backup(str(file_path))
                if backup_path:
                    self.logger.info(f"Created backup: {backup_path}")
            
            # Validate data before saving
            is_valid, issues = self.validator.validate_progress_schema(data)
            if not is_valid:
                self.logger.warning(f"Schema validation issues: {issues}")
                # Still attempt to save but log warning
            
            # Ensure JSON is serializable
            json_str = json.dumps(data, indent=2, default=str)
            
            # Write to file
            with open(file_path, 'w') as f:
                f.write(json_str)
            
            self.logger.info(f"Successfully saved progress for {student_id}")
            
            return SaveResult(
                success=True,
                file_path=str(file_path),
                timestamp=datetime.now(),
                backup_created=backup_path
            )
            
        except (IOError, OSError) as e:
            self.logger.error(f"Save failed for {student_id}: {e}")
            return SaveResult(
                success=False,
                file_path=str(file_path),
                timestamp=datetime.now(),
                error_message=str(e)
            )
        except TypeError as e:
            self.logger.error(f"Data serialization failed: {e}")
            return SaveResult(
                success=False,
                file_path=str(file_path),
                timestamp=datetime.now(),
                error_message=f"Serialization error: {e}"
            )
    
    def load(self, student_id: str) -> LoadResult:
        """
        Load student progress data with validation and recovery.
        
        Args:
            student_id: Unique student identifier
            
        Returns:
            LoadResult with data or recovery status
        """
        file_path = self._get_file_path(student_id)
        
        # Case 1: File doesn't exist - create empty progress
        if not file_path.exists():
            self.logger.info(f"No existing data for {student_id}, creating new")
            empty_data = self._create_empty_progress(student_id)
            return LoadResult(
                success=True,
                data=empty_data,
                used_recovery=False
            )
        
        # Case 2: Try to load and validate
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Validate schema
            is_valid, issues = self.validator.validate_progress_schema(data)
            
            if is_valid:
                self.logger.info(f"Successfully loaded progress for {student_id}")
                return LoadResult(
                    success=True,
                    data=data,
                    used_recovery=False
                )
            else:
                self.logger.warning(f"Schema validation failed: {issues}, attempting recovery")
                return self._recover_from_corrupt(str(file_path), student_id)
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse error for {student_id}: {e}")
            return self._recover_from_corrupt(str(file_path), student_id)
        except (IOError, OSError) as e:
            self.logger.error(f"File read error for {student_id}: {e}")
            return self._recover_from_corrupt(str(file_path), student_id)
    
    def _recover_from_corrupt(self, file_path: str, student_id: str) -> LoadResult:
        """
        Attempt to recover data from a corrupt file.
        
        Strategy:
        1. Try to restore from latest backup
        2. If no backup or backup also corrupt, create empty progress
        
        Args:
            file_path: Path to the corrupt file
            student_id: Student identifier
            
        Returns:
            LoadResult with recovered or empty data
        """
        self.logger.info(f"Attempting recovery for {student_id}")
        
        # Try to restore from backup
        backups = self.backup_manager.list_backups(file_path)
        if backups:
            self.logger.info(f"Found {len(backups)} backup(s), trying latest")
            latest_backup = backups[0]  # Already sorted newest first
            
            if self.backup_manager.restore_backup(latest_backup, file_path):
                self.logger.info(f"Restored from backup: {latest_backup}")
                # Try to load the restored file
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    is_valid, _ = self.validator.validate_progress_schema(data)
                    if is_valid:
                        return LoadResult(
                            success=True,
                            data=data,
                            used_recovery=True,
                            error_message=f"Recovered from backup: {latest_backup}"
                        )
                    else:
                        self.logger.warning("Restored backup also invalid")
                except (json.JSONDecodeError, IOError) as e:
                    self.logger.error(f"Restored backup also corrupt: {e}")
        
        # Last resort: create empty progress
        self.logger.warning(f"Creating fresh progress for {student_id}")
        empty_data = self._create_empty_progress(student_id)
        
        # Try to save the empty data to replace corrupt file
        self.save(student_id, empty_data)
        
        return LoadResult(
            success=True,
            data=empty_data,
            used_recovery=True,
            error_message="Created fresh progress (original data was corrupt)"
        )
    
    def _create_empty_progress(self, student_id: str) -> dict:
        """
        Create a new empty progress structure.
        
        Args:
            student_id: Unique student identifier
            
        Returns:
            Dictionary with empty progress data
        """
        # Use the same sanitization as filesystem path to ensure consistency
        safe_id = "".join(c for c in student_id if c.isalnum() or c in '_-')
        return {
            'version': '1.0',
            'student_id': safe_id,
            'created_at': datetime.now().isoformat(),
            'sessions': [],
            'mastered_words': [],
            'needs_practice': [],
            'achievements': []
        }
    
    def delete_progress(self, student_id: str) -> bool:
        """
        Delete a student's progress file.
        
        Args:
            student_id: Student identifier
            
        Returns:
            True if deletion succeeded or file didn't exist
        """
        file_path = self._get_file_path(student_id)
        
        try:
            if file_path.exists():
                file_path.unlink()
                self.logger.info(f"Deleted progress for {student_id}")
                
                # Also delete associated backups
                backups = self.backup_manager.list_backups(str(file_path))
                for backup in backups:
                    try:
                        Path(backup).unlink()
                        self.logger.debug(f"Deleted backup: {backup}")
                    except (IOError, OSError):
                        pass
            
            return True
            
        except (IOError, OSError) as e:
            self.logger.error(f"Failed to delete progress for {student_id}: {e}")
            return False
    
    def list_students(self) -> List[str]:
        """
        List all students with saved progress.
        
        Returns:
            List of student IDs
        """
        students = []
        
        try:
            for file_path in self.base_path.glob("*_progress.json"):
                student_id = file_path.stem.replace("_progress", "")
                students.append(student_id)
        except (IOError, OSError):
            pass
        
        return sorted(students)
    
    def get_file_path(self, student_id: str) -> str:
        """
        Get the file path for a student's progress.
        
        Args:
            student_id: Student identifier
            
        Returns:
            Absolute path to the progress file
        """
        return str(self._get_file_path(student_id))
    
    def exists(self, student_id: str) -> bool:
        """
        Check if a student's progress file exists.
        
        Args:
            student_id: Student identifier
            
        Returns:
            True if progress file exists
        """
        return self._get_file_path(student_id).exists()
    
    def has_profiles(self) -> bool:
        """
        Check if any student profiles exist.
        
        Returns:
            True if at least one profile exists, False otherwise
        """
        try:
            students = self.list_students()
            return len(students) > 0
        except Exception as e:
            self.logger.debug(f"No profiles found: {e}")
            return False


# Factory function
def create_data_store(base_path: str = "data/progress") -> DataStore:
    """
    Create a DataStore instance.
    
    Args:
        base_path: Base directory for progress files
        
    Returns:
        Configured DataStore instance
    """
    return DataStore(base_path=base_path)
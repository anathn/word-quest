"""
File Utilities Module

Provides file I/O utilities with backup and recovery functionality
for safe data persistence operations.

This component supports STORY-002-02: Data Persistence (JSON)
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging


class BackupManager:
    """
    Manages backup creation and recovery for data files.
    
    Features:
    - Create timestamped backups before save operations
    - Maintain maximum backup count (auto-cleanup old backups)
    - Support for recovery from backups
    """
    
    MAX_BACKUPS = 10  # Keep last 10 backups
    
    def __init__(self, backup_dir: str):
        """
        Initialize the backup manager.
        
        Args:
            backup_dir: Directory to store backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_backup_path(self, original_file: str) -> str:
        """
        Generate a timestamped backup file path.
        
        Args:
            original_file: Path to the original file
            
        Returns:
            Path for the backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = Path(original_file).name
        return str(self.backup_dir / f"backup_{timestamp}_{filename}")
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """
        Create a backup of the specified file.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to the backup file, or None if source doesn't exist
        """
        source = Path(file_path)
        if not source.exists():
            return None
        
        backup_path = self._generate_backup_path(file_path)
        try:
            shutil.copy2(source, backup_path)
            self._cleanup_old_backups()
            return backup_path
        except (IOError, OSError) as e:
            logging.error(f"Failed to create backup: {e}")
            return None
    
    def _cleanup_old_backups(self):
        """Remove old backups exceeding MAX_BACKUPS limit."""
        backup_files = sorted(self.backup_dir.glob("backup_*.json"))
        
        # Remove oldest backups if we exceed the limit
        while len(backup_files) > self.MAX_BACKUPS:
            oldest = backup_files.pop(0)
            try:
                oldest.unlink()
                logging.debug(f"Removed old backup: {oldest}")
            except (IOError, OSError) as e:
                logging.warning(f"Failed to remove old backup {oldest}: {e}")
    
    def list_backups(self, original_file: str) -> list:
        """
        List all backups for a specific file.
        
        Args:
            original_file: Path to the original file
            
        Returns:
            List of backup file paths sorted by timestamp (newest first)
        """
        filename = Path(original_file).name
        backup_files = sorted(
            self.backup_dir.glob(f"backup_*_{filename}"),
            reverse=True
        )
        return [str(f) for f in backup_files]
    
    def restore_backup(self, backup_path: str, target_path: str) -> bool:
        """
        Restore a file from a backup.
        
        Args:
            backup_path: Path to the backup file
            target_path: Path where to restore the file
            
        Returns:
            True if restore succeeded, False otherwise
        """
        try:
            shutil.copy2(backup_path, target_path)
            return True
        except (IOError, OSError) as e:
            logging.error(f"Failed to restore backup: {e}")
            return False


class DataValidator:
    """
    Validates JSON data structure and schema.
    
    Features:
    - Validate JSON syntax
    - Validate schema structure
    - Identify missing required fields
    """
    
    @staticmethod
    def validate_json_syntax(file_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate JSON file syntax.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, 'r') as f:
                json.load(f)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"JSON parse error: {e}"
        except (IOError, OSError) as e:
            return False, f"File read error: {e}"
    
    def validate_progress_schema(self, data: dict) -> tuple[bool, list]:
        """
        Validate progress data schema.
        
        Expected schema:
        {
            'version': str,
            'student_id': str,
            'created_at': str,
            'sessions': list,
            'mastered_words': list,
            'needs_practice': list,
            'achievements': list
        }
        
        Args:
            data: Dictionary to validate
            
        Returns:
            Tuple of (is_valid, list of missing/invalid field names)
        """
        required_fields = [
            'version',
            'student_id',
            'created_at',
            'sessions',
            'mastered_words',
            'needs_practice',
            'achievements'
        ]
        
        missing_fields = []
        invalid_fields = []
        
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        # Validate types
        type_validators = {
            'version': str,
            'student_id': str,
            'created_at': str,
            'sessions': list,
            'mastered_words': list,
            'needs_practice': list,
            'achievements': list
        }
        
        for field, expected_type in type_validators.items():
            if field in data and not isinstance(data[field], expected_type):
                invalid_fields.append(field)
        
        is_valid = not missing_fields and not invalid_fields
        issues = missing_fields + invalid_fields
        
        return is_valid, issues
    
    def recover_missing_fields(self, data: dict) -> dict:
        """
        Add missing fields with default values.
        
        Args:
            data: Original data dictionary
            
        Returns:
            Data with missing fields added
        """
        defaults = {
            'version': '1.0',
            'sessions': [],
            'mastered_words': [],
            'needs_practice': [],
            'achievements': []
        }
        
        recovered_data = data.copy()
        for field, default_value in defaults.items():
            if field not in recovered_data:
                recovered_data[field] = default_value
        
        # student_id and created_at must already exist or data is too corrupt
        return recovered_data


class FileUtils:
    """
    General file utility functions.
    
    Features:
    - Safe file operations
    - Directory creation
    - File existence checks
    """
    
    @staticmethod
    def ensure_directory(path: str) -> bool:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Directory path to ensure exists
            
        Returns:
            True if directory exists or was created successfully
        """
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True
        except (OSError, IOError) as e:
            logging.error(f"Failed to create directory {path}: {e}")
            return False
    
    @staticmethod
    def is_file_writable(file_path: str) -> bool:
        """
        Check if a file is writable.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is writable or doesn't exist (can be created)
        """
        path = Path(file_path)
        
        # Check if parent directory is writable
        if not FileUtils.ensure_directory(str(path.parent)):
            return False
        
        # If file exists, check write permission
        if path.exists():
            try:
                with open(path, 'a') as f:
                    pass
                return True
            except (IOError, OSError):
                return False
        
        return True
    
    @staticmethod
    def safe_delete(file_path: str) -> bool:
        """
        Safely delete a file if it exists.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if file was deleted or didn't exist
        """
        path = Path(file_path)
        if not path.exists():
            return True
        
        try:
            path.unlink()
            return True
        except (IOError, OSError) as e:
            logging.error(f"Failed to delete file {file_path}: {e}")
            return False


# Convenience functions
def create_backup_manager(base_dir: str = "data/progress") -> BackupManager:
    """Create a BackupManager for the progress directory."""
    backup_dir = os.path.join(base_dir, "backup")
    return BackupManager(backup_dir)


def create_validator() -> DataValidator:
    """Create a DataValidator instance."""
    return DataValidator()
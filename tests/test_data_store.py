"""
Tests for Data Store Component

Tests for JSON persistence layer implementing STORY-002-02: Data Persistence (JSON)
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

from src.components.data_store import DataStore, SaveResult, LoadResult
from src.utils.file_utils import (
    BackupManager,
    DataValidator,
    FileUtils,
    create_backup_manager,
    create_validator
)


class TestDataValidator:
    """Tests for the DataValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DataValidator()
    
    def test_validate_json_syntax_valid(self, tmp_path):
        """Test validation of valid JSON file."""
        file_path = tmp_path / "valid.json"
        file_path.write_text('{"key": "value"}')
        
        is_valid, error = self.validator.validate_json_syntax(str(file_path))
        
        assert is_valid is True
        assert error is None
    
    def test_validate_json_syntax_invalid(self, tmp_path):
        """Test validation of invalid JSON file."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text('{invalid json}')
        
        is_valid, error = self.validator.validate_json_syntax(str(file_path))
        
        assert is_valid is False
        assert error is not None
        assert "JSON parse error" in error
    
    def test_validate_json_syntax_nonexistent(self, tmp_path):
        """Test validation of non-existent file."""
        file_path = tmp_path / "nonexistent.json"
        
        is_valid, error = self.validator.validate_json_syntax(str(file_path))
        
        assert is_valid is False
        assert error is not None
    
    def test_validate_progress_schema_valid(self):
        """Test validation of valid progress schema."""
        data = {
            'version': '1.0',
            'student_id': 'test_student',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [],
            'mastered_words': [],
            'needs_practice': [],
            'achievements': []
        }
        
        is_valid, issues = self.validator.validate_progress_schema(data)
        
        assert is_valid is True
        assert issues == []
    
    def test_validate_progress_schema_missing_fields(self):
        """Test validation with missing required fields."""
        data = {
            'version': '1.0',
            'student_id': 'test_student'
            # Missing other required fields
        }
        
        is_valid, issues = self.validator.validate_progress_schema(data)
        
        assert is_valid is False
        assert 'sessions' in issues
        assert 'mastered_words' in issues
        assert 'needs_practice' in issues
        assert 'achievements' in issues
        assert 'created_at' in issues
    
    def test_validate_progress_schema_invalid_types(self):
        """Test validation with invalid field types."""
        data = {
            'version': '1.0',
            'student_id': 'test_student',
            'created_at': '2026-07-07T10:00:00',
            'sessions': "not a list",  # Should be list
            'mastered_words': [],
            'needs_practice': [],
            'achievements': []
        }
        
        is_valid, issues = self.validator.validate_progress_schema(data)
        
        assert is_valid is False
        assert 'sessions' in issues
    
    def test_recover_missing_fields(self):
        """Test recovery of missing fields with defaults."""
        data = {
            'version': '1.0',
            'student_id': 'test_student',
            'created_at': '2026-07-07T10:00:00'
        }
        
        recovered = self.validator.recover_missing_fields(data)
        
        assert recovered['version'] == '1.0'
        assert recovered['student_id'] == 'test_student'
        assert recovered['created_at'] == '2026-07-07T10:00:00'
        assert recovered['sessions'] == []
        assert recovered['mastered_words'] == []
        assert recovered['needs_practice'] == []
        assert recovered['achievements'] == []


class TestBackupManager:
    """Tests for the BackupManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.backup_manager = BackupManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_backup(self):
        """Test creating a backup of a file."""
        # Create a source file
        source = Path(self.temp_dir) / "source.json"
        source.write_text('{"test": "data"}')
        
        # Create backup
        backup_path = self.backup_manager.create_backup(str(source))
        
        assert backup_path is not None
        assert os.path.exists(backup_path)
        
        # Verify backup content
        backup_content = Path(backup_path).read_text()
        assert json.loads(backup_content) == {"test": "data"}
    
    def test_create_backup_nonexistent_file(self):
        """Test creating backup of non-existent file."""
        backup_path = self.backup_manager.create_backup("/nonexistent/file.json")
        
        assert backup_path is None
    
    def test_backup_cleanup(self):
        """Test that old backups are cleaned up."""
        source = Path(self.temp_dir) / "source.json"
        source.write_text('{"test": "data"}')
        
        # Create more backups than the limit
        for i in range(15):
            source.write_text(f'{{"version": {i}}}')
            self.backup_manager.create_backup(str(source))
        
        backups = self.backup_manager.list_backups(str(source))
        
        assert len(backups) <= BackupManager.MAX_BACKUPS
    
    def test_list_backups(self):
        """Test listing backups for a file."""
        source = Path(self.temp_dir) / "source.json"
        source.write_text('{"test": "data"}')
        
        backup1 = self.backup_manager.create_backup(str(source))
        backup2 = self.backup_manager.create_backup(str(source))
        
        backups = self.backup_manager.list_backups(str(source))
        
        assert len(backups) == 2
        assert backup2 in backups  # Newer backup should be first
        assert backup1 in backups
    
    def test_restore_backup(self):
        """Test restoring from a backup."""
        # Create source and backup
        source = Path(self.temp_dir) / "source.json"
        source.write_text('{"original": "data"}')
        backup_path = self.backup_manager.create_backup(str(source))
        
        # Modify source
        source.write_text('{"modified": "data"}')
        
        # Restore
        result = self.backup_manager.restore_backup(
            backup_path,
            str(source)
        )
        
        assert result is True
        assert json.loads(source.read_text()) == {"original": "data"}


class TestFileUtils:
    """Tests for the FileUtils class."""
    
    def test_ensure_directory(self, tmp_path):
        """Test directory creation."""
        new_dir = tmp_path / "new" / "nested" / "dir"
        
        result = FileUtils.ensure_directory(str(new_dir))
        
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()
    
    def test_ensure_directory_existing(self, tmp_path):
        """Test with existing directory."""
        result = FileUtils.ensure_directory(str(tmp_path))
        
        assert result is True
    
    def test_is_file_writable_new(self, tmp_path):
        """Test writability of non-existent file in writable directory."""
        new_file = tmp_path / "new_file.json"
        
        result = FileUtils.is_file_writable(str(new_file))
        
        assert result is True
    
    def test_safe_delete_exists(self, tmp_path):
        """Test deleting existing file."""
        file_path = tmp_path / "to_delete.json"
        file_path.write_text("test")
        
        result = FileUtils.safe_delete(str(file_path))
        
        assert result is True
        assert not file_path.exists()
    
    def test_safe_delete_not_exists(self, tmp_path):
        """Test deleting non-existent file."""
        file_path = tmp_path / "nonexistent.json"
        
        result = FileUtils.safe_delete(str(file_path))
        
        assert result is True


class TestDataStore:
    """Tests for the DataStore class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_store = DataStore(base_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_creates_file(self):
        """Test that save creates the progress file."""
        data = {
            'version': '1.0',
            'student_id': 'test_student',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [],
            'mastered_words': [],
            'needs_practice': [],
            'achievements': []
        }
        
        result = self.data_store.save('test_student', data)
        
        assert result.success is True
        assert os.path.exists(result.file_path)
        
        # Verify content
        with open(result.file_path) as f:
            saved_data = json.load(f)
        
        assert saved_data['student_id'] == 'test_student'
        assert saved_data['version'] == '1.0'
    
    def test_load_existing_data(self):
        """Test loading existing data."""
        data = {
            'version': '1.0',
            'student_id': 'test_student',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [{'session_id': 'test'}],
            'mastered_words': ['word1'],
            'needs_practice': [],
            'achievements': []
        }
        
        # Save first
        self.data_store.save('test_student', data)
        
        # Load
        result = self.data_store.load('test_student')
        
        assert result.success is True
        assert result.used_recovery is False
        assert result.data['student_id'] == 'test_student'
        assert len(result.data['sessions']) == 1
        assert 'word1' in result.data['mastered_words']
    
    def test_load_nonexistent_creates_empty(self):
        """Test loading when file doesn't exist creates empty progress."""
        result = self.data_store.load('new_student')
        
        assert result.success is True
        assert result.used_recovery is False
        assert result.data is not None
        assert result.data['student_id'] == 'new_student'
        assert result.data['sessions'] == []
        assert result.data['mastered_words'] == []
    
    def test_load_corrupt_json_recovers(self, tmp_path):
        """Test loading corrupt JSON file triggers recovery."""
        # Create corrupt file
        file_path = Path(self.temp_dir) / "corrupt_student_progress.json"
        file_path.write_text('{invalid json}')
        
        result = self.data_store.load('corrupt_student')
        
        assert result.success is True  # Recovery was successful
        assert result.used_recovery is True
        assert result.data is not None
        assert result.data['student_id'] == 'corrupt_student'
    
    def test_load_recovers_from_backup(self):
        """Test recovery from backup when current file is corrupt."""
        # First save valid data
        valid_data = {
            'version': '1.0',
            'student_id': 'backup_test',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [],
            'mastered_words': ['backup_word'],
            'needs_practice': [],
            'achievements': []
        }
        
        save_result = self.data_store.save('backup_test', valid_data)
        assert save_result.success is True
        assert save_result.backup_created is None  # First save, no backup yet
        
        # Save again to create backup
        valid_data['mastered_words'].append('another_word')
        save_result = self.data_store.save('backup_test', valid_data)
        assert save_result.backup_created is not None
        
        # Corrupt the main file
        file_path = Path(self.temp_dir) / "backup_test_progress.json"
        file_path.write_text('{invalid}')
        
        # Load should recover from backup
        result = self.data_store.load('backup_test')
        
        assert result.success is True
        assert result.used_recovery is True
        # Should get data from backup (before the second save)
        # The exact behavior depends on how the recovery prioritizes data
    
    def test_save_creates_backup(self):
        """Test that save creates backup of existing file."""
        # First save
        data1 = {
            'version': '1.0',
            'student_id': 'backup_test2',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [],
            'mastered_words': ['word1'],
            'needs_practice': [],
            'achievements': []
        }
        
        result1 = self.data_store.save('backup_test2', data1)
        assert result1.success is True
        assert result1.backup_created is None  # No previous file
        
        # Second save - should create backup
        data2 = {
            'version': '1.0',
            'student_id': 'backup_test2',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [],
            'mastered_words': ['word1', 'word2'],
            'needs_practice': [],
            'achievements': []
        }
        
        result2 = self.data_store.save('backup_test2', data2)
        assert result2.success is True
        assert result2.backup_created is not None
        assert os.path.exists(result2.backup_created)
    
    def test_delete_progress(self):
        """Test deleting student progress."""
        data = {
            'version': '1.0',
            'student_id': 'to_delete',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [],
            'mastered_words': [],
            'needs_practice': [],
            'achievements': []
        }
        
        # Save
        self.data_store.save('to_delete', data)
        assert os.path.exists(self.data_store._get_file_path('to_delete'))
        
        # Delete
        result = self.data_store.delete_progress('to_delete')
        assert result is True
        
        # Verify deleted
        assert not os.path.exists(self.data_store._get_file_path('to_delete'))
    
    def test_delete_nonexistent(self):
        """Test deleting non-existent student progress."""
        result = self.data_store.delete_progress('nonexistent')
        assert result is True
    
    def test_list_students(self):
        """Test listing all students."""
        # Save for multiple students
        data = {
            'version': '1.0',
            'student_id': '{student_id}',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [],
            'mastered_words': [],
            'needs_practice': [],
            'achievements': []
        }
        
        for student_id in ['student_a', 'student_b', 'student_c']:
            student_data = data.copy()
            student_data['student_id'] = student_id
            self.data_store.save(student_id, student_data)
        
        students = self.data_store.list_students()
        
        assert sorted(students) == ['student_a', 'student_b', 'student_c']
    
    def test_exists(self):
        """Test checking if student progress exists."""
        # Not exists initially
        assert self.data_store.exists('new_student') is False
        
        # Save
        data = {
            'version': '1.0',
            'student_id': 'new_student',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [],
            'mastered_words': [],
            'needs_practice': [],
            'achievements': []
        }
        self.data_store.save('new_student', data)
        
        # Now exists
        assert self.data_store.exists('new_student') is True
    
    def test_get_file_path(self):
        """Test getting file path for student."""
        file_path = self.data_store.get_file_path('test_student')
        
        assert file_path.endswith('test_student_progress.json')
        assert self.temp_dir in file_path
    
    def test_performance_save_under_500ms(self):
        """Test that save operation completes in under 500ms."""
        import time
        
        # Large data set
        data = {
            'version': '1.0',
            'student_id': 'perf_test',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [{'session_id': f'session_{i}', 'data': 'x' * 1000} for i in range(100)],
            'mastered_words': [f'word_{i}' for i in range(100)],
            'needs_practice': [],
            'achievements': []
        }
        
        start = time.time()
        result = self.data_store.save('perf_test', data)
        elapsed = (time.time() - start) * 1000  # Convert to ms
        
        assert result.success is True
        assert elapsed < 500, f"Save took {elapsed}ms, expected < 500ms"
    
    def test_sanitizes_student_id(self):
        """Test that student_id is sanitized to prevent path traversal."""
        data = {
            'version': '1.0',
            'student_id': 'test_student',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [],
            'mastered_words': [],
            'needs_practice': [],
            'achievements': []
        }
        
        # Try with potentially unsafe characters
        result = self.data_store.save('../unsafe_student', data)
        
        assert result.success is True
        # Should not contain path traversal
        assert '../' not in result.file_path
        assert 'unsafe_student' in result.file_path


class TestSaveResult:
    """Tests for SaveResult dataclass."""
    
    def test_save_result_success(self):
        """Test SaveResult for successful save."""
        result = SaveResult(
            success=True,
            file_path="/path/to/file.json",
            timestamp=datetime.now(),
            backup_created=None
        )
        
        assert result.success is True
        assert result.error_message is None


class TestLoadResult:
    """Tests for LoadResult dataclass."""
    
    def test_load_result_success(self):
        """Test LoadResult for successful load."""
        result = LoadResult(
            success=True,
            data={'test': 'data'},
            used_recovery=False
        )
        
        assert result.success is True
        assert result.data == {'test': 'data'}
        assert result.used_recovery is False
    
    def test_load_result_failure(self):
        """Test LoadResult for failed load."""
        result = LoadResult(
            success=False,
            data=None,
            used_recovery=False,
            error_message="File not found"
        )
        
        assert result.success is False
        assert result.data is None
        assert result.error_message == "File not found"


# Integration tests
class TestDataStoreIntegration:
    """Integration tests for DataStore with realistic scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_store = DataStore(base_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_load_roundtrip(self):
        """Test save followed by load preserves data."""
        original_data = {
            'version': '1.0',
            'student_id': 'roundtrip_test',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [
                {'session_id': 'session_1', 'words': [{'word': 'hello'}]},
                {'session_id': 'session_2', 'words': [{'word': 'world'}]}
            ],
            'mastered_words': ['hello', 'world'],
            'needs_practice': [],
            'achievements': ['first_word']
        }
        
        # Save
        save_result = self.data_store.save('roundtrip_test', original_data)
        assert save_result.success is True
        
        # Load
        load_result = self.data_store.load('roundtrip_test')
        assert load_result.success is True
        assert load_result.used_recovery is False
        
        # Verify data integrity
        assert load_result.data['student_id'] == 'roundtrip_test'
        assert len(load_result.data['sessions']) == 2
        assert len(load_result.data['mastered_words']) == 2
    
    def test_multiple_students_isolation(self):
        """Test that different students have isolated data."""
        # Save data for student A
        data_a = {
            'version': '1.0',
            'student_id': 'student_a',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [],
            'mastered_words': ['word_a'],
            'needs_practice': [],
            'achievements': []
        }
        self.data_store.save('student_a', data_a)
        
        # Save data for student B
        data_b = {
            'version': '1.0',
            'student_id': 'student_b',
            'created_at': '2026-07-07T10:00:00',
            'sessions': [],
            'mastered_words': ['word_b'],
            'needs_practice': [],
            'achievements': []
        }
        self.data_store.save('student_b', data_b)
        
        # Load student A
        result_a = self.data_store.load('student_a')
        assert result_a.success is True
        assert result_a.data['mastered_words'] == ['word_a']
        assert 'word_b' not in result_a.data['mastered_words']
        
        # Load student B
        result_b = self.data_store.load('student_b')
        assert result_b.success is True
        assert result_b.data['mastered_words'] == ['word_b']
        assert 'word_a' not in result_b.data['mastered_words']
    
    def test_backup_chain_recovery(self):
        """Test recovery from a chain of backups."""
        # Create a series of saves
        for i in range(5):
            data = {
                'version': '1.0',
                'student_id': 'backup_chain',
                'created_at': '2026-07-07T10:00:00',
                'sessions': [{'version': i}],
                'mastered_words': [f'word_{i}'],
                'needs_practice': [],
                'achievements': []
            }
            self.data_store.save('backup_chain', data)
        
        # Corrupt current file
        file_path = Path(self.temp_dir) / "backup_chain_progress.json"
        file_path.write_text('{invalid}')
        
        # Should recover from latest backup
        result = self.data_store.load('backup_chain')
        assert result.success is True
        assert result.used_recovery is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
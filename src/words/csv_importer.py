"""
CSV Importer Module

Provides CSV parsing, validation, and word list import functionality
for the Parent Dashboard word list management feature.
"""

import csv
import os
from typing import List, Dict, Tuple, Optional, TextIO
from dataclasses import dataclass, field
from enum import Enum
import uuid


class Difficulty(Enum):
    """Difficulty levels for spelling words."""
    BEGINNER = "beginner"
    MEDIUM = "medium"
    ADVANCED = "advanced"


@dataclass
class ParsedWord:
    """Represents a word parsed from CSV with validation status."""
    spelling: str
    definition: str
    difficulty: Difficulty
    row_number: int
    error: Optional[str] = None
    
    @property
    def is_valid(self) -> bool:
        """Check if the word was parsed successfully."""
        return self.error is None


@dataclass
class ImportResult:
    """Result of CSV import operation."""
    successful: List[ParsedWord] = field(default_factory=list)
    skipped: List[Tuple[int, str]] = field(default_factory=list)  # (row_number, reason)
    total_processed: int = 0
    
    @property
    def success_count(self) -> int:
        """Number of successfully parsed words."""
        return len(self.successful)
    
    @property
    def skip_count(self) -> int:
        """Number of rows that were skipped."""
        return len(self.skipped)
    
    def get_summary(self) -> str:
        """Get a human-readable import summary."""
        return f"Imported {self.success_count} words, skipped {self.skip_count}"


class CSVImporter:
    """
    Handles CSV file parsing and validation for word list imports.
    
    Features:
    - Auto-detect encoding (UTF-8, Latin-1, Windows-1252)
    - Auto-detect delimiter (comma, semicolon, tab)
    - Flexible column header recognition
    - Automatic difficulty assignment
    - Row-level validation with detailed error reporting
    """
    
    # Configuration constants
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MIN_WORD_LENGTH = 2
    MAX_WORD_LENGTH = 25
    
    # Column name variations to recognize (case-insensitive)
    WORD_COLUMNS = ["word", "spelling", "term", "vocabulary", "spelled word"]
    DEF_COLUMNS = ["definition", "definition", "meaning", "context", "description"]
    DIFF_COLUMNS = ["difficulty", "level", "grade", "category", "star"]
    
    # Default encoding fallbacks
    ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]
    
    # Valid difficulty value mappings
    DIFFICULTY_MAPPINGS = {
        "beginner": Difficulty.BEGINNER,
        "easy": Difficulty.BEGINNER,
        "b": Difficulty.BEGINNER,
        "1": Difficulty.BEGINNER,
        "low": Difficulty.BEGINNER,
        "medium": Difficulty.MEDIUM,
        "moderate": Difficulty.MEDIUM,
        "m": Difficulty.MEDIUM,
        "2": Difficulty.MEDIUM,
        "average": Difficulty.MEDIUM,
        "advanced": Difficulty.ADVANCED,
        "difficult": Difficulty.ADVANCED,
        "hard": Difficulty.ADVANCED,
        "a": Difficulty.ADVANCED,
        "3": Difficulty.ADVANCED,
        "high": Difficulty.ADVANCED,
    }
    
    def __init__(self, filepath: Optional[str] = None, file_obj: Optional[TextIO] = None):
        """
        Initialize CSV importer.
        
        Args:
            filepath: Path to the CSV file
            file_obj: File object (alternative to filepath)
        
        Raises:
            ValueError: If neither filepath nor file_obj is provided
        """
        if filepath is None and file_obj is None:
            raise ValueError("Either filepath or file_obj must be provided")
        
        self.filepath = filepath
        self.file_obj = file_obj
        self._content: Optional[str] = None
    
    def detect_encoding(self, content: bytes) -> str:
        """
        Auto-detect file encoding using heuristics.
        
        Args:
            content: Raw bytes from the file
            
        Returns:
            Detected encoding name
        """
        # Try common encodings in order of likelihood
        for encoding in self.ENCODINGS:
            try:
                content.decode(encoding)
                return encoding
            except (UnicodeDecodeError, LookupError):
                continue
        
        # Fallback to utf-8 with errors replaced
        return "utf-8"
    
    def detect_delimiter(self, sample: str) -> str:
        """
        Auto-detect CSV delimiter from sample content.
        
        Args:
            sample: Sample text from the file
            
        Returns:
            Detected delimiter character
        """
        # Count occurrences of potential delimiters
        delimiters = [",", ";", "\t"]
        counts = {d: sample.count(d) for d in delimiters}
        
        # Return delimiter with highest count (must have at least one)
        detected = max(counts, key=counts.get)
        if counts[detected] == 0:
            return ","  # Default to comma
        
        return detected
    
    def parse_header(self, row: List[str]) -> Dict[str, int]:
        """
        Identify column indices for word, definition, and difficulty.
        
        Args:
            row: First row of CSV (assumed to be header)
            
        Returns:
            Dictionary mapping field names to column indices
        """
        mapping: Dict[str, int] = {}
        
        for i, cell in enumerate(row):
            header = cell.lower().strip()
            
            if header in self.WORD_COLUMNS and "word" not in mapping:
                mapping["word"] = i
            elif header in self.DEF_COLUMNS and "definition" not in mapping:
                mapping["definition"] = i
            elif header in self.DIFF_COLUMNS and "difficulty" not in mapping:
                mapping["difficulty"] = i
        
        return mapping
    
    @staticmethod
    def is_safe_path(filepath: str) -> bool:
        """
        Check if filepath does not contain path traversal patterns.
        
        Args:
            filepath: The file path to check
            
        Returns:
            True if the path is safe (no path traversal), False otherwise
        """
        try:
            # Check for path traversal patterns
            if ".." in filepath:
                return False
            
            # Check for absolute paths that are system directories
            abs_path = os.path.abspath(filepath)
            system_dirs = ["/etc", "/bin", "/sbin", "/usr", "/root"]
            for sys_dir in system_dirs:
                if abs_path.startswith(sys_dir + os.sep) or abs_path == sys_dir:
                    return False
            
            return True
        except (OSError, ValueError):
            return False
    
    def _validate_word(self, spelling: str) -> Optional[str]:
        """
        Validate a spelled word.
        
        Args:
            spelling: The word text to validate
            
        Returns:
            Error message if invalid, None if valid
        """
        if not spelling:
            return "Missing word"
        
        if len(spelling) < self.MIN_WORD_LENGTH:
            return f"Word too short (minimum {self.MIN_WORD_LENGTH} letters)"
        
        if len(spelling) > self.MAX_WORD_LENGTH:
            return f"Word too long (maximum {self.MAX_WORD_LENGTH} letters)"
        
        # Check for valid characters (letters and hyphens only)
        cleaned = spelling.replace("-", "")
        if not cleaned.isalpha():
            return "Word contains invalid characters (letters and hyphens only)"
        
        return None
    
    @staticmethod
    def _generate_word_id() -> str:
        """
        Generate a unique word ID using UUID.
        
        Returns:
            Unique ID string (e.g., 'csv_8f3a2b1c')
        """
        return f"csv_{uuid.uuid4().hex[:8]}"
    
    def _auto_assign_difficulty(self, spelling: str) -> Difficulty:
        """
        Assign difficulty based on word characteristics.
        
        Uses word length as primary heuristic:
        - 2-5 letters: Beginner
        - 6-8 letters: Medium
        - 9+ letters: Advanced
        
        Args:
            spelling: The word text
            
        Returns:
            Assigned difficulty level
        """
        length = len(spelling)
        if length <= 5:
            return Difficulty.BEGINNER
        elif length <= 8:
            return Difficulty.MEDIUM
        else:
            return Difficulty.ADVANCED
    
    def _normalize_difficulty(self, value: str) -> Optional[Difficulty]:
        """
        Parse difficulty value from CSV cell.
        
        Args:
            value: Raw string value from CSV
            
        Returns:
            Normalized Difficulty enum or None if not found
        """
        if not value:
            return None
        
        value = value.lower().strip()
        return self.DIFFICULTY_MAPPINGS.get(value)
    
    def _parse_row(self, row: List[str], header: Dict[str, int], row_num: int) -> ParsedWord:
        """
        Parse a single CSV row into a ParsedWord.
        
        Args:
            row: CSV row as list of strings
            header: Header mapping from parse_header()
            row_num: Row number (1-indexed, including header)
            
        Returns:
            ParsedWord with either valid data or error message
        """
        try:
            # Get word (required)
            word_idx = header.get("word", 0)
            if word_idx >= len(row):
                return ParsedWord("", "", Difficulty.MEDIUM, row_num, "Missing word column")
            
            spelling = row[word_idx].strip().upper()
            
            # Validate word
            error = self._validate_word(spelling)
            if error:
                return ParsedWord("", "", Difficulty.MEDIUM, row_num, error)
            
            # Get definition (optional)
            def_idx = header.get("definition")
            definition = ""
            if def_idx is not None and def_idx < len(row):
                definition = row[def_idx].strip()
            
            # Get difficulty
            diff_idx = header.get("difficulty")
            difficulty = None
            if diff_idx is not None and diff_idx < len(row):
                difficulty = self._normalize_difficulty(row[diff_idx])
            
            # Auto-assign if not provided
            if difficulty is None:
                difficulty = self._auto_assign_difficulty(spelling)
            
            return ParsedWord(spelling, definition[:500] if definition else "", difficulty, row_num)
        
        except Exception as e:
            return ParsedWord("", "", Difficulty.MEDIUM, row_num, f"Parse error: {str(e)}")
    
    def parse_file(self) -> ImportResult:
        """
        Parse CSV file and return import results.
        
        Returns:
            ImportResult with successful words and skipped rows
        """
        successful: List[ParsedWord] = []
        skipped: List[Tuple[int, str]] = []
        
        # Validate file path to prevent path traversal attacks
        if self.filepath and not self.is_safe_path(self.filepath):
            return ImportResult(
                skipped=[(0, "Invalid file path")],
                total_processed=0
            )
        
        # Check file exists
        if self.filepath and not os.path.exists(self.filepath):
            return ImportResult(skipped=[(0, "File not found")], total_processed=0)
        
        # Check file size to prevent DoS attacks
        if self.filepath:
            try:
                file_size = os.path.getsize(self.filepath)
                if file_size > self.MAX_FILE_SIZE:
                    return ImportResult(
                        skipped=[(0, f"File too large (max {self.MAX_FILE_SIZE // 1024 // 1024}MB)")],
                        total_processed=0
                    )
            except OSError:
                return ImportResult(skipped=[(0, "Could not read file size")], total_processed=0)
        
        # Read file content
        try:
            if self.file_obj:
                content = self.file_obj.read()
                if isinstance(content, bytes):
                    encoding = self.detect_encoding(content)
                    content = content.decode(encoding)
            else:
                if not self.filepath:
                    return ImportResult(skipped=[(0, "No file specified")], total_processed=0)
                
                encoding = self.detect_encoding(open(self.filepath, "rb").read())
                with open(self.filepath, "r", encoding=encoding) as f:
                    content = f.read()
            
            self._content = content
            
        except FileNotFoundError:
            return ImportResult(skipped=[(0, "File not found")], total_processed=0)
        except PermissionError:
            return ImportResult(skipped=[(0, "Permission denied")], total_processed=0)
        except Exception as e:
            # Log detailed error internally, show generic message to user
            import logging
            logging.error(f"CSV parse error: {e}")
            return ImportResult(skipped=[(0, "Could not read file")], total_processed=0)
        
        # Parse content
        lines = content.strip().split("\n")
        if not lines or not any(line.strip() for line in lines):
            return ImportResult(skipped=[(0, "File is empty")], total_processed=0)
        
        # Detect delimiter from first non-empty line
        first_line = next((l for l in lines if l.strip()), "")
        delimiter = self.detect_delimiter(first_line)
        
        # Parse CSV using Python's csv module
        try:
            reader = csv.reader(lines, delimiter=delimiter)
            rows = [row for row in reader]
        except Exception as e:
            return ImportResult(skipped=[(0, f"CSV parsing error: {str(e)}")], total_processed=0)
        
        # Filter empty rows
        rows = [row for row in rows if any(cell.strip() for cell in row)]
        
        if not rows:
            return ImportResult(skipped=[(0, "No data found")], total_processed=0)
        
        # Check if first row is header
        header_mapping: Dict[str, int] = {}
        start_row = 0
        
        first_row_lower = [c.lower().strip() for c in rows[0]]
        has_header = any(
            any(header_var in cell for header_var in self.WORD_COLUMNS)
            for cell in first_row_lower
        )
        
        if has_header:
            header_mapping = self.parse_header(rows[0])
            start_row = 1
        else:
            # No header, assume first column is word
            header_mapping = {"word": 0}
            start_row = 0
        
        # Parse data rows
        total_processed = 0
        for i, row in enumerate(rows[start_row:], start=start_row + 1):
            total_processed += 1
            
            # Skip completely empty rows
            if not row or all(not cell.strip() for cell in row):
                continue
            
            # Skip rows with missing data
            if len(row) < 1:
                skipped.append((i, "Missing columns"))
                continue
            
            parsed = self._parse_row(row, header_mapping, i)
            if parsed.is_valid:
                successful.append(parsed)
            else:
                skipped.append((i, parsed.error or "Validation error"))
        
        return ImportResult(
            successful=successful,
            skipped=skipped,
            total_processed=total_processed
        )
    
    @staticmethod
    def create_sample_csv(output_path: str) -> None:
        """
        Create a sample CSV template file.
        
        Args:
            output_path: Path where to save the sample file
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        sample_data = [
            ["word", "definition", "difficulty"],
            ["example", "a set of facts or circumstances", "medium"],
            ["practice", "to do something repeatedly to improve", "medium"],
            ["beautiful", "very pleasing to look at", "easy"],
            ["accomplish", "to succeed in doing something", "hard"],
        ]
        
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(sample_data)


def import_from_csv(filepath: str) -> ImportResult:
    """
    Convenience function to import words from a CSV file.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        ImportResult with parsed words and error information
    """
    importer = CSVImporter(filepath)
    return importer.parse_file()
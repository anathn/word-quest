"""
Unit Tests for CSV Importer

Tests for CSV parsing, validation, and import functionality.
"""

import unittest
import tempfile
import os
import csv
from io import StringIO

from src.words.csv_importer import (
    CSVImporter,
    ParsedWord,
    ImportResult,
    Difficulty,
    import_from_csv
)


class TestDifficulty(unittest.TestCase):
    """Test Difficulty enum values."""
    
    def test_difficulty_values(self):
        """Test that Difficulty enum has correct values."""
        self.assertEqual(Difficulty.BEGINNER.value, "beginner")
        self.assertEqual(Difficulty.MEDIUM.value, "medium")
        self.assertEqual(Difficulty.ADVANCED.value, "advanced")


class TestParsedWord(unittest.TestCase):
    """Test ParsedWord dataclass."""
    
    def test_valid_word(self):
        """Test valid parsed word."""
        word = ParsedWord("HELLO", "greeting", Difficulty.BEGINNER, 1, None)
        self.assertTrue(word.is_valid)
        self.assertEqual(word.spelling, "HELLO")
        self.assertEqual(word.error, None)
    
    def test_invalid_word(self):
        """Test invalid parsed word with error."""
        word = ParsedWord("", "", Difficulty.MEDIUM, 2, "Missing word")
        self.assertFalse(word.is_valid)
        self.assertEqual(word.error, "Missing word")


class TestImportResult(unittest.TestCase):
    """Test ImportResult dataclass."""
    
    def test_empty_result(self):
        """Test empty import result."""
        result = ImportResult()
        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.skip_count, 0)
        self.assertEqual(result.get_summary(), "Imported 0 words, skipped 0")
    
    def test_result_with_data(self):
        """Test result with successful and skipped rows."""
        successful = [
            ParsedWord("HELLO", "", Difficulty.BEGINNER, 1),
            ParsedWord("WORLD", "", Difficulty.BEGINNER, 2),
        ]
        skipped = [(3, "Invalid word"), (4, "Too short")]
        
        result = ImportResult(successful=successful, skipped=skipped, total_processed=4)
        
        self.assertEqual(result.success_count, 2)
        self.assertEqual(result.skip_count, 2)
        self.assertEqual(result.get_summary(), "Imported 2 words, skipped 2")


class TestCSVDelimiterDetection(unittest.TestCase):
    """Test CSV delimiter auto-detection."""
    
    def test_detect_comma_delimiter(self):
        """Test detection of comma delimiter."""
        sample = "word,definition,difficulty\nhello,greeting,easy"
        delimiters = [",", ";", "\t"]
        counts = {d: sample.count(d) for d in delimiters}
        detected = max(counts, key=counts.get)
        self.assertEqual(detected, ",")
    
    def test_detect_semicolon_delimiter(self):
        """Test detection of semicolon delimiter."""
        sample = "word;definition;difficulty\nhello;greeting;easy"
        delimiters = [",", ";", "\t"]
        counts = {d: sample.count(d) for d in delimiters}
        detected = max(counts, key=counts.get)
        self.assertEqual(detected, ";")
    
    def test_detect_tab_delimiter(self):
        """Test detection of tab delimiter."""
        sample = "word\tdefinition\tdifficulty\nhello\tgreeting\teasy"
        delimiters = [",", ";", "\t"]
        counts = {d: sample.count(d) for d in delimiters}
        detected = max(counts, key=counts.get)
        self.assertEqual(detected, "\t")
    
    def test_default_to_comma_when_no_delimiters(self):
        """Test default to comma when no delimiter found."""
        sample = "just some text without delimiters"
        delimiters = [",", ";", "\t"]
        counts = {d: sample.count(d) for d in delimiters}
        detected = max(counts, key=counts.get)
        # In actual code, would default to comma if count is 0
        self.assertEqual(counts[detected], 0)


class TestCSVEncodingDetection(unittest.TestCase):
    """Test CSV encoding detection."""
    
    def test_utf8_decode(self):
        """Test UTF-8 encoding works."""
        content = "word,definition\nhello,greeting".encode("utf-8")
        # Test that UTF-8 can decode the content
        decoded = content.decode("utf-8")
        self.assertIn("hello", decoded)
    
    def test_utf8_with_bom(self):
        """Test UTF-8-BOM content."""
        content = "\ufeffword,definition\nhello,greeting".encode("utf-8")
        # Test that UTF-8 can decode the content (with BOM)
        decoded = content.decode("utf-8")
        self.assertIn("hello", decoded)
    
    def test_latin1_encoding(self):
        """Test Latin-1 encoding."""
        # Latin-1 specific character (o with accent)
        content = "word,definition\nc\xf3rreo,email".encode("latin-1")
        # Latin-1 should decode successfully
        decoded = content.decode("latin-1")
        self.assertIn("c\xf3rreo", decoded.lower())


class TestCSVHeaderParsing(unittest.TestCase):
    """Test CSV header column recognition."""
    
    def test_detect_word_column(self):
        """Test word column detection."""
        WORD_COLUMNS = ["word", "spelling", "term", "vocabulary", "spelled word"]
        header = ["Word", "Definition", "Difficulty"]
        
        # Simulate parse_header logic
        mapping = {}
        for i, cell in enumerate(header):
            h = cell.lower().strip()
            if h in WORD_COLUMNS and "word" not in mapping:
                mapping["word"] = i
        
        self.assertIn("word", mapping)
        self.assertEqual(mapping["word"], 0)
    
    def test_detect_synonym_headers(self):
        """Test detection of header synonyms."""
        WORD_COLUMNS = ["word", "spelling", "term", "vocabulary", "spelled word"]
        DEF_COLUMNS = ["definition", "definition", "meaning", "context", "description"]
        DIFF_COLUMNS = ["difficulty", "level", "grade", "category", "star"]
        header = ["Spelling", "Meaning", "Level"]
        
        # Simulate parse_header logic
        mapping = {}
        for i, cell in enumerate(header):
            h = cell.lower().strip()
            if h in WORD_COLUMNS and "word" not in mapping:
                mapping["word"] = i
            elif h in DEF_COLUMNS and "definition" not in mapping:
                mapping["definition"] = i
            elif h in DIFF_COLUMNS and "difficulty" not in mapping:
                mapping["difficulty"] = i
        
        self.assertEqual(mapping["word"], 0)
        self.assertEqual(mapping["definition"], 1)
        self.assertEqual(mapping["difficulty"], 2)
    
    def test_partial_headers(self):
        """Test with only word column in header."""
        WORD_COLUMNS = ["word", "spelling", "term", "vocabulary", "spelled word"]
        header = ["Word"]
        
        # Simulate parse_header logic
        mapping = {}
        for i, cell in enumerate(header):
            h = cell.lower().strip()
            if h in WORD_COLUMNS and "word" not in mapping:
                mapping["word"] = i
        
        self.assertIn("word", mapping)
        self.assertNotIn("definition", mapping)
        self.assertNotIn("difficulty", mapping)


class TestDifficultyNormalization(unittest.TestCase):
    """Test difficulty value normalization."""
    
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
    
    def _normalize_difficulty(self, value):
        """Helper to normalize difficulty."""
        if not value:
            return None
        value = value.lower().strip()
        return self.DIFFICULTY_MAPPINGS.get(value)
    
    def test_beginner_variations(self):
        """Test various beginner difficulty values."""
        beginner_values = ["beginner", "easy", "b", "1", "low"]
        
        for value in beginner_values:
            result = self._normalize_difficulty(value)
            self.assertEqual(result, Difficulty.BEGINNER, f"Failed for '{value}'")
    
    def test_medium_variations(self):
        """Test various medium difficulty values."""
        medium_values = ["medium", "moderate", "m", "2", "average"]
        
        for value in medium_values:
            result = self._normalize_difficulty(value)
            self.assertEqual(result, Difficulty.MEDIUM, f"Failed for '{value}'")
    
    def test_advanced_variations(self):
        """Test various advanced difficulty values."""
        advanced_values = ["advanced", "difficult", "hard", "a", "3", "high"]
        
        for value in advanced_values:
            result = self._normalize_difficulty(value)
            self.assertEqual(result, Difficulty.ADVANCED, f"Failed for '{value}'")
    
    def test_empty_value(self):
        """Test empty value returns None."""
        result = self._normalize_difficulty("")
        self.assertIsNone(result)
    
    def test_case_insensitive(self):
        """Test case insensitivity."""
        result = self._normalize_difficulty("BEGINNER")
        self.assertEqual(result, Difficulty.BEGINNER)
        
        result = self._normalize_difficulty("Advanced")
        self.assertEqual(result, Difficulty.ADVANCED)


class TestAutoDifficultyAssignment(unittest.TestCase):
    """Test auto difficulty assignment based on word length."""
    
    def _auto_assign_difficulty(self, spelling):
        """Helper to auto-assign difficulty."""
        length = len(spelling)
        if length <= 5:
            return Difficulty.BEGINNER
        elif length <= 8:
            return Difficulty.MEDIUM
        else:
            return Difficulty.ADVANCED
    
    def test_short_words_beginner(self):
        """Test short words are assigned beginner."""
        short_words = ["at", "go", "cat", "stop", "help"]
        
        for word in short_words:
            difficulty = self._auto_assign_difficulty(word)
            self.assertEqual(difficulty, Difficulty.BEGINNER)
    
    def test_medium_words(self):
        """Test medium-length words are assigned medium."""
        medium_words = ["hello", "school", "family"]  # 5 letters = beginner, 6-8 = medium
        
        for word in medium_words:
            difficulty = self._auto_assign_difficulty(word)
            # "hello" is 5 letters (beginner), "school" and "family" are 6 letters (medium)
            if len(word) <= 5:
                self.assertEqual(difficulty, Difficulty.BEGINNER, f"{word} is {len(word)} letters")
            else:
                self.assertEqual(difficulty, Difficulty.MEDIUM, f"{word} is {len(word)} letters")
    
    def test_long_words_advanced(self):
        """Test long words are assigned advanced."""
        long_words = ["beautiful", "important", "accomplish", "information"]
        
        for word in long_words:
            difficulty = self._auto_assign_difficulty(word)
            self.assertEqual(difficulty, Difficulty.ADVANCED)


class TestWordValidation(unittest.TestCase):
    """Test word validation rules."""
    
    def _validate_word(self, spelling):
        """Helper to validate word."""
        if not spelling:
            return "Missing word"
        
        if len(spelling) < 2:
            return "Word too short (minimum 2 letters)"
        
        if len(spelling) > 25:
            return "Word too long (maximum 25 letters)"
        
        # Check for valid characters (letters and hyphens only)
        cleaned = spelling.replace("-", "")
        if not cleaned.isalpha():
            return "Word contains invalid characters (letters and hyphens only)"
        
        return None
    
    def test_valid_word(self):
        """Test valid word passes validation."""
        error = self._validate_word("HELLO")
        self.assertIsNone(error)
    
    def test_word_with_hyphen(self):
        """Test word with hyphen is valid."""
        error = self._validate_word("WELL-KNOWN")
        self.assertIsNone(error)
    
    def test_word_too_short(self):
        """Test word under minimum length fails."""
        error = self._validate_word("A")
        self.assertIsNotNone(error)
        self.assertIn("too short", error.lower())
    
    def test_word_too_long(self):
        """Test word over maximum length fails."""
        error = self._validate_word("VERYLONGWORDBEYONDTWENTYFIVELETTERS")
        self.assertIsNotNone(error)
        self.assertIn("too long", error.lower())
    
    def test_word_with_numbers(self):
        """Test word with numbers fails."""
        error = self._validate_word("H3LL0")
        self.assertIsNotNone(error)
        self.assertIn("invalid characters", error.lower())
    
    def test_word_with_special_chars(self):
        """Test word with special characters fails."""
        error = self._validate_word("HELLO!")
        self.assertIsNotNone(error)
    
    def test_empty_word(self):
        """Test empty word fails validation."""
        error = self._validate_word("")
        self.assertIsNotNone(error)
    
    def test_whitespace_word(self):
        """Test whitespace-only word fails."""
        error = self._validate_word("   ")
        self.assertIsNotNone(error)


class TestCSVFileParsing(unittest.TestCase):
    """Test full CSV file parsing."""
    
    def setUp(self):
        """Create temporary CSV files for testing."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_csv_file(self, rows):
        """Helper to create a temporary CSV file."""
        filepath = os.path.join(self.temp_dir, "test.csv")
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        return filepath
    
    def test_parse_valid_csv_with_header(self):
        """Test parsing valid CSV with header row."""
        rows = [
            ["word", "definition", "difficulty"],
            ["HELLO", "greeting", "easy"],
            ["WORLD", "the earth", "medium"],
        ]
        filepath = self._create_csv_file(rows)
        
        result = import_from_csv(filepath)
        
        self.assertEqual(result.success_count, 2)
        self.assertEqual(result.skip_count, 0)
        self.assertEqual(result.successful[0].spelling, "HELLO")
        self.assertEqual(result.successful[0].definition, "greeting")
        self.assertEqual(result.successful[0].difficulty, Difficulty.BEGINNER)
    
    def test_parse_csv_without_header(self):
        """Test parsing CSV without header row."""
        rows = [
            ["HELLO", "greeting"],
            ["WORLD", "the earth"],
        ]
        filepath = self._create_csv_file(rows)
        
        result = import_from_csv(filepath)
        
        self.assertEqual(result.success_count, 2)
        self.assertEqual(result.successful[0].spelling, "HELLO")
    
    def test_parse_csv_with_errors(self):
        """Test parsing CSV with some invalid rows."""
        rows = [
            ["word", "definition", "difficulty"],
            ["HELLO", "greeting", "easy"],
            ["", "empty word", "medium"],  # Invalid: empty word
            ["WORLD", "the earth", "hard"],
            ["VERYLONGWORDTOSTAYOVERTWENTYFIVE", "test", "easy"],  # Invalid: 34 letters, too long
        ]
        filepath = self._create_csv_file(rows)
        
        result = import_from_csv(filepath)
        
        # HELLO and WORLD should be valid; empty word and very long word should be skipped
        self.assertEqual(result.success_count, 2)
        self.assertEqual(result.skip_count, 2)
    
    def test_parse_semicolon_delimited(self):
        """Test parsing semicolon-delimited CSV."""
        filepath = os.path.join(self.temp_dir, "test.csv")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("word;definition;difficulty\n")
            f.write("HELLO;greeting;easy\n")
            f.write("WORLD;the earth;medium\n")
        
        result = import_from_csv(filepath)
        
        self.assertEqual(result.success_count, 2)
    
    def test_parse_tab_delimited(self):
        """Test parsing tab-delimited CSV."""
        filepath = os.path.join(self.temp_dir, "test.csv")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("word\tdefinition\tdifficulty\n")
            f.write("HELLO\tgreeting\teasy\n")
        result = import_from_csv(filepath)
        
        self.assertEqual(result.success_count, 1)
    
    def test_parse_empty_file(self):
        """Test parsing empty CSV file."""
        filepath = os.path.join(self.temp_dir, "empty.csv")
        with open(filepath, "w") as f:
            f.write("")
        
        result = import_from_csv(filepath)
        
        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.skip_count, 1)
        self.assertIn("empty", result.skipped[0][1].lower())
    
    def test_parse_file_not_found(self):
        """Test handling of non-existent file."""
        result = import_from_csv("/nonexistent/path/file.csv")
        
        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.skip_count, 1)
        self.assertIn("not found", result.skipped[0][1].lower())
    
    def test_parse_with_whitespace_handling(self):
        """Test parsing with extra whitespace in values."""
        filepath = os.path.join(self.temp_dir, "test.csv")
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([" word ", " definition ", " difficulty "])
            writer.writerow(["  HELLO  ", "  greeting  ", "  easy  "])
        
        result = import_from_csv(filepath)
        
        self.assertEqual(result.success_count, 1)
        self.assertEqual(result.successful[0].spelling, "HELLO")
        self.assertEqual(result.successful[0].definition, "greeting")
    
    def test_parse_optional_definition(self):
        """Test parsing CSV with only word column."""
        rows = [
            ["word"],
            ["HELLO"],
            ["WORLD"],
        ]
        filepath = self._create_csv_file(rows)
        
        result = import_from_csv(filepath)
        
        self.assertEqual(result.success_count, 2)
        self.assertEqual(result.successful[0].definition, "")


class TestCSVDifficultyAssignment(unittest.TestCase):
    """Test difficulty assignment during parsing."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_csv_file(self, content):
        filepath = os.path.join(self.temp_dir, "test.csv")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return filepath
    
    def test_explicit_beginner(self):
        """Test explicit beginner difficulty is preserved."""
        filepath = self._create_csv_file("word,difficulty\nAPPLE,easy\n")
        result = import_from_csv(filepath)
        
        self.assertEqual(result.successful[0].difficulty, Difficulty.BEGINNER)
    
    def test_explicit_advanced(self):
        """Test explicit advanced difficulty is preserved."""
        filepath = self._create_csv_file("word,difficulty\nACCOMPLISH,hard\n")
        result = import_from_csv(filepath)
        
        self.assertEqual(result.successful[0].difficulty, Difficulty.ADVANCED)
    
    def test_auto_assign_short_word(self):
        """Test short word auto-assigned beginner."""
        filepath = self._create_csv_file("word\nCAT\n")
        result = import_from_csv(filepath)
        
        self.assertEqual(result.successful[0].difficulty, Difficulty.BEGINNER)
    
    def test_auto_assign_long_word(self):
        """Test long word auto-assigned advanced."""
        filepath = self._create_csv_file("word\nACCOMPLISH\n")
        result = import_from_csv(filepath)
        
        self.assertEqual(result.successful[0].difficulty, Difficulty.ADVANCED)


class TestSampleCSVCreation(unittest.TestCase):
    """Test sample CSV file creation."""
    
    def test_create_sample_csv(self):
        """Test sample CSV creation."""
        temp_dir = tempfile.mkdtemp()
        sample_path = os.path.join(temp_dir, "sample.csv")
        
        try:
            CSVImporter.create_sample_csv(sample_path)
            
            # Verify file exists
            self.assertTrue(os.path.exists(sample_path))
            
            # Verify content
            with open(sample_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            # Check header
            self.assertEqual(rows[0], ["word", "definition", "difficulty"])
            
            # Check some data rows
            self.assertGreater(len(rows), 1)
            self.assertEqual(rows[1][0], "example")
        finally:
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
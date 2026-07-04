"""
Unit tests for InputValidator and AnswerValidator.

Tests cover:
- Character validation
- Input normalization
- Answer comparison
- Length validation
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.validators import InputValidator, AnswerValidator, ValidationResult


class TestInputValidator(unittest.TestCase):
    """Tests for the InputValidator class."""
    
    def test_normalize_lowercase(self):
        """Test normalization to lowercase."""
        self.assertEqual(InputValidator.normalize("ABC"), "abc")
        self.assertEqual(InputValidator.normalize("AbCdE"), "abcde")
    
    def test_normalize_strips_whitespace(self):
        """Test that whitespace is stripped."""
        self.assertEqual(InputValidator.normalize("  hello  "), "hello")
        self.assertEqual(InputValidator.normalize("\ttest\n"), "test")
    
    def test_normalize_none(self):
        """Test normalization of None."""
        self.assertEqual(InputValidator.normalize(None), "")
    
    def test_normalize_empty(self):
        """Test normalization of empty string."""
        self.assertEqual(InputValidator.normalize(""), "")
    
    def test_is_valid_character_letter(self):
        """Test valid alphabetic characters."""
        self.assertTrue(InputValidator.is_valid_character("a"))
        self.assertTrue(InputValidator.is_valid_character("Z"))
        self.assertTrue(InputValidator.is_valid_character("m"))
    
    def test_is_valid_character_invalid(self):
        """Test invalid characters."""
        self.assertFalse(InputValidator.is_valid_character("1"))
        self.assertFalse(InputValidator.is_valid_character("!"))
        self.assertFalse(InputValidator.is_valid_character(" "))
        self.assertFalse(InputValidator.is_valid_character(""))
        self.assertFalse(InputValidator.is_valid_character("ab"))
    
    def test_is_valid_character_special(self):
        """Test special characters are invalid."""
        self.assertFalse(InputValidator.is_valid_character("@"))
        self.assertFalse(InputValidator.is_valid_character("#"))
        self.assertFalse(InputValidator.is_valid_character("$"))
        self.assertFalse(InputValidator.is_valid_character("-"))
        self.assertFalse(InputValidator.is_valid_character("_"))
    
    def test_is_valid_input_string_valid(self):
        """Test validation of valid input strings."""
        is_valid, invalid = InputValidator.is_valid_input_string("hello")
        self.assertTrue(is_valid)
        self.assertEqual(invalid, [])
    
    def test_is_valid_input_string_invalid(self):
        """Test validation of invalid input strings."""
        is_valid, invalid = InputValidator.is_valid_input_string("hel1o!")
        self.assertFalse(is_valid)
        self.assertIn("1", invalid)
        self.assertIn("!", invalid)
    
    def test_validate_answer_correct(self):
        """Test correct answer validation."""
        self.assertTrue(InputValidator.validate_answer("because", "because"))
        self.assertTrue(InputValidator.validate_answer("Because", "because"))
        self.assertTrue(InputValidator.validate_answer("BECAUSE", "because"))
        self.assertTrue(InputValidator.validate_answer("  because  ", "because"))
    
    def test_validate_answer_incorrect(self):
        """Test incorrect answer validation."""
        self.assertFalse(InputValidator.validate_answer("becasue", "because"))
        self.assertFalse(InputValidator.validate_answer("becausee", "because"))
        self.assertFalse(InputValidator.validate_answer("bec", "because"))
    
    def test_is_within_length_limit_within(self):
        """Test length limit check when within limit."""
        self.assertTrue(InputValidator.is_within_length_limit("abc", 5))
        self.assertTrue(InputValidator.is_within_length_limit("abc", 3))
    
    def test_is_within_length_limit_exceeds(self):
        """Test length limit check when exceeds limit."""
        self.assertFalse(InputValidator.is_within_length_limit("abcde", 3))
        self.assertFalse(InputValidator.is_within_length_limit("abcdef", 5))
    
    def test_sanitize_input(self):
        """Test sanitization removes invalid characters."""
        # Numbers and symbols should be removed
        self.assertEqual(InputValidator.sanitize_input("hello1!"), "hello")
        self.assertEqual(InputValidator.sanitize_input("abc123def"), "abcdef")
        self.assertEqual(InputValidator.sanitize_input("!!!"), "")
    
    def test_get_remaining_length(self):
        """Test remaining length calculation."""
        self.assertEqual(InputValidator.get_remaining_length("abc", "abcdef"), 3)
        self.assertEqual(InputValidator.get_remaining_length("", "word"), 4)
        self.assertEqual(InputValidator.get_remaining_length("word", "word"), 0)
    
    def test_get_remaining_length_over(self):
        """Test remaining length when over limit."""
        self.assertEqual(InputValidator.get_remaining_length("abcde", "word"), 0)


class TestAnswerValidator(unittest.TestCase):
    """Tests for the AnswerValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator_no_starters = AnswerValidator("because")
        self.validator_with_starters = AnswerValidator("because", "bec")
    
    def test_init_no_starters(self):
        """Test initialization without starter letters."""
        self.assertEqual(self.validator_no_starters.target_word, "because")
        self.assertEqual(self.validator_no_starters.starter_letters, "")
        self.assertEqual(self.validator_no_starters.required_letters, "because")
    
    def test_init_with_starters(self):
        """Test initialization with starter letters."""
        self.assertEqual(self.validator_with_starters.target_word, "because")
        self.assertEqual(self.validator_with_starters.starter_letters, "bec")
        self.assertEqual(self.validator_with_starters.required_letters, "ause")
    
    def test_validate_correct_no_starters(self):
        """Test correct answer without starters."""
        result = self.validator_no_starters.validate("because")
        self.assertTrue(result.is_correct)
        self.assertEqual(result.full_answer, "because")
    
    def test_validate_correct_with_starters(self):
        """Test correct answer with starters."""
        result = self.validator_with_starters.validate("ause")
        self.assertTrue(result.is_correct)
        self.assertEqual(result.full_answer, "because")
    
    def test_validate_case_insensitive(self):
        """Test case-insensitive validation."""
        result = self.validator_with_starters.validate("AUSE")
        self.assertTrue(result.is_correct)
        
        result = self.validator_with_starters.validate("AuSe")
        self.assertTrue(result.is_correct)
    
    def test_validate_incorrect(self):
        """Test incorrect answer validation."""
        result = self.validator_with_starters.validate("xyz")
        self.assertFalse(result.is_correct)
        self.assertEqual(result.full_answer, "becxyz")
    
    def test_is_complete_exact(self):
        """Test completion check with exact length."""
        self.assertTrue(self.validator_with_starters.is_complete("ause"))
        self.assertFalse(self.validator_with_starters.is_complete("aus"))
        self.assertFalse(self.validator_with_starters.is_complete(""))
    
    def test_get_progress_correct(self):
        """Test progress tracking with correct input."""
        self.assertEqual(self.validator_with_starters.get_progress("ause"), 4)
        self.assertEqual(self.validator_with_starters.get_progress("au"), 2)
        self.assertEqual(self.validator_with_starters.get_progress("a"), 1)
    
    def test_get_progress_incorrect(self):
        """Test progress tracking stops at first error."""
        self.assertEqual(self.validator_with_starters.get_progress("axse"), 1)
        self.assertEqual(self.validator_with_starters.get_progress("xuse"), 0)


class TestValidationResult(unittest.TestCase):
    """Tests for the ValidationResult dataclass."""
    
    def test_correct_result(self):
        """Test correct validation result."""
        result = ValidationResult(
            is_correct=True,
            student_input="ause",
            full_answer="because",
            target_word="because",
            starter_letters="bec"
        )
        self.assertTrue(result.is_correct)
        self.assertEqual(str(result), "✓ CORRECT: 'because' vs 'because'")
    
    def test_incorrect_result(self):
        """Test incorrect validation result."""
        result = ValidationResult(
            is_correct=False,
            student_input="xyz",
            full_answer="becxyz",
            target_word="because",
            starter_letters="bec"
        )
        self.assertFalse(result.is_correct)
        self.assertIn("INCORRECT", str(result))


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def test_single_letter_word(self):
        """Test single letter word."""
        validator = AnswerValidator("a")
        result = validator.validate("a")
        self.assertTrue(result.is_correct)
    
    def test_empty_starter_letters(self):
        """Test with empty starter letters."""
        validator = AnswerValidator("test", "")
        self.assertEqual(validator.required_letters, "test")
    
    def test_all_letters_as_starters(self):
        """Test with all letters as starters."""
        validator = AnswerValidator("test", "test")
        self.assertEqual(validator.required_letters, "")
        self.assertTrue(validator.is_complete(""))
    
    def test_unicode_characters(self):
        """Test unicode characters are rejected."""
        # Latin extended characters should be rejected
        self.assertFalse(InputValidator.is_valid_character("ñ"))
        self.assertFalse(InputValidator.is_valid_character("é"))
        # Chinese characters should be rejected
        self.assertFalse(InputValidator.is_valid_character("中文"))
        # But basic ASCII letters should pass
        self.assertTrue(InputValidator.is_valid_character("a"))
    
    def test_whitespace_only(self):
        """Test whitespace-only input."""
        is_valid, invalid = InputValidator.is_valid_input_string("   ")
        self.assertFalse(is_valid)
        self.assertEqual(len(invalid), 3)  # All spaces are invalid


if __name__ == '__main__':
    unittest.main()

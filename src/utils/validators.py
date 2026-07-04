"""
Input Validation Utilities

Provides validation functions for keyboard input and answer comparison.
Ensures only valid characters are accepted and handles case-insensitive comparison.
"""

from dataclasses import dataclass
import re
from typing import Optional, Tuple


class InputValidator:
    """
    Static utility class for input validation.
    
    Features:
    - Character validation (A-Z, a-z only)
    - Input normalization for comparison
    - Answer validation
    - Length validation
    """
    
    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize input text for comparison.
        
        Removes leading/trailing whitespace and converts to lowercase.
        
        Args:
            text: The input text to normalize
            
        Returns:
            Normalized text (lowercase, stripped)
        """
        if text is None:
            return ""
        return text.strip().lower()
    
    @staticmethod
    def is_valid_character(char: str) -> bool:
        """
        Check if a character is a valid alphabetic character.
        
        Only accepts ASCII letters A-Z and a-z.
        
        Args:
            char: The character to validate
            
        Returns:
            True if character is A-Z or a-z, False otherwise
        """
        if not char or len(char) != 1:
            return False
        # Only accept ASCII letters, not unicode letters
        return 'a' <= char.lower() <= 'z'
    
    @staticmethod
    def is_valid_input_string(text: str) -> Tuple[bool, str]:
        """
        Validate an input string character by character.
        
        Args:
            text: The input string to validate
            
        Returns:
            Tuple of (is_valid, invalid_chars) where invalid_chars is a list of invalid characters
        """
        invalid_chars = []
        for char in text:
            if not InputValidator.is_valid_character(char):
                invalid_chars.append(char)
        
        return len(invalid_chars) == 0, invalid_chars
    
    @staticmethod
    def validate_answer(student_input: str, correct_answer: str) -> bool:
        """
        Compare student input with correct answer.
        
        Uses case-insensitive comparison after normalization.
        
        Args:
            student_input: The student's answer
            correct_answer: The correct answer to compare against
            
        Returns:
            True if answers match (case-insensitive), False otherwise
        """
        return InputValidator.normalize(student_input) == InputValidator.normalize(correct_answer)
    
    @staticmethod
    def is_within_length_limit(text: str, max_length: int) -> bool:
        """
        Check if text is within the maximum length limit.
        
        Args:
            text: The text to check
            max_length: Maximum allowed length
            
        Returns:
            True if text length <= max_length, False otherwise
        """
        return len(text) <= max_length
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize input by removing invalid characters.
        
        Args:
            text: The input text to sanitize
            
        Returns:
            Text with only valid alphabetic characters
        """
        return ''.join(char for char in text if InputValidator.is_valid_character(char))
    
    @staticmethod
    def get_remaining_length(current_input: str, target_word: str) -> int:
        """
        Calculate how many more characters can be entered.
        
        Args:
            current_input: Current input text
            target_word: The target word length
            
        Returns:
            Number of characters that can still be entered
        """
        return max(0, len(target_word) - len(current_input))


class AnswerValidator:
    """
    Validates complete answers against target words.
    
    Provides detailed feedback on answer validation including
    partial matches and common errors.
    """
    
    def __init__(self, target_word: str, starter_letters: str = ""):
        """
        Initialize the answer validator.
        
        Args:
            target_word: The correct answer word
            starter_letters: Letters already provided as hints
        """
        self.target_word = InputValidator.normalize(target_word)
        self.starter_letters = InputValidator.normalize(starter_letters)
        self.required_letters = self.target_word[len(self.starter_letters):]
    
    def validate(self, student_input: str) -> 'ValidationResult':
        """
        Validate a student's answer.
        
        Args:
            student_input: The student's input (letters typed after starters)
            
        Returns:
            ValidationResult with validation details
        """
        normalized_input = InputValidator.normalize(student_input)
        full_answer = self.starter_letters + normalized_input
        
        is_correct = full_answer == self.target_word
        
        return ValidationResult(
            is_correct=is_correct,
            student_input=student_input,
            full_answer=full_answer,
            target_word=self.target_word,
            starter_letters=self.starter_letters
        )
    
    def is_complete(self, student_input: str) -> bool:
        """
        Check if the student has typed enough characters.
        
        Args:
            student_input: The student's current input
            
        Returns:
            True if input length matches required letters count
        """
        normalized_input = InputValidator.normalize(student_input)
        return len(normalized_input) == len(self.required_letters)
    
    def get_progress(self, student_input: str) -> int:
        """
        Get the number of correctly typed letters.
        
        Args:
            student_input: The student's current input
            
        Returns:
            Number of correct letters from the start
        """
        normalized_input = InputValidator.normalize(student_input)
        correct_count = 0
        
        for i, char in enumerate(normalized_input):
            if i < len(self.required_letters) and char == self.required_letters[i]:
                correct_count += 1
            else:
                break
        
        return correct_count


@dataclass
class ValidationResult:
    """Result of answer validation."""
    is_correct: bool
    student_input: str
    full_answer: str
    target_word: str
    starter_letters: str
    
    def __str__(self) -> str:
        status = "✓ CORRECT" if self.is_correct else "✗ INCORRECT"
        return f"{status}: '{self.full_answer}' vs '{self.target_word}'"

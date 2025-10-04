"""
Input Validation Utilities
Validates user inputs like trigger words and session IDs.
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Trigger word validation pattern
TRIGGER_WORD_PATTERN = re.compile(r'^[a-z0-9_]+$')
TRIGGER_WORD_MIN_LENGTH = 3
TRIGGER_WORD_MAX_LENGTH = 50


def validate_trigger_word(word: str) -> Tuple[bool, str]:
    """
    Validate trigger word format.

    Args:
        word: Trigger word to validate

    Returns:
        Tuple of (is_valid: bool, message: str)
        - is_valid: True if valid, False otherwise
        - message: Success message or error description
    """
    if not word:
        return (False, "Trigger word is required")

    # Check length
    if len(word) < TRIGGER_WORD_MIN_LENGTH:
        return (False, f"Trigger word must be at least {TRIGGER_WORD_MIN_LENGTH} characters long")

    if len(word) > TRIGGER_WORD_MAX_LENGTH:
        return (False, f"Trigger word must be at most {TRIGGER_WORD_MAX_LENGTH} characters long")

    # Check pattern (lowercase, numbers, underscores only)
    if not TRIGGER_WORD_PATTERN.match(word):
        return (False, "Trigger word must contain only lowercase letters, numbers, and underscores (no spaces or hyphens)")

    logger.debug(f"Trigger word validated: {word}")
    return (True, "Valid trigger word")


def normalize_trigger_word(word: str) -> str:
    """
    Normalize trigger word by converting to lowercase and replacing invalid characters.

    Args:
        word: Input trigger word

    Returns:
        Normalized trigger word
    """
    # Convert to lowercase
    normalized = word.lower()

    # Replace spaces and hyphens with underscores
    normalized = normalized.replace(' ', '_').replace('-', '_')

    # Remove any other special characters
    normalized = re.sub(r'[^a-z0-9_]', '', normalized)

    # Remove consecutive underscores
    normalized = re.sub(r'_+', '_', normalized)

    # Remove leading/trailing underscores
    normalized = normalized.strip('_')

    logger.debug(f"Normalized trigger word: '{word}' → '{normalized}'")
    return normalized


def validate_session_id(session_id: str) -> Tuple[bool, str]:
    """
    Validate session ID format.

    Args:
        session_id: Session ID to validate

    Returns:
        Tuple of (is_valid: bool, message: str)
    """
    if not session_id:
        return (False, "Session ID is required")

    # Session IDs should be 32-character hex strings (UUID without hyphens)
    if not re.match(r'^[a-f0-9]{32}$', session_id):
        return (False, "Invalid session ID format")

    return (True, "Valid session ID")


def get_trigger_word_examples() -> list:
    """
    Get example trigger words.

    Returns:
        List of valid trigger word examples
    """
    return [
        "ide_main_hall",
        "ide_drawing_studio",
        "ide_lecture_hall",
        "ide_person",
        "test_space",
        "workspace_01"
    ]


def auto_fix_trigger_word(word: str) -> Tuple[bool, str, str]:
    """
    Attempt to auto-fix a trigger word.

    Args:
        word: Input trigger word

    Returns:
        Tuple of (can_fix: bool, fixed_word: str, message: str)
    """
    if not word:
        return (False, "", "Trigger word cannot be empty")

    # Try normalizing
    fixed = normalize_trigger_word(word)

    # Check if normalized version is valid
    is_valid, message = validate_trigger_word(fixed)

    if is_valid:
        if fixed != word:
            return (True, fixed, f"Auto-fixed: '{word}' → '{fixed}'")
        else:
            return (True, fixed, "Trigger word is valid")
    else:
        return (False, fixed, f"Cannot auto-fix: {message}")

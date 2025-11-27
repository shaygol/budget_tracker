"""
Security and validation utilities for Budget Tracker.
"""
from pathlib import Path
from typing import Optional
import logging

from code.config import (
    MAX_FILE_SIZE_MB,
    MAX_MERCHANT_NAME_LENGTH,
    ALLOWED_FILE_EXTENSIONS,
    TRANSACTIONS_DIR
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_file_path(file_path: Path, base_dir: Path = TRANSACTIONS_DIR) -> Path:
    """
    Validate that file path is safe and within allowed directory.

    Args:
        file_path: Path to validate
        base_dir: Base directory that file must be within

    Returns:
        Resolved absolute path

    Raises:
        ValidationError: If path is unsafe
    """
    try:
        # Resolve to absolute path
        abs_path = file_path.resolve()
        abs_base = base_dir.resolve()

        # Check if path is within base directory
        try:
            abs_path.relative_to(abs_base)
        except ValueError:
            raise ValidationError(
                f"Security Error: File path '{file_path}' is outside the allowed directory.\n"
                f"Files must be located within: {base_dir}\n"
                f"This prevents potential security risks. Please move the file to the correct location."
            )

        return abs_path

    except Exception as e:
        raise ValidationError(
            f"Invalid File Path: Unable to process the file path.\n"
            f"Error details: {e}\n"
            f"Please check that the file exists and the path is correct."
        )


def validate_file_size(file_path: Path, max_size_mb: int = MAX_FILE_SIZE_MB) -> bool:
    """
    Validate file size is within limits.

    Args:
        file_path: Path to file
        max_size_mb: Maximum size in megabytes

    Returns:
        True if valid

    Raises:
        ValidationError: If file too large
    """
    if not file_path.exists():
        raise ValidationError(
            f"File Not Found: '{file_path}' does not exist.\n"
            f"Please verify the file exists and try again."
        )

    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > max_size_mb:
        raise ValidationError(
            f"File Too Large: '{file_path.name}' exceeds the size limit.\n"
            f"File size: {size_mb:.1f}MB\n"
            f"Maximum allowed: {max_size_mb}MB\n"
            f"Please use a smaller file or contact support if this limit should be increased."
        )

    logger.debug(f"File {file_path.name} size: {size_mb:.2f}MB - OK")
    return True


def validate_file_extension(file_path: Path, allowed_extensions: list = None) -> bool:
    """
    Validate file has allowed extension.

    Args:
        file_path: Path to file
        allowed_extensions: List of allowed extensions (with dot)

    Returns:
        True if valid

    Raises:
        ValidationError: If extension not allowed
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_FILE_EXTENSIONS

    extension = file_path.suffix.lower()

    if extension not in allowed_extensions:
        raise ValidationError(
            f"Unsupported File Type: '{extension}' files are not supported.\n"
            f"Supported file types: {', '.join(allowed_extensions)}\n"
            f"Please convert your file to one of the supported formats."
        )

    return True


def sanitize_merchant_name(name: str) -> str:
    """
    Sanitize merchant name to prevent injection attacks.

    Args:
        name: Raw merchant name

    Returns:
        Sanitized name
    """
    if not name:
        return ""

    # Truncate to max length
    name = str(name)[:MAX_MERCHANT_NAME_LENGTH]

    # Prefix with single quote if starts with suspicious characters
    suspicious_starts = ['=', '+', '-', '@', '\t', '\r']
    if any(name.startswith(char) for char in suspicious_starts):
        name = "'" + name
        logger.warning(f"Potentially dangerous merchant name sanitized: {name[:50]}")

    return name.strip()


def validate_excel_file(file_path: Path) -> bool:
    """
    Comprehensive validation for Excel files.

    Args:
        file_path: Path to Excel file

    Returns:
        True if all validations pass

    Raises:
        ValidationError: If any validation fails
    """
    validate_file_extension(file_path)
    validate_file_size(file_path)
    # Additional check: ensure it's a real file
    if not file_path.is_file():
        raise ValidationError(
            f"Invalid File: '{file_path}' is not a valid file.\n"
            f"It may be a directory or a special system item.\n"
            f"Please select a regular Excel file (.xlsx or .xls)."
        )

    return True

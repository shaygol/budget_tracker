"""
Security and validation utilities for Budget Tracker.
"""
from pathlib import Path
from typing import Optional, Tuple
import logging


from src.config import (
    MAX_FILE_SIZE_MB,
    MAX_MERCHANT_NAME_LENGTH,
    ALLOWED_FILE_EXTENSIONS,
    TRANSACTIONS_DIR
)

logger = logging.getLogger(__name__)


def validate_path_traversal(file_path: Path, base_dir: Path) -> Tuple[bool, Optional[str]]:
    """
    Validate that file path is within base directory (prevents path traversal attacks).

    Args:
        file_path: Absolute path to validate
        base_dir: Base directory that file must be within

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Ensure both paths are absolute and normalized
        abs_path = file_path.resolve()
        abs_base = base_dir.resolve()

        # Check if the resolved path is within the base directory
        try:
            # Use relative_to to check if path is within base
            abs_path.relative_to(abs_base)
            return True, None
        except ValueError:
            # Path is not within base directory
            return False, f"Path traversal detected: '{file_path}' is outside allowed directory '{base_dir}'"

    except Exception as e:
        return False, f"Error validating path: {str(e)}"


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

        # Use enhanced traversal validation
        is_valid, error_msg = validate_path_traversal(abs_path, abs_base)
        if not is_valid:
            raise ValidationError(
                f"Security Error: {error_msg}\n"
                f"Files must be located within: {base_dir}\n"
                f"This prevents potential security risks."
            )

        return abs_path

    except ValidationError:
        raise
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

    # Convert to string and strip
    name = str(name).strip()

    # Remove null bytes and control characters
    name = ''.join(char for char in name if ord(char) >= 32 or char in '\n\r\t')

    # Truncate to max length
    name = name[:MAX_MERCHANT_NAME_LENGTH]

    # Prefix with single quote if starts with suspicious characters
    suspicious_starts = ['=', '+', '-', '@', '\t', '\r']
    if any(name.startswith(char) for char in suspicious_starts):
        name = "'" + name
        logger.warning(f"Potentially dangerous merchant name sanitized: {name[:50]}")

    return name


def sanitize_category_name(name: str) -> str:
    """
    Sanitize category or subcategory name to prevent injection attacks.

    Args:
        name: Raw category/subcategory name

    Returns:
        Sanitized name
    """
    if not name:
        return ""

    # Convert to string and strip
    name = str(name).strip()

    # Remove null bytes and control characters (except newlines/tabs)
    name = ''.join(char for char in name if ord(char) >= 32 or char in '\n\r\t')

    # Remove Excel formula injection patterns
    dangerous_patterns = ['=', '+', '-', '@']
    if any(name.startswith(pattern) for pattern in dangerous_patterns):
        name = "'" + name
        logger.warning(f"Potentially dangerous category name sanitized: {name[:50]}")

    # Limit length
    max_length = 200
    if len(name) > max_length:
        name = name[:max_length]
        logger.warning(f"Category name truncated to {max_length} characters")

    return name


def validate_user_input(input_str: str, input_type: str) -> tuple[bool, Optional[str]]:
    """
    Generic validation for user input.

    Args:
        input_str: Input string to validate
        input_type: Type of input ('merchant', 'category', 'subcategory', 'path')

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not input_str:
        return False, f"{input_type} cannot be empty"

    input_str = str(input_str).strip()

    # Check for null bytes
    if '\x00' in input_str:
        return False, f"{input_type} contains invalid characters"

    # Type-specific validation
    if input_type == 'merchant':
        if len(input_str) > MAX_MERCHANT_NAME_LENGTH:
            return False, f"Merchant name too long (max {MAX_MERCHANT_NAME_LENGTH} characters)"
    elif input_type in ('category', 'subcategory'):
        if len(input_str) > 200:
            return False, f"{input_type} name too long (max 200 characters)"
    elif input_type == 'path':
        # Path validation is handled by validate_file_path
        pass

    return True, None


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

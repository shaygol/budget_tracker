
import pytest
from pathlib import Path
from src.validators import (
    validate_file_path,
    validate_file_size,
    validate_file_extension,
    sanitize_merchant_name,
    validate_excel_file,
    ValidationError,
    MAX_FILE_SIZE_MB,
    MAX_MERCHANT_NAME_LENGTH
)

# --- Path Validation Tests ---

def test_validate_file_path_valid(tmp_path):
    # Create a dummy file in the temp directory
    safe_file = tmp_path / "safe.xlsx"
    safe_file.touch()

    # Should pass when base_dir is tmp_path
    result = validate_file_path(safe_file, base_dir=tmp_path)
    assert result == safe_file.resolve()

def test_validate_file_path_traversal_attempt(tmp_path):
    # Try to access a file outside the base directory
    unsafe_path = tmp_path / "../outside.xlsx"

    with pytest.raises(ValidationError, match="Security Error"):
        validate_file_path(unsafe_path, base_dir=tmp_path)

# --- File Size Tests ---

def test_validate_file_size_valid(tmp_path):
    # Create a small file
    f = tmp_path / "test.xlsx"
    f.write_bytes(b"0" * 1024)  # 1KB

    assert validate_file_size(f) is True

def test_validate_file_size_too_large(tmp_path):
    # Create a "large" file (simulated by setting low limit)
    f = tmp_path / "large.xlsx"
    f.write_bytes(b"0" * 1024 * 1024 * 2)  # 2MB

    with pytest.raises(ValidationError, match="File Too Large"):
        validate_file_size(f, max_size_mb=1)

def test_validate_file_size_missing_file(tmp_path):
    f = tmp_path / "nonexistent.xlsx"
    with pytest.raises(ValidationError, match="File Not Found"):
        validate_file_size(f)

# --- Extension Tests ---

def test_validate_file_extension_valid(tmp_path):
    f = tmp_path / "test.xlsx"
    assert validate_file_extension(f) is True

def test_validate_file_extension_invalid(tmp_path):
    f = tmp_path / "malicious.exe"
    with pytest.raises(ValidationError, match="Unsupported File Type"):
        validate_file_extension(f, allowed_extensions=['.xlsx'])

def test_validate_file_extension_case_insensitive(tmp_path):
    f = tmp_path / "TEST.XLSX"
    assert validate_file_extension(f) is True

# --- Merchant Sanitization Tests ---

def test_sanitize_merchant_name_normal():
    assert sanitize_merchant_name("Supermarket") == "Supermarket"
    assert sanitize_merchant_name(" Cafe Aroma ") == "Cafe Aroma"

def test_sanitize_merchant_name_formula_injection():
    # Should prefix with single quote
    assert sanitize_merchant_name("=SUM(A1:B2)") == "'=SUM(A1:B2)"
    assert sanitize_merchant_name("+Dangerous") == "'+Dangerous"
    assert sanitize_merchant_name("-Negative") == "'-Negative"
    assert sanitize_merchant_name("@Twitter") == "'@Twitter"

def test_sanitize_merchant_name_length_limit():
    long_name = "A" * 300
    sanitized = sanitize_merchant_name(long_name)
    assert len(sanitized) == 200

def test_sanitize_merchant_name_empty():
    assert sanitize_merchant_name("") == ""
    assert sanitize_merchant_name(None) == ""

# --- Comprehensive Excel Validation Tests ---

def test_validate_excel_file_valid(tmp_path):
    f = tmp_path / "valid.xlsx"
    f.write_bytes(b"fake excel content")

    # Mocking size check implicitly by using default large limit
    assert validate_excel_file(f) is True

def test_validate_excel_file_not_a_file(tmp_path):
    d = tmp_path / "directory.xlsx"
    d.mkdir()

    with pytest.raises(ValidationError, match="Invalid File"):
        validate_excel_file(d)

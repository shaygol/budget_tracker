import pytest
from pathlib import Path
from code.validators import (
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
    
    with pytest.raises(ValidationError, match="outside allowed directory"):
        validate_file_path(unsafe_path, base_dir=tmp_path)

# --- File Size Tests ---

def test_validate_file_size_valid(tmp_path):
    # Create a small file
    f = tmp_path / "small.xlsx"
    f.write_bytes(b"0" * 1024)  # 1KB
    
    assert validate_file_size(f, max_size_mb=1) is True

def test_validate_file_size_too_large(tmp_path):
    # Create a "large" file (simulated by setting low limit)
    f = tmp_path / "large.xlsx"
    f.write_bytes(b"0" * 1024 * 1024 * 2)  # 2MB
    
    with pytest.raises(ValidationError, match="is too large"):
        validate_file_size(f, max_size_mb=1)

def test_validate_file_size_missing_file(tmp_path):
    f = tmp_path / "nonexistent.xlsx"
    with pytest.raises(ValidationError, match="File not found"):
        validate_file_size(f)

# --- Extension Tests ---

def test_validate_file_extension_valid(tmp_path):
    f = tmp_path / "test.xlsx"
    assert validate_file_extension(f, allowed_extensions=['.xlsx']) is True

def test_validate_file_extension_invalid(tmp_path):
    f = tmp_path / "malicious.exe"
    with pytest.raises(ValidationError, match="not allowed"):
        validate_file_extension(f, allowed_extensions=['.xlsx'])

def test_validate_file_extension_case_insensitive(tmp_path):
    f = tmp_path / "TEST.XLSX"
    assert validate_file_extension(f, allowed_extensions=['.xlsx']) is True

# --- Merchant Sanitization Tests ---

def test_sanitize_merchant_name_normal():
    assert sanitize_merchant_name("Amazon") == "Amazon"
    assert sanitize_merchant_name("Super-Pharm") == "Super-Pharm"

def test_sanitize_merchant_name_formula_injection():
    # Should prefix with single quote
    assert sanitize_merchant_name("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_merchant_name("+cmd.exe") == "'+cmd.exe"
    assert sanitize_merchant_name("-100") == "'-100"
    assert sanitize_merchant_name("@import") == "'@import"

def test_sanitize_merchant_name_length_limit():
    long_name = "A" * (MAX_MERCHANT_NAME_LENGTH + 50)
    sanitized = sanitize_merchant_name(long_name)
    assert len(sanitized) == MAX_MERCHANT_NAME_LENGTH

def test_sanitize_merchant_name_empty():
    assert sanitize_merchant_name(None) == ""
    assert sanitize_merchant_name("") == ""

# --- Comprehensive Excel Validation Tests ---

def test_validate_excel_file_valid(tmp_path):
    f = tmp_path / "valid.xlsx"
    f.write_bytes(b"content")
    
    # Mocking size check implicitly by using default large limit
    assert validate_excel_file(f) is True

def test_validate_excel_file_not_a_file(tmp_path):
    d = tmp_path / "directory.xlsx"
    d.mkdir()
    
    with pytest.raises(ValidationError, match="is not a file"):
        validate_excel_file(d)

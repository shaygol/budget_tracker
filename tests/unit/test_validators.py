import pytest

from src.validators import (
    MAX_MERCHANT_NAME_LENGTH,
    ValidationError,
    sanitize_merchant_name,
    validate_excel_file,
    validate_file_extension,
    validate_file_path,
    validate_file_size,
)


def test_file_path_size_and_extension_validations(tmp_path):
    safe_file = tmp_path / "safe.xlsx"
    safe_file.touch()
    assert validate_file_path(safe_file, base_dir=tmp_path) == safe_file.resolve()

    unsafe_path = tmp_path / "../outside.xlsx"
    with pytest.raises(ValidationError, match="Security Error"):
        validate_file_path(unsafe_path, base_dir=tmp_path)

    small = tmp_path / "small.xlsx"
    small.write_bytes(b"0" * 1024)
    assert validate_file_size(small) is True

    large = tmp_path / "large.xlsx"
    large.write_bytes(b"0" * 1024 * 1024 * 2)
    with pytest.raises(ValidationError, match="File Too Large"):
        validate_file_size(large, max_size_mb=1)

    missing = tmp_path / "missing.xlsx"
    with pytest.raises(ValidationError, match="File Not Found"):
        validate_file_size(missing)

    assert validate_file_extension(tmp_path / "ok.xlsx") is True
    assert validate_file_extension(tmp_path / "TEST.XLSX") is True
    with pytest.raises(ValidationError, match="Unsupported File Type"):
        validate_file_extension(tmp_path / "bad.exe", allowed_extensions=[".xlsx"])


def test_sanitize_merchant_name_and_validate_excel_file(tmp_path):
    normal_cases = [
        ("Supermarket", "Supermarket"),
        (" Cafe Aroma ", "Cafe Aroma"),
        ("", ""),
        (None, ""),
    ]
    for raw, expected in normal_cases:
        assert sanitize_merchant_name(raw) == expected

    injection_cases = [
        ("=SUM(A1:B2)", "'=SUM(A1:B2)"),
        ("+Dangerous", "'+Dangerous"),
        ("-Negative", "'-Negative"),
        ("@Twitter", "'@Twitter"),
    ]
    for raw, expected in injection_cases:
        assert sanitize_merchant_name(raw) == expected

    long_name = "A" * 300
    assert len(sanitize_merchant_name(long_name)) == MAX_MERCHANT_NAME_LENGTH

    valid_file = tmp_path / "valid.xlsx"
    valid_file.write_bytes(b"fake excel content")
    assert validate_excel_file(valid_file) is True

    not_file = tmp_path / "directory.xlsx"
    not_file.mkdir()
    with pytest.raises(ValidationError, match="Invalid File"):
        validate_excel_file(not_file)

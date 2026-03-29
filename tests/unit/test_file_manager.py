# ===== tests/test_file_manager.py =====
"""
Tests for file management utilities.
"""
import pytest
import pandas as pd
from src import file_manager
from src.file_manager import ensure_dirs


def test_load_transaction_files_empty_directory(temp_dir):
    """Test loading from an empty directory."""
    from src.file_manager import load_transaction_files
    result = load_transaction_files(temp_dir)

    assert result == []


def test_ensure_dirs_creates_directories(temp_dir):
    """Test that ensure_dirs creates directories."""
    new_dir = temp_dir / 'new_folder'

    ensure_dirs([new_dir])

    assert new_dir.exists()
    assert new_dir.is_dir()


def test_ensure_dirs_handles_existing(temp_dir):
    """Test that ensure_dirs handles existing directories."""
    existing_dir = temp_dir / 'existing'
    existing_dir.mkdir()

    # Should not raise an error
    ensure_dirs([existing_dir])

    assert existing_dir.exists()


def test_load_transaction_file_excel_with_header_detection(tmp_path):
    """Test loading a real Excel transaction file with header detection."""
    file_path = tmp_path / "transactions.xlsx"

    raw_df = pd.DataFrame([
        ["Statement period", "", "", ""],
        ["Generated automatically", "", "", ""],
        ["תאריך", "שם בית העסק", "סכום", "שם כרטיס"],
        ["01/01/2025", "Supermarket", 100.50, "1234"],
        ["02/01/2025", "Coffee Shop", 24.90, "1234"],
    ])
    raw_df.to_excel(file_path, index=False, header=False)

    result = file_manager._load_transaction_file(file_path)

    assert result is not None
    assert len(result) == 2
    assert list(result["שם בית העסק"]) == ["Supermarket", "Coffee Shop"]
    assert list(result["סכום"]) == [100.50, 24.90]
    assert set(result["source_file"]) == {"transactions.xlsx"}


def test_load_transaction_file_pdf_from_extracted_rows(monkeypatch, tmp_path):
    """Test loading a statement-style PDF transaction file from extracted lines."""
    file_path = tmp_path / "transactions.pdf"
    file_path.write_bytes(b"%PDF-1.4\n")

    extracted_lines = [
        "תוקסע טוריפי",
        "₪ 100.00 ₪ 100.00   4321 Demo Wallet סיטרכ ההזמ יוליב יאנפ המגודל תונח 01/02/2026",
        "₪ 991.20 ₪ 11,900.00 אל  12 - מ 12 םולשת תיבו טוהיר המגודל תיב תונח 02/03/2025",
        "₪ -36.00 ₪ -36.00 אל          יוכיז תודעסמ    SHOPONLINE 13/02/2026",
        '₪ 3,971.63 02/03/26 ךיראתל כ"הס',
    ]

    monkeypatch.setattr(file_manager, "_extract_pdf_lines", lambda _: extracted_lines)

    result = file_manager._load_transaction_file(file_path)

    assert result is not None
    assert len(result) == 3
    assert list(result["שם בית העסק"]) == [
        "חנות לדוגמה",
        "חנות בית לדוגמה",
        "SHOPONLINE",
    ]
    assert result.iloc[0]["כרטיס"] == "4321"
    assert result.iloc[1]["סכום קנייה"] == "₪ 11,900.00"
    assert "פנאי בילוי" in result.iloc[0]["הערות"]
    assert "מסעדות" in result.iloc[2]["הערות"]
    assert set(result["source_file"]) == {"transactions.pdf"}

    from src.normalizer import Normalizer
    normalized = Normalizer().normalize(result)
    assert len(normalized) == 3
    assert "merchant" in normalized.columns


def test_load_transaction_file_pdf_with_due_date_and_continuation(monkeypatch, tmp_path):
    """Test PDF parsing with optional due date and continuation lines."""
    file_path = tmp_path / "transactions_2.pdf"
    file_path.write_bytes(b"%PDF-1.4\n")

    extracted_lines = [
        "תוקסע טוריפי",
        "₪ 58.00 15/02/26 ₪ 57.38 אל םיילטיגיד םיתוריש EXAMPLENET 10/02/2026",
        "₪ 44.00 ₪ 44.00 הבוטל תלגיע STOREONLINE 11/02/2026",
        "4321 Digital Wallet",
        '₪ 102.00 15/02/26 ךיראתל כ"הס',
        "PRD-123456 footer line",
    ]

    monkeypatch.setattr(file_manager, "_extract_pdf_lines", lambda _: extracted_lines)

    result = file_manager._load_transaction_file(file_path)

    assert result is not None
    assert len(result) == 2
    assert list(result["שם בית העסק"]) == [
        "EXAMPLENET שירותים דיגיטליים",
        "STOREONLINE",
    ]
    assert result.iloc[0]["חיוב לתאריך"] == "15/02/26"
    assert result.iloc[0]["סכום קנייה"] == "₪ 57.38"
    assert result.iloc[1]["כרטיס"] == "4321"
    assert "עיגלת לטובה" in result.iloc[1]["הערות"]
    assert "Digital Wallet" in result.iloc[1]["הערות"]

    from src.normalizer import Normalizer
    normalized = Normalizer().normalize(result)
    assert len(normalized) == 2
    assert list(normalized["merchant"]) == [
        "EXAMPLENET שירותים דיגיטליים",
        "STOREONLINE",
    ]


def test_load_transaction_file_pdf_strips_branch_codes_and_keeps_foreign_currency(monkeypatch, tmp_path):
    """Test PDF parsing for short numeric merchant codes and dollar amounts."""
    file_path = tmp_path / "transactions_3.pdf"
    file_path.write_bytes(b"%PDF-1.4\n")

    extracted_lines = [
        "תוקסע טוריפי",
        "$ 23.79 $ 23.79 אל םייללכ םיתוריש STOREUSD 25/02/2026",
        "₪ 172.83 ₪ 2,074.00 אל 12 - מ 5 םולשת ניפו חוטיב הבוח חוטיב 9 10/10/2025",
        "םוכס ךיראת םוכס סיטרכ טוריפ ףנע קסעה תיב םש ךיראת",
        '₪ 196.62 15/02/26 ךיראתל כ"הס',
    ]

    monkeypatch.setattr(file_manager, "_extract_pdf_lines", lambda _: extracted_lines)

    result = file_manager._load_transaction_file(file_path)

    assert result is not None
    assert len(result) == 2
    assert list(result["שם בית העסק"]) == [
        "STOREUSD שירותים כלליים",
        "ביטוח חובה",
    ]
    assert result.iloc[1]["סכום קנייה"] == "₪ 2,074.00"
    assert result.iloc[1]["הערות"].startswith("ביטוח ופינ")
    assert "9" in result.iloc[1]["הערות"]

    from src.normalizer import Normalizer
    normalized = Normalizer().normalize(result)
    assert len(normalized) == 2
    assert list(normalized["amount"]) == [23.79, 172.83]


def test_load_transaction_file_pdf_splits_foreign_merchant_suffixes(monkeypatch, tmp_path):
    """Test foreign merchants keep the merchant name and move sector/country to details."""
    file_path = tmp_path / "transactions_4.pdf"
    file_path.write_bytes(b"%PDF-1.4\n")

    extracted_lines = [
        "תוקסע טוריפי",
        "$ 7.92 $ 7.92 אל 3968 טנרטניא סיטרכ ההזמ .הינטירב יוליב יאנפ PAYPAL *GOOGLE YOUTUBE 07/02/2026",
        "חמו",
        '₪ 7.92 15/02/26 ךיראתל כ"הס',
    ]

    monkeypatch.setattr(file_manager, "_extract_pdf_lines", lambda _: extracted_lines)

    result = file_manager._load_transaction_file(file_path)

    assert result is not None
    assert len(result) == 1
    assert result.iloc[0]["שם בית העסק"] == "PAYPAL *GOOGLE YOUTUBE"
    assert "פנאי בילוי" in result.iloc[0]["הערות"]
    assert "בריטניה" in result.iloc[0]["הערות"]
    assert "חמו" not in result.iloc[0]["הערות"]

    from src.normalizer import Normalizer
    normalized = Normalizer().normalize(result)
    assert len(normalized) == 1
    assert normalized.iloc[0]["merchant"] == "PAYPAL *GOOGLE YOUTUBE"

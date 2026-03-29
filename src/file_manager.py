import os
import json
import hashlib
import re
from pathlib import Path
from zipfile import BadZipFile
from datetime import datetime
from openpyxl import load_workbook
import pandas as pd
import logging
from typing import List, Optional, Dict
from pypdf import PdfReader
from src.config import SUPPORTED_EXTENSIONS, ARCHIVE_DIR, TRANSACTIONS_DIR, FILE_HEADER_KEYWORDS, PROCESSED_HASHES_PATH
from src.pdf_statement_rules import (
    MERCHANT_STOP_TOKENS,
    PDF_DETAIL_NOISE_TOKENS,
    PDF_DETAIL_PHRASES,
    PDF_HEADER_KEYWORD_TOKENS,
    PDF_NOISE_LINE_MARKERS,
    PDF_SECTOR_SUFFIXES,
)

logger = logging.getLogger(__name__)
DATE_PATTERN = re.compile(r"\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b")
PDF_TRANSACTION_LINE_PATTERN = re.compile(
    r"^\s*(?P<amount>[₪$]\s*-?[\d,.]+)\s+"
    r"(?:(?P<charge_due_date>\d{2}/\d{2}/\d{2})\s+)?"
    r"(?:(?P<purchase_amount>[₪$]\s*-?[\d,.]+)\s+)?"
    r"(?P<body>.+?)\s+"
    r"(?P<transaction_date>\d{2}/\d{2}/\d{4})\s*$"
)

def _normalize_for_matching(text: str) -> str:
    """
    Normalize text for flexible header matching.
    Removes quotes, extra spaces, and converts to lowercase for comparison.
    """
    # Remove various quote characters
    text = text.replace('"', '').replace("'", '').replace('"', '').replace('"', '').replace("'", '').replace("'", '')
    # Remove extra spaces and convert to lowercase
    text = ' '.join(text.split()).lower()
    return text

def _detect_header_row(raw: pd.DataFrame) -> Optional[int]:
    """
    Detects the header row index in a raw DataFrame by searching for common keywords.
    Uses flexible matching to handle variations in formatting.
    Searches first 50 rows to find header in files with multi-section layouts.
    """
    # Search up to 50 rows to handle files with multiple sections
    max_rows = min(50, len(raw))
    
    for i in range(max_rows):
        row = raw.iloc[i]
        line = ' '.join(str(cell) for cell in row)
        line_normalized = _normalize_for_matching(line)
        
        # Check each mandatory field with normalized matching
        has_date = any(_normalize_for_matching(keyword) in line_normalized 
                      for keyword in FILE_HEADER_KEYWORDS['mandatory']['transaction_date'])
        has_merchant = any(_normalize_for_matching(keyword) in line_normalized 
                          for keyword in FILE_HEADER_KEYWORDS['mandatory']['merchant'])
        has_amount = any(_normalize_for_matching(keyword) in line_normalized 
                        for keyword in FILE_HEADER_KEYWORDS['mandatory']['amount'])
        has_card = any(_normalize_for_matching(keyword) in line_normalized 
                      for keyword in FILE_HEADER_KEYWORDS['optional']['card'])
        has_misc = any(_normalize_for_matching(keyword) in line_normalized 
                      for keyword in FILE_HEADER_KEYWORDS['optional']['misc'])
        
        flags = [has_card, has_date, has_amount, has_merchant, has_misc]
        # If we have all 3 mandatory fields, that's good enough
        if has_date and has_merchant and has_amount:
            return i

    return None


def _build_invalid_file_error(file_path: Path) -> ValueError:
    return ValueError(
        f"Invalid Transaction File: Could not find the header row in '{file_path.name}'.\n"
        f"\nThe file must contain column headers with at least:\n"
        f"  - תאריך (Date)\n"
        f"  - שם בית העסק (Merchant)\n"
        f"  - סכום (Amount)\n"
        f"\nPlease verify this is a valid credit card transaction export file."
    )


def _contains_hebrew(text: str) -> bool:
    return any('\u0590' <= char <= '\u05FF' for char in text)


def _normalize_pdf_inline_token(token: str) -> str:
    token = token.strip()
    if not token:
        return token
    if _contains_hebrew(token):
        return token[::-1]
    return token


def _normalize_pdf_token_group(tokens: List[str]) -> List[str]:
    normalized: List[str] = []
    idx = 0

    while idx < len(tokens):
        token = tokens[idx]
        if _contains_hebrew(token):
            normalized.append(token)
            idx += 1
            continue

        group: List[str] = []
        while idx < len(tokens) and not _contains_hebrew(tokens[idx]):
            group.append(tokens[idx])
            idx += 1

        numeric_suffix: List[str] = []
        while group and re.fullmatch(r"\d{4}", group[-1]):
            numeric_suffix.insert(0, group.pop())

        if len(numeric_suffix) == 1 and numeric_suffix[0].startswith('0'):
            numeric_suffix[0] = numeric_suffix[0][::-1]

        if group:
            group = list(reversed(group))

        normalized.extend(group + numeric_suffix)

    return normalized


def _normalize_pdf_body_text(text: str) -> str:
    tokens = [part for part in re.split(r"\s+", text.strip()) if part]
    tokens.reverse()
    tokens = [_normalize_pdf_inline_token(token) for token in tokens]
    tokens = _normalize_pdf_token_group(tokens)
    return ' '.join(tokens).strip()


def _normalize_compact_hebrew(text: str) -> str:
    return _normalize_for_matching(text).replace(' ', '')


def _is_pdf_noise_line(line: str) -> bool:
    normalized = _normalize_for_matching(line)
    if not normalized:
        return True

    normalized_body = _normalize_for_matching(_normalize_pdf_body_text(line))
    if any(marker in normalized for marker in PDF_NOISE_LINE_MARKERS):
        return True
    if any(marker in normalized_body for marker in PDF_NOISE_LINE_MARKERS):
        return True

    body_tokens = {
        token.strip('.,:;()[]{}')
        for token in _normalize_pdf_body_text(line).split()
        if token.strip('.,:;()[]{}')
    }
    keyword_hits = sum(1 for token in body_tokens if token in PDF_HEADER_KEYWORD_TOKENS)
    return keyword_hits >= 3


def _is_pdf_detail_token(token: str) -> bool:
    cleaned = token.strip('.,:;()[]{}')
    if cleaned in MERCHANT_STOP_TOKENS:
        return True
    if re.fullmatch(r"\d{4}", cleaned):
        return True
    if re.fullmatch(r"[\d,.]+", cleaned):
        return True
    return False


def _split_pdf_sector_phrase(merchant: str) -> tuple[str, str]:
    tokens = merchant.split()
    if not any(re.search(r"[A-Za-z]", token) for token in tokens):
        return merchant, ''

    for suffix in PDF_SECTOR_SUFFIXES:
        suffix_tokens = suffix.split()
        suffix_len = len(suffix_tokens)
        for idx in range(len(tokens) - suffix_len + 1):
            if tokens[idx:idx + suffix_len] != suffix_tokens:
                continue
            if not any(re.search(r"[A-Za-z]", token) for token in tokens[:idx]):
                continue

            merchant_part = ' '.join(tokens[:idx]).strip()
            detail_part = ' '.join(tokens[idx:]).strip()
            if merchant_part and detail_part:
                return merchant_part, detail_part

    return merchant, ''


def _strip_pdf_sector_suffix(merchant: str) -> tuple[str, str]:
    merchant = merchant.strip()
    compact_merchant = _normalize_compact_hebrew(merchant)

    for suffix in PDF_SECTOR_SUFFIXES:
        compact_suffix = _normalize_compact_hebrew(suffix)
        if compact_merchant.endswith(compact_suffix):
            cut_index = len(merchant) - len(suffix)
            stripped = merchant[:cut_index].strip()
            if stripped:
                return stripped, merchant[cut_index:].strip()

    return merchant, ''


def _extract_pdf_detail_phrase(merchant: str) -> tuple[str, str]:
    normalized_merchant = _normalize_for_matching(merchant)
    for phrase in PDF_DETAIL_PHRASES:
        phrase_idx = normalized_merchant.find(_normalize_for_matching(phrase))
        if phrase_idx == -1:
            continue

        words = merchant.split()
        rebuilt_prefix: List[str] = []
        rebuilt_suffix: List[str] = []
        normalized_progress = ''

        for word in words:
            candidate = (normalized_progress + ' ' + _normalize_for_matching(word)).strip()
            if phrase_idx >= len(candidate):
                rebuilt_prefix.append(word)
                normalized_progress = candidate
            else:
                rebuilt_suffix.append(word)

        prefix = ' '.join(rebuilt_prefix).strip()
        suffix = ' '.join(rebuilt_suffix).strip()
        if prefix and suffix:
            return prefix, suffix

    return merchant, ''


def _clean_pdf_details(details: str) -> str:
    if not details:
        return ''

    tokens = [token for token in details.split() if token]
    filtered_tokens = [
        token for token in tokens
        if _normalize_for_matching(token.strip('.,:;()[]{}')) not in PDF_DETAIL_NOISE_TOKENS
    ]
    cleaned = ' '.join(filtered_tokens).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def _is_short_noise_continuation(continuation: str) -> bool:
    tokens = continuation.split()
    if len(tokens) != 1:
        return False
    token = tokens[0]
    if re.search(r"[A-Za-z0-9]", token):
        return False
    return len(token) <= 4


def _clean_pdf_merchant_and_details(merchant: str, details: str) -> tuple[str, str]:
    merchant = merchant.strip()
    details = details.strip()

    merchant, detail_from_phrase = _extract_pdf_detail_phrase(merchant)
    merchant, detail_from_sector_phrase = _split_pdf_sector_phrase(merchant)
    merchant, sector_suffix = _strip_pdf_sector_suffix(merchant)
    merchant_tokens = merchant.split()

    if len(merchant_tokens) >= 2 and re.fullmatch(r"\d{1,3}", merchant_tokens[0]):
        detail_from_phrase = f"{detail_from_phrase} {merchant_tokens[0]}".strip()
        merchant = ' '.join(merchant_tokens[1:]).strip()
        merchant_tokens = merchant.split()

    if len(merchant_tokens) >= 2 and re.fullmatch(r"\d{1,4}", merchant_tokens[-1]):
        details = f"{merchant_tokens[-1]} {details}".strip()
        merchant = ' '.join(merchant_tokens[:-1]).strip()

    extra_details = [
        part for part in [
            sector_suffix,
            detail_from_sector_phrase,
            details,
            detail_from_phrase,
        ]
        if part
    ]
    merged_details = _clean_pdf_details(' '.join(extra_details).strip())
    return merchant, merged_details


def _split_pdf_merchant_and_details(body_text: str) -> tuple[str, str]:
    tokens = [token for token in body_text.split() if token]
    if not tokens:
        return '', ''

    merchant_tokens: List[str] = []
    details_tokens: List[str] = []
    stop_found = False

    for token in tokens:
        if not stop_found and not _is_pdf_detail_token(token):
            merchant_tokens.append(token)
        else:
            stop_found = True
            details_tokens.append(token)

    if not merchant_tokens:
        merchant_tokens = tokens[:3]
        details_tokens = tokens[3:]

    merchant = ' '.join(merchant_tokens).strip()
    details = ' '.join(details_tokens).strip()
    return _clean_pdf_merchant_and_details(merchant, details)


def _append_pdf_continuation_to_record(record: Dict[str, str], line: str) -> None:
    continuation = _normalize_pdf_body_text(line)
    if not continuation:
        return
    if _is_short_noise_continuation(continuation):
        return

    card_match = re.search(r"\b\d{4}\b", continuation)
    if card_match and not record.get('כרטיס'):
        record['כרטיס'] = card_match.group(0)

    existing_text = ' '.join([
        record.get('שם בית העסק', ''),
        record.get('הערות', ''),
    ]).strip()
    if continuation and continuation in existing_text:
        return

    continuation = _clean_pdf_details(continuation)
    if not continuation:
        return

    if record.get('הערות'):
        record['הערות'] = f"{record['הערות']} {continuation}".strip()
    else:
        record['הערות'] = continuation


def _build_pdf_transaction_record(match: re.Match) -> Dict[str, str]:
    body_text = _normalize_pdf_body_text(match.group('body'))
    merchant, details = _split_pdf_merchant_and_details(body_text)
    record: Dict[str, str] = {
        'תאריך': match.group('transaction_date'),
        'שם בית העסק': merchant or body_text,
        'סכום': match.group('amount'),
        'הערות': details or body_text,
    }

    purchase_amount = match.group('purchase_amount')
    if purchase_amount:
        record['סכום קנייה'] = purchase_amount

    charge_due_date = match.group('charge_due_date')
    if charge_due_date:
        record['חיוב לתאריך'] = charge_due_date

    card_match = re.search(r"\b\d{4}\b", body_text)
    if card_match:
        record['כרטיס'] = card_match.group(0)

    return record


def _rows_to_dataframe(rows: List[List[str]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    max_width = max(len(row) for row in rows)
    normalized_rows = [
        row + [None] * (max_width - len(row))
        for row in rows
    ]
    return pd.DataFrame(normalized_rows)


def _is_header_like_line(cells: List[str]) -> bool:
    line_normalized = _normalize_for_matching(' '.join(cell for cell in cells if cell))
    has_date = any(
        _normalize_for_matching(keyword) in line_normalized
        for keyword in FILE_HEADER_KEYWORDS['mandatory']['transaction_date']
    )
    has_merchant = any(
        _normalize_for_matching(keyword) in line_normalized
        for keyword in FILE_HEADER_KEYWORDS['mandatory']['merchant']
    )
    has_amount = any(
        _normalize_for_matching(keyword) in line_normalized
        for keyword in FILE_HEADER_KEYWORDS['mandatory']['amount']
    )
    return has_date and has_merchant and has_amount


def _find_matching_column(headers: List[str], aliases: List[str]) -> Optional[int]:
    normalized_aliases = {_normalize_for_matching(alias) for alias in aliases}
    for idx, header in enumerate(headers):
        if _normalize_for_matching(header) in normalized_aliases:
            return idx
    return None


def _append_pdf_continuation(previous_row: List[str], headers: List[str], extra_cells: List[str]) -> None:
    extra_text = ' '.join(cell for cell in extra_cells if cell).strip()
    if not extra_text:
        return

    target_idx = _find_matching_column(headers, FILE_HEADER_KEYWORDS['optional']['misc'])
    if target_idx is None:
        target_idx = _find_matching_column(headers, FILE_HEADER_KEYWORDS['mandatory']['merchant'])
    if target_idx is None:
        target_idx = len(previous_row) - 1

    previous_value = previous_row[target_idx].strip()
    previous_row[target_idx] = f"{previous_value} {extra_text}".strip()


def _normalize_pdf_table(rows: List[List[str]], file_path: Path) -> pd.DataFrame:
    raw = _rows_to_dataframe(rows)
    if raw.empty:
        raise ValueError(f"Invalid Transaction File: '{file_path.name}' does not contain readable text.")

    header_idx = _detect_header_row(raw)
    if header_idx is None:
        raise _build_invalid_file_error(file_path)

    headers = [
        '' if pd.isna(cell) else str(cell).strip()
        for cell in raw.iloc[header_idx].tolist()
    ]
    expected_width = len(headers)
    normalized_rows: List[List[str]] = []

    for row_values in raw.iloc[header_idx + 1:].values.tolist():
        cells = [
            '' if pd.isna(cell) else str(cell).strip()
            for cell in row_values
        ]

        while cells and not cells[-1]:
            cells.pop()

        if not any(cells):
            continue

        if _is_header_like_line(cells):
            continue

        if len(cells) > expected_width:
            cells = cells[:expected_width - 1] + [' '.join(cells[expected_width - 1:]).strip()]
        elif len(cells) < expected_width:
            has_date = any(DATE_PATTERN.search(cell) for cell in cells if cell)
            if normalized_rows and not has_date:
                _append_pdf_continuation(normalized_rows[-1], headers, cells)
                continue
            cells = cells + [''] * (expected_width - len(cells))

        normalized_rows.append(cells)

    df = pd.DataFrame(normalized_rows, columns=headers)
    df['source_file'] = file_path.name
    return df


def _split_pdf_line(line: str) -> List[str]:
    cleaned = line.replace('\u00a0', ' ').replace('\uf0b7', ' ').strip()
    if not cleaned:
        return []

    cells = [part.strip() for part in re.split(r"\s{2,}|\t+", cleaned) if part.strip()]
    return cells or [cleaned]


def _extract_pdf_lines(file_path: Path) -> List[str]:
    import pdfplumber

    lines: List[str] = []
    with pdfplumber.open(str(file_path)) as pdf:
        for page in pdf.pages:
            for line in page.extract_text_lines(layout=True):
                text = (line.get('text') or '').strip()
                if text:
                    lines.append(' '.join(text.split()))
    return lines


def _extract_pdf_rows(file_path: Path) -> List[List[str]]:
    reader = PdfReader(str(file_path))
    rows: List[List[str]] = []

    for page in reader.pages:
        try:
            text = page.extract_text(extraction_mode="layout")
        except TypeError:
            text = page.extract_text()

        if not text:
            text = page.extract_text()
        if not text:
            continue

        for line in text.splitlines():
            cells = _split_pdf_line(line)
            if cells:
                rows.append(cells)

    return rows


def _load_layout_aware_pdf_transaction_file(file_path: Path) -> Optional[pd.DataFrame]:
    records: List[Dict[str, str]] = []
    current_record: Optional[Dict[str, str]] = None

    for line in _extract_pdf_lines(file_path):
        if _is_pdf_noise_line(line):
            continue

        match = PDF_TRANSACTION_LINE_PATTERN.match(line)
        if match:
            if current_record and current_record.get('שם בית העסק'):
                records.append(current_record)

            current_record = _build_pdf_transaction_record(match)
            continue

        if (
            current_record
            and not DATE_PATTERN.search(line)
            and not line.lstrip().startswith(('₪', '$'))
        ):
            _append_pdf_continuation_to_record(current_record, line)

    if current_record and current_record.get('שם בית העסק'):
        records.append(current_record)

    if not records:
        return None

    df = pd.DataFrame(records)
    df['source_file'] = file_path.name
    return df


def _load_excel_transaction_file(file_path: Path) -> pd.DataFrame:
    raw = pd.read_excel(file_path, header=None, engine='openpyxl')
    header_idx = _detect_header_row(raw)
    if header_idx is None:
        raise _build_invalid_file_error(file_path)
    df = pd.read_excel(file_path, header=header_idx, engine='openpyxl')
    df['source_file'] = file_path.name
    return df


def _load_pdf_transaction_file(file_path: Path) -> pd.DataFrame:
    try:
        layout_df = _load_layout_aware_pdf_transaction_file(file_path)
        if layout_df is not None and not layout_df.empty:
            return layout_df
    except Exception as exc:
        logger.warning(f"Layout-aware PDF parsing failed for {file_path.name}: {exc}")

    rows = _extract_pdf_rows(file_path)
    return _normalize_pdf_table(rows, file_path)

def _load_transaction_file(file_path: Path) -> Optional[pd.DataFrame]:
    try:
        suffix = file_path.suffix.lower()
        if suffix == '.pdf':
            df = _load_pdf_transaction_file(file_path)
        else:
            df = _load_excel_transaction_file(file_path)
        logger.info(f"Loaded file: {file_path.name} (rows: {len(df)})")
        return df
    except Exception as e:
        logger.error(f"Failed to load {file_path.name}: {e}")
        return None


def load_transaction_files(transactions_dir: str | Path) -> List[pd.DataFrame]:
    """
    Load all supported transaction files with a recognizable header row.
    """
    files = list(Path(transactions_dir).glob('*'))
    dataframes = []
    for file_path in files:
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        df = _load_transaction_file(file_path)
        if df is not None:
            dataframes.append(df)
            archive_files(file_path.name)

    return dataframes

def is_valid_excel_file(path: str) -> bool:
    """
    Check if the given path points to a valid Excel (.xlsx) file.
    """
    if not os.path.exists(path):
        return False
    try:
        # Try to open it as an Excel workbook
        load_workbook(path)
        return True
    except (BadZipFile, OSError, ValueError):
        logger.debug('Failed to open workbook')
        return False

def ensure_dirs(dirs: List[Path | str]) -> None:
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def archive_files(file_name: Optional[str] = None) -> None:
    logger.debug(f"Archived file '{file_name}'")
    archive_dir_path = ARCHIVE_DIR
    ensure_dirs([archive_dir_path])
    file_list = [file_name] if file_name else os.listdir(TRANSACTIONS_DIR)

    for filename in file_list:
        source_path = TRANSACTIONS_DIR / filename
        dest_path = archive_dir_path / filename

        if source_path.is_file():
            try:
                os.replace(source_path, dest_path)
                logger.info(f"Archived {filename}")
            except PermissionError:
                logger.error(f"PermissionError: '{file_name}' is open")
                print(f"\nCan't archive file '{file_name}' since it's still open\n")


def _compute_file_hash(file_path: Path, chunk_size: int = 8192) -> Optional[str]:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash {file_path}: {e}")
        return None


def _load_processed_hashes() -> Dict:
    """Load the processed file hashes registry."""
    if PROCESSED_HASHES_PATH.exists():
        try:
            with open(PROCESSED_HASHES_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load processed hashes: {e}")
    return {}


def _save_processed_hashes(hashes: Dict) -> None:
    """Save the processed file hashes registry."""
    try:
        PROCESSED_HASHES_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PROCESSED_HASHES_PATH, 'w', encoding='utf-8') as f:
            json.dump(hashes, f, indent=2, ensure_ascii=False)
    except IOError as e:
        logger.error(f"Failed to save processed hashes: {e}")


def check_already_processed(file_paths: List[Path]) -> List[tuple]:
    """
    Check which files have already been processed based on content hash.

    Returns:
        List of (file_path, original_filename, processed_date) for already-processed files
    """
    hashes = _load_processed_hashes()
    already_processed = []
    for fp in file_paths:
        file_hash = _compute_file_hash(fp)
        if file_hash and file_hash in hashes:
            entry = hashes[file_hash]
            already_processed.append((fp, entry.get('filename', '?'), entry.get('date', '?')))
    return already_processed


def mark_files_as_processed(file_paths: List[Path]) -> None:
    """Record file hashes after successful processing."""
    hashes = _load_processed_hashes()
    for fp in file_paths:
        file_hash = _compute_file_hash(fp)
        if file_hash:
            hashes[file_hash] = {
                'filename': fp.name,
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    _save_processed_hashes(hashes)
    logger.info(f"Recorded {len(file_paths)} processed file hash(es)")
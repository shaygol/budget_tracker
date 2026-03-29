import os
import json
import hashlib
from pathlib import Path
from zipfile import BadZipFile
from datetime import datetime
from openpyxl import load_workbook
import pandas as pd
import logging
from typing import List, Optional, Dict
from src.config import SUPPORTED_EXTENSIONS, ARCHIVE_DIR, TRANSACTIONS_DIR, FILE_HEADER_KEYWORDS, PROCESSED_HASHES_PATH

logger = logging.getLogger(__name__)

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

def _load_transaction_file(file_path: Path) -> Optional[pd.DataFrame]:
    try:
        raw = pd.read_excel(file_path, header=None, engine='openpyxl')
        header_idx = _detect_header_row(raw)
        if header_idx is None:
            raise ValueError(
                f"Invalid Transaction File: Could not find the header row in '{file_path.name}'.\n"
                f"\nThe file must contain column headers with at least:\n"
                f"  - תאריך (Date)\n"
                f"  - שם בית העסק (Merchant)\n"
                f"  - סכום (Amount)\n"
                f"\nPlease verify this is a valid credit card transaction export file."
            )
        df = pd.read_excel(file_path, header=header_idx, engine='openpyxl')
        df['source_file'] = file_path.name
        logger.info(f"Loaded file: {file_path.name} (rows: {len(df)}, header row at: {header_idx})")
        return df
    except Exception as e:
        logger.error(f"Failed to load {file_path.name}: {e}")
        return None


def load_transaction_files(transactions_dir: str | Path) -> List[pd.DataFrame]:
    """
    Load all Excel files from the transactions directory that have a recognizable header row.
    """
    files = list(Path(transactions_dir).glob('*'))
    dataframes = []
    for file_path in files:
        if file_path.suffix not in SUPPORTED_EXTENSIONS:
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
# ===== code/file_manager.py =====
import os
from pathlib import Path
from zipfile import BadZipFile
from openpyxl import load_workbook
import pandas as pd
import logging
from typing import List, Optional
from code.config import SUPPORTED_EXTENSIONS, ARCHIVE_DIR, TRANSACTIONS_DIR, FILE_HEADER_KEYWORDS

logger = logging.getLogger(__name__)

def _detect_header_row(raw: pd.DataFrame) -> Optional[int]:
    """
    Detects the header row index in a raw DataFrame by searching for common keywords.
    """
    for i, row in raw.iterrows():
        line = ' '.join(str(cell) for cell in row)
        has_date = any(keyword in line for keyword in FILE_HEADER_KEYWORDS['mandatory']['transaction_date'])
        has_merchant = any(keyword in line for keyword in FILE_HEADER_KEYWORDS['mandatory']['merchant'])
        has_amount = any(keyword in line for keyword in FILE_HEADER_KEYWORDS['mandatory']['amount'])
        has_card = any(keyword in line for keyword in FILE_HEADER_KEYWORDS['optional']['card'])
        has_misc = any(keyword in line for keyword in FILE_HEADER_KEYWORDS['optional']['misc'])
        flags = [has_card, has_date, has_amount, has_merchant, has_misc]
        if  sum(flags) > len(FILE_HEADER_KEYWORDS['mandatory']):
            return i

    return None

def _load_transaction_file(file_path: Path) -> Optional[pd.DataFrame]:
    try:
        raw = pd.read_excel(file_path, header=None, engine='openpyxl')
        header_idx = _detect_header_row(raw)
        if header_idx is None:
            raise ValueError("Could not detect header row with keywords in file.")
        df = pd.read_excel(file_path, header=header_idx, engine='openpyxl')
        df['source_file'] = file_path.name
        logger.info(f"Loaded file: {file_path.name} (rows: {len(df)}, header row at: {header_idx})")
        return df
    except Exception as e:
        logger.error(f"Failed to load {file_path.name}: {e}")
        return None


def load_transaction_files(transactions_dir: str) -> List[pd.DataFrame]:
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
    
def ensure_dirs(dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def archive_files(file_name = None):
    logger.debug(f"Archived file '{file_name}'")
    archive_dir_path = TRANSACTIONS_DIR / ARCHIVE_DIR
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
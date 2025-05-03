# ===== code/file_loader.py =====
from pathlib import Path
import pandas as pd
import logging
from typing import List

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = ['.xlsx', '.xls']

def load_transaction_files(transactions_dir: str) -> List[pd.DataFrame]:
    """
    Load all Excel files from the transactions directory, 
    detect header row dynamically (looking for card, date, and amount keywords),
    and return DataFrames with correct headers.
    """
    files = list(Path(transactions_dir).glob('*'))
    dataframes = []
    for file_path in files:
        if file_path.suffix not in SUPPORTED_EXTENSIONS:
            continue
        try:
            raw = pd.read_excel(file_path, header=None, engine='openpyxl')
            header_idx = None
            for i, row in raw.iterrows():
                line = ' '.join(str(cell) for cell in row)
                has_card = 'שם כרטיס' in line
                has_date = 'תאריך' in line or 'חיוב לתאריך' in line
                has_amount = 'סכום' in line
                if has_card and has_date and has_amount:
                    header_idx = i
                    break
            if header_idx is None:
                raise ValueError("Could not detect header row with keywords in file.")

            df = pd.read_excel(file_path, header=header_idx, engine='openpyxl')
            df['__source_file'] = file_path.name
            dataframes.append(df)
            logger.info(f"Loaded file: {file_path.name} (rows: {len(df)}, header row at: {header_idx})")
        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")
    return dataframes
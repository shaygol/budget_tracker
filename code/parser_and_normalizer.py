# ===== code/parser_and_normalizer.py =====
from pathlib import Path
import pandas as pd
import logging
from typing import List

logger = logging.getLogger(__name__)

INPUT_DIR = Path("transactions")

SUPPORTED_EXTENSIONS = [".xlsx", ".xls"]

def is_excel_file(file_path: Path) -> bool:
    return file_path.suffix in SUPPORTED_EXTENSIONS

def load_transaction_files() -> List[pd.DataFrame]:
    if not INPUT_DIR.exists():
        logger.warning(f"Input folder '{INPUT_DIR}' does not exist. No files loaded.")
        return []

    files = [f for f in INPUT_DIR.glob("*") if is_excel_file(f)]

    if not files:
        logger.warning(f"No Excel files found in '{INPUT_DIR}'.")
        return []

    dataframes = []
    for file_path in files:
        try:
            df = pd.read_excel(file_path)
            df["__source_file"] = file_path.name  # helpful for traceability/debugging
            dataframes.append(df)
            logger.info(f"Loaded file: {file_path.name} ({len(df)} rows)")
        except Exception as e:
            logger.error(f"Failed to read {file_path.name}: {e}")

    return dataframes

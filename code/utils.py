# ===== code/utils.py =====
import os
import logging
from bidi.algorithm import get_display
import arabic_reshaper
from openpyxl import load_workbook
from zipfile import BadZipFile

logger = logging.getLogger(__name__)

def ensure_dirs(dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def rtl(text):
    # return '\u200f' + text
    # return text[::-1]
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

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
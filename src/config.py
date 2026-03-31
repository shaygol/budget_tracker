from pathlib import Path
import logging
import sys

# Base directory is the parent of the 'src' directory (root of repo)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    BASE_DIR = Path(__file__).parent.parent.resolve()

# App version (read from VERSION file, fallback to 'dev')
_version_file = BASE_DIR / 'VERSION'
APP_VERSION = _version_file.read_text(encoding='utf-8').strip() if _version_file.exists() else 'dev'

# User Files Directory
USER_FILES_DIR = BASE_DIR / 'UserFiles'

# Subdirectories
APPDATA_DIR = BASE_DIR / 'appdata'
BACKUPS_ROOT = USER_FILES_DIR / 'backups'
TRANSACTIONS_DIR = APPDATA_DIR / 'pending'
ARCHIVE_DIR = BACKUPS_ROOT / 'transactions'
DASHBOARD_BACKUP_DIR = BACKUPS_ROOT / 'dashboards'

# Files
CATEGORIES_FILE_PATH = USER_FILES_DIR / 'categories.json'
DASHBOARD_FILE_PATH = USER_FILES_DIR / 'dashboard.xlsx'
PROCESSED_HASHES_PATH = APPDATA_DIR / 'processed_hashes.json'

LOG_FILE_NAME = 'budget.log'
TEMPLATE_SHEET_NAME = "Template"

SUPPORTED_EXTENSIONS = ['.xlsx', '.xls', '.pdf']

# Default log level
LOG_SEVERITY = logging.DEBUG

# Mapping from string to logging level
LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

# Reverse mapping for display
LOG_LEVEL_NAMES = {v: k for k, v in LOG_LEVEL_MAP.items()}


def get_log_level() -> int:
    """
    Get current log level from config.py.

    Returns:
        Logging level constant (e.g., logging.DEBUG)
    """
    return LOG_SEVERITY


def set_log_level(level_name: str) -> None:
    """
    Set the log level from a string name.

    Args:
        level_name: Log level name (e.g., 'DEBUG', 'INFO')
    """
    global LOG_SEVERITY
    LOG_SEVERITY = LOG_LEVEL_MAP.get(level_name, logging.DEBUG)


def get_log_level_name() -> str:
    """
    Get current log level as string name.

    Returns:
        Log level name (e.g., 'DEBUG')
    """
    level = get_log_level()
    return LOG_LEVEL_NAMES.get(level, 'DEBUG')


FILE_HEADER_KEYWORDS = {
    'mandatory': {
        'transaction_date': ['תאריך', 'תאריך עסקה', 'תאריך רכישה', 'date'],
        'merchant': ['שם בית העסק', 'שם בית עסק', 'בית עסק', 'עסק', 'merchant'],
        'amount': ['סכום', 'סכום חיוב', 'סכום חיוב בשח', 'סכום עסקה', 'amount'],
    },
    'optional': {
        'charge_due_date': ['חיוב לתאריך'],
        'purchase_amount': ['סכום קנייה', 'סכום עסקה מקורי'],
        'card': ['שם כרטיס', '4 ספרות אחרונות', 'ספרות אחרונות', 'כרטיס'],
        'misc': ['ענף', 'הערות'],
    }
}

# Security and Validation Constants
MAX_FILE_SIZE_MB = 50  # Maximum file size for supported transaction files
MAX_CATEGORIES = 10000  # Maximum number of categories to prevent unbounded growth
MAX_MERCHANT_NAME_LENGTH = 200  # Maximum length for merchant names
BACKUP_SUFFIX = '.backup'
PROCESSING_TIMEOUT_SECONDS = 300  # 5 minutes max processing time
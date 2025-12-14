from pathlib import Path
import logging
import sys

# Base directory is the parent of the 'src' directory (root of repo)
if getattr(sys, 'frozen', False):
    # If running as compiled exe, use the executable's directory
    BASE_DIR = Path(sys.executable).parent.resolve()
else:
    # If running as script, use the standard path
    BASE_DIR = Path(__file__).parent.parent.resolve()

# User Files Directory
USER_FILES_DIR = BASE_DIR / 'UserFiles'

# Subdirectories
OUTPUT_DIR = BASE_DIR / 'output'
BACKUPS_ROOT = USER_FILES_DIR / 'backups'
TRANSACTIONS_DIR = BACKUPS_ROOT
ARCHIVE_DIR = BACKUPS_ROOT / 'archive'
DASHBOARD_BACKUP_DIR = BACKUPS_ROOT / 'dashboard'

# Files
CATEGORIES_FILE_PATH = USER_FILES_DIR / 'categories.json'
DASHBOARD_FILE_PATH = USER_FILES_DIR / 'dashboard.xlsx'

LOG_FILE_NAME = 'budget.log'
TEMPLATE_SHEET_NAME = "Template"

SUPPORTED_EXTENSIONS = ['.xlsx', '.xls']

# Default log level - can be overridden by settings.json
LOG_SEVERITY = logging.DEBUG

# Settings file for user preferences
SETTINGS_FILE = USER_FILES_DIR / 'settings.json'

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
    Get current log level from settings.json or use default from config.py.

    Returns:
        Logging level constant (e.g., logging.DEBUG)
    """
    if SETTINGS_FILE.exists():
        try:
            import json
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                level_name = settings.get('log_level', None)
                if level_name and level_name.upper() in LOG_LEVEL_MAP:
                    return LOG_LEVEL_MAP[level_name.upper()]
        except (json.JSONDecodeError, IOError):
            pass

    # Fallback to config.py default
    return LOG_SEVERITY


def set_log_level(level_name: str) -> None:
    """
    Set log level and save to settings.json.

    Args:
        level_name: Log level name ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    if level_name.upper() not in LOG_LEVEL_MAP:
        raise ValueError(f"Invalid log level: {level_name}")

    import json

    # Load existing settings or create new
    settings = {}
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except (json.JSONDecodeError, IOError):
            settings = {}

    # Update log level
    settings['log_level'] = level_name.upper()

    # Save to file
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def get_log_level_name() -> str:
    """
    Get current log level as string name.

    Returns:
        Log level name (e.g., 'DEBUG')
    """
    level = get_log_level()
    return LOG_LEVEL_NAMES.get(level, 'DEBUG')


def reset_log_level_to_default() -> None:
    """Reset log level to default from config.py."""
    if SETTINGS_FILE.exists():
        try:
            import json
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                settings.pop('log_level', None)

            # If settings is now empty, delete file; otherwise save
            if not settings:
                SETTINGS_FILE.unlink()
            else:
                with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, IOError):
            pass

FILE_HEADER_KEYWORDS = {
    'mandatory': {
        'transaction_date': ['תאריך', 'תאריך עסקה'],
        'merchant': ['שם בית העסק', 'שם בית עסק'],
        'amount': ['סכום', 'סכום חיוב בש\'\'ח', 'סכום חיוב'],
    },
    'optional': {
        'charge_due_date': ['חיוב לתאריך'],
        'purchase_amount': ['סכום קנייה', 'סכום עסקה מקורי'],
        'card': ['שם כרטיס', '4 ספרות אחרונות', 'ספרות אחרונות'],
        'misc': ['ענף', 'הערות'],
    }
}

# Security and Validation Constants
MAX_FILE_SIZE_MB = 50  # Maximum file size for Excel files
MAX_CATEGORIES = 10000  # Maximum number of categories to prevent unbounded growth
MAX_MERCHANT_NAME_LENGTH = 200  # Maximum length for merchant names
ALLOWED_FILE_EXTENSIONS = ['.xlsx', '.xls']
BACKUP_SUFFIX = '.backup'
PROCESSING_TIMEOUT_SECONDS = 300  # 5 minutes max processing time
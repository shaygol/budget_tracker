# ===== code/config.py =====
from pathlib import Path
import logging

OUTPUT_DIR = Path('output')
TRANSACTIONS_DIR = Path('transactions')
CATEGORIES_FILE_PATH = Path('categories.json')
DASHBOARD_FILE_PATH = Path('dashboard.xlsx')

LOG_FILE_NAME = 'budget.log'
TEMPLATE_SHEET_NAME = "Template"

SUPPORTED_EXTENSIONS = ['.xlsx', '.xls']
ARCHIVE_DIR = 'archive'

LOG_SEVERITY = logging.DEBUG

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
# ===== code/config.py =====
from pathlib import Path
import logging

OUTPUT_DIR = Path('output')
TRANSACTIONS_DIR = Path('transactions')
CATEGORIES_FILE_PATH = Path('categories.json')
DASHBOARD_FILE_PATH = Path('dashboard.xlsx')
LOG_FILE_NAME = 'budget.log'

SUPPORTED_EXTENSIONS = ['.xlsx', '.xls']
ARCHIVE_DIR ='archive'

LOG_SEVERITY  = logging.DEBUG

FILE_HEADER_KEYWORDS = {
    'transaction_date': ['תאריך', 'תאריך עסקה'],
    'charge_due_date': ['חיוב לתאריך'],
    'merchant': ['שם בית העסק', 'שם בית עסק'],
    'amount': ['סכום', 'סכום חיוב בש\'\'ח', 'סכום חיוב'],
    'purchase_amount': ['סכום קנייה', 'סכום עסקה מקורי'],
    'card': ['שם כרטיס', '4 ספרות אחרונות', 'ספרות אחרונות'],
}

MAPPING_HEADER_KEYWORDS = {
    'תאריך': 'transaction_date',
    'חיוב לתאריך': 'charge_due_date',
    'שם בית עסק': 'merchant',
    'סכום חיוב בש\'\'ח': 'amount',
    'סכום קנייה': 'purchase_amount',
}

TEMPLATE_SHEET_NAME = "Template"
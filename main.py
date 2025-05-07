import pandas as pd
from pathlib import Path
from code.file_manager import ensure_dirs
from code.logger import setup_logging
from code.file_manager import load_transaction_files
from code.normalizer import Normalizer
from code.category_manager import CategoryManager
from code.previewer import Previewer
from code.dashboard_writer import DashboardWriter

OUTPUT_DIR = Path('output')
TRANSACTIONS_DIR = Path('transactions')
CATEGORIES_FILE_PATH = Path('categories.json')
DASHBOARD_FILE_PATH = Path('dashboard.xlsx')
LOG_FILE_NAME = 'budget.log'

def main():
    ensure_dirs([OUTPUT_DIR])
    setup_logging(OUTPUT_DIR, LOG_FILE_NAME)

    dfs = load_transaction_files(TRANSACTIONS_DIR)
    if not dfs:
        print("No transaction files found. Exiting.")
        return

    df = pd.concat(dfs, ignore_index=True)
    df = Normalizer.normalize(df)

    cat_mgr = CategoryManager(CATEGORIES_FILE_PATH, DASHBOARD_FILE_PATH)
    df = cat_mgr.map_categories(df)

    preview = Previewer()
    summary = preview.preview(df)

    writer = DashboardWriter(DASHBOARD_FILE_PATH)
    writer.update(summary)

if __name__ == '__main__':
    main()

import os
import pandas as pd
from code.utils import ensure_dirs
from code.logger import setup_logging
from code.file_loader import load_transaction_files
from code.normalizer import Normalizer
from code.category_manager import CategoryManager
from code.previewer import Previewer
from code.dashboard_writer import DashboardWriter

OUTPUT_DIR = 'output'
TRANSACTIONS_DIR = 'transactions'
CATEGORIES_FILE = 'config/categories.json'
DASHBOARD_FILE = 'dashboard.xlsx'

def main():
    ensure_dirs([OUTPUT_DIR])
    setup_logging(OUTPUT_DIR)

    dfs = load_transaction_files(TRANSACTIONS_DIR)
    if not dfs:
        print("No transaction files found. Exiting.")
        return

    df = pd.concat(dfs, ignore_index=True)
    df = Normalizer.normalize(df)

    cat_mgr = CategoryManager(CATEGORIES_FILE, DASHBOARD_FILE)
    df = cat_mgr.map_categories(df)

    preview = Previewer()
    summary = preview.preview(df)

    writer = DashboardWriter(DASHBOARD_FILE)
    writer.update(summary)

if __name__ == '__main__':
    main()

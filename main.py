import pandas as pd
from code.file_manager import ensure_dirs
from code.logger import setup_logging
from code.file_manager import load_transaction_files
from code.normalizer import Normalizer
from code.category_manager import CategoryManager
from code.previewer import Previewer
from code.dashboard_writer import DashboardWriter
from code.normalizer import Normalizer
from code.config import OUTPUT_DIR, LOG_FILE_NAME, TRANSACTIONS_DIR, CATEGORIES_FILE_PATH, DASHBOARD_FILE_PATH

def main():
    try:
        ensure_dirs([OUTPUT_DIR])
        setup_logging(OUTPUT_DIR, LOG_FILE_NAME)

        dfs = load_transaction_files(TRANSACTIONS_DIR)
        if not dfs:
            print("No valid transaction files found.")
            return

        normalizer = Normalizer()
        df = pd.concat(dfs, ignore_index=True)
        df = normalizer.normalize(df)


        cat_mgr = CategoryManager(CATEGORIES_FILE_PATH, DASHBOARD_FILE_PATH)
        df = cat_mgr.map_categories(df)

        preview = Previewer()
        summary = preview.preview(df)

        writer = DashboardWriter(DASHBOARD_FILE_PATH)
        writer.update(summary)
    except KeyboardInterrupt:
        print("\n[INFO] Operation cancelled by user.")

if __name__ == '__main__':
    main()

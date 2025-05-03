# ===== code/parser_formatter.py =====
import pandas as pd
import glob
import os
import logging

class ParserFormatter:
    def __init__(self, transactions_dir: str):
        self.transactions_dir = transactions_dir

    def load_and_format(self) -> pd.DataFrame:
        all_dfs = []
        pattern = os.path.join(self.transactions_dir, '*.xls*')
        files = glob.glob(pattern)
        logging.info(f'Found {len(files)} transaction files')
        for fp in files:
            try:
                df = pd.read_excel(fp)
                df['__source_file'] = os.path.basename(fp)
                all_dfs.append(df)
                logging.info(f'Loaded {fp} ({len(df)} rows)')
            except Exception as e:
                logging.error(f'Failed to read {fp}: {e}')
        if not all_dfs:
            logging.warning('No transactions loaded, exiting')
            exit(0)
        combined = pd.concat(all_dfs, ignore_index=True)
        return combined
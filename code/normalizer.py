# ===== code/normalizer.py =====
import pandas as pd
import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

class Normalizer:
    @staticmethod
    def normalize(df: pd.DataFrame) -> pd.DataFrame:
        """
        1. Debug print original columns.
        2. Clean headers: strip, normalize quotes, remove control chars.
        3. Lowercase English-only names.
        4. Debug print cleaned and case-normalized columns.
        5. Rename to standard English names.
        6. Debug print final columns.
        7. Drop invalid rows and derive year/month/monthly_amount.
        """
        # 1. Original
        orig_cols = list(df.columns)
        logger.debug(f"Original columns:\n{orig_cols}\n")

        # 2. Clean headers
        cleaned = []
        for col in orig_cols:
            s = str(col).strip()
            # normalize quotes
            s = s.replace('״', '"').replace('”', '"').replace('“', '"').replace("׳", "'").replace("’", "'")
            # remove direction/control chars
            s = re.sub(r'[\u200f\u202a\u202c]', '', s)
            cleaned.append(s)
        df.columns = cleaned
        logger.debug(f"After cleaning control chars and quotes:\n{list(df.columns)}\n")

        # 3. Lowercase English-only
        def lower_if_ascii(name):
            return name.lower() if all(ord(c) < 128 for c in name) else name
        df.columns = [lower_if_ascii(col) for col in df.columns]
        logger.debug(f"After ASCII lowercase:\n{list(df.columns)}\n")

        # 5. Rename mapping
        mapping = {
            'תאריך': 'transaction_date',
            'חיוב לתאריך': 'charge_due_date',
            'שם בית עסק': 'merchant',
            'סכום חיוב בש\'\'ח': 'amount',
            'סכום קנייה': 'purchase_amount',
        }
        df = df.rename(columns=mapping)
        logger.debug(f"After renaming to standard names:\n{list(df.columns)}\n")

        # Ensure merchant exists
        if 'merchant' not in df.columns:
            raise KeyError(f"Missing 'merchant' column. Available: {list(df.columns)}")

        # Copy purchase_amount if needed
        if 'purchase_amount' in df.columns and 'amount' not in df.columns:
            df['amount'] = df['purchase_amount']
            logger.debug("Copied 'purchase_amount' to 'amount'")

        # Drop rows with missing critical fields
        df = df.dropna(subset=['merchant', 'transaction_date', 'amount'], how='any')

        # Convert types
        df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='coerce')
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df = df.dropna(subset=['transaction_date', 'amount', 'merchant'])

        # Derive
        df['year'] = df['transaction_date'].dt.year
        df['month'] = df['transaction_date'].dt.month
        df['monthly_amount'] = df['amount']

        logger.debug("Normalization complete.")
        return df

    def normalize_text(text):
        if not isinstance(text, str):
            return text
        text = text.strip()
        text = unicodedata.normalize('NFKC', text)
        return text
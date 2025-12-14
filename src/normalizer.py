import pandas as pd
import re
import unicodedata
import logging
from src.config import FILE_HEADER_KEYWORDS

logger = logging.getLogger(__name__)

class Normalizer:
    """
    Generic, extensible normalizer for transaction DataFrames.
    Uses FILE_HEADER_KEYWORDS from config for column mapping.
    """


    def __init__(self):
        # build cleaned alias→field map once
        merged_keywords = {**FILE_HEADER_KEYWORDS['mandatory'], **FILE_HEADER_KEYWORDS['optional']}
        self._alias_map = self._build_alias_map(merged_keywords)
        self.MANDATORY_FIELDS = FILE_HEADER_KEYWORDS['mandatory'].keys()

    @staticmethod
    def _clean_name(name: str) -> str:
        s = unicodedata.normalize("NFKD", str(name))
        s = re.sub(r'[\n\r\t\u200f\u200e]', "", s)
        return s.strip()

    def _build_alias_map(self, keywords: dict) -> dict[str, str]:
        """
        Build a lookup of cleaned alias -> target field.
        """
        alias_map: dict[str, str] = {}
        for field, aliases in keywords.items():
            if not isinstance(aliases, list):
                continue
            for alias in aliases:
                key = self._clean_name(alias).replace(" ", "").lower()
                alias_map[key] = field
        return alias_map

    def _map_columns(self, cols: list[str]) -> dict[str, str]:
        """
        Map raw df.columns to standard field names using alias_map,
        ensuring each field is only assigned once.
        """
        mapping: dict[str, str] = {}
        assigned_fields = set()

        for col in cols:
            clean = self._clean_name(col).replace(" ", "").lower()
            field = self._alias_map.get(clean)
            if field and field not in assigned_fields:
                mapping[col] = field
                assigned_fields.add(field)

        missing = self.MANDATORY_FIELDS - assigned_fields
        if missing:
            logger.warning(f"Missing expected columns: {missing}")
        return mapping

    @staticmethod
    def _parse_date(series: pd.Series) -> pd.Series:
        return pd.to_datetime(series, dayfirst=True, errors='coerce')

    @staticmethod
    def _parse_amount(series: pd.Series) -> pd.Series:
        s = series.astype(str).str.replace(r"[,\s₪]", "", regex=True)
        return pd.to_numeric(s, errors='coerce')

    @staticmethod
    def _parse_str(series: pd.Series) -> pd.Series:
        return series.astype(str).str.strip()

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        # 1. Clean column names
        df = df.rename(columns=lambda c: self._clean_name(c))
        logger.debug(f"Cleaned columns: {list(df.columns)}")

        # 2. Map to standard fields
        rename_map = self._map_columns(list(df.columns))
        df = df.rename(columns=rename_map)
        logger.debug(f"Mapped columns: {list(df.columns)}")

        # 3. Check mandatory fields
        missing = self.MANDATORY_FIELDS - set(df.columns)
        if missing:
            logger.error(f"Missing required columns: {missing}")

            # Build helpful error message
            missing_list = ', '.join(missing)
            expected_names = {
                'transaction_date': 'תאריך / תאריך עסקה',
                'merchant': 'שם בית העסק / שם בית עסק',
                'amount': 'סכום / סכום חיוב בש"ח'
            }

            suggestions = '\n'.join([f"  - {field}: Expected column names like '{expected_names.get(field, field)}'"
                                    for field in missing])

            raise ValueError(
                f"Missing Required Columns in Excel File\\n"
                f"\\nThe following required columns were not found: {missing_list}\\n"
                f"\\nExpected column names:\\n{suggestions}\\n"
                f"\\nPlease ensure your Excel file has the correct column headers.\\n"
                f"Available columns in file: {', '.join(df.columns)}"
            )

        # 4. Drop rows missing any mandatory field
        before_drop = len(df)
        df = df.dropna(subset=list(self.MANDATORY_FIELDS))
        dropped = before_drop - len(df)
        if dropped > 0:
            logger.warning(f"Dropped {dropped} rows missing mandatory fields")

        # 5. Field-specific parsing
        df['transaction_date'] = self._parse_date(df['transaction_date'])
        before_date_drop = len(df)
        df = df.dropna(subset=['transaction_date'])
        dropped_date = before_date_drop - len(df)
        if dropped_date > 0:
            logger.warning(f"Dropped {dropped_date} rows with invalid dates")

        df['amount'] = self._parse_amount(df['amount'])
        before_amount_drop = len(df)
        df = df.dropna(subset=['amount'])
        dropped_amount = before_amount_drop - len(df)
        if dropped_amount > 0:
            logger.warning(f"Dropped {dropped_amount} rows with invalid amounts")

        df['merchant'] = self._parse_str(df['merchant'])

        # Sanitize merchant names to prevent formula injection
        from src.validators import sanitize_merchant_name
        df['merchant'] = df['merchant'].apply(sanitize_merchant_name)

        # Optional fields
        if 'purchase_amount' in df.columns:
            df['purchase_amount'] = self._parse_amount(df['purchase_amount'])
        if 'card' in df.columns:
            df['card'] = self._parse_str(df['card'])
        if 'misc' in df.columns:
            df['misc'] = self._parse_str(df['misc'])

        # 6. Derived fields
        df['year'] = df['transaction_date'].dt.year
        df['month'] = df['transaction_date'].dt.month
        df['monthly_amount'] = df['amount']

        logger.info(f"Normalization complete: {len(df)} rows")
        return df.reset_index(drop=True)

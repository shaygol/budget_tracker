"""
Transaction validation before writing to dashboard.
"""
import logging
from typing import List, Tuple, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class TransactionValidationError(Exception):
    """Exception for transaction validation errors."""
    pass


class TransactionValidator:
    """Validates transaction data before writing to dashboard."""

    def __init__(self, valid_categories: dict):
        """
        Initialize validator.

        Args:
            valid_categories: Dictionary of valid categories and subcategories
        """
        self.valid_categories = valid_categories

    def validate_summary_data(self, summary_df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate summary DataFrame before writing to dashboard.

        Args:
            summary_df: DataFrame with transaction summary

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required columns
        required_cols = {'year', 'month', 'category', 'subcat', 'monthly_amount'}
        missing_cols = required_cols - set(summary_df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
            return False, errors

        # Check for empty DataFrame
        if summary_df.empty:
            errors.append("Summary DataFrame is empty")
            return False, errors

        # Validate data types
        if not pd.api.types.is_numeric_dtype(summary_df['year']):
            errors.append("Year column must be numeric")
        if not pd.api.types.is_numeric_dtype(summary_df['month']):
            errors.append("Month column must be numeric")
        if not pd.api.types.is_numeric_dtype(summary_df['monthly_amount']):
            errors.append("Monthly amount column must be numeric")

        # Validate year range
        current_year = datetime.now().year
        if summary_df['year'].min() < 2000 or summary_df['year'].max() > current_year + 1:
            errors.append(f"Year values must be between 2000 and {current_year + 1}")

        # Validate month range
        invalid_months = summary_df[(summary_df['month'] < 1) | (summary_df['month'] > 12)]
        if not invalid_months.empty:
            errors.append(f"Invalid month values found: {invalid_months['month'].unique().tolist()}")

        # Validate amounts
        negative_amounts = summary_df[summary_df['monthly_amount'] < 0]
        if not negative_amounts.empty:
            errors.append(f"Found {len(negative_amounts)} transaction(s) with negative amounts")

        # Validate categories exist in template
        invalid_categories = []
        for _, row in summary_df.iterrows():
            cat = str(row['category']).strip()
            subcat = str(row['subcat']).strip()

            if cat not in self.valid_categories:
                invalid_categories.append(f"Category '{cat}' not found in template")
            elif subcat not in self.valid_categories.get(cat, []):
                invalid_categories.append(f"Subcategory '{subcat}' not found under category '{cat}'")

        if invalid_categories:
            errors.extend(invalid_categories[:10])  # Limit to first 10
            if len(invalid_categories) > 10:
                errors.append(f"... and {len(invalid_categories) - 10} more category errors")

        # Check for duplicate transactions (same year, month, category, subcat)
        duplicates = summary_df.duplicated(subset=['year', 'month', 'category', 'subcat'], keep=False)
        if duplicates.any():
            dup_count = duplicates.sum()
            errors.append(f"Found {dup_count} potential duplicate transaction(s)")

        # Check for future dates
        future_dates = summary_df[
            (summary_df['year'] > current_year) |
            ((summary_df['year'] == current_year) & (summary_df['month'] > datetime.now().month))
        ]
        if not future_dates.empty:
            errors.append(f"Found {len(future_dates)} transaction(s) with future dates")

        is_valid = len(errors) == 0
        return is_valid, errors

    def validate_transaction_structure(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate transaction DataFrame structure.

        Args:
            df: Transaction DataFrame

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check required columns
        required_cols = {'merchant', 'amount', 'year', 'month'}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
            return False, errors

        # Check for empty DataFrame
        if df.empty:
            errors.append("Transaction DataFrame is empty")
            return False, errors

        # Validate data types
        if 'amount' in df.columns and not pd.api.types.is_numeric_dtype(df['amount']):
            errors.append("Amount column must be numeric")

        # Check for missing values in required fields
        for col in required_cols:
            if col in df.columns and df[col].isna().any():
                missing_count = df[col].isna().sum()
                errors.append(f"Found {missing_count} missing value(s) in '{col}' column")

        is_valid = len(errors) == 0
        return is_valid, errors


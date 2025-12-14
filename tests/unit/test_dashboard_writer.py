# ===== tests/test_dashboard_writer.py =====
"""
Tests for the DashboardWriter class.
"""
import pytest
import pandas as pd
from pathlib import Path
from openpyxl import Workbook
from src.dashboard_writer import DashboardWriter


def test_dashboard_writer_validates_summary():
    """Test that DashboardWriter validates summary DataFrame."""
    writer = DashboardWriter(Path('dummy.xlsx'))

    # Missing columns
    invalid_df = pd.DataFrame({'year': [2024]})
    assert writer._validate_summary(invalid_df) is False

    # Valid columns
    valid_df = pd.DataFrame({
        'year': [2024],
        'month': [1],
        'category': ['Food'],
        'subcat': ['Groceries'],
        'monthly_amount': [100.0]
    })
    assert writer._validate_summary(valid_df) is True


def test_dashboard_writer_validates_empty_dataframe():
    """Test that DashboardWriter rejects empty DataFrames."""
    writer = DashboardWriter(Path('dummy.xlsx'))

    empty_df = pd.DataFrame(columns=['year', 'month', 'category', 'subcat', 'monthly_amount'])
    assert writer._validate_summary(empty_df) is False


def test_dashboard_writer_conflict_resolver_callback():
    """Test that conflict resolver callback is used when provided."""
    writer = DashboardWriter(Path('dummy.xlsx'))

    # Mock conflict resolver
    def resolver(month_key):
        return 'override'

    result = writer._prompt_user_decision('2024-1', conflict_resolver=resolver)
    assert result == 'override'


def test_dashboard_writer_gets_category_ranges(temp_dir):
    """Test that category row ranges are correctly identified."""
    # Create a simple workbook
    wb = Workbook()
    ws = wb.active
    ws['A2'] = 'Food'
    ws['A3'] = 'Food'
    ws['A4'] = 'Shopping'

    dashboard_path = temp_dir / 'test_dashboard.xlsx'
    wb.save(dashboard_path)

    writer = DashboardWriter(dashboard_path)
    ranges = writer._get_category_row_ranges(ws)

    assert 'Food' in ranges
    assert 'Shopping' in ranges

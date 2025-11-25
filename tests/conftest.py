# ===== tests/conftest.py =====
"""
Pytest configuration and shared fixtures for Budget Tracker tests.
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def sample_transactions_df():
    """Create a sample transactions DataFrame for testing."""
    return pd.DataFrame({
        'date': pd.to_datetime(['2024-01-15', '2024-01-20', '2024-02-10']),
        'merchant': ['Amazon', 'Supermarket', 'Amazon'],
        'amount': [150.0, 75.5, 200.0],
        'monthly_amount': [150.0, 75.5, 200.0]
    })


@pytest.fixture
def sample_normalized_df():
    """Create a normalized DataFrame with categories."""
    return pd.DataFrame({
        'date': pd.to_datetime(['2024-01-15', '2024-01-20', '2024-02-10']),
        'merchant': ['Amazon', 'Supermarket', 'Amazon'],
        'amount': [150.0, 75.5, 200.0],
        'monthly_amount': [150.0, 75.5, 200.0],
        'year': [2024, 2024, 2024],
        'month': [1, 1, 2],
        'category': ['Shopping', 'Food', 'Shopping'],
        'subcat': ['Online', 'Groceries', 'Online']
    })


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_categories():
    """Sample category mapping."""
    return {
        'Amazon': ['Shopping', 'Online'],
        'Supermarket': ['Food', 'Groceries']
    }


@pytest.fixture
def sample_excel_file(temp_dir):
    """Create a sample Excel file for testing."""
    df = pd.DataFrame({
        'Date': ['15/01/2024', '20/01/2024'],
        'Description': ['Amazon purchase', 'Supermarket'],
        'Amount': [150.0, 75.5]
    })
    file_path = temp_dir / 'transactions.xlsx'
    df.to_excel(file_path, index=False)
    return file_path

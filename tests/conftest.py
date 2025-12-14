"""
Pytest configuration for the test suite.
Ensures the project root is in the Python path for imports.
"""
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add the project root to sys.path so we can import 'src' module
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))






@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def sample_categories():
    """Provide sample categories for testing."""
    return {
        'Amazon': ['Shopping', 'Online'],
        'Supermarket': ['Food', 'Groceries']
    }


@pytest.fixture
def sample_normalized_df():
    """Provide a sample normalized DataFrame for testing."""
    return pd.DataFrame({
        'merchant': ['Amazon', 'Supermarket', 'Amazon'],
        'amount': [150.0, 50.0, 200.0],
        'year': [2024, 2024, 2024],
        'month': [1, 1, 2],
        'category': ['Shopping', 'Food', 'Shopping'],
        'subcat': ['Online', 'Groceries', 'Online'],
        'monthly_amount': [150.0, 50.0, 200.0]
    })


@pytest.fixture
def translations():
    """Provide translations object for GUI tests."""
    from src.translations import Translations
    return Translations('en')

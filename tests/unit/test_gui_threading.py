"""
Tests for GUI threading components.
"""
import pytest
import pandas as pd
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from gui_app import ProcessThread
from src.translations import Translations
from src.config import TRANSACTIONS_DIR
from pathlib import Path





@pytest.fixture
def translations():
    """Create translations object."""
    return Translations('en')


class TestProcessThread:
    """Tests for ProcessThread."""

    def test_thread_creation(self, qapp, translations):
        """Test that thread can be created."""
        thread = ProcessThread(translations)
        assert thread is not None
        assert thread.translations == translations
        assert thread.category_response is None
        assert thread.response_ready is False
        assert thread._should_stop is False

    def test_thread_stop(self, qapp, translations):
        """Test stopping the thread."""
        thread = ProcessThread(translations)
        thread.stop()

        assert thread._should_stop is True

    def test_timeout_handling(self, qapp, translations):
        """Test timeout timer setup."""
        thread = ProcessThread(translations)

        assert thread.timeout_timer is not None
        assert thread.timeout_timer.isSingleShot() is True

    def test_map_categories_gui_no_unknown(self, qapp, translations, tmp_path):
        """Test category mapping with no unknown merchants."""
        from src.category_manager import CategoryManager
        from openpyxl import Workbook

        # Create test dashboard
        dashboard_file = tmp_path / 'dashboard.xlsx'
        wb = Workbook()
        ws = wb.active
        ws.title = 'Template'
        ws['A1'] = 'Category'
        ws['B1'] = 'Subcategory'
        ws['A2'] = 'Food'
        ws['B2'] = 'Groceries'
        wb.save(dashboard_file)

        # Create categories file
        categories_file = tmp_path / 'categories.json'
        import json
        with open(categories_file, 'w') as f:
            json.dump({'Merchant1': ['Food', 'Groceries']}, f)

        thread = ProcessThread(translations)
        cat_mgr = CategoryManager(categories_file, dashboard_file)

        df = pd.DataFrame({
            'merchant': ['Merchant1', 'Merchant1'],
            'amount': [100.0, 200.0]
        })

        result_df = thread._map_categories_gui(df, cat_mgr)

        assert 'category' in result_df.columns
        assert 'subcat' in result_df.columns
        assert result_df['category'].iloc[0] == 'Food'
        assert result_df['subcat'].iloc[0] == 'Groceries'


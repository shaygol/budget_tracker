"""
Tests for GUI dialog components.
"""
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from gui_app import CategoryDialog, ConflictDialog
from src.translations import Translations





@pytest.fixture
def translations():
    """Create translations object."""
    return Translations('en')


class TestCategoryDialog:
    """Tests for CategoryDialog."""

    def test_dialog_creation(self, qapp, translations):
        """Test that dialog can be created."""
        dialog = CategoryDialog('Test Merchant', [('Food', 'Groceries'), ('Shopping', 'Online')], translations)
        assert dialog is not None
        assert dialog.merchant == 'Test Merchant'
        assert dialog.selected_category is None

    def test_dialog_accepts_selection(self, qapp, translations):
        """Test that dialog stores selected category on accept."""
        choices = [('Food', 'Groceries'), ('Shopping', 'Online')]
        dialog = CategoryDialog('Test Merchant', choices, translations)

        # Select first category and subcategory
        dialog.category_combo.setCurrentIndex(0)  # Select 'Food'
        # Subcategory should auto-update, but ensure it's set
        if dialog.subcategory_combo.count() > 0:
            dialog.subcategory_combo.setCurrentIndex(0)  # Select first subcategory
        dialog.accept()

        assert dialog.selected_category is not None
        assert dialog.selected_category[0] == 'Food'
        assert dialog.selected_category[1] == 'Groceries'

    def test_dialog_rejects_without_selection(self, qapp, translations):
        """Test that dialog returns None when rejected."""
        choices = [('Food', 'Groceries'), ('Shopping', 'Online')]
        dialog = CategoryDialog('Test Merchant', choices, translations)

        dialog.reject()

        assert dialog.selected_category is None

    def test_dialog_populates_choices(self, qapp, translations):
        """Test that dialog populates category and subcategory combo boxes."""
        choices = [('Food', 'Groceries'), ('Shopping', 'Online'), ('Transport', 'Bus')]
        dialog = CategoryDialog('Test Merchant', choices, translations)

        # Should have 3 categories (Food, Shopping, Transport)
        assert dialog.category_combo.count() == 3
        # Categories should be sorted alphabetically
        assert dialog.category_combo.itemText(0) == 'Food'
        assert dialog.category_combo.itemText(1) == 'Shopping'
        assert dialog.category_combo.itemText(2) == 'Transport'

        # Subcategory combo should be populated based on selected category
        dialog.category_combo.setCurrentIndex(0)  # Select 'Food'
        assert dialog.subcategory_combo.count() == 1
        assert dialog.subcategory_combo.itemText(0) == 'Groceries'


class TestConflictDialog:
    """Tests for ConflictDialog."""

    def test_dialog_creation(self, qapp, translations):
        """Test that dialog can be created."""
        dialog = ConflictDialog('2024-01', translations)
        assert dialog is not None
        assert dialog.month_key == '2024-01'
        assert dialog.decision == 'skip'

    def test_dialog_override_decision(self, qapp, translations):
        """Test that dialog sets override decision."""
        dialog = ConflictDialog('2024-01', translations)
        dialog.set_decision('override')

        assert dialog.decision == 'override'

    def test_dialog_add_decision(self, qapp, translations):
        """Test that dialog sets add decision."""
        dialog = ConflictDialog('2024-01', translations)
        dialog.set_decision('add')

        assert dialog.decision == 'add'

    def test_dialog_skip_decision(self, qapp, translations):
        """Test that dialog sets skip decision (default)."""
        dialog = ConflictDialog('2024-01', translations)
        # Default is skip, but test explicit setting
        dialog.set_decision('skip')

        assert dialog.decision == 'skip'


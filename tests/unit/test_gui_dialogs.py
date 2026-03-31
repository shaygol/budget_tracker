"""
Tests for GUI dialog components.
"""
import pytest
from gui_app import CategoryDialog, ConflictDialog
from src.translations import Translations





@pytest.fixture
def translations():
    """Create translations object."""
    return Translations('en')


class TestCategoryDialog:
    """Grouped tests for CategoryDialog."""

    def test_category_dialog_flows(self, qapp, translations):
        choices = [("Food", "Groceries"), ("Shopping", "Online"), ("Transport", "Bus")]
        dialog = CategoryDialog("Test Merchant", choices, translations)

        assert dialog is not None
        assert dialog.merchant == "Test Merchant"
        assert dialog.selected_category is None
        assert dialog.category_combo.count() == 3
        assert dialog.category_combo.itemText(0) == "Food"
        assert dialog.category_combo.itemText(1) == "Shopping"
        assert dialog.category_combo.itemText(2) == "Transport"

        dialog.category_combo.setCurrentIndex(0)
        assert dialog.subcategory_combo.count() == 1
        assert dialog.subcategory_combo.itemText(0) == "Groceries"

        dialog.subcategory_combo.setCurrentIndex(0)
        dialog.accept()
        assert dialog.selected_category == ("Food", "Groceries")

        rejected = CategoryDialog("Another Merchant", choices, translations)
        rejected.reject()
        assert rejected.selected_category is None


class TestConflictDialog:
    """Grouped tests for ConflictDialog."""

    def test_conflict_dialog_decision_flows(self, qapp, translations):
        dialog = ConflictDialog("2024-01", translations)
        assert dialog is not None
        assert dialog.month_key == "2024-01"
        assert dialog.decision == "skip"

        for decision in ("override", "add", "skip"):
            dialog.set_decision(decision)
            assert dialog.decision == decision


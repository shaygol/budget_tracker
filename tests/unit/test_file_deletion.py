"""Tests for file deletion functionality."""
import pytest
from pathlib import Path
import pandas as pd
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt
from gui_app import BudgetTrackerGUI


class TestFileDeletion:
    """Tests for the delete file feature."""
    
    def test_delete_file_removes_from_filesystem(self, qtbot, tmp_path, monkeypatch):
        """Test that deleting a file removes it from the filesystem."""
        # Create a test transaction file
        from src.config import TRANSACTIONS_DIR
        monkeypatch.setattr('src.config.TRANSACTIONS_DIR', tmp_path)
        monkeypatch.setattr('gui_app.TRANSACTIONS_DIR', tmp_path)
        
        test_file = tmp_path / "test_transaction.xlsx"
        df = pd.DataFrame({
            'transaction_date': ['2024-01-01'],
            'merchant': ['Test'],
            'amount': [100.0]
        })
        df.to_excel(test_file, index=False)
        
        assert test_file.exists(), "Test file should exist before deletion"
        
        # Create GUI and simulate deletion
        app = BudgetTrackerGUI()
        qtbot.addWidget(app)
        
        # Refresh to load the file
        app.refresh_files()
        
        # Select the file
        app.file_list.setCurrentRow(0)
        
        # Mock the confirmation dialog to always return Yes
        monkeypatch.setattr(QMessageBox, 'question', lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
        
        # Delete the file
        app.delete_selected_file()
        
        assert not test_file.exists(), "File should be deleted from filesystem"
    
    def test_delete_file_updates_file_list(self, qtbot, tmp_path, monkeypatch):
        """Test that deleting a file updates the GUI file list."""
        from src.config import TRANSACTIONS_DIR
        monkeypatch.setattr('src.config.TRANSACTIONS_DIR', tmp_path)
        monkeypatch.setattr('gui_app.TRANSACTIONS_DIR', tmp_path)
        
        # Create test files
        for i in range(3):
            test_file = tmp_path / f"transaction_{i}.xlsx"
            df = pd.DataFrame({
                'transaction_date': ['2024-01-01'],
                'merchant': ['Test'],
                'amount': [100.0]
            })
            df.to_excel(test_file, index=False)
        
        app = BudgetTrackerGUI()
        qtbot.addWidget(app)
        app.refresh_files()
        
        initial_count = app.file_list.count()
        assert initial_count == 3, "Should have 3 files initially"
        
        # Select and delete first file
        app.file_list.setCurrentRow(0)
        monkeypatch.setattr(QMessageBox, 'question', lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
        monkeypatch.setattr(QMessageBox, 'information', lambda *args, **kwargs: None)
        
        app.delete_selected_file()
        
        assert app.file_list.count() == 2, "Should have 2 files after deletion"
    
    def test_delete_without_selection_shows_warning(self, qtbot, tmp_path, monkeypatch):
        """Test that attempting to delete without selection shows a warning."""
        from src.config import TRANSACTIONS_DIR
        monkeypatch.setattr('src.config.TRANSACTIONS_DIR', tmp_path)
        monkeypatch.setattr('gui_app.TRANSACTIONS_DIR', tmp_path)
        
        app = BudgetTrackerGUI()
        qtbot.addWidget(app)
        
        warning_shown = False
        
        def mock_warning(*args, **kwargs):
            nonlocal warning_shown
            warning_shown = True
        
        monkeypatch.setattr(QMessageBox, 'warning', mock_warning)
        
        # Try to delete without selecting a file
        app.delete_selected_file()
        
        assert warning_shown, "Warning should be shown when no file is selected"
    
    def test_delete_confirmation_can_be_cancelled(self, qtbot, tmp_path, monkeypatch):
        """Test that user can cancel the delete operation."""
        from src.config import TRANSACTIONS_DIR
        monkeypatch.setattr('src.config.TRANSACTIONS_DIR', tmp_path)
        monkeypatch.setattr('gui_app.TRANSACTIONS_DIR', tmp_path)
        
        test_file = tmp_path / "test_transaction.xlsx"
        df = pd.DataFrame({
            'transaction_date': ['2024-01-01'],
            'merchant': ['Test'],
            'amount': [100.0]
        })
        df.to_excel(test_file, index=False)
        
        app = BudgetTrackerGUI()
        qtbot.addWidget(app)
        app.refresh_files()
        app.file_list.setCurrentRow(0)
        
        # Mock the confirmation dialog to return No
        monkeypatch.setattr(QMessageBox, 'question', lambda *args, **kwargs: QMessageBox.StandardButton.No)
        
        app.delete_selected_file()
        
        assert test_file.exists(), "File should still exist when deletion is cancelled"
        assert app.file_list.count() == 1, "File list should be unchanged"
    
    def test_delete_nonexistent_file_shows_error(self, qtbot, tmp_path, monkeypatch):
        """Test that deleting a file that doesn't exist shows an error."""
        from src.config import TRANSACTIONS_DIR
        monkeypatch.setattr('src.config.TRANSACTIONS_DIR', tmp_path)
        monkeypatch.setattr('gui_app.TRANSACTIONS_DIR', tmp_path)
        
        app = BudgetTrackerGUI()
        qtbot.addWidget(app)
        
        # Manually add an item to the list without creating the file
        app.file_list.addItem("nonexistent.xlsx")
        app.file_list.setCurrentRow(0)
        
        warning_shown = False
        
        def mock_warning(*args, **kwargs):
            nonlocal warning_shown
            warning_shown = True
        
        monkeypatch.setattr(QMessageBox, 'question', lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
        monkeypatch.setattr(QMessageBox, 'warning', mock_warning)
        
        app.delete_selected_file()
        
        assert warning_shown, "Warning should be shown for nonexistent file"

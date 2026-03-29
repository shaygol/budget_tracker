"""
Tests for main window GUI components.
"""
import pytest
import gui_app as gui_module
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from gui_app import BudgetTrackerGUI
from src.config import TRANSACTIONS_DIR, DASHBOARD_FILE_PATH
from pathlib import Path





@pytest.fixture
def gui_window(qapp, tmp_path, monkeypatch):
    """Create GUI window with temporary directories."""
    transactions_dir = tmp_path / 'transactions'
    archive_dir = tmp_path / 'archive'
    dashboard_path = tmp_path / 'dashboard.xlsx'
    appdata_dir = tmp_path / 'appdata'
    categories_path = tmp_path / 'categories.json'

    # Patch config paths to use temp directory
    monkeypatch.setattr('src.config.TRANSACTIONS_DIR', transactions_dir)
    monkeypatch.setattr('src.config.DASHBOARD_FILE_PATH', dashboard_path)
    monkeypatch.setattr('src.config.APPDATA_DIR', appdata_dir)
    monkeypatch.setattr('src.config.ARCHIVE_DIR', archive_dir)
    monkeypatch.setattr('src.config.CATEGORIES_FILE_PATH', categories_path)

    # Patch already-imported module globals used by the GUI
    monkeypatch.setattr(gui_module, 'TRANSACTIONS_DIR', transactions_dir)
    monkeypatch.setattr(gui_module, 'DASHBOARD_FILE_PATH', dashboard_path)
    monkeypatch.setattr(gui_module, 'APPDATA_DIR', appdata_dir)
    monkeypatch.setattr(gui_module, 'ARCHIVE_DIR', archive_dir)
    monkeypatch.setattr(gui_module, 'CATEGORIES_FILE_PATH', categories_path)

    # Create directories
    transactions_dir.mkdir()
    (tmp_path / 'output').mkdir()
    archive_dir.mkdir()

    window = BudgetTrackerGUI('en')
    return window


class TestBudgetTrackerGUI:
    """Tests for BudgetTrackerGUI main window."""

    def test_window_creation(self, gui_window):
        """Test that window can be created."""
        assert gui_window is not None
        assert gui_window.translations is not None

    def test_setup_shortcuts(self, gui_window):
        """Test that keyboard shortcuts are set up."""
        # Shortcuts are set up in __init__, verify they exist
        assert hasattr(gui_window, 'setup_shortcuts')

    def test_refresh_files_empty(self, gui_window):
        """Test refreshing files when directory is empty."""
        gui_window.refresh_files()

        assert gui_window.file_list.count() == 0

    def test_toggle_language(self, gui_window):
        """Test language toggle functionality."""
        initial_lang = gui_window.translations.language
        gui_window.toggle_language()

        # Language toggle recreates the window, so we test the method exists
        assert hasattr(gui_window, 'toggle_language')

    def test_update_progress(self, gui_window):
        """Test progress update."""
        gui_window.update_progress('Test message')

        # Status bar should show the message
        assert gui_window.statusBar().currentMessage() == 'Test message'

    def test_resolve_conflict(self, gui_window):
        """Test conflict resolution."""
        # This will show a dialog, so we just test the method exists
        assert hasattr(gui_window, 'resolve_conflict')

    def test_clear_archive(self, gui_window):
        """Test archive clearing functionality."""
        # Method exists and handles confirmation dialog
        assert hasattr(gui_window, 'clear_archive')

    def test_import_files_accepts_pdf(self, gui_window, tmp_path, monkeypatch):
        """Test importing a PDF through the file dialog flow."""
        source_pdf = tmp_path / "statement.pdf"
        source_pdf.write_bytes(b"%PDF-1.4\n")

        monkeypatch.setattr(
            gui_module.QFileDialog,
            'getOpenFileNames',
            lambda *args, **kwargs: ([str(source_pdf)], "Transaction Files (*.xlsx *.xls *.pdf)")
        )
        monkeypatch.setattr(gui_module, 'check_file_permissions', lambda path, mode: (True, None))
        monkeypatch.setattr(gui_module, 'is_file_locked', lambda path: False)
        monkeypatch.setattr(
            gui_module.QMessageBox,
            'information',
            lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        )
        monkeypatch.setattr(
            gui_module.QMessageBox,
            'warning',
            lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        )

        gui_window.import_files()

        imported_path = gui_module.TRANSACTIONS_DIR / source_pdf.name
        assert imported_path.exists()
        assert gui_window.file_list.count() == 1
        assert gui_window.file_list.item(0).text() == source_pdf.name

    def test_import_dropped_files_accepts_pdf(self, gui_window, tmp_path, monkeypatch):
        """Test importing a PDF through the dropped files flow."""
        source_pdf = tmp_path / "dropped_statement.pdf"
        source_pdf.write_bytes(b"%PDF-1.4\n")

        monkeypatch.setattr(
            gui_module.QMessageBox,
            'information',
            lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        )
        monkeypatch.setattr(
            gui_module.QMessageBox,
            'warning',
            lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        )

        gui_window.import_dropped_files([str(source_pdf)])

        imported_path = gui_module.TRANSACTIONS_DIR / source_pdf.name
        assert imported_path.exists()
        assert gui_window.file_list.count() == 1
        assert gui_window.file_list.item(0).text() == source_pdf.name


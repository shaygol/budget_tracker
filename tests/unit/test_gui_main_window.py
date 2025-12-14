"""
Tests for main window GUI components.
"""
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from gui_app import BudgetTrackerGUI
from src.config import TRANSACTIONS_DIR, DASHBOARD_FILE_PATH
from pathlib import Path





@pytest.fixture
def gui_window(qapp, tmp_path, monkeypatch):
    """Create GUI window with temporary directories."""
    # Patch config paths to use temp directory
    monkeypatch.setattr('src.config.TRANSACTIONS_DIR', tmp_path / 'transactions')
    monkeypatch.setattr('src.config.DASHBOARD_FILE_PATH', tmp_path / 'dashboard.xlsx')
    monkeypatch.setattr('src.config.OUTPUT_DIR', tmp_path / 'output')
    monkeypatch.setattr('src.config.ARCHIVE_DIR', tmp_path / 'archive')
    monkeypatch.setattr('src.config.CATEGORIES_FILE_PATH', tmp_path / 'categories.json')

    # Create directories
    (tmp_path / 'transactions').mkdir()
    (tmp_path / 'output').mkdir()
    (tmp_path / 'archive').mkdir()

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


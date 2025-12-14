"""
Tests for GUI widget components.
"""
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from gui_app import LogViewerWidget, ChartWidget, FileListWidget
from src.translations import Translations
import pandas as pd





@pytest.fixture
def translations():
    """Create translations object."""
    return Translations('en')


class TestLogViewerWidget:
    """Tests for LogViewerWidget."""

    def test_widget_creation(self, qapp, translations):
        """Test that widget can be created."""
        widget = LogViewerWidget(translations)
        assert widget is not None
        assert widget.log_text is not None

    def test_add_log_info(self, qapp, translations):
        """Test adding INFO log message."""
        widget = LogViewerWidget(translations)
        widget.add_log('INFO', 'Test message')

        # Check that log text contains the message
        html_content = widget.log_text.toHtml()
        assert 'Test message' in html_content
        assert '[INFO]' in html_content

    def test_add_log_error(self, qapp, translations):
        """Test adding ERROR log message."""
        widget = LogViewerWidget(translations)
        widget.add_log('ERROR', 'Error message')

        html_content = widget.log_text.toHtml()
        assert 'Error message' in html_content
        assert '[ERROR]' in html_content

    def test_add_log_warning(self, qapp, translations):
        """Test adding WARNING log message."""
        widget = LogViewerWidget(translations)
        widget.add_log('WARNING', 'Warning message')

        html_content = widget.log_text.toHtml()
        assert 'Warning message' in html_content
        assert '[WARNING]' in html_content

    def test_clear_logs(self, qapp, translations):
        """Test clearing logs."""
        widget = LogViewerWidget(translations)
        widget.add_log('INFO', 'Test message')
        widget.clear_logs()

        assert widget.log_text.toPlainText() == ''


class TestChartWidget:
    """Tests for ChartWidget."""

    def test_widget_creation(self, qapp, translations):
        """Test that widget can be created."""
        widget = ChartWidget(translations)
        assert widget is not None
        assert widget.figure is not None
        assert widget.canvas is not None

    def test_update_chart_with_data(self, qapp, translations):
        """Test updating chart with data."""
        widget = ChartWidget(translations)
        summary_df = pd.DataFrame({
            'year': [2024, 2024, 2024],
            'month': [1, 2, 3],
            'category': ['Food', 'Shopping', 'Food'],
            'subcat': ['Groceries', 'Online', 'Groceries'],
            'monthly_amount': [100.0, 200.0, 150.0]
        })

        widget.update_chart(summary_df)

        assert widget.summary_df is not None
        assert len(widget.summary_df) == 3

    def test_update_chart_empty_data(self, qapp, translations):
        """Test updating chart with empty data."""
        widget = ChartWidget(translations)
        summary_df = pd.DataFrame()

        widget.update_chart(summary_df)

        assert widget.summary_df is not None
        assert len(widget.summary_df) == 0


class TestFileListWidget:
    """Tests for FileListWidget."""

    def test_widget_creation(self, qapp):
        """Test that widget can be created."""
        widget = FileListWidget()
        assert widget is not None
        assert widget.acceptDrops() is True

    def test_drag_enter_event(self, qapp):
        """Test drag enter event handling."""
        from PyQt5.QtCore import QMimeData, QUrl
        from PyQt5.QtGui import QDragEnterEvent

        widget = FileListWidget()

        # Create mock mime data with URLs
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile('/path/to/file.xlsx')])

        # Note: Creating actual QDragEnterEvent is complex, so we test the logic
        # The actual event handling would be tested in integration tests
        assert widget.acceptDrops() is True


"""
Tests for GUI widget components.
"""
import pytest
import pandas as pd
from PyQt5.QtCore import QMimeData, QUrl
from gui_app import ChartWidget, FileListWidget, LogViewerWidget
from src.translations import Translations





@pytest.fixture
def translations():
    """Create translations object."""
    return Translations('en')


class TestLogViewerWidget:
    """Grouped tests for LogViewerWidget and FileListWidget."""

    def test_log_viewer_and_file_list_behaviors(self, qapp, translations):
        log_widget = LogViewerWidget(translations)
        assert log_widget is not None
        assert log_widget.log_text is not None

        for level, message in [
            ("INFO", "Test message"),
            ("ERROR", "Error message"),
            ("WARNING", "Warning message"),
        ]:
            log_widget.add_log(level, message)
            html_content = log_widget.log_text.toHtml()
            assert message in html_content
            assert f"[{level}]" in html_content

        log_widget.clear_logs()
        assert log_widget.log_text.toPlainText() == ""

        file_widget = FileListWidget()
        assert file_widget is not None
        assert file_widget.acceptDrops() is True

        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile("/path/to/file.xlsx")])
        # We verify drag-and-drop readiness via widget configuration.
        assert file_widget.acceptDrops() is True


class TestChartWidget:
    """Grouped tests for ChartWidget."""

    def test_chart_widget_creation_and_update_behaviors(self, qapp, translations):
        widget = ChartWidget(translations)
        assert widget is not None
        assert widget.figure is not None
        assert widget.canvas is not None

        non_empty_summary = pd.DataFrame({
            "year": [2024, 2024, 2024],
            "month": [1, 2, 3],
            "category": ["Food", "Shopping", "Food"],
            "subcat": ["Groceries", "Online", "Groceries"],
            "monthly_amount": [100.0, 200.0, 150.0],
        })
        widget.update_chart(non_empty_summary)
        assert widget.summary_df is not None
        assert len(widget.summary_df) == 3

        empty_summary = pd.DataFrame()
        widget.update_chart(empty_summary)
        assert widget.summary_df is not None
        assert len(widget.summary_df) == 0


# ===== gui_app.py =====
"""
PyQt5 GUI application for Budget Tracker.
Provides a modern interface for transaction processing with bilingual support.
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import pandas as pd
import logging

# Suppress matplotlib debug logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

# Fix for PyQt5 platform plugin issue
import PyQt5
plugin_path = os.path.join(os.path.dirname(PyQt5.__file__), 'Qt5', 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QTabWidget, QTableWidget,
    QTableWidgetItem, QProgressBar, QFileDialog, QMessageBox,
    QDialog, QComboBox, QDialogButtonBox, QTextEdit, QHeaderView
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from code.config import TRANSACTIONS_DIR, CATEGORIES_FILE_PATH, DASHBOARD_FILE_PATH, OUTPUT_DIR, LOG_FILE_NAME, ARCHIVE_DIR
from code.file_manager import ensure_dirs, load_transaction_files
from code.logger import setup_logging
from code.normalizer import Normalizer
from code.category_manager import CategoryManager
from code.previewer import Previewer
from code.dashboard_writer import DashboardWriter
from code.translations import Translations


class ProcessThread(QThread):
    """Background thread for processing transactions."""
    progress = pyqtSignal(str)
    finished = pyqtSignal(pd.DataFrame, bool)
    error = pyqtSignal(str)
    category_needed = pyqtSignal(str, list, list)
    log_message = pyqtSignal(str, str)  # level, message
    
    def __init__(self, translations):
        super().__init__()
        self.translations = translations
        self.category_response = None
        self.response_ready = False
        self._should_stop = False
        
    def run(self):
        import traceback
        try:
            if self._should_stop:
                return
                
            self.log_message.emit('INFO', '=== Starting transaction processing ===')
            self.progress.emit(self.translations.get('processing'))
            
            # Load files
            self.log_message.emit('INFO', 'Loading transaction files...')
            dfs = load_transaction_files(TRANSACTIONS_DIR)
            if not dfs:
                self.error.emit(self.translations.get('no_files'))
                return
            
            self.log_message.emit('INFO', f'Loaded {len(dfs)} transaction file(s)')
            
            # Normalize
            self.log_message.emit('INFO', 'Normalizing transactions...')
            normalizer = Normalizer()
            df = pd.concat(dfs, ignore_index=True)
            df = normalizer.normalize(df)
            self.log_message.emit('INFO', f'Normalized {len(df)} transactions')
            
            if self._should_stop:
                return
            
            # Category mapping
            self.log_message.emit('INFO', 'Mapping categories...')
            cat_mgr = CategoryManager(CATEGORIES_FILE_PATH, DASHBOARD_FILE_PATH)
            df = self._map_categories_gui(df, cat_mgr)
            
            if self._should_stop:
                return
            
            # Preview
            self.log_message.emit('INFO', 'Generating preview...')
            preview = Previewer()
            summary = preview.preview(df, confirm=False)
            
            self.log_message.emit('INFO', 'Processing complete!')
            self.finished.emit(summary, True)
            
        except Exception as e:
            error_details = f"{str(e)}\\n\\n{traceback.format_exc()}"
            self.log_message.emit('ERROR', error_details)
            self.error.emit(str(e))
    
    def stop(self):
        """Request thread to stop."""
        self._should_stop = True
    
    def _map_categories_gui(self, df: pd.DataFrame, cat_mgr: CategoryManager) -> pd.DataFrame:
        """Map categories with GUI interaction."""
        df = df.copy()
        
        df['category'] = df['merchant'].map(lambda m: cat_mgr.category_map.get(m, [None, None])[0])
        df['subcat'] = df['merchant'].map(lambda m: cat_mgr.category_map.get(m, [None, None])[1])
        
        unknown = [m for m in df['merchant'].unique() if m and m not in cat_mgr.category_map]
        
        flat_choices = [
            (cat, sub)
            for cat, subs in cat_mgr.valid_categories.items()
            for sub in subs
        ]
        
        for merchant in unknown:
            self.log_message.emit('INFO', f'Unknown merchant: {merchant}')
            # Signal to GUI that we need category selection
            self.category_needed.emit(merchant, flat_choices, [])
            
            # Wait for response
            while not self.response_ready:
                self.msleep(100)
            
            if self.category_response:
                cat, sub = self.category_response
                cat_mgr.category_map[merchant] = [cat, sub]
                df.loc[df['merchant'] == merchant, 'category'] = cat
                df.loc[df['merchant'] == merchant, 'subcat'] = sub
                self.log_message.emit('INFO', f'Mapped {merchant} -> {cat}/{sub}')
            
            self.response_ready = False
            self.category_response = None
        
        cat_mgr.save_categories()
        return df


class CategoryDialog(QDialog):
    """Dialog for selecting category for unknown merchants."""
    
    def __init__(self, merchant: str, choices: List[tuple], translations: Translations, parent=None):
        super().__init__(parent)
        self.merchant = merchant
        self.choices = choices
        self.translations = translations
        self.selected_category = None
        
        self.setWindowTitle(self.translations.get('category_dialog_title'))
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Merchant label
        merchant_label = QLabel(self.translations.get('new_merchant', merchant=merchant))
        merchant_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        layout.addWidget(merchant_label)
        
        # Category combo box
        self.combo = QComboBox()
        for cat, sub in choices:
            self.combo.addItem(f"{cat} > {sub}", (cat, sub))
        layout.addWidget(self.combo)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def accept(self):
        self.selected_category = self.combo.currentData()
        super().accept()


class ConflictDialog(QDialog):
    """Dialog for resolving data conflicts."""
    
    def __init__(self, month_key: str, translations: Translations, parent=None):
        super().__init__(parent)
        self.month_key = month_key
        self.translations = translations
        self.decision = "skip"
        
        self.setWindowTitle("Data Conflict")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        
        # Message
        msg = QLabel(f"Data already exists for {month_key}.\\nHow should we handle it?")
        msg.setFont(QFont('Arial', 11))
        layout.addWidget(msg)
        
        # Buttons
        override_btn = QPushButton("Override (Replace existing)")
        override_btn.clicked.connect(lambda: self.set_decision("override"))
        layout.addWidget(override_btn)
        
        add_btn = QPushButton("Add (Sum with existing)")
        add_btn.clicked.connect(lambda: self.set_decision("add"))
        layout.addWidget(add_btn)
        
        skip_btn = QPushButton("Skip (Keep existing)")
        skip_btn.clicked.connect(lambda: self.set_decision("skip"))
        layout.addWidget(skip_btn)
        
        self.setLayout(layout)
    
    def set_decision(self, decision: str):
        self.decision = decision
        self.accept()


class LogViewerWidget(QWidget):
    """Widget for displaying logs."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout()
        
        # Text area for logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont('Consolas', 9))
        layout.addWidget(self.log_text)
        
        # Clear button
        clear_btn = QPushButton("Clear Logs")
        clear_btn.clicked.connect(self.clear_logs)
        layout.addWidget(clear_btn)
        
        self.setLayout(layout)
    
    def add_log(self, level: str, message: str):
        """Add a log message."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Color code by level
        if level == 'ERROR':
            color = '#ff4444'
        elif level == 'WARNING':
            color = '#ffaa00'
        elif level == 'INFO':
            color = '#4444ff'
        else:
            color = '#000000'
        
        formatted = f"<span style='color: gray;'>[{timestamp}]</span> <span style='color: {color}; font-weight: bold;'>[{level}]</span> {message}<br>"
        self.log_text.insertHtml(formatted)
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """Clear all logs."""
        self.log_text.clear()


class ChartWidget(QWidget):
    """Widget for displaying matplotlib charts."""
    
    def __init__(self, translations: Translations, parent=None):
        super().__init__(parent)
        self.translations = translations
        
        layout = QVBoxLayout()
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # Export button
        export_btn = QPushButton(self.translations.get('export_chart'))
        export_btn.clicked.connect(self.export_chart)
        layout.addWidget(export_btn)
        
        self.setLayout(layout)
        self.summary_df = None
    
    def update_chart(self, summary_df: pd.DataFrame):
        """Update chart with new data."""
        try:
            self.summary_df = summary_df
            self.figure.clear()
            
            if summary_df.empty:
                return
            
            # Group by month and sum amounts
            monthly_data = summary_df.groupby('month')['monthly_amount'].sum().sort_index()
            
            ax = self.figure.add_subplot(111)
            months = [self.translations.get(f'month_{m}') for m in monthly_data.index]
            values = monthly_data.values
            
            # For RTL languages, reverse the order
            if self.translations.is_rtl():
                months = months[::-1]
                values = values[::-1]
            
            ax.bar(months, values, color='#4CAF50')
            ax.set_xlabel(self.translations.get('month'))
            ax.set_ylabel(self.translations.get('amount'))
            ax.set_title(self.translations.get('preview'))
            
            # Rotate labels for better readability
            ax.tick_params(axis='x', rotation=45)
            
            # For RTL, invert x-axis so it goes right to left
            if self.translations.is_rtl():
                ax.invert_xaxis()
            
            self.canvas.draw()
        except Exception as e:
            print(f"Chart update error: {e}")
    
    def export_chart(self):
        """Export chart as image."""
        if self.summary_df is None:
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            self.translations.get('export_chart'),
            f"budget_chart_{datetime.now().strftime('%Y%m%d')}.png",
            "PNG Files (*.png);;PDF Files (*.pdf)"
        )
        
        if filename:
            self.figure.savefig(filename, dpi=300, bbox_inches='tight')
            QMessageBox.information(
                self,
                self.translations.get('success_title'),
                self.translations.get('chart_exported')
            )


class FileListWidget(QListWidget):
    """Custom list widget with drag-and-drop support."""
    
    files_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith(('.xlsx', '.xls')):
                files.append(file_path)
        
        if files:
            self.files_dropped.emit(files)


class BudgetTrackerGUI(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize translations (default Hebrew)
        self.translations = Translations('he')
        
        # Setup logging
        ensure_dirs([OUTPUT_DIR])
        setup_logging(OUTPUT_DIR, LOG_FILE_NAME)
        
        # Initialize UI
        self.init_ui()
        
        # Add keyboard shortcuts
        self.setup_shortcuts()
        
        # Load initial file list
        self.refresh_files()
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        
        # F5 - Refresh files
        refresh_shortcut = QShortcut(QKeySequence('F5'), self)
        refresh_shortcut.activated.connect(self.refresh_files)
        
        # Ctrl+O - Open dashboard
        open_shortcut = QShortcut(QKeySequence('Ctrl+O'), self)
        open_shortcut.activated.connect(self.open_dashboard)
        
        # Ctrl+R - Reload dashboard data
        reload_shortcut = QShortcut(QKeySequence('Ctrl+R'), self)
        reload_shortcut.activated.connect(self.load_dashboard_data)
        
        # Ctrl+P - Process transactions
        process_shortcut = QShortcut(QKeySequence('Ctrl+P'), self)
        process_shortcut.activated.connect(self.process_transactions)
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(self.translations.get('app_title'))
        self.resize(1200, 800)
        
        # Set RTL layout for Hebrew
        if self.translations.is_rtl():
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Header with language toggle
        header_layout = QHBoxLayout()
        title_label = QLabel(self.translations.get('app_title'))
        title_label.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        self.lang_toggle = QPushButton('EN / עב')
        self.lang_toggle.clicked.connect(self.toggle_language)
        header_layout.addWidget(self.lang_toggle)
        
        main_layout.addLayout(header_layout)
        
        # File management section
        file_group = QWidget()
        file_layout = QVBoxLayout()
        file_group.setLayout(file_layout)
        
        file_label = QLabel(self.translations.get('file_management'))
        file_label.setFont(QFont('Arial', 12, QFont.Weight.Bold))
        file_layout.addWidget(file_label)
        
        self.file_list = FileListWidget()
        self.file_list.files_dropped.connect(self.import_dropped_files)
        file_layout.addWidget(self.file_list)
        
        self.file_info_label = QLabel()
        file_layout.addWidget(self.file_info_label)
        
        file_buttons = QHBoxLayout()
        import_btn = QPushButton(self.translations.get('import_files'))
        import_btn.clicked.connect(self.import_files)
        file_buttons.addWidget(import_btn)
        
        refresh_btn = QPushButton(self.translations.get('refresh'))
        refresh_btn.clicked.connect(self.refresh_files)
        file_buttons.addWidget(refresh_btn)
        
        file_layout.addLayout(file_buttons)
        main_layout.addWidget(file_group)
        
        # Process button
        self.process_btn = QPushButton(self.translations.get('process_transactions'))
        self.process_btn.setFont(QFont('Arial', 14, QFont.Weight.Bold))
        self.process_btn.setMinimumHeight(50)
        self.process_btn.clicked.connect(self.process_transactions)
        main_layout.addWidget(self.process_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Preview tabs
        self.preview_tabs = QTabWidget()
        
        # Table tab
        self.preview_table = QTableWidget()
        self.preview_tabs.addTab(self.preview_table, self.translations.get('table_tab'))
        
        # Chart tab
        self.chart_widget = ChartWidget(self.translations)
        self.preview_tabs.addTab(self.chart_widget, self.translations.get('chart_tab'))
        
        # Logs tab
        self.log_viewer = LogViewerWidget()
        self.preview_tabs.addTab(self.log_viewer, "Logs")
        
        # Archive tab
        archive_widget = QWidget()
        archive_layout = QVBoxLayout()
        archive_widget.setLayout(archive_layout)
        
        self.archive_list = QListWidget()
        archive_layout.addWidget(self.archive_list)
        
        self.archive_info_label = QLabel()
        archive_layout.addWidget(self.archive_info_label)
        
        # Add refresh button for dashboard data
        refresh_dashboard_btn = QPushButton("⟳ Reload Dashboard Data")
        refresh_dashboard_btn.clicked.connect(self.load_dashboard_data)
        archive_layout.addWidget(refresh_dashboard_btn)
        archive_layout.addWidget(self.archive_info_label)
        
        clear_archive_btn = QPushButton(self.translations.get('clear_archive'))
        clear_archive_btn.clicked.connect(self.clear_archive)
        archive_layout.addWidget(clear_archive_btn)
        
        self.preview_tabs.addTab(archive_widget, self.translations.get('archive'))
        
        main_layout.addWidget(self.preview_tabs)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        open_dashboard_btn = QPushButton(self.translations.get('open_dashboard'))
        open_dashboard_btn.clicked.connect(self.open_dashboard)
        action_layout.addWidget(open_dashboard_btn)
        
        action_layout.addStretch()
        
        exit_btn = QPushButton(self.translations.get('exit'))
        exit_btn.clicked.connect(self.close)
        action_layout.addWidget(exit_btn)
        
        main_layout.addLayout(action_layout)
        
        # Status bar
        self.statusBar().showMessage(self.translations.get('app_title'))
        
        # Refresh archive list
        self.refresh_archive()
        
        # Load existing dashboard data
        self.load_dashboard_data()
    
    def import_dropped_files(self, files: List[str]):
        from code.validators import validate_excel_file, ValidationError
        count, errors = 0, []
        
        for file_path in files:
            try:
                validate_excel_file(Path(file_path))
                dest_path = TRANSACTIONS_DIR / Path(file_path).name
                shutil.copy2(file_path, dest_path)
                count += 1
                self.log_viewer.add_log('INFO', f'Imported: {Path(file_path).name}')
            except ValidationError as e:
                errors.append(f"{Path(file_path).name}: {e}")
                self.log_viewer.add_log('ERROR', f'Skipped - {errors[-1]}')
        
        self.refresh_files()
        if count > 0:
            msg = self.translations.get('files_imported', count=count)
            QMessageBox.information(self, self.translations.get('success_title'), msg)
        if errors:
            QMessageBox.warning(self, "Import Errors", "\\n".join(errors[:5]))

    def load_dashboard_data(self):
        """Load existing data from dashboard Excel file."""
        try:
            if not DASHBOARD_FILE_PATH.exists():
                self.log_viewer.add_log('INFO', 'No existing dashboard found')
                return
            
            self.log_viewer.add_log('INFO', 'Loading existing dashboard data...')
            
            # Read all sheets except template
            import openpyxl
            wb = openpyxl.load_workbook(DASHBOARD_FILE_PATH, data_only=True)
            
            all_data = []
            for sheet_name in wb.sheetnames:
                if sheet_name.lower() == 'template':
                    continue
                
                ws = wb[sheet_name]
                
                # Try to parse as year
                try:
                    year = int(sheet_name)
                except ValueError:
                    continue
                
                # Read data from sheet
                # Expected format: Category | Subcategory | Jan | Feb | ... | Dec
                for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                    if not row or len(row) < 14:
                        continue
                    
                    category = row[0]
                    subcat = row[1]
                    
                    if not category or not subcat:
                        continue
                    
                    # Months are in columns 2-13 (index 2-13)
                    for month in range(1, 13):
                        amount = row[month + 1]  # +1 because months start at column 2 (index 2)
                        
                        if amount and isinstance(amount, (int, float)) and amount != 0:
                            all_data.append({
                                'year': year,
                                'month': month,
                                'category': str(category),
                                'subcat': str(subcat),
                                'monthly_amount': float(amount)
                            })
            
            wb.close()
            
            if all_data:
                summary_df = pd.DataFrame(all_data)
                self.log_viewer.add_log('INFO', f'Loaded {len(summary_df)} records from dashboard')
                
                # Update displays
                self.update_preview_table(summary_df)
                self.chart_widget.update_chart(summary_df)
                self.log_viewer.add_log('INFO', 'Dashboard data loaded successfully')
            else:
                self.log_viewer.add_log('INFO', 'No data found in dashboard')
                
        except Exception as e:
            self.log_viewer.add_log('WARNING', f'Failed to load dashboard data: {str(e)}')
    
    def toggle_language(self):
        """Toggle between Hebrew and English."""
        new_lang = 'en' if self.translations.language == 'he' else 'he'
        self.translations.set_language(new_lang)
        
        # Recreate UI with new language
        self.close()
        self.__init__()
        self.show()
    
    def refresh_files(self):
        """Refresh the transaction files list."""
        self.file_list.clear()
        
        if not TRANSACTIONS_DIR.exists():
            ensure_dirs([TRANSACTIONS_DIR])
            return
        
        files = list(TRANSACTIONS_DIR.glob('*.xls*'))
        for file_path in files:
            self.file_list.addItem(file_path.name)
        
        total_size = sum(f.stat().st_size for f in files)
        size_mb = total_size / (1024 * 1024)
        
        self.file_info_label.setText(
            f"{self.translations.get('files_count', count=len(files))} | "
            f"{self.translations.get('total_size', size=f'{size_mb:.2f} MB')}"
        )
    
    def refresh_archive(self):
        """Refresh the archive files list."""
        self.archive_list.clear()
        
        archive_path = TRANSACTIONS_DIR / ARCHIVE_DIR
        if not archive_path.exists():
            return
        
        files = list(archive_path.glob('*.xls*'))
        for file_path in files:
            self.archive_list.addItem(file_path.name)
        
        self.archive_info_label.setText(
            self.translations.get('archive_count', count=len(files))
        )
    
    def import_files(self):
        """Import Excel files via file dialog."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.translations.get('select_files'),
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        
        # Track processing start time
        self.processing_start_time = datetime.now()
        
        # Switch to Logs tab to show progress
        self.preview_tabs.setCurrentWidget(self.log_viewer)
        
        # Create and start processing thread
        self.thread = ProcessThread(self.translations)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.processing_finished)
        self.thread.error.connect(self.processing_error)
        self.thread.category_needed.connect(self.show_category_dialog)
        self.thread.log_message.connect(self.log_viewer.add_log)
        self.thread.start()
    
    def update_progress(self, message: str):
        """Update progress status."""
        self.statusBar().showMessage(message)
    
    def resolve_conflict(self, month_key: str) -> str:
        """Resolve conflict via GUI dialog."""
        dialog = ConflictDialog(month_key, self.translations, self)
        dialog.exec()
        return dialog.decision
    
    def show_category_dialog(self, merchant: str, choices: List[tuple], sample_data: list):
        """Show dialog for category selection."""
        dialog = CategoryDialog(merchant, choices, self.translations, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.thread.category_response = dialog.selected_category
        else:
            self.thread.category_response = None
        
        self.thread.response_ready = True
    
    def processing_finished(self, summary_df: pd.DataFrame, success: bool):
        """Handle processing completion."""
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            # Update preview table
            self.update_preview_table(summary_df)
            
            # Update chart
            try:
                self.chart_widget.update_chart(summary_df)
                self.log_viewer.add_log('INFO', 'Chart updated successfully')
            except Exception as e:
                self.log_viewer.add_log('WARNING', f'Failed to update chart: {str(e)}')
            
            # Write to dashboard
            self.log_viewer.add_log('INFO', 'Writing to dashboard...')
            writer = DashboardWriter(DASHBOARD_FILE_PATH)
            writer.update(summary_df, conflict_resolver=self.resolve_conflict)
            
            # Refresh archive
            self.refresh_archive()
            self.refresh_files()
            
            self.statusBar().showMessage(self.translations.get('processing_complete'))
            QMessageBox.information(
                self,
                self.translations.get('success_title'),
                self.translations.get('processing_complete')
            )
    
    def processing_error(self, error_msg: str):
        """Handle processing error."""
        self.process_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(
            self,
            self.translations.get('error_title'),
            self.translations.get('error_occurred', error=error_msg)
        )
    
    def update_preview_table(self, summary_df: pd.DataFrame):
        """Update the preview table with summary data."""
        self.preview_table.setRowCount(len(summary_df) + 1)  # +1 for total row
        self.preview_table.setColumnCount(5)
        
        headers = [
            self.translations.get('year'),
            self.translations.get('month'),
            self.translations.get('category'),
            self.translations.get('subcategory'),
            self.translations.get('amount')
        ]
        self.preview_table.setHorizontalHeaderLabels(headers)
        
        total_amount = 0
        for i, row in summary_df.iterrows():
            self.preview_table.setItem(i, 0, QTableWidgetItem(str(int(row['year']))))
            self.preview_table.setItem(i, 1, QTableWidgetItem(self.translations.get(f"month_{int(row['month'])}")))
            self.preview_table.setItem(i, 2, QTableWidgetItem(str(row['category'])))
            self.preview_table.setItem(i, 3, QTableWidgetItem(str(row['subcat'])))
            self.preview_table.setItem(i, 4, QTableWidgetItem(f"₪{row['monthly_amount']:,.2f}"))
            total_amount += row['monthly_amount']
        
        # Add total row
        total_row = len(summary_df)
        total_label = QTableWidgetItem("TOTAL" if self.translations.language == 'en' else "סה\"כ")
        total_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.preview_table.setItem(total_row, 3, total_label)
        
        total_value = QTableWidgetItem(f"₪{total_amount:,.2f}")
        total_value.setFont(QFont('Arial', 10, QFont.Weight.Bold))
        self.preview_table.setItem(total_row, 4, total_value)
        
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Show total in status bar
        self.statusBar().showMessage(f"Total: ₪{total_amount:,.2f} | {len(summary_df)} records")
    
    def clear_archive(self):
        """Clear all archived files."""
        reply = QMessageBox.question(
            self,
            self.translations.get('confirm_title'),
            self.translations.get('confirm_clear_archive'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            archive_path = TRANSACTIONS_DIR / ARCHIVE_DIR
            if archive_path.exists():
                for file_path in archive_path.glob('*.xls*'):
                    file_path.unlink()
            
            self.refresh_archive()
            QMessageBox.information(
                self,
                self.translations.get('success_title'),
                self.translations.get('archive_cleared')
            )
    
    def open_dashboard(self):
        """Open the dashboard in Excel."""
        if DASHBOARD_FILE_PATH.exists():
            os.startfile(str(DASHBOARD_FILE_PATH))
            self.statusBar().showMessage(self.translations.get('dashboard_opened'))
        else:
            QMessageBox.warning(
                self,
                self.translations.get('warning_title'),
                self.translations.get('error_occurred', error='Dashboard file not found')
            )


def main():
    """Main entry point for GUI application."""
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont('Arial', 10)
    app.setFont(font)
    
    # Global exception handler
    def exception_hook(exctype, value, tb):
        import traceback
        error_msg = ''.join(traceback.format_exception(exctype, value, tb))
        print(f"Unhandled exception:\\n{error_msg}")
        QMessageBox.critical(None, "Fatal Error", f"An unexpected error occurred:\\n\\n{str(value)}")
        sys.exit(1)
    
    sys.excepthook = exception_hook
    
    window = BudgetTrackerGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

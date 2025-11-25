# ===== code/translations.py =====
"""
Bilingual translation module for Hebrew/English UI support.
"""

class Translations:
    """Manages UI text translations for Hebrew and English."""
    
    # Hebrew translations
    HE = {
        # Window titles
        'app_title': 'מעקב תקציב',
        'category_dialog_title': 'בחר קטגוריה',
        'confirm_title': 'אישור',
        'error_title': 'שגיאה',
        'success_title': 'הצלחה',
        'warning_title': 'אזהרה',
        
        # File management section
        'file_management': 'ניהול קבצים',
        'import_files': 'ייבא קבצים',
        'refresh': 'רענן',
        'files_count': 'קבצים: {count}',
        'total_size': 'גודל כולל: {size}',
        'drag_drop_hint': 'גרור קבצי Excel לכאן',
        
        # Process section
        'process_transactions': 'עבד עסקאות',
        'processing': 'מעבד...',
        'processing_complete': 'עיבוד הושלם',
        
        # Category learning
        'new_merchant': 'בית עסק חדש: {merchant}',
        'select_category': 'בחר קטגוריה',
        'category': 'קטגוריה',
        'subcategory': 'תת-קטגוריה',
        'save': 'שמור',
        'cancel': 'ביטול',
        'exit': 'יציאה',
        
        # Preview section
        'preview': 'תצוגה מקדימה',
        'table_tab': 'טבלה',
        'chart_tab': 'גרף',
        'year': 'שנה',
        'month': 'חודש',
        'amount': 'סכום',
        'total_amount': 'סכום כולל: ₪{amount:,.2f}',
        
        # Archive section
        'archive': 'ארכיון',
        'clear_archive': 'נקה ארכיון',
        'archive_count': 'קבצים בארכיון: {count}',
        'confirm_clear_archive': 'האם אתה בטוח שברצונך למחוק את כל הקבצים בארכיון?',
        
        # Actions
        'open_dashboard': 'פתח דשבורד ב-Excel',
        'export_chart': 'ייצא גרף',
        
        # Messages
        'no_files': 'לא נמצאו קבצי עסקאות',
        'select_files': 'בחר קבצי Excel',
        'file_imported': 'קובץ יובא בהצלחה',
        'files_imported': '{count} קבצים יובאו בהצלחה',
        'dashboard_opened': 'הדשבורד נפתח ב-Excel',
        'chart_exported': 'הגרף יוצא בהצלחה',
        'archive_cleared': 'הארכיון נוקה בהצלחה',
        'error_occurred': 'אירעה שגיאה: {error}',
        
        # Months
        'month_1': 'ינואר',
        'month_2': 'פברואר',
        'month_3': 'מרץ',
        'month_4': 'אפריל',
        'month_5': 'מאי',
        'month_6': 'יוני',
        'month_7': 'יולי',
        'month_8': 'אוגוסט',
        'month_9': 'ספטמבר',
        'month_10': 'אוקטובר',
        'month_11': 'נובמבר',
        'month_12': 'דצמבר',
    }
    
    # English translations
    EN = {
        # Window titles
        'app_title': 'Budget Tracker',
        'category_dialog_title': 'Select Category',
        'confirm_title': 'Confirm',
        'error_title': 'Error',
        'success_title': 'Success',
        'warning_title': 'Warning',
        
        # File management section
        'file_management': 'File Management',
        'import_files': 'Import Files',
        'refresh': 'Refresh',
        'files_count': 'Files: {count}',
        'total_size': 'Total Size: {size}',
        'drag_drop_hint': 'Drag Excel files here',
        
        # Process section
        'process_transactions': 'Process Transactions',
        'processing': 'Processing...',
        'processing_complete': 'Processing Complete',
        
        # Category learning
        'new_merchant': 'New Merchant: {merchant}',
        'select_category': 'Select Category',
        'category': 'Category',
        'subcategory': 'Subcategory',
        'save': 'Save',
        'cancel': 'Cancel',
        'exit': 'Exit',
        
        # Preview section
        'preview': 'Preview',
        'table_tab': 'Table',
        'chart_tab': 'Chart',
        'year': 'Year',
        'month': 'Month',
        'amount': 'Amount',
        'total_amount': 'Total Amount: ₪{amount:,.2f}',
        
        # Archive section
        'archive': 'Archive',
        'clear_archive': 'Clear Archive',
        'archive_count': 'Archived Files: {count}',
        'confirm_clear_archive': 'Are you sure you want to delete all archived files?',
        
        # Actions
        'open_dashboard': 'Open Dashboard in Excel',
        'export_chart': 'Export Chart',
        
        # Messages
        'no_files': 'No transaction files found',
        'select_files': 'Select Excel Files',
        'file_imported': 'File imported successfully',
        'files_imported': '{count} files imported successfully',
        'dashboard_opened': 'Dashboard opened in Excel',
        'chart_exported': 'Chart exported successfully',
        'archive_cleared': 'Archive cleared successfully',
        'error_occurred': 'An error occurred: {error}',
        
        # Months
        'month_1': 'January',
        'month_2': 'February',
        'month_3': 'March',
        'month_4': 'April',
        'month_5': 'May',
        'month_6': 'June',
        'month_7': 'July',
        'month_8': 'August',
        'month_9': 'September',
        'month_10': 'October',
        'month_11': 'November',
        'month_12': 'December',
    }
    
    def __init__(self, language='he'):
        """
        Initialize translations with specified language.
        
        Args:
            language: 'he' for Hebrew or 'en' for English
        """
        self.language = language
        self._translations = self.HE if language == 'he' else self.EN
    
    def get(self, key, **kwargs):
        """
        Get translated text for a key with optional formatting.
        
        Args:
            key: Translation key
            **kwargs: Format arguments for string formatting
            
        Returns:
            Translated and formatted string
        """
        text = self._translations.get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text
    
    def set_language(self, language):
        """
        Change the current language.
        
        Args:
            language: 'he' for Hebrew or 'en' for English
        """
        self.language = language
        self._translations = self.HE if language == 'he' else self.EN
    
    def is_rtl(self):
        """Check if current language is right-to-left."""
        return self.language == 'he'

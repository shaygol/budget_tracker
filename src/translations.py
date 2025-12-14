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
        'refresh_all': 'רענן דשבורד',
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
        'skip': 'דלג',
        'exit': 'יציאה',

        # Preview section
        'year_overview': 'תצוגה שנתית',
        'year_overview_category': 'תצוגה שנתית - {category}',
        'table_tab': 'טבלה',
        'chart_tab': 'גרף',
        'year': 'שנה',
        'month': 'חודש',
        'amount': 'סכום',
        'total_amount': 'סכום כולל: ₪{amount:,.2f}',
        'total_spending': 'סה\"כ הוצאות',
        'avg_monthly': 'ממוצע חודשי',
        'top_category_label': 'קטגוריה מובילה',
        'vs_average': 'לעומת הממוצע',
        'not_available': 'לא זמין',

        # Archive section
        'archive': 'ארכיון',
        'clear_archive': 'נקה ארכיון',
        'archive_count': 'קבצים בארכיון: {count}',
        'confirm_clear_archive': 'האם אתה בטוח שברצונך למחוק את כל הקבצים בארכיון?',

        # Actions
        'open_dashboard': 'פתח דשבורד באקסל',
        'export_chart': 'ייצא גרף',
        'manage_categories': 'נהל קטגוריות',
        'category_management_title': 'ניהול קטגוריות',
        'search': 'חיפוש:',
        'search_merchants': 'חפש בתי עסק...',
        'clear': 'נקה',
        'merchant': 'בית עסק',
        'edit': 'ערוך',
        'delete': 'מחק',
        'close': 'סגור',
        'back': 'חזור',
        'show_all_categories': 'הצג את כל הקטגוריות',
        'showing_all_categories': 'מציג את כל הקטגוריות',
        'filtered_by_category': 'מסונן לפי: {category}',
        'category_details': 'פרטי קטגוריה',
        'reprocess_question': 'האם ברצונך לעבד מחדש את העסקאות כעת כדי לעדכן את הדשבורד?',
        'reprocess_note': '(תוכל גם לעשות זאת מאוחר יותר על ידי לחיצה על "עבד עסקאות")',
        'mapping_updated': 'מיפוי קטגוריות עודכן',
        'mapping_deleted': 'מיפוי קטגוריה נמחק',
        'reprocess_to_update': 'ייתכן שתצטרך לעבד מחדש עסקאות כדי שהשינויים יופיעו בדשבורד',
        'edit_category_from_table': 'ערוך קטגוריה מהטבלה',
        'select_category_to_edit': 'בחר קטגוריה לעריכה',
        'edit_transaction_category': 'ערוך קטגוריית עסקה',
        'current_category': 'קטגוריה נוכחית',
        'new_category': 'קטגוריה חדשה',
        'reprocess_required': 'נדרש עיבוד מחדש',
        'reprocess_required_note': 'על מנת שהשינויים יופיעו בדשבורד, יש לעבד מחדש את העסקאות',

        # Messages
        'no_files': 'לא נמצאו קבצי עסקאות',
        'select_files': 'בחר קבצי Excel',
        'file_imported': 'קובץ יובא בהצלחה',
        'files_imported': '{count} קבצים יובאו בהצלחה',
        'dashboard_opened': 'הדשבורד נפתח באקסל',
        'chart_exported': 'הגרף יוצא בהצלחה',
        'archive_cleared': 'הארכיון נוקה בהצלחה',
        'error_occurred': 'אירעה שגיאה: {error}',
        'timeout_error': 'זמן העיבוד פג - הפעולה ארכה יותר מדי זמן. נסה שוב עם קבצים קטנים יותר.',

        # Conflict dialog
        'conflict_title': 'התנגשות נתונים',
        'conflict_message': 'נתונים כבר קיימים עבור {month_key}.\nכיצד לטפל בכך?',
        'override_btn': 'החלף (החלף את הקיים)',
        'add_btn': 'הוסף (חבר לקיים)',
        'skip_btn': 'דלג (שמור את הקיים)',

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
        'refresh_all': 'Refresh Dashboard',
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
        'skip': 'Skip',
        'exit': 'Exit',

        # Preview section
        'year_overview': 'Year Overview',
        'year_overview_category': 'Year Overview - {category}',
        'table_tab': 'Table',
        'chart_tab': 'Chart',
        'year': 'Year',
        'month': 'Month',
        'amount': 'Amount',
        'total_amount': 'Total Amount: ₪{amount:,.2f}',
        'total_spending': 'Total Spending',
        'avg_monthly': 'Avg Monthly',
        'top_category_label': 'Top Category',
        'vs_average': 'vs Avg',
        'not_available': 'N/A',

        # Archive section
        'archive': 'Archive',
        'clear_archive': 'Clear Archive',
        'archive_count': 'Archived Files: {count}',
        'confirm_clear_archive': 'Are you sure you want to delete all archived files?',

        # Actions
        'open_dashboard': 'Open Dashboard in Excel',
        'export_chart': 'Export Chart',
        'manage_categories': 'Manage Categories',
        'category_management_title': 'Category Management',
        'search': 'Search:',
        'search_merchants': 'Search merchants...',
        'clear': 'Clear',
        'merchant': 'Merchant',
        'edit': 'Edit',
        'delete': 'Delete',
        'close': 'Close',
        'back': 'Back',
        'show_all_categories': 'Show All Categories',
        'showing_all_categories': 'Showing all categories',
        'filtered_by_category': 'Filtered by: {category}',
        'category_details': 'Category Details',
        'reprocess_question': 'Would you like to reprocess transactions now to update the dashboard?',
        'reprocess_note': '(You can also do this later by clicking "Process Transactions")',
        'mapping_updated': 'Category mapping updated',
        'mapping_deleted': 'Category mapping deleted',
        'reprocess_to_update': 'You may need to reprocess transactions for changes to appear in the dashboard',
        'edit_category_from_table': 'Edit Category from Table',
        'select_category_to_edit': 'Select category to edit',
        'edit_transaction_category': 'Edit Transaction Category',
        'current_category': 'Current Category',
        'new_category': 'New Category',
        'reprocess_required': 'Reprocessing Required',
        'reprocess_required_note': 'To see changes in the dashboard, transactions need to be reprocessed',
        'no_data': 'No data available',
        'no_data_found': 'No data found for category',
        'total': 'Total',
        'info_title': 'Information',
        'settings': 'Settings',
        'log_level': 'Log Level',
        'log_level_info': 'Controls which log messages are displayed. DEBUG shows all messages, ERROR shows only errors.',
        'restore_defaults': 'Restore Defaults',
        'restore_defaults_confirm': 'Restore all settings to defaults?',
        'defaults_restored': 'Default settings restored.',
        'settings_saved': 'Settings saved successfully.\n\nLog level changed. New messages will use the new level.',

        # Messages
        'no_files': 'No transaction files found',
        'select_files': 'Select Excel Files',
        'file_imported': 'File imported successfully',
        'files_imported': '{count} files imported successfully',
        'dashboard_opened': 'Dashboard opened in Excel',
        'chart_exported': 'Chart exported successfully',
        'archive_cleared': 'Archive cleared successfully',
        'error_occurred': 'An error occurred: {error}',
        'timeout_error': 'Processing timeout - operation took too long. Try again with smaller files.',

        # Conflict dialog
        'conflict_title': 'Data Conflict',
        'conflict_message': 'Data already exists for {month_key}.\nHow should we handle it?',
        'override_btn': 'Override (Replace existing)',
        'add_btn': 'Add (Sum with existing)',
        'skip_btn': 'Skip (Keep existing)',

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

    def __init__(self, language: str = 'he') -> None:
        """
        Initialize translations with specified language.

        Args:
            language: 'he' for Hebrew or 'en' for English
        """
        self.language = language
        self._translations = self.HE if language == 'he' else self.EN

    def get(self, key: str, default: str = None, **kwargs) -> str:
        """
        Get translated text for a key with optional formatting.

        Args:
            key: Translation key
            default: Default value if key not found (defaults to key itself)
            **kwargs: Format arguments for string formatting

        Returns:
            Translated and formatted string
        """
        if default is None:
            default = key
        text = self._translations.get(key, default)
        if kwargs:
            return text.format(**kwargs)
        return text

    def set_language(self, language: str) -> None:
        """
        Change the current language.

        Args:
            language: 'he' for Hebrew or 'en' for English
        """
        self.language = language
        self._translations = self.HE if language == 'he' else self.EN

    def is_rtl(self) -> bool:
        """Check if current language is right-to-left."""
        return self.language == 'he'

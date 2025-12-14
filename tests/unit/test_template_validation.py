"""
Unit tests for template validation in category_manager.py
"""

import pytest
import tempfile
from pathlib import Path
from openpyxl import Workbook
from src.category_manager import (
    safe_get_cell_value,
    normalize_category_name,
    is_header_value,
    ValidationResult,
    CategoryManager
)


class TestSafeGetCellValue:
    """Tests for safe_get_cell_value function."""

    def test_normal_string_value(self):
        """Test reading normal string values."""
        wb = Workbook()
        ws = wb.active
        ws['A1'] = 'Test Category'
        assert safe_get_cell_value(ws['A1']) == 'Test Category'

    def test_numeric_value(self):
        """Test reading numeric values."""
        wb = Workbook()
        ws = wb.active
        ws['A1'] = 123
        assert safe_get_cell_value(ws['A1']) == '123'

    def test_none_value(self):
        """Test handling None values."""
        wb = Workbook()
        ws = wb.active
        ws['A1'] = None
        assert safe_get_cell_value(ws['A1']) is None

    def test_empty_string(self):
        """Test handling empty strings."""
        wb = Workbook()
        ws = wb.active
        ws['A1'] = '   '
        assert safe_get_cell_value(ws['A1']) is None

    def test_excel_error(self):
        """Test handling Excel errors."""
        wb = Workbook()
        ws = wb.active
        ws['A1'] = '#REF!'
        assert safe_get_cell_value(ws['A1']) is None

    def test_whitespace_trimming(self):
        """Test that whitespace is properly trimmed."""
        wb = Workbook()
        ws = wb.active
        ws['A1'] = '  Test  '
        assert safe_get_cell_value(ws['A1']) == 'Test'


class TestNormalizeCategoryName:
    """Tests for normalize_category_name function."""

    def test_normal_name(self):
        """Test normalizing a normal category name."""
        assert normalize_category_name('הוצאות בית') == 'הוצאות בית'

    def test_whitespace_trimming(self):
        """Test trimming leading/trailing whitespace."""
        assert normalize_category_name('  קניות  ') == 'קניות'

    def test_multiple_spaces_collapse(self):
        """Test collapsing multiple spaces."""
        assert normalize_category_name('קניות    חודשיות') == 'קניות חודשיות'

    def test_none_input(self):
        """Test handling None input."""
        assert normalize_category_name(None) is None

    def test_empty_string(self):
        """Test handling empty string."""
        assert normalize_category_name('') is None
        assert normalize_category_name('   ') is None


class TestIsHeaderValue:
    """Tests for is_header_value function."""

    def test_hebrew_category_header(self):
        """Test detecting Hebrew category headers."""
        assert is_header_value('נושא', 'category') is True
        assert is_header_value('נושא הוצאה', 'category') is True

    def test_english_category_header(self):
        """Test detecting English category headers."""
        assert is_header_value('Category', 'category') is True
        assert is_header_value('category', 'category') is True

    def test_hebrew_subcategory_header(self):
        """Test detecting Hebrew subcategory headers."""
        assert is_header_value('פירוט', 'subcategory') is True
        assert is_header_value('פירוט הוצאות', 'subcategory') is True

    def test_non_header_value(self):
        """Test that non-header values return False."""
        assert is_header_value('קניות', 'category') is False
        assert is_header_value('מזון', 'subcategory') is False

    def test_none_value(self):
        """Test handling None."""
        assert is_header_value(None, 'category') is False


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_initial_state(self):
        """Test ValidationResult initial state."""
        result = ValidationResult()
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_add_error(self):
        """Test adding errors."""
        result = ValidationResult()
        result.add_error('Test error')
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == 'Test error'

    def test_add_warning(self):
        """Test adding warnings."""
        result = ValidationResult()
        result.add_warning('Test warning')
        assert result.is_valid is True  # Warnings don't invalidate
        assert len(result.warnings) == 1
        assert result.warnings[0] == 'Test warning'


class TestTemplateValidation:
    """Tests for template structure validation."""

    def create_test_dashboard(self, data):
        """Helper to create a test dashboard with given data."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_file.close()

        wb = Workbook()
        ws = wb.active
        ws.title = 'Template'

        # Add headers
        ws['A1'] = 'נושא הוצאה'
        ws['B1'] = 'פירוט הוצאות'

        # Add data
        for i, (cat, subcat) in enumerate(data, start=2):
            ws[f'A{i}'] = cat
            ws[f'B{i}'] = subcat

        wb.save(temp_file.name)
        return Path(temp_file.name)

    def test_valid_template(self, tmp_path):
        """Test validation of a valid template."""
        data = [
            ('הוצאות בית', 'חשמל'),
            ('', 'גז'),
            ('קניות', 'מזון'),
            ('', 'ביגוד'),
        ]

        dashboard_path = self.create_test_dashboard(data)
        categories_path = tmp_path / 'categories.json'
        categories_path.write_text('{}')

        try:
            manager = CategoryManager(categories_path, dashboard_path)
            validation = manager.validate_template_structure()

            assert validation.is_valid is True
            assert len(validation.errors) == 0
        finally:
            dashboard_path.unlink()

    def test_duplicate_category(self, tmp_path):
        """Test detection of duplicate categories."""
        data = [
            ('הוצאות בית', 'חשמל'),
            ('קניות', 'מזון'),
            ('הוצאות בית', 'מים'),  # Duplicate category
        ]

        dashboard_path = self.create_test_dashboard(data)
        categories_path = tmp_path / 'categories.json'
        categories_path.write_text('{}')

        try:
            manager = CategoryManager(categories_path, dashboard_path, strict_validation=False)
            validation = manager.validate_template_structure()

            assert validation.is_valid is False
            assert any('Duplicate category' in err for err in validation.errors)
        finally:
            dashboard_path.unlink()

    def test_duplicate_subcategory(self, tmp_path):
        """Test detection of duplicate subcategories within same category."""
        data = [
            ('הוצאות בית', 'חשמל'),
            ('', 'גז'),
            ('', 'חשמל'),  # Duplicate subcategory in same category
        ]

        dashboard_path = self.create_test_dashboard(data)
        categories_path = tmp_path / 'categories.json'
        categories_path.write_text('{}')

        try:
            manager = CategoryManager(categories_path, dashboard_path, strict_validation=False)
            validation = manager.validate_template_structure()

            assert validation.is_valid is False
            assert any('Duplicate subcategory' in err for err in validation.errors)
        finally:
            dashboard_path.unlink()

    def test_empty_template(self, tmp_path):
        """Test detection of empty template."""
        data = []  # No data

        dashboard_path = self.create_test_dashboard(data)
        categories_path = tmp_path / 'categories.json'
        categories_path.write_text('{}')

        try:
            manager = CategoryManager(categories_path, dashboard_path, strict_validation=False)
            validation = manager.validate_template_structure()

            assert validation.is_valid is False
            assert any('empty' in err.lower() for err in validation.errors)
        finally:
            dashboard_path.unlink()

    def test_category_without_subcategories_warning(self, tmp_path):
        """Test warning for categories with no subcategories."""
        data = [
            ('הוצאות בית', None),  # Category with no subcategory
        ]

        dashboard_path = self.create_test_dashboard(data)
        categories_path = tmp_path / 'categories.json'
        categories_path.write_text('{}')

        try:
            manager = CategoryManager(categories_path, dashboard_path)
            validation = manager.validate_template_structure()

            # Should have warnings but might still be valid depending on how we handle it
            assert any('no subcategories' in warn for warn in validation.warnings)
        finally:
            dashboard_path.unlink()

    def test_single_subcategory_warning(self, tmp_path):
        """Test warning for categories with only one subcategory."""
        data = [
            ('הוצאות בית', 'חשמל'),  # Only one subcategory
        ]

        dashboard_path = self.create_test_dashboard(data)
        categories_path = tmp_path / 'categories.json'
        categories_path.write_text('{}')

        try:
            manager = CategoryManager(categories_path, dashboard_path)
            validation = manager.validate_template_structure()

            assert any('only one subcategory' in warn for warn in validation.warnings)
        finally:
            dashboard_path.unlink()

    def test_long_category_name_warning(self, tmp_path):
        """Test warning for very long category names."""
        long_name = 'א' * 150  # 150 characters
        data = [
            (long_name, 'test'),
        ]

        dashboard_path = self.create_test_dashboard(data)
        categories_path = tmp_path / 'categories.json'
        categories_path.write_text('{}')

        try:
            manager = CategoryManager(categories_path, dashboard_path)
            validation = manager.validate_template_structure()

            assert any('very long' in warn for warn in validation.warnings)
        finally:
            dashboard_path.unlink()

    def test_suspicious_characters_warning(self, tmp_path):
        """Test warning for suspicious characters in category names."""
        data = [
            ('קניות|מזון', 'test'),  # Contains pipe character
            ('', 'test2;data'),  # Contains semicolon
        ]

        dashboard_path = self.create_test_dashboard(data)
        categories_path = tmp_path / 'categories.json'
        categories_path.write_text('{}')

        try:
            manager = CategoryManager(categories_path, dashboard_path, strict_validation=False)
            validation = manager.validate_template_structure()

            assert any('suspicious characters' in warn for warn in validation.warnings)
        finally:
            dashboard_path.unlink()

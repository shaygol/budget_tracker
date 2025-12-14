"""
Smoke tests to verify application deployment and required files.
These tests verify the actual file system state, not mocked logic.
"""
import pytest
from pathlib import Path
from src.config import (
    DASHBOARD_FILE_PATH,
    CATEGORIES_FILE_PATH,
    USER_FILES_DIR,
    BACKUPS_ROOT,
    ARCHIVE_DIR,
    DASHBOARD_BACKUP_DIR,
    OUTPUT_DIR
)


class TestDeploymentSmoke:
    """Verify the application is correctly deployed."""

    def test_user_files_directory_exists(self):
        """Verify UserFiles directory exists."""
        assert USER_FILES_DIR.exists(), \
            f"UserFiles directory not found at {USER_FILES_DIR}"
        assert USER_FILES_DIR.is_dir(), \
            f"{USER_FILES_DIR} exists but is not a directory"

    def test_dashboard_file_exists(self):
        """Verify dashboard.xlsx exists in the correct location."""
        assert DASHBOARD_FILE_PATH.exists(), \
            f"Dashboard file not found at {DASHBOARD_FILE_PATH}.\n" \
            f"Expected location: UserFiles/dashboard.xlsx\n" \
            f"Please ensure the file has been moved from the root directory."

    def test_categories_file_exists(self):
        """Verify categories.json exists in the correct location."""
        assert CATEGORIES_FILE_PATH.exists(), \
            f"Categories file not found at {CATEGORIES_FILE_PATH}.\n" \
            f"Expected location: UserFiles/categories.json\n" \
            f"Please ensure the file has been moved from the root directory."

    def test_backup_directories_exist(self):
        """Verify backup directory structure exists."""
        assert BACKUPS_ROOT.exists(), \
            f"Backups directory not found at {BACKUPS_ROOT}"
        assert ARCHIVE_DIR.exists(), \
            f"Archive directory not found at {ARCHIVE_DIR}"
        assert DASHBOARD_BACKUP_DIR.exists(), \
            f"Dashboard backup directory not found at {DASHBOARD_BACKUP_DIR}"

    def test_output_directory_exists(self):
        """Verify output directory exists for logs."""
        assert OUTPUT_DIR.exists(), \
            f"Output directory not found at {OUTPUT_DIR}"


class TestApplicationStartup:
    """Verify the application can start successfully."""

    def test_import_main_module(self):
        """Verify main module can be imported without errors."""
        try:
            import main
        except Exception as e:
            pytest.fail(f"Failed to import main module: {e}")

    def test_import_core_modules(self):
        """Verify all core modules can be imported."""
        modules = [
            'src.config',
            'src.file_manager',
            'src.normalizer',
            'src.category_manager',
            'src.dashboard_writer',
            'src.previewer',
            'src.validators',
            'src.translations'
        ]

        for module_name in modules:
            try:
                __import__(module_name)
            except Exception as e:
                pytest.fail(f"Failed to import {module_name}: {e}")

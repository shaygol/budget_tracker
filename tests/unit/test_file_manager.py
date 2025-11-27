# ===== tests/test_file_manager.py =====
"""
Tests for file management utilities.
"""
import pytest
import pandas as pd
from pathlib import Path
from code.file_manager import ensure_dirs


def test_load_transaction_files_empty_directory(temp_dir):
    """Test loading from an empty directory."""
    from code.file_manager import load_transaction_files
    result = load_transaction_files(temp_dir)

    assert result == []


def test_ensure_dirs_creates_directories(temp_dir):
    """Test that ensure_dirs creates directories."""
    new_dir = temp_dir / 'new_folder'

    ensure_dirs([new_dir])

    assert new_dir.exists()
    assert new_dir.is_dir()


def test_ensure_dirs_handles_existing(temp_dir):
    """Test that ensure_dirs handles existing directories."""
    existing_dir = temp_dir / 'existing'
    existing_dir.mkdir()

    # Should not raise an error
    ensure_dirs([existing_dir])

    assert existing_dir.exists()

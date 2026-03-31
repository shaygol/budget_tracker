"""Tests for SHA256-based duplicate file detection."""
import pytest
import shutil
import tempfile
from pathlib import Path
import pandas as pd
from gui_app import calculate_file_hash


class TestDuplicateDetection:
    """Tests for duplicate file detection using SHA256 hashing."""
    
    def test_identical_files_produce_same_hash(self, tmp_path):
        """Test that identical files produce the same SHA256 hash."""
        df = pd.DataFrame({
            'transaction_date': ['2024-01-01'],
            'merchant': ['Test Merchant'],
            'amount': [100.0]
        })
        
        file1 = tmp_path / "file1.xlsx"
        file2 = tmp_path / "file2.xlsx"
        
        df.to_excel(file1, index=False)
        shutil.copy2(file1, file2)
        
        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)
        
        assert hash1 == hash2, "Identical files should produce same hash"
        assert len(hash1) == 64, "SHA256 hash should be 64 characters"
    
    def test_different_files_produce_different_hashes(self, tmp_path):
        """Test that different files produce different hashes."""
        df1 = pd.DataFrame({
            'transaction_date': ['2024-01-01'],
            'merchant': ['Merchant A'],
            'amount': [100.0]
        })
        
        df2 = pd.DataFrame({
            'transaction_date': ['2024-01-01'],
            'merchant': ['Merchant B'],
            'amount': [200.0]
        })
        
        file1 = tmp_path / "file1.xlsx"
        file2 = tmp_path / "file2.xlsx"
        
        df1.to_excel(file1, index=False)
        df2.to_excel(file2, index=False)
        
        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)
        
        assert hash1 != hash2, "Different files should produce different hashes"
    
    def test_same_content_different_name_same_hash(self, tmp_path):
        """Test that files with same content but different names have same hash."""
        df = pd.DataFrame({
            'transaction_date': ['2024-01-01'],
            'merchant': ['Test Merchant'],
            'amount': [100.0]
        })
        
        file1 = tmp_path / "january.xlsx"
        file2 = tmp_path / "transactions.xlsx"
        
        df.to_excel(file1, index=False)
        shutil.copy2(file1, file2)
        
        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)
        
        assert hash1 == hash2, "Same content should produce same hash regardless of filename"
    
    def test_modified_file_produces_different_hash(self, tmp_path):
        """Test that modifying a file changes its hash."""
        df_original = pd.DataFrame({
            'transaction_date': ['2024-01-01'],
            'merchant': ['Test Merchant'],
            'amount': [100.0]
        })
        
        file_path = tmp_path / "test.xlsx"
        df_original.to_excel(file_path, index=False)
        original_hash = calculate_file_hash(file_path)
        
        # Modify the file
        df_modified = pd.DataFrame({
            'transaction_date': ['2024-01-01'],
            'merchant': ['Test Merchant'],
            'amount': [100.0],
            'notes': ['New column']  # Add a column
        })
        
        df_modified.to_excel(file_path, index=False)
        modified_hash = calculate_file_hash(file_path)
        
        assert original_hash != modified_hash, "Modified file should have different hash"
    
    def test_hash_calculation_is_consistent(self, tmp_path):
        """Test that hash calculation is consistent across multiple calls."""
        df = pd.DataFrame({
            'transaction_date': ['2024-01-01'],
            'merchant': ['Test Merchant'],
            'amount': [100.0]
        })
        
        file_path = tmp_path / "test.xlsx"
        df.to_excel(file_path, index=False)
        
        # Calculate hash multiple times
        hash1 = calculate_file_hash(file_path)
        hash2 = calculate_file_hash(file_path)
        hash3 = calculate_file_hash(file_path)
        
        assert hash1 == hash2 == hash3, "Hash should be consistent across calls"
    
    def test_large_file_hash_calculation(self, tmp_path):
        """Test hash calculation on larger files."""
        # Create a larger dataset
        df = pd.DataFrame({
            'transaction_date': pd.date_range('2024-01-01', periods=1000),
            'merchant': [f'Merchant {i}' for i in range(1000)],
            'amount': [100.0 + i for i in range(1000)]
        })
        
        file_path = tmp_path / "large.xlsx"
        df.to_excel(file_path, index=False)
        
        hash_result = calculate_file_hash(file_path)
        
        assert hash_result is not None, "Should calculate hash for large files"
        assert len(hash_result) == 64, "Hash should be 64 characters"

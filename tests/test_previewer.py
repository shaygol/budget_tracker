# ===== tests/test_previewer.py =====
"""
Tests for the Previewer class.
"""
import pytest
import pandas as pd
from code.previewer import Previewer


def test_previewer_creates_summary(sample_normalized_df):
    """Test that previewer creates a summary grouped by year/month/category."""
    previewer = Previewer()
    
    summary = previewer.preview(sample_normalized_df, confirm=False)
    
    assert 'year' in summary.columns
    assert 'month' in summary.columns
    assert 'category' in summary.columns
    assert 'subcat' in summary.columns
    assert 'monthly_amount' in summary.columns


def test_previewer_sums_amounts(sample_normalized_df):
    """Test that previewer correctly sums amounts."""
    previewer = Previewer()
    
    summary = previewer.preview(sample_normalized_df, confirm=False)
    
    # Should sum the two Amazon entries (150 + 200 = 350)
    shopping_total = summary[summary['category'] == 'Shopping']['monthly_amount'].sum()
    assert shopping_total == 350.0


def test_previewer_no_confirm_mode():
    """Test that previewer works without confirmation."""
    previewer = Previewer()
    df = pd.DataFrame({
        'year': [2024],
        'month': [1],
        'category': ['Shopping'],
        'subcat': ['Online'],
        'monthly_amount': [100.0]
    })
    
    # Should not block
    summary = previewer.preview(df, confirm=False)
    
    assert len(summary) == 1
    assert summary['monthly_amount'].sum() == 100.0


def test_previewer_groups_by_all_dimensions():
    """Test that previewer groups by year, month, category, and subcat."""
    previewer = Previewer()
    df = pd.DataFrame({
        'year': [2024, 2024, 2024, 2024],
        'month': [1, 1, 2, 2],
        'category': ['Food', 'Food', 'Shopping', 'Shopping'],
        'subcat': ['Groceries', 'Groceries', 'Online', 'Online'],
        'monthly_amount': [50.0, 50.0, 100.0, 100.0]
    })
    
    summary = previewer.preview(df, confirm=False)
    
    # Should have 2 rows (Jan Food + Feb Shopping)
    assert len(summary) == 2
    assert summary['monthly_amount'].tolist() == [100.0, 200.0]

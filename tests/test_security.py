import pytest
import pandas as pd
from code.normalizer import Normalizer
from code.validators import sanitize_merchant_name

class TestSecurity:
    """Integration tests for security features."""

    def test_formula_injection_prevention_in_normalizer(self):
        """Test that Normalizer correctly sanitizes malicious merchant names."""
        # Create a DataFrame with malicious payloads
        data = {
            'transaction_date': ['01/01/2023', '02/01/2023', '03/01/2023'],
            'merchant': [
                '=SUM(A1:A100)',      # Classic formula injection
                '+cmd| /c calc.exe',  # Command injection attempt
                'Normal Merchant'     # Safe data
            ],
            'amount': [100, 200, 300]
        }
        df = pd.DataFrame(data)
        
        # Normalize
        normalizer = Normalizer()
        normalized_df = normalizer.normalize(df)
        
        # Verify sanitization
        merchants = normalized_df['merchant'].tolist()
        
        # 1. Formula should be quoted
        assert merchants[0] == "'=SUM(A1:A100)"
        assert merchants[0].startswith("'")
        
        # 2. Command injection should be quoted
        assert merchants[1] == "'+cmd| /c calc.exe"
        assert merchants[1].startswith("'")
        
        # 3. Normal merchant should be untouched
        assert merchants[2] == "Normal Merchant"

    def test_large_category_name_handling(self):
        """Test handling of extremely long strings."""
        long_string = "A" * 10000
        sanitized = sanitize_merchant_name(long_string)
        
        # Should be truncated to MAX_MERCHANT_NAME_LENGTH (200)
        assert len(sanitized) == 200
        assert sanitized == "A" * 200

    def test_special_characters_handling(self):
        """Test that special characters don't break the normalizer."""
        data = {
            'transaction_date': ['01/01/2023'],
            'merchant': ['Merchant & Sons < > " \''],
            'amount': [100]
        }
        df = pd.DataFrame(data)
        
        normalizer = Normalizer()
        normalized_df = normalizer.normalize(df)
        
        # Should preserve legitimate special chars but be safe
        result = normalized_df['merchant'].iloc[0]
        assert result == 'Merchant & Sons < > " \''

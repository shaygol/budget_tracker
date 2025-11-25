# ===== code/previewer.py =====
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def format_prompt(text):
    return text

class Previewer:
    def preview(self, df: pd.DataFrame, confirm: bool = True) -> pd.DataFrame:
        """
        Display a monthly summary and confirm with the user.
        """
        summary = (
            df
            .groupby(['year', 'month', 'category', 'subcat'])['monthly_amount']
            .sum()
            .reset_index()
        )
        print("\n--- Preview Summary ---")
        # Apply format_prompt display only to Hebrew columns
        summary['category'] = summary['category'].apply(lambda x: format_prompt(str(x)) if isinstance(x, str) else x)
        summary['subcat'] = summary['subcat'].apply(lambda x: format_prompt(str(x)) if isinstance(x, str) else x)
        total = summary['monthly_amount'].sum()
        print(summary.to_string(index=False))
        print(f"\nTotal Amount: {total:,.2f}")

        if confirm:
            input("\nPress Enter to confirm and update the dashboard...")
            logger.debug("User confirmed preview summary.")
        return summary

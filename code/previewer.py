# ===== code/previewer.py =====
import pandas as pd
import logging
from code.utils import format_prompt

logger = logging.getLogger(__name__)

class Previewer:
    def preview(self, df: pd.DataFrame) -> pd.DataFrame:
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
        print(summary.to_string(index=False))

        input("\nPress Enter to confirm and update the dashboard...")
        logger.info("User confirmed preview summary.")
        return summary
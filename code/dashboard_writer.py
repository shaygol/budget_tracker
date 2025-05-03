
# ===== code/dashboard_writer.py =====
import pandas as pd
import os
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment
import logging
from code.utils import is_valid_excel_file

logger = logging.getLogger(__name__)

class DashboardWriter:
    def __init__(self, dashboard_path):
        self.dashboard_path = dashboard_path

    def update(self, summary_df: pd.DataFrame) -> None:
        # Ensure necessary columns are present in the summary DataFrame
        required_cols = {'year', 'month', 'category', 'subcat', 'monthly_amount'}
        if not required_cols.issubset(summary_df.columns):
            logger.error(f"Missing required columns: {required_cols - set(summary_df.columns)}")
            return

        # Define month numbers (1, 2, 3, ..., 12)
        all_months = [str(m) for m in range(1, 13)]

        # Extract all categories and subcategories from the dataset
        all_categories = summary_df['category'].unique()
        all_subcategories = summary_df['subcat'].unique()

        years = sorted(summary_df['year'].unique())

        # Check if file exists, and determine mode
        file_exists = os.path.exists(self.dashboard_path)
        if file_exists and is_valid_excel_file(self.dashboard_path):
            mode = 'a'  # append mode if the file exists
        else:
            mode = 'w'  # write mode if the file does not exist (new file)

        # Writing data to the Excel file
        with pd.ExcelWriter(self.dashboard_path, engine='openpyxl', mode=mode) as writer:
            for yr in years:
                df_year = summary_df[summary_df['year'] == yr]
                rows = []

                # Loop through each category (grouped by category)
                for category in all_categories:
                    # Add the category row only once, leaving the subcategories to follow
                    rows.append([category] + [''] * (len(all_months) + 1))  # Empty cells for subcategories

                    # Find the subcategories for the category, whether they have data or not
                    subcats_for_category = df_year[df_year['category'] == category]['subcat'].unique()
                    for subcat in all_subcategories:
                        if subcat in subcats_for_category:
                            subcat_df = df_year[(df_year['category'] == category) & (df_year['subcat'] == subcat)]
                            row = ['', "    " + subcat] + [0] * 12  # Initialize the row with 0s for each month
                            for _, r in subcat_df.iterrows():
                                month_idx = int(r['month']) - 1  # Adjust to 0-based index
                                row[2 + month_idx] = r['monthly_amount']  # Set the month value
                            rows.append(row)
                        else:
                            # If no data for this subcategory, add an empty row with zeros
                            rows.append(['', "    " + subcat] + [0] * 12)

                # Create the DataFrame for this year
                result_df = pd.DataFrame(rows, columns=['נושא', 'פירוט הוצאות'] + all_months)

                # Ensure that if the sheet already exists, we don't overwrite it in append mode
                if file_exists:
                    # Load existing workbook to append new data
                    book = load_workbook(self.dashboard_path)
                    if str(int(yr)) in book.sheetnames:
                        logger.info(f"Sheet for {yr} already exists. Appending data.")
                    else:
                        result_df.to_excel(writer, sheet_name=str(int(yr)), index=False)
                else:
                    result_df.to_excel(writer, sheet_name=str(int(yr)), index=False)

        # Apply formatting after writing
        self._format_excel(years)

    def _format_excel(self, years):
        wb = load_workbook(self.dashboard_path)
        for yr in years:
            ws = wb[str(int(yr))]

            # Set RTL (Right-to-left) for Hebrew layout
            ws.sheet_view.rightToLeft = True

            # Format header row with bold font
            header_font = Font(bold=True)
            for cell in ws[1]:
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center')

            # Bold category rows (rows where column A is not empty)
            for row in ws.iter_rows(min_row=2):
                if row[0].value:  # Check if the category cell is not empty
                    for cell in row:
                        cell.font = Font(bold=True)

            # Adjust column widths based on content
            for col in ws.columns:
                max_len = max(len(str(cell.value)) if cell.value else 0 for cell in col)
                col_letter = col[0].column_letter  # Get column name (A, B, C...)
                ws.column_dimensions[col_letter].width = max(10, max_len + 2)

        wb.save(self.dashboard_path)
        logger.info("Excel formatting applied.")




# Version 1.0: Work but messy
#import pandas as pd
#import logging
#import os
#from code.utils import is_valid_excel_file
#
#logger = logging.getLogger(__name__)
#
#class DashboardWriter:
#    def __init__(self, dashboard_path):
#        self.dashboard_path = dashboard_path
#
#    def update(self, summary_df: pd.DataFrame) -> None:
#        years = summary_df['year'].unique()
#
#        file_exists = os.path.exists(self.dashboard_path)
#        mode = 'a' if file_exists and is_valid_excel_file(self.dashboard_path) else 'w'
#
#        if mode == 'w':
#            logger.warning("Dashboard file not found or invalid. A new file will be created.")
#
#        with pd.ExcelWriter(self.dashboard_path, engine='openpyxl', mode=mode, if_sheet_exists='overlay') as writer:
#            for yr in years:
#                sheet = str(int(yr))
#                year_data = summary_df[summary_df['year'] == yr]
#
#                try:
#                    existing = pd.read_excel(self.dashboard_path, sheet_name=sheet)
#                except Exception:
#                    existing = pd.DataFrame(columns=['category', 'subcat'] + [str(m) for m in range(1, 13)] + ['avg_monthly', 'cumulative'])
#
#                for _, row in year_data.iterrows():
#                    cond = (existing['category'] == row['category']) & (existing['subcat'] == row['subcat'])
#                    col = str(int(row['month']))
#
#                    if cond.any():
#                        existing.loc[cond, col] = row['monthly_amount']
#                    else:
#                        new = pd.DataFrame([{
#                            'category': row['category'],
#                            'subcat': row['subcat'],
#                            **{str(m): 0 for m in range(1, 13)},
#                            col: row['monthly_amount']
#                        }])
#                        existing = pd.concat([existing, new], ignore_index=True)
#
#                # Calculate average and cumulative
#                existing['avg_monthly'] = existing[[str(m) for m in range(1, 13)]].mean(axis=1)
#                existing['cumulative'] = existing[[str(m) for m in range(1, 13)]].sum(axis=1)
#
#                existing.to_excel(writer, sheet_name=sheet, index=False)
#                logger.info(f"Updated sheet {sheet}")
#
#        logger.info("Dashboard update completed successfully.")
#
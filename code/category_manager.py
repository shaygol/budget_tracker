import json
import sys
import logging
from typing import List, Tuple
import pandas as pd
from openpyxl import load_workbook
from code.previewer import format_prompt

logger = logging.getLogger(__name__)


class CategoryManager:
    def __init__(self, categories_path: str, dashboard_path: str):
        self.categories_path = categories_path
        self.dashboard_path = dashboard_path

        self.category_map = self._load_category_map()
        self.valid_categories = self.load_category_structure_from_template()

    def _load_category_map(self) -> dict:
        try:
            with open(self.categories_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning(f"Categories file not found or invalid: {self.categories_path}. Starting with empty map.")
            return {}

    def load_category_structure_from_template(self) -> dict:
        """
        Loads the category structure from the 'Template' sheet in the given Excel dashboard.
        Skips header rows and supports merged cells in the first column for categories.
        """
        wb = load_workbook(self.dashboard_path, data_only=True)
        try:
            ws = wb["Template"]
        except KeyError:
            logger.error("The worksheet 'Template' does not exist in the dashboard file.")
            raise ValueError("Missing 'Template' worksheet in the dashboard. Please ensure it exists and is named correctly.")

        categories = {}
        current_category = None

        for row in ws.iter_rows(min_row=2, max_col=2):  # skip row 1 (headers)
            cat_cell, subcat_cell = row
            cat_val = cat_cell.value
            subcat_val = subcat_cell.value

            # Skip rows that look like headers
            if str(cat_val).strip() in ["נושא", "נושא הוצאה"] or str(subcat_val).strip() in ["פירוט", "פירוט הוצאות"]:
                continue

            # Detect new category
            if cat_val and str(cat_val).strip():
                current_category = str(cat_val).strip()
                if current_category not in categories:
                    categories[current_category] = []

            # Add subcategory
            if subcat_val and current_category:
                subcategory = str(subcat_val).strip()
                categories[current_category].append(subcategory)

        logger.info("=== Current category structure from Template ===")
        for category, subcategories in categories.items():
            logger.info(f"{category}: {subcategories}")
        logger.info("===============================================")

        return categories



    def map_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        df['category'] = df['merchant'].map(lambda m: self.category_map.get(m, [None, None])[0])
        df['subcat']   = df['merchant'].map(lambda m: self.category_map.get(m, [None, None])[1])

        unknown = [m for m in df['merchant'].unique() if m and m not in self.category_map]
        flat_choices: List[Tuple[str, str]] = [
            (cat, sub)
            for cat, subs in self.valid_categories.items()
            for sub in subs
        ]

        try:
            for merchant in unknown:
                print(format_prompt(f"New merchant detected: {merchant}"))
                for idx, (cat, sub) in enumerate(flat_choices, start=1):
                    print(format_prompt(f"{idx}. {cat} > {sub}"))
                while True:
                    choice = input("Select category number (or 'exit'): ").strip().lower()
                    if choice == "exit":
                        print("Saving mapped categories and exiting.")
                        self.save_categories()
                        sys.exit()
                    elif not choice.isdigit():
                        print(format_prompt("Please enter a number."))
                        continue
                    idx = int(choice)
                    if 1 <= idx <= len(flat_choices):
                        cat, sub = flat_choices[idx - 1]
                        self.category_map[merchant] = [cat, sub]
                        df.loc[df['merchant'] == merchant, 'category'] = cat
                        df.loc[df['merchant'] == merchant, 'subcat'] = sub
                        break
                    else:
                        print(format_prompt("Choice out of range."))
        except KeyboardInterrupt:
            print(format_prompt("Exiting, mapped categories not saved."))
            sys.exit()
        else:
            self.save_categories()

        # Revalidate existing mappings
        df = self._handle_removed_subcategories(df)

        logger.info("Category mapping complete.")
        return df

    def _handle_removed_subcategories(self, df: pd.DataFrame) -> pd.DataFrame:
        valid_subcats = {
            (cat, sub)
            for cat, subs in self.valid_categories.items()
            for sub in subs
        }

        used_pairs = {
            (cat, sub)
            for cat, sub in zip(df['category'], df['subcat'])
            if pd.notna(cat) and pd.notna(sub)
        }

        removed_pairs = used_pairs - valid_subcats
        if not removed_pairs:
            return df

        print(format_prompt("⚠️ Some previously used subcategories are no longer in the template."))
        flat_choices = [
            (cat, sub)
            for cat, subs in self.valid_categories.items()
            for sub in subs
        ]
        for idx, (cat, sub) in enumerate(flat_choices, start=1):
            print(format_prompt(f"{idx}. {cat} > {sub}"))

        for old_cat, old_sub in removed_pairs:
            print(format_prompt(f"\nSubcategory no longer exists: {old_cat} > {old_sub}"))
            while True:
                choice = input("Choose a new category number for this data (or type 'exit'): ").strip().lower()
                if choice == 'exit':
                    print("Exiting.")
                    sys.exit()
                if not choice.isdigit():
                    print(format_prompt("Please enter a number."))
                    continue
                idx = int(choice)
                if 1 <= idx <= len(flat_choices):
                    new_cat, new_sub = flat_choices[idx - 1]
                    mask = (df['category'] == old_cat) & (df['subcat'] == old_sub)
                    df.loc[mask, 'category'] = new_cat
                    df.loc[mask, 'subcat'] = new_sub
                    logger.info(f"Reassigned {mask.sum()} records from {old_cat} > {old_sub} to {new_cat} > {new_sub}")
                    break
                else:
                    print(format_prompt("Choice out of range."))

        return df

    def save_categories(self):
        with open(self.categories_path, 'w', encoding='utf-8') as f:
            json.dump(self.category_map, f, ensure_ascii=False, indent=2)

import json
import sys
import logging
from typing import List, Tuple
import pandas as pd
from openpyxl import load_workbook
from code.utils import rtl

logger = logging.getLogger(__name__)


class CategoryManager:
    def __init__(self, categories_path: str, dashboard_path: str):
        self.categories_path = categories_path
        self.dashboard_path = dashboard_path

        self.category_map = self._load_category_map()
        self.valid_categories = self._load_template_categories()

    def _load_category_map(self) -> dict:
        try:
            with open(self.categories_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning(f"Categories file not found or invalid: {self.categories_path}. Starting with empty map.")
            return {}

    def _load_template_categories(self) -> dict:
        wb = load_workbook(self.dashboard_path, read_only=True, data_only=True)
        try:
            ws = wb['Template']
        except KeyError:
            logger.error("The worksheet 'Template' does not exist in the dashboard file.")
            raise ValueError("Missing 'Template' worksheet in the dashboard. Please ensure it exists and is named correctly.")

        categories = {}
        current_cat = None
        for row in ws.iter_rows(min_row=2, max_col=2):
            cat_cell, subcat_cell = row
            cat_val = cat_cell.value
            subcat_val = subcat_cell.value

            if cat_val:
                current_cat = str(cat_val).strip()
                categories[current_cat] = []

            if subcat_val and current_cat:
                categories[current_cat].append(str(subcat_val).strip())

        logger.info("=== Current category structure from Template ===")
        for cat, subs in categories.items():
            logger.info(f"{cat}: {subs}")
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
                print(rtl(f"New merchant detected: {merchant}"))
                for idx, (cat, sub) in enumerate(flat_choices, start=1):
                    print(rtl(f"{idx}. {cat} > {sub}"))
                while True:
                    choice = input("Select category number (or 'exit'): ").strip().lower()
                    if choice == "exit":
                        print("Saving mapped categories and exiting.")
                        self.save_categories()
                        sys.exit()
                    elif not choice.isdigit():
                        print(rtl("Please enter a number."))
                        continue
                    idx = int(choice)
                    if 1 <= idx <= len(flat_choices):
                        cat, sub = flat_choices[idx - 1]
                        self.category_map[merchant] = [cat, sub]
                        df.loc[df['merchant'] == merchant, 'category'] = cat
                        df.loc[df['merchant'] == merchant, 'subcat'] = sub
                        break
                    else:
                        print(rtl("Choice out of range."))
        except KeyboardInterrupt:
            print(rtl("Exiting, mapped categories not saved."))
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

        print(rtl("⚠️ Some previously used subcategories are no longer in the template."))
        flat_choices = [
            (cat, sub)
            for cat, subs in self.valid_categories.items()
            for sub in subs
        ]
        for idx, (cat, sub) in enumerate(flat_choices, start=1):
            print(rtl(f"{idx}. {cat} > {sub}"))

        for old_cat, old_sub in removed_pairs:
            print(rtl(f"\nSubcategory no longer exists: {old_cat} > {old_sub}"))
            while True:
                choice = input("Choose a new category number for this data (or type 'exit'): ").strip().lower()
                if choice == 'exit':
                    print("Exiting.")
                    sys.exit()
                if not choice.isdigit():
                    print(rtl("Please enter a number."))
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
                    print(rtl("Choice out of range."))

        return df

    def save_categories(self):
        with open(self.categories_path, 'w', encoding='utf-8') as f:
            json.dump(self.category_map, f, ensure_ascii=False, indent=2)

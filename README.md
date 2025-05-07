# Budget Tracker

**Budget Tracker** is a Python-based tool for processing, categorizing, and summarizing monthly financial transactions from Excel files.
It supports Hebrew-language inputs and it outputs a categorized summary into a pre-designed Excel dashboard.



## Features

- Load and normalize Excel transaction files (`.xlsx`, `.xls`).
- Automatically detect and clean header inconsistencies (e.g. formatting issues, special characters).
- Map merchants to user-defined budget categories and subcategories.
- Prompt the user to categorize unknown merchants.
- Output categorized monthly summaries into an existing formatted dashboard.
- Automatically clone a "Template" sheet to create a new sheet for each year.
- Modular and extensible codebase.



## Usage

1. **Place transaction files** in the `transactions/` folder.
2. **Prepare the dashboard**:
   - Ensure `dashboard.xlsx` exists and contains a sheet named `Template`.
   - Design and categorized the template sheet as you want.
3. **Run the script**:
```bash
python main.py
```

### Categorize unknown merchants:
When prompted, assign categories and subcategories.

### Review and approve summary:
Preview is shown for confirmation before writing to the dashboard.

## Requirements
Python 3.8+

Dependencies listed in requirements.txt (e.g. pandas, openpyxl)

Install dependencies using:
```bash
pip install -r requirements.txt
```

## Notes
- Hebrew support is built-in; no encoding changes are needed for transaction files.
- The script automatically creates missing folders (transactions, output, config) if needed.
- Errors during processing (e.g. missing columns) are logged and reported with full traceability.

## License
This project is private and not intended for redistribution.
All rights reserved.
# Budget Tracker

**Budget Tracker** is a Python-based tool for processing, categorizing, and summarizing monthly financial transactions from Excel files.
It supports Hebrew-language inputs and outputs a categorized summary into a pre-designed Excel dashboard.

## Features

- **GUI Interface**: Easy-to-use graphical interface for importing and managing files.
- **Automated Processing**: Load and normalize Excel transaction files (`.xlsx`, `.xls`).
- **Smart Categorization**: Map merchants to user-defined budget categories and subcategories.
- **Dashboard Integration**: Output categorized monthly summaries into an existing formatted dashboard.
- **Backups**: Automatic backups of your dashboard and archived transaction files.
- **Hebrew Support**: Built-in support for Hebrew text and date formats.

## Folder Structure

The application organizes your data in the `UserFiles` directory:
- `UserFiles/dashboard.xlsx`: Your main dashboard file.
- `UserFiles/categories.json`: Your saved category mappings.
- `UserFiles/backups/`: Automatic backups of dashboard and archives.
- `UserFiles/temp_processing/`: Temporary location for processing files (CLI mode).

## Usage

### GUI Mode (Recommended)
1. Run the application:
   ```bash
   python main.py --gui
   ```
2. **Import Files**: Drag & drop Excel files or use the "Import Files" button.
3. **Categorize**: The app will prompt you to map any new merchants.
4. **Update**: Review the summary and update your dashboard.

### CLI Mode
1. Place transaction files in `UserFiles/temp_processing/`.
2. Run the script:
   ```bash
   python main.py
   ```
3. Follow the interactive prompts in the terminal.

## Setup

1. **Prerequisites**: Python 3.8+
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **First Run**:
   - Ensure `UserFiles/dashboard.xlsx` exists and contains a sheet named `Template`.
   - The application will create necessary folders on first run.

## Upcoming Features

- [ ] **GUI Enhancements**
    - [ ] **Category Management**: Add a dialog to view, edit, and delete existing category mappings directly from the GUI.
    - [ ] **History View**: Add a tab to view a log of past imports and archived files.
    - [ ] **Advanced Charts**: Add interactive pie charts and trend lines to the dashboard view.

- [ ] **Reporting & Export**
    - [ ] **PDF Reports**: Generate a printable monthly summary PDF.
    - [ ] **CSV Export**: Option to export the processed data to a clean CSV file.

- [ ] **Deployment**
    - [ ] **Executable Creation**: Use PyInstaller to bundle the application into a single `.exe` file for easy distribution without Python installation.

## Bug Fixes & Maintenance

- [ ] **Test Coverage**: Increase unit test coverage for `gui_app.py`.
- [ ] **Documentation**: Add docstrings to all GUI methods.

## License
This project is private and not intended for redistribution.
All rights reserved.
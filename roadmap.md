# Improvements & Roadmap

### Recently Completed ✅
- [x] **Delete File Button**: Delete transaction files from GUI with confirmation
- [x] **Duplicate Detection**: SHA256 hash-based duplicate file detection on import
- [x] **Dashboard Update Info**: Display last modified date and time for dashboard
- [x] **Open Archive Button**: Quick access to archived transaction files
- [x] **File Preview**: Show transaction count, date range, and total when selecting file
- [x] **Interactive Chart Filtering**: Click category to show subcategory breakdown with RTL support
- [x] **Robust File Parsing**: Flexible header detection (handles quote variations, extra spaces, simplified names)
- [x] **PDF Transaction Import**: Import text-based credit card statement PDFs through the same GUI flow as Excel
- [x] **PDF Statement Parsing Hardening**: Added layout-aware parsing, merchant cleanup, foreign-currency support, and focused parser tests
- [x] **Pre-loaded Common Mappings**: Default merchant-to-category mappings for 211 common Israeli merchants

---

### Known Issues 🐛
_(Currently none)_

---

### Future Features
- [x] **Interactive Table Filtering**: Clicking a category row in the table (e.g., "רכב") filters the chart
- [x] **Category Management**: GUI dialog to view, edit, and delete existing category mappings
- [ ] **PDF Report Export**: Generate formatted PDF reports with Hebrew RTL support
  - Include charts and summary statistics
  - Period selection (monthly/yearly/all-time)
  - Hebrew text rendering with proper RTL support
  - Requires: reportlab, Pillow
- [ ] **CSV Export**: Export transaction data and summaries to CSV format
- [ ] **Budget Goals**: Set monthly limits per category and track progress.
- [ ] **History View**: Tab to view a log of past imports and archived files.
- [ ] **Advanced Charts**: Interactive pie charts and trend lines.
- [ ] **Dashboard Excel Auto-Charts**: Re-introduce reliable auto-generation of yearly sheet charts from template/category data.
- [x] **Deployment**: Bundle application into a single `.exe` file using PyInstaller
- [ ] **Maintenance**: Increase GUI test coverage and add docstrings.
- [x] **icon**: Add icon to application
- [ ] **deployment**: Add deployment zip file.

---

### File Parsing Enhancements (Low Priority)
- [ ] **Enhanced Header Detection**
  - [ ] Data type validation below header (verify dates, numbers in expected columns)
  - [ ] Keyword specificity scoring (prefer "תאריך עסקה" over "תאריך")
  - [ ] Multi-language header detection priority (Hebrew first, then English)
  - [ ] Column position hints (amount typically in rightmost columns)
- [ ] **File Format Support**
  - [ ] CSV import support
  - [x] PDF bank statement parsing
  - [ ] Direct bank API integration

---

### Template Management (Low Priority)
- [ ] **Template Sync Tool** (`code/template_sync.py`)
  - [ ] Detect orphaned data (categories removed from Template)
  - [ ] Reorganize year sheets to match Template order
  - [ ] Warn about manual edits to year sheets
- [ ] **Template Export/Import** (`code/template_io.py`)
  - [ ] Export template structure to JSON
  - [ ] Import template from JSON to create/update Template sheet
  - [ ] Template versioning with hash tracking
  - [ ] Migration assistant for template changes
  - [ ] Share templates between users


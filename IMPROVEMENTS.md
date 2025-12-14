# Improvements & Roadmap

### Future Features
- [ ] **Interactive Table Filtering**: Clicking a category row in the table (e.g., "רכב") should update the chart to show a breakdown of that category's subcategories or filter the chart to show that category's monthly trend.
- [ ] **Budget Goals**: Set monthly limits per category and track progress.
- [ ] **Category Management**: GUI dialog to view, edit, and delete existing category mappings.
- [ ] **History View**: Tab to view a log of past imports and archived files.
- [ ] **Advanced Charts**: Interactive pie charts and trend lines.
- [ ] **Reporting & Export**: Generate PDF reports and CSV exports.
- [ ] **Deployment**: Bundle application into a single `.exe` file using PyInstaller.
- [ ] **Maintenance**: Increase GUI test coverage and add docstrings.
- [ ] **icon**: Add icon to application.
- [ ] **deployment**: Add deployment zip file.

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


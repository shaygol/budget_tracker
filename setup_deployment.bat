@echo off

:: =============================================================
:: Budget Tracker - Build & Deployment Script
:: =============================================================

:: -------------------------------------------------------------
:: Step 0: Run Tests
:: -------------------------------------------------------------
echo Running tests...
venv\Scripts\python.exe -m pytest
if %ERRORLEVEL% NEQ 0 (
    echo Tests failed! Aborting build.
    pause
    exit /b %ERRORLEVEL%
)
echo Tests passed successfully.

:: -------------------------------------------------------------
:: Step 1: Build Executable
:: -------------------------------------------------------------
echo Building Budget Tracker executable...

:: Check if icon exists, otherwise use NONE
if exist "badget_tracker.ico" (
    set ICON_ARG=--icon="badget_tracker.ico"
    set ICON_DATA=--add-data "badget_tracker.ico;."
) else (
    set ICON_ARG=--icon=NONE
    set ICON_DATA=
)

venv\Scripts\pyinstaller.exe ^
    --name "BudgetTracker" ^
    --onefile ^
    --windowed ^
    %ICON_ARG% ^
    %ICON_DATA% ^
    --hidden-import=pandas ^
    --hidden-import=openpyxl ^
    --hidden-import=matplotlib ^
    --hidden-import=matplotlib.backends.backend_qt5agg ^
    --hidden-import=PyQt5 ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtWidgets ^
    --noconsole ^
    --clean ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo Build failed! Exiting.
    pause
    exit /b %ERRORLEVEL%
)

echo Build complete. Proceeding to deployment setup...
echo.

:: -------------------------------------------------------------
:: Step 2: Create Deployment Package
:: -------------------------------------------------------------

:: Create deployment folder
if not exist "deployment" mkdir "deployment"

:: Copy executable
echo Copying executable...
copy "dist\BudgetTracker.exe" "deployment\" /Y

:: Copy logo (icon) if present for distribution
if exist "badget_tracker.ico" (
    echo Copying application icon...
    copy "badget_tracker.ico" "deployment\" /Y
) else (
    echo Icon file badget_tracker.ico not found - skipping icon copy.
)

:: Create UserFiles structure
echo Creating UserFiles structure...
if not exist "deployment\UserFiles" mkdir "deployment\UserFiles"
if not exist "deployment\UserFiles\backups" mkdir "deployment\UserFiles\backups"
if not exist "deployment\UserFiles\backups\archive" mkdir "deployment\UserFiles\backups\archive"
if not exist "deployment\UserFiles\backups\dashboard" mkdir "deployment\UserFiles\backups\dashboard"

:: -------------------------------------------------------------
:: Step 3: Setup Dashboard (Copy & Clean)
:: -------------------------------------------------------------
echo Processing dashboard.xlsx...
venv\Scripts\python.exe setup_dashboard.py

:: -------------------------------------------------------------
:: Step 4: Create Configuration Files
:: -------------------------------------------------------------
echo Creating empty categories.json...
echo {}> "deployment\UserFiles\categories.json"

echo Creating deployment README...
(
    echo Budget Tracker - Deployment Package
    echo ====================================
    echo .
    echo CONTENTS:
    echo - BudgetTracker.exe - The main application
    echo - UserFiles/ - Your data folder
    echo   - dashboard.xlsx - Your budget dashboard (Template sheet only)
    echo   - categories.json - Your category mappings
    echo   - backups/archive/ - Processed transaction files
    echo   - backups/dashboard/ - Dashboard backups
    echo .
    echo HOW TO USE:
    echo 1. Double-click BudgetTracker.exe to launch the application
    echo 2. Use the GUI to import transaction files
    echo 3. All your data will be saved in the UserFiles folder
    echo .
    echo IMPORTANT:
    echo - Keep the UserFiles folder next to BudgetTracker.exe
    echo - The dashboard.xlsx MUST have a "Template" sheet with your categories
    echo - Backup the UserFiles folder regularly
    echo .
    echo FIRST TIME SETUP:
    echo - If dashboard.xlsx doesn't exist, copy your existing one here
    echo - If it's your first time, create a Template sheet with:
    echo   Column A: Category names
    echo   Column B: Subcategory names
    echo .
) > "deployment\README.txt"

:: -------------------------------------------------------------
:: Step 5: Cleanup
:: -------------------------------------------------------------
echo Cleaning up build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "BudgetTracker.spec" del "BudgetTracker.spec"

echo.
echo =============================================================
echo Deployment package created in 'deployment' folder!
echo =============================================================
echo.
echo Next steps:
echo 1. Verify that deployment\UserFiles\dashboard.xlsx contains only the Template sheet and header.
echo 2. Test the application by running deployment\BudgetTracker.exe
echo 3. Zip the deployment folder to share with others
echo.
pause


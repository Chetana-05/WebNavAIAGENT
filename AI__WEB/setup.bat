@echo off
echo ==============================================
echo Web Navigator AI Agent - First Time Setup
echo ==============================================

echo [1/3] Creating Python virtual environment (.venv)...
python -m venv .venv
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python was not found or failed to create .venv.
    echo Please make sure Python 3.10+ is installed and 'Add python.exe to PATH' was checked during installation.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Installing dependencies from requirements.txt...
call .\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Dependency installation failed.
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Installing Playwright Chromium browser...
playwright install chromium
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Playwright browser installation failed.
    pause
    exit /b %errorlevel%
)

echo.
echo ==============================================
echo SUCCESS! Setup is complete.
echo You can now run the app via VS Code or run_web.bat
echo ==============================================
pause

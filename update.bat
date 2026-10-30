@echo off
setlocal enabledelayedexpansion
title GDGC-JISU1 Dashboard Updater

echo ===================================================
echo   GDGC-JISU1 Learn with Communities - Daily Updater
echo ===================================================
echo.

cd /d "%~dp0"

set "DOWNLOADS=%USERPROFILE%\Downloads"
set "RAW_DIR=data\raw"

if not exist "%RAW_DIR%" mkdir "%RAW_DIR%"

echo [1/3] Checking for new report in Downloads...
set "LATEST_CSV="
for /f "delims=" %%F in ('dir /b /o-d /a-d "%DOWNLOADS%\*GDGC*JISU*.csv" 2^>nul') do (
    if not defined LATEST_CSV (
        set "LATEST_CSV=%%F"
    )
)

if defined LATEST_CSV (
    echo   Found newest CSV in Downloads: "!LATEST_CSV!"
    echo   Copying to data\raw\...
    copy /y "%DOWNLOADS%\!LATEST_CSV!" "%RAW_DIR%\" >nul
) else (
    echo   No new CSV found in Downloads matching *GDGC*JISU*.csv
    echo   Using existing files in data\raw\...
)

echo.
echo [2/3] Processing daily data and updating stats...
set PYTHONIOENCODING=utf-8
python scripts\ingest_csv.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Ingestion failed. Please check the error above.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [3/4] Committing and pushing updates to GitHub...
git add data/
git commit -m "Update daily report data" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   Pushing to GitHub (Vercel will auto-deploy)...
    git push origin main
) else (
    echo   No changes detected or git commit skipped.
)

echo.
echo [4/4] Checking local dashboard server...
netstat -ano | findstr :8080 | findstr LISTENING >nul
if %ERRORLEVEL% neq 0 (
    echo   Starting local server at http://localhost:8080...
    start "" /b python -m http.server 8080
    timeout /t 1 >nul
) else (
    echo   Server already running on port 8080.
)

echo   Opening dashboard in browser...
start "" "http://localhost:8080"

echo.
echo ===================================================
echo   SUCCESS! Dashboard has been updated.
echo   You can close this window now.
echo ===================================================
echo.
pause


@echo off
setlocal

set APP_NAME=Inventory Tracker

:: === Read version from version.txt ===
set /p VERSION=<version.txt
echo 📦 Current version: v%VERSION%

:: === Auto bump patch number ===
for /f "tokens=1-3 delims=." %%a in ("%VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
    set PATCH=%%c
)

set /a PATCH+=1
set NEW_VERSION=%MAJOR%.%MINOR%.%PATCH%

:: Write new version back to file
echo %NEW_VERSION% > version.txt
echo 🚀 New version: v%NEW_VERSION%

:: === Clean old builds ===
echo 🧹 Cleaning old builds...
rmdir /s /q dist
rmdir /s /q build
del /q "%APP_NAME%.spec"

:: === Build with new version in name ===
echo ⚙️ Building %APP_NAME% v%NEW_VERSION%...
pyinstaller --noconfirm --windowed ^
    --name "%APP_NAME%_v%NEW_VERSION%" ^
    --icon=icon.ico ^
    --add-data "config/firebase.json;config" ^
    --add-data "config/serviceAccountKey.json;config" ^
    --add-data "db\inventory_empty.db;db" ^
    --add-data "assets;assets" ^
    main.py

echo ✅ Build finished: dist\%APP_NAME%_v%NEW_VERSION%\
pause


@REM run build.bat
@echo off
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo        Combine Photos Studio - Windows Builder
echo ============================================================
echo.

where py >nul 2>&1
if %errorlevel%==0 (
    set "PY=py"
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python 3 was not found.
        echo Install Python from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    set "PY=python"
)

echo [1/5] Installing build dependencies...
%PY% -m pip install --upgrade pip
if errorlevel 1 goto :fail
%PY% -m pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo [2/5] Generating application icon...
%PY% generate_icon.py
if errorlevel 1 goto :fail

echo.
echo [3/5] Cleaning previous output...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist CombinePhotosStudio.spec del /q CombinePhotosStudio.spec

echo.
echo [4/5] Building one-file Windows application...
%PY% -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name CombinePhotosStudio ^
  --icon combine_photos_studio.ico ^
  --version-file version_info.txt ^
  --add-data "combine_photos_studio.ico;." ^
  --add-data "combine_photos_studio_icon.png;." ^
  --collect-all customtkinter ^
  --collect-all pillow_heif ^
  --hidden-import tifffile ^
  --hidden-import imagecodecs ^
  combine_photos_studio.py
if errorlevel 1 goto :fail

echo.
echo [5/5] Verifying one-file archive...
if not exist "dist\CombinePhotosStudio.exe" goto :fail
for %%A in ("dist\CombinePhotosStudio.exe") do set SIZE=%%~zA
if %SIZE% LSS 5000000 (
    echo [ERROR] Built EXE is unexpectedly small: %SIZE% bytes.
    goto :fail
)
%PY% -m PyInstaller.utils.cliutils.archive_viewer -l "dist\CombinePhotosStudio.exe" >nul
if errorlevel 1 (
    echo [ERROR] PyInstaller archive verification failed.
    goto :fail
)

echo.
echo ============================================================
echo BUILD COMPLETE - VERIFIED
echo.
echo dist\CombinePhotosStudio.exe
echo ============================================================
echo.
pause
exit /b 0

:fail
echo.
echo [ERROR] Build failed.
pause
exit /b 1

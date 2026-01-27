@echo off
setlocal
chcp 65001 >nul
color 0B
cls

:: ============================================================================
:: BUILD CONFIGURATION
:: ============================================================================
set "PROJECT_NAME=MoveIT_AD_Automation"
set "MAIN_FILE=main.py"
set "CONFIG_FILE=config.json"
set "OUTPUT_DIR=ENTREGA_FINAL"
set "ICON_MODE=NONE" 

:: ============================================================================
:: SYSTEM BANNER
:: ============================================================================
echo.
echo  =========================================================================
echo   MOVEIT BUILD SYSTEM - RELEASE 1.0
echo   Automated Deployment Pipeline
echo  =========================================================================
echo.

:: ============================================================================
:: PHASE 1: ENVIRONMENT CHECK
:: ============================================================================
echo [INFO] Checking system requirements...

:: 1. Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo [ERROR] Python is not recognized in the system PATH.
    echo         Please install Python and check "Add to PATH".
    pause
    exit /b
)

:: 2. Check Flet Library
python -c "import flet" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Flet library not found. Attempting to install...
    pip install flet pyinstaller
)

:: 3. Check Source Files
if not exist "%MAIN_FILE%" (
    color 0C
    echo [ERROR] Source file '%MAIN_FILE%' not found in current directory.
    pause
    exit /b
)

echo [OK] System ready for build.
echo.

:: ============================================================================
:: PHASE 2: CLEANUP
:: ============================================================================
echo [INFO] Cleaning workspace...

if exist "build" rmdir /S /Q "build" >nul 2>&1
if exist "dist" rmdir /S /Q "dist" >nul 2>&1
if exist "*.spec" del /Q "*.spec" >nul 2>&1
if exist "%OUTPUT_DIR%" rmdir /S /Q "%OUTPUT_DIR%" >nul 2>&1

echo [OK] Workspace clean.
echo.

:: ============================================================================
:: PHASE 3: COMPILATION
:: ============================================================================
echo [INFO] Starting build process...
echo        Target: %PROJECT_NAME%.exe
echo        Please wait...

:: Executa via módulo Python para garantir compatibilidade universal
python -m flet pack %MAIN_FILE% --name "%PROJECT_NAME%" --icon "%ICON_MODE%" --product-name "MoveIT AD Tool" --file-description "AD Automation Utility" --copyright "Corporate IT"

if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo [FATAL ERROR] Compilation failed.
    echo Check the error messages above.
    pause
    exit /b
)

echo.
echo [SUCCESS] Build completed.
echo.

:: ============================================================================
:: PHASE 4: PACKAGING
:: ============================================================================
echo [INFO] Packaging artifacts...

mkdir "%OUTPUT_DIR%"

:: Move executable
if exist "dist\%PROJECT_NAME%.exe" (
    move /Y "dist\%PROJECT_NAME%.exe" "%OUTPUT_DIR%\" >nul
    echo      + Executable moved to output directory.
) else (
    color 0C
    echo [ERROR] Output binary not found in dist folder.
    pause
    exit /b
)

:: Copy configuration template
if exist "%CONFIG_FILE%" (
    copy /Y "%CONFIG_FILE%" "%OUTPUT_DIR%\" >nul
    echo      + Configuration file included.
)

:: Final cleanup
rmdir /S /Q "build" >nul 2>&1
rmdir /S /Q "dist" >nul 2>&1
del /Q "%PROJECT_NAME%.spec" >nul 2>&1

echo.
echo =========================================================================
echo  BUILD FINISHED SUCCESSFULLY
echo =========================================================================
echo.
echo  Output Location: .\%OUTPUT_DIR%\%PROJECT_NAME%.exe
echo.
echo  NOTE: Ensure to run the application as Administrator for AD operations.
echo.
pause
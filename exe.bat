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
echo   MOVEIT BUILD SYSTEM - VERSAO 1.0
echo   Pipeline de Automacao de Build
echo  =========================================================================
echo.

:: ============================================================================
:: PHASE 1: ENVIRONMENT CHECK
:: ============================================================================
echo [INFO] Verificando requisitos do sistema...

:: 1. Check Python installation
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo [ERRO] Python nao foi reconhecido no PATH do sistema.
    echo        Por favor, instale o Python e marque a opcao "Add to PATH".
    pause
    exit /b
)

:: 2. Check Flet Library and PyInstaller
python -c "import flet" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [AVISO] Biblioteca Flet nao encontrada. Tentando instalar dependencias...
    pip install flet pyinstaller
)

:: 3. Check Source Files presence
if not exist "%MAIN_FILE%" (
    color 0C
    echo [ERRO] Arquivo fonte '%MAIN_FILE%' nao encontrado no diretorio atual.
    pause
    exit /b
)

echo [OK] Sistema pronto para a compilacao.
echo.

:: ============================================================================
:: PHASE 2: CLEANUP
:: ============================================================================
echo [INFO] Limpando area de trabalho...

if exist "build" rmdir /S /Q "build" >nul 2>&1
if exist "dist" rmdir /S /Q "dist" >nul 2>&1
if exist "*.spec" del /Q "*.spec" >nul 2>&1
if exist "%OUTPUT_DIR%" rmdir /S /Q "%OUTPUT_DIR%" >nul 2>&1

echo [OK] Area de trabalho limpa.
echo.

:: ============================================================================
:: PHASE 3: COMPILATION
:: ============================================================================
echo [INFO] Iniciando processo de empacotamento...
echo        Alvo: %PROJECT_NAME%.exe
echo        Isso pode levar alguns minutos. Por favor, aguarde...

:: Executes via Python module to ensure universal compatibility across PCs
flet pack %MAIN_FILE% --name "%PROJECT_NAME%" --product-name "MoveIT AD Tool" --file-description "AD Automation Utility" --copyright "Corporate IT"

if %ERRORLEVEL% NEQ 0 (
    color 0C
    echo.
    echo [ERRO FATAL] A compilacao falhou.
    echo Verifique as mensagens de erro detalhadas acima.
    pause
    exit /b
)

echo.
echo [SUCESSO] Compilacao concluida.
echo.

:: ============================================================================
:: PHASE 4: PACKAGING
:: ============================================================================
echo [INFO] Organizando os artefatos finais...

mkdir "%OUTPUT_DIR%"

:: Move executable to output folder
if exist "dist\%PROJECT_NAME%.exe" (
    move /Y "dist\%PROJECT_NAME%.exe" "%OUTPUT_DIR%\" >nul
    echo      + Executavel movido para a pasta de entrega.
) else (
    color 0C
    echo [ERRO] Arquivo .exe nao foi encontrado na pasta dist apos compilar.
    pause
    exit /b
)

:: Copy configuration template
if exist "%CONFIG_FILE%" (
    copy /Y "%CONFIG_FILE%" "%OUTPUT_DIR%\" >nul
    echo      + Arquivo de configuracao (config.json) incluido.
)

:: Final cleanup of temporary build folders
rmdir /S /Q "build" >nul 2>&1
rmdir /S /Q "dist" >nul 2>&1
del /Q "%PROJECT_NAME%.spec" >nul 2>&1

echo.
echo =========================================================================
echo  BUILD FINALIZADO COM SUCESSO
echo =========================================================================
echo.
echo  O seu software esta pronto na pasta: .\%OUTPUT_DIR%\
echo  Arquivo principal: %PROJECT_NAME%.exe
echo.
echo  [NOTA IMPORTANTE]
echo  Lembre-se de executar o programa como Administrador para operacoes no AD.
echo.
pause

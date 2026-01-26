@echo off
chcp 65001 >nul
color 0A
cls

echo ========================================================
echo      GERADOR DE EXECUTAVEL - MOVEDOR AD PRO 2.0
echo ========================================================
echo.

echo [1/4] Verificando e instalando dependencias...
pip install flet pandas pyinstaller --disable-pip-version-check
echo.

echo [2/4] Compilando o software (Isso pode demorar um pouco)...
echo       Aguarde...
pyinstaller --name "MovedorAD_Pro" --onefile --noconsole --uac-admin --clean main.py

echo.
echo [3/4] Organizando os arquivos para entrega...

if not exist "ENTREGA_FINAL" mkdir "ENTREGA_FINAL"

move /Y "dist\MovedorAD_Pro.exe" "ENTREGA_FINAL\" >nul

if exist "config.json" (
    copy /Y "config.json" "ENTREGA_FINAL\" >nul
) else (
    echo AVISO: config.json nao encontrado para copiar! Voce tera que criar na mao.
)

rmdir /S /Q "build"
rmdir /S /Q "dist"
del /Q "MovedorAD_Pro.spec"

echo.
echo ========================================================
echo      SUCESSO! SEU SOFTWARE ESTA PRONTO.
echo ========================================================
echo.
echo Verifique a pasta: ENTREGA_FINAL
echo.
pause
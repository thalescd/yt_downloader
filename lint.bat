@echo off
echo === YT Downloader - Lint ===
echo.

if not exist .venv\ (
    echo ERRO: Ambiente virtual nao encontrado.
    echo Execute setup.bat primeiro.
    pause
    exit /b 1
)

echo [1/3] Ruff - estilo e imports...
.venv\Scripts\ruff check .
if errorlevel 1 (
    echo ERRO: Problemas encontrados pelo Ruff. Rode ".venv\Scripts\ruff check --fix ." para corrigir automaticamente.
    pause
    exit /b 1
)

echo [2/3] Ruff - formatacao...
.venv\Scripts\ruff format --check .
if errorlevel 1 (
    echo ERRO: Codigo fora do padrao de formatacao. Rode ".venv\Scripts\ruff format ." para corrigir automaticamente.
    pause
    exit /b 1
)

echo [3/3] Pyright...
.venv\Scripts\pyright
if errorlevel 1 (
    echo ERRO: Problemas de tipo encontrados pelo Pyright.
    pause
    exit /b 1
)

echo.
echo Tudo certo!
pause

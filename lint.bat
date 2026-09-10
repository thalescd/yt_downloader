@echo off
echo === YT Downloader - Verificacoes ===
echo.

if not exist .venv\ (
    echo ERRO: Ambiente virtual nao encontrado.
    echo Execute setup.bat primeiro.
    pause
    exit /b 1
)

echo [1/4] Ruff - estilo e imports...
.venv\Scripts\ruff check .
if errorlevel 1 (
    echo ERRO: Problemas encontrados pelo Ruff. Rode ".venv\Scripts\ruff check --fix ." para corrigir automaticamente.
    pause
    exit /b 1
)

echo [2/4] Ruff - formatacao...
.venv\Scripts\ruff format --check .
if errorlevel 1 (
    echo ERRO: Codigo fora do padrao de formatacao. Rode ".venv\Scripts\ruff format ." para corrigir automaticamente.
    pause
    exit /b 1
)

rem --pythonpath amarra a checagem ao venv: sem ele o Pyright resolve os
rem imports contra o Python do PATH, que nao tem as dependencias instaladas.
echo [3/4] Pyright...
.venv\Scripts\pyright --pythonpath .venv\Scripts\python.exe
if errorlevel 1 (
    echo ERRO: Problemas de tipo encontrados pelo Pyright.
    pause
    exit /b 1
)

echo [4/4] Pytest...
.venv\Scripts\pytest
if errorlevel 1 (
    echo ERRO: Testes falharam.
    pause
    exit /b 1
)

echo.
echo Tudo certo!
pause

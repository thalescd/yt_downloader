@echo off
echo === YT Downloader - Setup ===
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado no PATH.
    echo Instale o Python 3.8+ em https://python.org e marque "Add to PATH".
    pause
    exit /b 1
)

if not exist .venv\ (
    echo Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo ERRO: Falha ao criar o ambiente virtual.
        pause
        exit /b 1
    )
) else (
    echo Ambiente virtual ja existe, pulando criacao.
)

echo Instalando dependencias...
.venv\Scripts\pip install -r requirements.txt
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias.
    pause
    exit /b 1
)

echo.
echo Setup concluido! Abrindo o app...
.venv\Scripts\python app.py

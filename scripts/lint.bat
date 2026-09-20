@echo off
rem Casca fina: as verificacoes vivem em scripts\tasks.py, uma vez so para
rem Windows e Linux.
cd /d "%~dp0.."

python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado no PATH.
    echo Instale o Python 3.12+ em https://python.org e marque "Add to PATH".
    pause
    exit /b 1
)

python scripts\tasks.py lint
rem Pausa sempre: aberto com duplo clique, o resultado sumiria com a janela.
pause

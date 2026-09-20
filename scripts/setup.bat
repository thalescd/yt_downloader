@echo off
rem Casca fina: a logica das tarefas vive em scripts\tasks.py, uma vez so para
rem Windows e Linux. So a checagem do proprio Python fica aqui, porque ela
rem precisa acontecer antes de conseguirmos executar qualquer Python.
cd /d "%~dp0.."

python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado no PATH.
    echo Instale o Python 3.12+ em https://python.org e marque "Add to PATH".
    pause
    exit /b 1
)

python scripts\tasks.py setup
rem Sem pausa no caminho feliz: o setup termina abrindo o app.
if errorlevel 1 pause

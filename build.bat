@echo off
echo === YT Downloader - Build ===
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado no PATH.
    echo Instale o Python 3.8+ em https://python.org e marque "Add to PATH".
    pause
    exit /b 1
)

if not exist .venv\ (
    echo ERRO: Ambiente virtual nao encontrado.
    echo Execute setup.bat primeiro e tente novamente.
    pause
    exit /b 1
)

echo Instalando dependencias de build...
.venv\Scripts\pip install -r requirements-dev.txt
if errorlevel 1 (
    echo ERRO: Falha ao instalar dependencias de build.
    echo Tente rodar setup.bat novamente para recriar o ambiente.
    pause
    exit /b 1
)

echo Gerando executavel...
.venv\Scripts\pyinstaller --onefile --windowed --name "YT Downloader" --collect-all pytubefix --collect-all sv_ttk app.py
if errorlevel 1 (
    echo ERRO: Falha ao gerar o executavel.
    pause
    exit /b 1
)

echo.
echo Pronto! Executavel gerado em: dist\YT Downloader.exe
pause

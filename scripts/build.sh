#!/usr/bin/env bash
# Equivalente Linux de build.bat.
#
# Atenção: gera um binário LINUX, não um .exe. O PyInstaller não faz
# compilação cruzada — o executável do Windows precisa ser gerado no Windows,
# com build.bat.
set -euo pipefail
# Os comandos abaixo assumem a raiz do projeto, não a pasta scripts/.
cd "$(dirname "$0")/.."

echo "=== YT Downloader - Build (Linux) ==="
echo

if [ ! -d .venv ]; then
    echo "ERRO: ambiente virtual não encontrado."
    echo "Execute ./scripts/setup.sh primeiro."
    exit 1
fi

echo "Instalando dependências de build..."
.venv/bin/pip install -r requirements-dev.txt

# --icon é ignorado fora de Windows/macOS, então nem é passado aqui.
echo "Gerando executável..."
.venv/bin/pyinstaller \
    --onefile \
    --windowed \
    --name "yt-downloader" \
    --collect-all pytubefix \
    --collect-all sv_ttk \
    --paths . \
    yt_downloader/__main__.py

echo
echo "Pronto! Executável gerado em: dist/yt-downloader"

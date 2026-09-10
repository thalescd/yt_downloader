#!/usr/bin/env bash
# Equivalente Linux de setup.bat: prepara o ambiente e abre o app.
set -euo pipefail
# Os comandos abaixo assumem a raiz do projeto, não a pasta scripts/.
cd "$(dirname "$0")/.."

echo "=== YT Downloader - Setup ==="
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERRO: python3 não encontrado no PATH."
    echo "Instale o Python 3.12+ pelo gerenciador de pacotes da sua distribuição."
    exit 1
fi

# No Windows o tkinter vem junto do instalador; no Linux costuma ser um pacote
# à parte, e a falta dele só apareceria como ImportError ao abrir o app.
if ! python3 -c "import tkinter" >/dev/null 2>&1; then
    echo "ERRO: o módulo tkinter não está disponível."
    echo "Instale o pacote correspondente à sua distribuição:"
    echo "  Debian/Ubuntu : sudo apt install python3-tk"
    echo "  Fedora        : sudo dnf install python3-tkinter"
    echo "  Arch          : sudo pacman -S tk"
    exit 1
fi

if [ ! -d .venv ]; then
    echo "Criando ambiente virtual..."
    if ! python3 -m venv .venv; then
        echo "ERRO: falha ao criar o ambiente virtual."
        echo "No Debian/Ubuntu pode faltar o pacote: sudo apt install python3-venv"
        exit 1
    fi
else
    echo "Ambiente virtual já existe, pulando criação."
fi

echo "Instalando dependências..."
.venv/bin/pip install -r requirements.txt

echo
echo "Setup concluído! Abrindo o app..."
exec .venv/bin/python -m yt_downloader

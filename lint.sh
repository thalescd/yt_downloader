#!/usr/bin/env bash
# Equivalente Linux de lint.bat: as mesmas quatro etapas que o CI executa.
set -uo pipefail
cd "$(dirname "$0")"

echo "=== YT Downloader - Verificações ==="
echo

if [ ! -d .venv ]; then
    echo "ERRO: ambiente virtual não encontrado."
    echo "Execute ./setup.sh primeiro."
    exit 1
fi

echo "[1/4] Ruff - estilo e imports..."
if ! .venv/bin/ruff check .; then
    echo 'ERRO: problemas encontrados pelo Ruff. Rode ".venv/bin/ruff check --fix ." para corrigir automaticamente.'
    exit 1
fi

echo "[2/4] Ruff - formatação..."
if ! .venv/bin/ruff format --check .; then
    echo 'ERRO: código fora do padrão de formatação. Rode ".venv/bin/ruff format ." para corrigir automaticamente.'
    exit 1
fi

# --pythonpath amarra a checagem ao venv: sem ele o Pyright resolve os
# imports contra o Python do PATH, que não tem as dependências instaladas.
echo "[3/4] Pyright..."
if ! .venv/bin/pyright --pythonpath .venv/bin/python; then
    echo "ERRO: problemas de tipo encontrados pelo Pyright."
    exit 1
fi

echo "[4/4] Pytest..."
if ! .venv/bin/pytest; then
    echo "ERRO: testes falharam."
    exit 1
fi

echo
echo "Tudo certo!"

#!/usr/bin/env bash
# Casca fina: a lógica do build vive em scripts/tasks.py, uma vez só para
# Windows e Linux.
#
# Atenção: gera um binário para este sistema, não um .exe. O PyInstaller não
# faz compilação cruzada — o executável do Windows precisa ser gerado lá.
set -euo pipefail
cd "$(dirname "$0")/.."

exec python3 scripts/tasks.py build

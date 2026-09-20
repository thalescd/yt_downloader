#!/usr/bin/env bash
# Casca fina: a lógica das tarefas vive em scripts/tasks.py, uma vez só para
# Windows e Linux. Só a checagem do próprio Python fica aqui, porque ela
# precisa acontecer antes de conseguirmos executar qualquer Python.
set -euo pipefail
cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null 2>&1; then
    echo "ERRO: python3 não encontrado no PATH." >&2
    echo "Instale o Python 3.12+ pelo gerenciador de pacotes da sua distribuição." >&2
    exit 1
fi

exec python3 scripts/tasks.py setup

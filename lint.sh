#!/usr/bin/env bash
# Definição única das verificações do projeto: o CI chama este mesmo script,
# de modo que as etapas não precisem ser mantidas em dois lugares.
# O lint.bat é o equivalente para Windows, onde batch e bash não se misturam.
#
# Com .venv, usa as ferramentas dele. Sem .venv — caso do CI, que instala no
# Python do próprio runner —, usa as do PATH.
set -uo pipefail
cd "$(dirname "$0")"

echo "=== YT Downloader - Verificações ==="
echo

if [ -d .venv ]; then
    ruff_cmd=(.venv/bin/ruff)
    # --pythonpath amarra a checagem ao venv: sem ele o Pyright resolve os
    # imports contra o Python do PATH, que não tem as dependências instaladas.
    pyright_cmd=(.venv/bin/pyright --pythonpath .venv/bin/python)
    pytest_cmd=(.venv/bin/pytest)
    corrigir=".venv/bin/ruff"
elif command -v ruff >/dev/null 2>&1; then
    ruff_cmd=(ruff)
    pyright_cmd=(pyright)
    pytest_cmd=(pytest)
    corrigir="ruff"
else
    echo "ERRO: ambiente virtual não encontrado e as ferramentas não estão no PATH."
    echo "Execute ./setup.sh e depois instale as dependências de desenvolvimento:"
    echo "  .venv/bin/pip install -r requirements-dev.txt"
    exit 1
fi

echo "[1/4] Ruff - estilo e imports..."
if ! "${ruff_cmd[@]}" check .; then
    echo "ERRO: problemas encontrados pelo Ruff. Rode \"$corrigir check --fix .\" para corrigir automaticamente."
    exit 1
fi

# env -u: o formatador não aceita --output-format, e reclama se a variável
# estiver definida (o CI a usa para anotar o PR na etapa anterior).
echo "[2/4] Ruff - formatação..."
if ! env -u RUFF_OUTPUT_FORMAT "${ruff_cmd[@]}" format --check .; then
    echo "ERRO: código fora do padrão de formatação. Rode \"$corrigir format .\" para corrigir automaticamente."
    exit 1
fi

echo "[3/4] Pyright..."
if ! "${pyright_cmd[@]}"; then
    echo "ERRO: problemas de tipo encontrados pelo Pyright."
    exit 1
fi

echo "[4/4] Pytest..."
if ! "${pytest_cmd[@]}"; then
    echo "ERRO: testes falharam."
    exit 1
fi

echo
echo "Tudo certo!"

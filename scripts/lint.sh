#!/usr/bin/env bash
# Casca fina: as verificações vivem em scripts/tasks.py, uma vez só para
# Windows e Linux. O CI chama este script, de modo que as etapas não precisem
# ser mantidas em dois lugares.
#
# Com .venv, o tasks.py usa as ferramentas dele. Sem .venv — caso do CI, que
# instala no Python do próprio runner —, usa as do PATH.
set -euo pipefail
cd "$(dirname "$0")/.."

exec python3 scripts/tasks.py lint

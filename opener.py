from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import log

_log = log.get(__name__)


def open_folder(folder: Path) -> None:
    """Abre a pasta no gerenciador de arquivos do sistema.

    Levanta OSError, ou subprocess.CalledProcessError, se o gerenciador não
    puder ser acionado — em ambiente gráfico mínimo o xdg-open pode faltar.
    """
    if sys.platform == "win32":
        os.startfile(folder)
        return

    comando = "open" if sys.platform == "darwin" else "xdg-open"
    _log.info("Abrindo %s com %s", folder, comando)
    subprocess.run([comando, str(folder)], check=True)

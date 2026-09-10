from __future__ import annotations

import sys
from pathlib import Path


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def log_dir() -> Path:
    """Pasta de logs, ao lado do executável.

    O app é portátil: configuração, histórico e logs ficam todos junto do
    executável, e só os downloads vão para fora. Se a pasta for
    somente-leitura, log.setup() cai para stderr em vez de impedir o app
    de abrir.
    """
    return app_dir() / "logs"

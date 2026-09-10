from __future__ import annotations

import os
import sys
from pathlib import Path

from version import APP_NAME


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def log_dir() -> Path:
    """Pasta de logs, sempre gravável pelo usuário.

    Não usa app_dir() de propósito: instalado em Program Files ele é
    somente-leitura, e é exatamente nesse cenário que o log importa.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / APP_NAME / "logs"
    return Path.home() / ".local" / "state" / "yt-downloader" / "logs"

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from paths import log_dir
from version import __version__

_MAX_BYTES = 512 * 1024
_BACKUP_COUNT = 3
_configured = False


def setup() -> None:
    """Configura o logging para arquivo. Silencioso e idempotente.

    Nunca levanta exceção: se o log não puder ser criado, o app segue
    funcionando sem ele.
    """
    global _configured
    if _configured:
        return
    _configured = True

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")

    try:
        directory = log_dir()
        directory.mkdir(parents=True, exist_ok=True)
        handler: logging.Handler = RotatingFileHandler(
            directory / "app.log",
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        handler.setFormatter(fmt)
        root.addHandler(handler)
    except Exception:
        # Sem disco/permissão: cai para stderr, que existe quando rodando
        # via terminal e é descartado no executável --windowed.
        fallback = logging.StreamHandler(sys.stderr)
        fallback.setFormatter(fmt)
        root.addHandler(fallback)

    logging.getLogger(__name__).info("YT Downloader %s iniciado", __version__)


def get(name: str) -> logging.Logger:
    return logging.getLogger(name)

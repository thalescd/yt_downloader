from __future__ import annotations

import configparser
from dataclasses import dataclass

from yt_downloader import log
from yt_downloader.paths import app_dir

_log = log.get(__name__)

_CONFIG_FILE = app_dir() / "config.ini"
_VALID_THEMES = {"dark", "light"}


@dataclass
class Config:
    theme: str = "dark"
    max_entries: int = 100


def load() -> Config:
    cfg = Config()
    if not _CONFIG_FILE.exists():
        return cfg
    parser = configparser.ConfigParser()
    try:
        parser.read(_CONFIG_FILE, encoding="utf-8")
        theme = parser.get("app", "theme", fallback="dark")
        cfg.theme = theme if theme in _VALID_THEMES else "dark"
        max_e = parser.getint("history", "max_entries", fallback=100)
        cfg.max_entries = max_e if max_e > 0 else 100
    except Exception:
        _log.exception("Falha ao ler %s; usando configuração padrão", _CONFIG_FILE)
    return cfg


def save(cfg: Config) -> None:
    _CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    parser = configparser.ConfigParser()
    parser["app"] = {"theme": cfg.theme}
    parser["history"] = {"max_entries": str(cfg.max_entries)}
    with _CONFIG_FILE.open("w", encoding="utf-8") as f:
        parser.write(f)

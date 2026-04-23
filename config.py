from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path

_CONFIG_DIR = Path.home() / ".yt_downloader"
_CONFIG_FILE = _CONFIG_DIR / "config.ini"
_VALID_THEMES = {"dark", "light"}


@dataclass
class Config:
    tema: str = "dark"
    max_entradas: int = 100


def carregar() -> Config:
    cfg = Config()
    if not _CONFIG_FILE.exists():
        return cfg
    parser = configparser.ConfigParser()
    try:
        parser.read(_CONFIG_FILE, encoding="utf-8")
        tema = parser.get("app", "tema", fallback="dark")
        cfg.tema = tema if tema in _VALID_THEMES else "dark"
        max_e = parser.getint("historico", "max_entradas", fallback=100)
        cfg.max_entradas = max_e if max_e > 0 else 100
    except Exception:
        pass
    return cfg


def salvar(cfg: Config) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    parser = configparser.ConfigParser()
    parser["app"] = {"tema": cfg.tema}
    parser["historico"] = {"max_entradas": str(cfg.max_entradas)}
    with _CONFIG_FILE.open("w", encoding="utf-8") as f:
        parser.write(f)

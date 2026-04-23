from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

_HISTORY_FILE = Path.home() / ".yt_downloader" / "historico.json"


def nova_entrada(url: str, titulo: str, tipo: str, resolucao: str, caminho: str) -> dict:
    return {
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "url": url,
        "titulo": titulo,
        "tipo": tipo,
        "resolucao": resolucao,
        "caminho": caminho,
    }


def carregar() -> list[dict]:
    if not _HISTORY_FILE.exists():
        return []
    try:
        return json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def salvar(entrada: dict, max_entradas: int = 100) -> None:
    entradas = carregar()
    entradas.insert(0, entrada)
    _escrever(entradas[:max_entradas])


def salvar_varias(entradas: list[dict], max_entradas: int = 100) -> None:
    existentes = carregar()
    _escrever((entradas + existentes)[:max_entradas])


def limpar() -> None:
    _HISTORY_FILE.unlink(missing_ok=True)


def _escrever(entradas: list[dict]) -> None:
    _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _HISTORY_FILE.write_text(json.dumps(entradas, ensure_ascii=False, indent=2), encoding="utf-8")

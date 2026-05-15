from __future__ import annotations

import json
from datetime import datetime

from paths import app_dir

_HISTORY_FILE = app_dir() / "history.json"


def new_entry(url: str, title: str, media_type: str, resolution: str, path: str) -> dict:
    return {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "url": url,
        "title": title,
        "type": media_type,
        "resolution": resolution,
        "path": path,
    }


def load() -> list[dict]:
    if not _HISTORY_FILE.exists():
        return []
    try:
        return json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save(entry: dict, max_entries: int = 100) -> None:
    entries = load()
    entries.insert(0, entry)
    _write(entries[:max_entries])


def save_many(entries: list[dict], max_entries: int = 100) -> None:
    existing = load()
    _write((entries + existing)[:max_entries])


def clear() -> None:
    _HISTORY_FILE.unlink(missing_ok=True)


def _write(entries: list[dict]) -> None:
    _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _HISTORY_FILE.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

from __future__ import annotations

import json
from pathlib import Path

import pytest

from yt_downloader import history


@pytest.fixture
def history_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "history.json"
    monkeypatch.setattr(history, "_HISTORY_FILE", path)
    return path


def _entry(title: str) -> dict:
    return history.new_entry("https://youtu.be/x", title, "vídeo", "1080p", f"/tmp/{title}.mp4")


def test_new_entry_tem_todos_os_campos() -> None:
    entry = _entry("Vídeo")
    assert set(entry) == {"date", "url", "title", "type", "resolution", "path"}
    assert entry["title"] == "Vídeo"


def test_sem_arquivo_devolve_lista_vazia(history_file: Path) -> None:
    assert history.load() == []


def test_save_insere_no_topo(history_file: Path) -> None:
    history.save(_entry("primeiro"))
    history.save(_entry("segundo"))
    titulos = [e["title"] for e in history.load()]
    assert titulos == ["segundo", "primeiro"]


def test_save_respeita_max_entries(history_file: Path) -> None:
    for i in range(10):
        history.save(_entry(f"v{i}"), max_entries=3)
    entries = history.load()
    assert len(entries) == 3
    assert [e["title"] for e in entries] == ["v9", "v8", "v7"]


def test_save_many_preserva_a_ordem_e_trunca(history_file: Path) -> None:
    history.save(_entry("antigo"))
    history.save_many([_entry("a"), _entry("b")], max_entries=2)
    assert [e["title"] for e in history.load()] == ["a", "b"]


def test_save_many_com_lista_vazia_mantem_o_existente(history_file: Path) -> None:
    history.save(_entry("antigo"))
    history.save_many([], max_entries=100)
    assert [e["title"] for e in history.load()] == ["antigo"]


def test_json_corrompido_devolve_lista_vazia(history_file: Path) -> None:
    history_file.write_text("{quebrado", encoding="utf-8")
    assert history.load() == []


def test_clear_remove_o_arquivo(history_file: Path) -> None:
    history.save(_entry("um"))
    assert history_file.exists()
    history.clear()
    assert not history_file.exists()


def test_clear_sem_arquivo_nao_falha(history_file: Path) -> None:
    history.clear()


def test_acentos_gravados_sem_escape(history_file: Path) -> None:
    history.save(_entry("Coração"))
    assert "Coração" in history_file.read_text(encoding="utf-8")
    assert json.loads(history_file.read_text(encoding="utf-8"))[0]["title"] == "Coração"

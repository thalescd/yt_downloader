from __future__ import annotations

from pathlib import Path

import pytest

from yt_downloader import config


@pytest.fixture
def config_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "config.ini"
    monkeypatch.setattr(config, "_CONFIG_FILE", path)
    return path


def test_sem_arquivo_devolve_padroes(config_file: Path) -> None:
    cfg = config.load()
    assert cfg.theme == "dark"
    assert cfg.max_entries == 100


def test_le_valores_gravados(config_file: Path) -> None:
    config.save(config.Config(theme="light", max_entries=25))
    cfg = config.load()
    assert cfg.theme == "light"
    assert cfg.max_entries == 25


def test_tema_invalido_cai_para_dark(config_file: Path) -> None:
    config_file.write_text("[app]\ntheme = roxo\n", encoding="utf-8")
    assert config.load().theme == "dark"


@pytest.mark.parametrize("valor", ["0", "-5"])
def test_max_entries_nao_positivo_cai_para_100(config_file: Path, valor: str) -> None:
    config_file.write_text(f"[history]\nmax_entries = {valor}\n", encoding="utf-8")
    assert config.load().max_entries == 100


def test_max_entries_nao_numerico_cai_para_100(config_file: Path) -> None:
    config_file.write_text("[history]\nmax_entries = muitos\n", encoding="utf-8")
    assert config.load().max_entries == 100


def test_arquivo_corrompido_nao_derruba_o_app(config_file: Path) -> None:
    config_file.write_text("isso não é um ini válido", encoding="utf-8")
    cfg = config.load()
    assert cfg.theme == "dark"
    assert cfg.max_entries == 100


def test_secoes_ausentes_usam_fallback(config_file: Path) -> None:
    config_file.write_text("[app]\ntheme = light\n", encoding="utf-8")
    cfg = config.load()
    assert cfg.theme == "light"
    assert cfg.max_entries == 100


def test_save_cria_o_diretorio(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    destino = tmp_path / "novo" / "sub" / "config.ini"
    monkeypatch.setattr(config, "_CONFIG_FILE", destino)
    config.save(config.Config())
    assert destino.exists()

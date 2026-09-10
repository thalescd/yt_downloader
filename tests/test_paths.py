from __future__ import annotations

from pathlib import Path

import pytest

from yt_downloader import config, history, paths


def test_config_fica_ao_lado_do_executavel() -> None:
    assert config._CONFIG_FILE.parent == paths.app_dir()


def test_historico_fica_ao_lado_do_executavel() -> None:
    assert history._HISTORY_FILE.parent == paths.app_dir()


def test_logs_ficam_ao_lado_do_executavel() -> None:
    """O app é portátil: nada de estado escondido em AppData."""
    assert paths.log_dir().parent == paths.app_dir()


def test_app_dir_acompanha_o_executavel_quando_congelado(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Com --onefile, sys.executable é o .exe em si, não a pasta temporária
    de extração — é o que faz o modo portátil funcionar."""
    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths.sys, "executable", str(tmp_path / "dist" / "YT Downloader.exe"))
    assert paths.app_dir() == tmp_path / "dist"


def test_app_dir_usa_a_raiz_do_projeto_quando_nao_congelado(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A raiz, não a pasta do pacote: config.ini e logs/ não podem cair
    dentro de yt_downloader/, que é código versionado."""
    monkeypatch.delattr(paths.sys, "frozen", raising=False)
    raiz = Path(paths.__file__).resolve().parents[1]
    assert paths.app_dir() == raiz
    assert paths.app_dir().name == "yt_downloader"
    assert not (paths.app_dir() / "__init__.py").exists()

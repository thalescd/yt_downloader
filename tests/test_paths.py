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


def test_pasta_salva_e_reaproveitada(tmp_path: Path) -> None:
    destino = tmp_path / "Videos"
    destino.mkdir()
    assert paths.download_dir(str(destino)) == destino


def test_sem_pasta_salva_cai_para_downloads() -> None:
    assert paths.download_dir("") == Path.home() / "Downloads"


def test_pasta_que_sumiu_cai_para_downloads(tmp_path: Path) -> None:
    """O caminho salvo pode ter ido embora com o pendrive, ou sido renomeado.
    Melhor abrir em Downloads do que exibir um destino que falharia só na hora
    de baixar."""
    assert paths.download_dir(str(tmp_path / "nao-existe")) == Path.home() / "Downloads"


def test_caminho_que_virou_arquivo_cai_para_downloads(tmp_path: Path) -> None:
    arquivo = tmp_path / "destino"
    arquivo.touch()
    assert paths.download_dir(str(arquivo)) == Path.home() / "Downloads"


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

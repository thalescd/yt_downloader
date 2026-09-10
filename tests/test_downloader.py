from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

import downloader


# --------------------------------------------------------------------------
# Dublês dos objetos do pytubefix (nenhum teste toca a rede)
# --------------------------------------------------------------------------
def _num(value: str | None) -> int:
    """Extrai o prefixo numérico de "1080p" / "128kbps"."""
    if not value:
        return 0
    digits = "".join(c for c in value if c.isdigit())
    return int(digits) if digits else 0


class FakeStream:
    def __init__(
        self,
        resolution: str | None = None,
        abr: str | None = None,
        progressive: bool = False,
        adaptive: bool = False,
        only_video: bool = False,
        only_audio: bool = False,
    ) -> None:
        self.resolution = resolution
        self.abr = abr
        self.progressive = progressive
        self.adaptive = adaptive
        self.only_video = only_video
        self.only_audio = only_audio
        self.default_filename = f"{resolution or abr}.mp4"

    def __repr__(self) -> str:  # pragma: no cover - só ajuda no output do pytest
        return f"<FakeStream {self.resolution or self.abr}>"


class FakeStreamQuery:
    def __init__(self, streams: list[FakeStream]) -> None:
        self._streams = list(streams)

    def filter(self, **criteria) -> FakeStreamQuery:
        result = self._streams
        for key, expected in criteria.items():
            if expected is None:
                continue
            if key == "res":
                result = [s for s in result if s.resolution == expected]
            else:
                result = [s for s in result if getattr(s, key) == expected]
        return FakeStreamQuery(result)

    def order_by(self, attribute: str) -> FakeStreamQuery:
        return FakeStreamQuery(sorted(self._streams, key=lambda s: _num(getattr(s, attribute))))

    def first(self) -> FakeStream | None:
        return self._streams[0] if self._streams else None

    def last(self) -> FakeStream | None:
        return self._streams[-1] if self._streams else None


class FakeYouTube:
    def __init__(self, streams: list[FakeStream], title: str = "Vídeo de Teste") -> None:
        self.streams = FakeStreamQuery(streams)
        self.title = title


def _progressive(*resolutions: str) -> list[FakeStream]:
    return [FakeStream(resolution=r, progressive=True) for r in resolutions]


def _adaptive(*resolutions: str) -> list[FakeStream]:
    return [FakeStream(resolution=r, adaptive=True, only_video=True) for r in resolutions]


def _pick_progressive(streams: list[FakeStream], resolution: str) -> str | None:
    """Resolução escolhida entre os streams progressivos, ou None se não houver.

    O cast existe porque as funções de produção anotam `yt: YouTube`; os dublês
    só precisam expor `.streams`.
    """
    chosen = downloader._get_progressive_stream(cast(Any, FakeYouTube(streams)), resolution)
    return chosen.resolution if chosen else None


def _pick_adaptive(streams: list[FakeStream], resolution: str) -> str | None:
    chosen = downloader._get_adaptive_video_stream(cast(Any, FakeYouTube(streams)), resolution)
    return chosen.resolution if chosen else None


# --------------------------------------------------------------------------
# _sanitize
# --------------------------------------------------------------------------
@pytest.mark.parametrize("char", list('<>:"/\\|?*'))
def test_sanitize_troca_caracteres_proibidos_no_windows(char: str) -> None:
    assert downloader._sanitize(f"a{char}b") == "a_b"


def test_sanitize_remove_caracteres_de_controle() -> None:
    assert downloader._sanitize("a\x00b\x1fc") == "a_b_c"


def test_sanitize_remove_ponto_e_espaco_das_pontas() -> None:
    assert downloader._sanitize("  nome...  ") == "nome"


def test_sanitize_preserva_acentos_e_emoji() -> None:
    assert downloader._sanitize("Ação 🎵") == "Ação 🎵"


def test_sanitize_mantem_nome_ja_valido() -> None:
    assert downloader._sanitize("Vídeo Normal 2024") == "Vídeo Normal 2024"


# --------------------------------------------------------------------------
# _unique_path
# --------------------------------------------------------------------------
def test_unique_path_devolve_o_mesmo_quando_livre(tmp_path: Path) -> None:
    alvo = tmp_path / "v.mp4"
    assert downloader._unique_path(alvo) == alvo


def test_unique_path_numera_na_colisao(tmp_path: Path) -> None:
    alvo = tmp_path / "v.mp4"
    alvo.touch()
    assert downloader._unique_path(alvo) == tmp_path / "v (1).mp4"


def test_unique_path_incrementa_ate_achar_livre(tmp_path: Path) -> None:
    (tmp_path / "v.mp4").touch()
    (tmp_path / "v (1).mp4").touch()
    (tmp_path / "v (2).mp4").touch()
    assert downloader._unique_path(tmp_path / "v.mp4") == tmp_path / "v (3).mp4"


def test_unique_path_preserva_a_extensao(tmp_path: Path) -> None:
    (tmp_path / "musica.webm").touch()
    assert downloader._unique_path(tmp_path / "musica.webm").suffix == ".webm"


# --------------------------------------------------------------------------
# Seleção de stream progressivo
# --------------------------------------------------------------------------
def test_progressive_best_pega_a_maior_resolucao() -> None:
    assert _pick_progressive(_progressive("360p", "720p", "480p"), "best") == "720p"


def test_progressive_devolve_a_resolucao_exata_quando_existe() -> None:
    assert _pick_progressive(_progressive("360p", "480p", "720p"), "480p") == "480p"


def test_progressive_cai_para_a_proxima_resolucao_abaixo() -> None:
    assert _pick_progressive(_progressive("360p", "480p"), "1080p") == "480p"


def test_progressive_ultimo_recurso_entrega_resolucao_maior() -> None:
    """Pedindo 480p com só 720p disponível, o fallback desce sem achar nada e o
    último recurso entrega 720p — ou seja, a qualidade pedida é um teto
    aproximado, não uma garantia."""
    assert _pick_progressive(_progressive("720p"), "480p") == "720p"


def test_progressive_resolucao_desconhecida_comeca_do_topo() -> None:
    assert _pick_progressive(_progressive("360p", "1080p"), "4320p") == "1080p"


def test_progressive_sem_streams_devolve_none() -> None:
    assert _pick_progressive([], "best") is None


# --------------------------------------------------------------------------
# Seleção de stream adaptativo (vídeo separado, exige ffmpeg)
# --------------------------------------------------------------------------
def test_adaptive_best_prefere_1080p() -> None:
    assert _pick_adaptive(_adaptive("360p", "1080p", "720p"), "best") == "1080p"


def test_adaptive_devolve_a_resolucao_exata() -> None:
    assert _pick_adaptive(_adaptive("360p", "720p", "1080p"), "720p") == "720p"


def test_adaptive_cai_para_baixo_quando_falta_a_pedida() -> None:
    assert _pick_adaptive(_adaptive("360p", "480p"), "1080p") == "480p"


def test_adaptive_sem_streams_devolve_none() -> None:
    assert _pick_adaptive([], "720p") is None


def test_adaptive_ignora_streams_de_audio() -> None:
    misto = [*_adaptive("720p"), FakeStream(abr="128kbps", adaptive=True, only_audio=True)]
    assert _pick_adaptive(misto, "best") == "720p"


# --------------------------------------------------------------------------
# ffmpeg
# --------------------------------------------------------------------------
def test_has_ffmpeg_reflete_o_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(downloader.shutil, "which", lambda _: "/usr/bin/ffmpeg")
    assert downloader.has_ffmpeg()
    monkeypatch.setattr(downloader.shutil, "which", lambda _: None)
    assert not downloader.has_ffmpeg()


def test_merge_streams_monta_o_comando_certo(monkeypatch: pytest.MonkeyPatch) -> None:
    capturado: dict = {}

    def fake_run(cmd, **kwargs):
        capturado["cmd"] = cmd
        capturado["kwargs"] = kwargs

    monkeypatch.setattr(downloader.subprocess, "run", fake_run)
    downloader._merge_streams("v.mp4", "a.webm", "saida.mp4")

    assert capturado["cmd"] == [
        "ffmpeg",
        "-y",
        "-i",
        "v.mp4",
        "-i",
        "a.webm",
        "-c",
        "copy",
        "saida.mp4",
    ]
    assert capturado["kwargs"]["check"] is True


def test_download_rejeita_url_invalida(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(*args, **kwargs):
        raise downloader.RegexMatchError("YouTube", "regex")

    monkeypatch.setattr(downloader, "YouTube", explode)
    with pytest.raises(ValueError, match="URL inválida"):
        downloader.download("não é url", False, "/tmp")

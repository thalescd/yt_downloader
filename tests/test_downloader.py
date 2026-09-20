from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from yt_downloader import downloader


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


# --------------------------------------------------------------------------
# Pasta da playlist
# --------------------------------------------------------------------------
def test_playlist_ganha_subpasta_com_o_proprio_nome(tmp_path: Path) -> None:
    destino = downloader._playlist_folder(str(tmp_path), "musicas")
    assert destino == tmp_path / "musicas"
    assert destino.is_dir()


def test_pasta_existente_e_reaproveitada(tmp_path: Path) -> None:
    """Rebaixar a mesma playlist completa a pasta que já existe, em vez de
    criar "musicas (1)" ao lado — os arquivos continuam protegidos um a um."""
    (tmp_path / "musicas").mkdir()
    (tmp_path / "musicas" / "ja-baixado.mp4").touch()

    destino = downloader._playlist_folder(str(tmp_path), "musicas")
    assert destino == tmp_path / "musicas"
    assert (destino / "ja-baixado.mp4").exists()


def test_nome_da_pasta_e_sanitizado(tmp_path: Path) -> None:
    destino = downloader._playlist_folder(str(tmp_path), 'Rock: o "melhor"/2024')
    assert destino == tmp_path / "Rock_ o _melhor__2024"
    assert destino.is_dir()


def test_nome_longo_demais_e_truncado(tmp_path: Path) -> None:
    """O caminho no Windows para em 260 caracteres, e o que a pasta não
    consumir sobra para o nome do vídeo."""
    destino = downloader._playlist_folder(str(tmp_path), "a" * 300)
    assert len(destino.name) == downloader._MAX_FOLDER_NAME


def test_truncagem_nao_deixa_ponto_no_fim(tmp_path: Path) -> None:
    """O Windows recusa pasta terminada em ponto, e o corte pode criar uma."""
    titulo = "b" * (downloader._MAX_FOLDER_NAME - 1) + ".. sufixo"
    destino = downloader._playlist_folder(str(tmp_path), titulo)
    assert not destino.name.endswith((".", " "))
    assert destino.is_dir()


@pytest.mark.parametrize("titulo", ["", "   ", "..."])
def test_titulo_inutilizavel_cai_no_destino_escolhido(tmp_path: Path, titulo: str) -> None:
    assert downloader._playlist_folder(str(tmp_path), titulo) == tmp_path


def test_titulo_so_de_caracteres_proibidos_vira_sublinhados(tmp_path: Path) -> None:
    """Não é o mesmo caso do título vazio: "///" tem conteúdo, e o sanitizador
    troca proibido por "_" como faz em qualquer nome de arquivo do app."""
    assert downloader._playlist_folder(str(tmp_path), "///") == tmp_path / "___"


def test_nome_ocupado_por_arquivo_cai_no_destino_escolhido(tmp_path: Path) -> None:
    """Perder o agrupamento é melhor do que abortar o download inteiro."""
    (tmp_path / "musicas").touch()
    assert downloader._playlist_folder(str(tmp_path), "musicas") == tmp_path


# --------------------------------------------------------------------------
# download_playlist usa a subpasta
# --------------------------------------------------------------------------
class FakePlaylist:
    """`title` é property porque no pytubefix também é — e é justamente por
    fazer parsing na hora do acesso que ela pode levantar."""

    def __init__(self, titulo: str = "Minha Playlist", quantos: int = 2) -> None:
        self._titulo = titulo
        self.video_urls = [f"https://youtu.be/v{i}" for i in range(quantos)]

    @property
    def title(self) -> str:
        return self._titulo


class PlaylistSemTitulo(FakePlaylist):
    """Playlist cujo título explode ao ser lido, como quando o YouTube muda o
    layout da página e o parsing do pytubefix deixa de casar."""

    @property
    def title(self) -> str:
        raise KeyError("title")


def _playlist_com(monkeypatch: pytest.MonkeyPatch, pl: FakePlaylist) -> list[str]:
    """Aparelha download_playlist e devolve a lista que recebe cada destino."""
    destinos: list[str] = []
    monkeypatch.setattr(downloader, "Playlist", lambda url: pl)
    monkeypatch.setattr(downloader, "YouTube", lambda url, **kw: FakeYouTube([], "Vídeo"))
    monkeypatch.setattr(
        downloader,
        "_download_video",
        lambda yt, audio, out, res: (destinos.append(out), (f"{out}/x.mp4", "720p"))[1],
    )
    return destinos


def test_videos_da_playlist_vao_para_a_subpasta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destinos = _playlist_com(monkeypatch, FakePlaylist("musicas"))
    downloader.download_playlist("https://youtube.com/playlist?list=x", False, str(tmp_path))
    assert destinos == [str(tmp_path / "musicas")] * 2


def test_cada_item_traz_a_url_do_proprio_video(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A url da playlist em todas as linhas do histórico impediria voltar a um
    vídeo específico pelo botão "Copiar URL"."""
    pl = FakePlaylist("musicas", quantos=3)
    _playlist_com(monkeypatch, pl)
    baixados, _ = downloader.download_playlist(
        "https://youtube.com/playlist?list=x", False, str(tmp_path)
    )
    assert [url for url, _, _ in baixados] == pl.video_urls


def test_item_baixado_tem_url_caminho_e_qualidade(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _playlist_com(monkeypatch, FakePlaylist("musicas", quantos=1))
    baixados, _ = downloader.download_playlist(
        "https://youtube.com/playlist?list=x", False, str(tmp_path)
    )
    url, caminho, qualidade = baixados[0]
    assert url.startswith("https://")
    assert caminho.endswith(".mp4")
    assert qualidade == "720p"


def test_titulo_que_explode_nao_derruba_a_playlist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """O título é só o nome da pasta: sem ele os vídeos ainda baixam, soltos
    no destino escolhido."""
    destinos = _playlist_com(monkeypatch, PlaylistSemTitulo())
    baixados, falhas = downloader.download_playlist(
        "https://x/playlist?list=y", False, str(tmp_path)
    )
    assert destinos == [str(tmp_path)] * 2
    assert len(baixados) == 2 and not falhas


def test_playlist_vazia_continua_reclamando(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _playlist_com(monkeypatch, FakePlaylist(quantos=0))
    with pytest.raises(RuntimeError, match="não contém vídeos"):
        downloader.download_playlist("https://x/playlist?list=y", False, str(tmp_path))

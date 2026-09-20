from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from pytubefix import Playlist, YouTube
from pytubefix.exceptions import RegexMatchError

from yt_downloader import log

_log = log.get(__name__)

_RESOLUTION_FALLBACK = ["1080p", "720p", "480p", "360p"]

# Títulos de playlist podem ser bem longos, e o Windows ainda impõe 260
# caracteres de caminho. O que o nome da pasta não consumir sobra para o nome
# do vídeo, que costuma ser igualmente comprido.
_MAX_FOLDER_NAME = 120


def download(
    url: str,
    audio_only: bool,
    output_path: str,
    on_progress=None,
    resolution: str = "best",
) -> tuple[str, str]:
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
    except RegexMatchError:
        raise ValueError("URL inválida. Verifique o link e tente novamente.")
    return _download_video(yt, audio_only, output_path, resolution)


def download_playlist(
    url: str,
    audio_only: bool,
    output_path: str,
    on_progress=None,
    on_video_start: Optional[Callable[[int, int, str], None]] = None,
    resolution: str = "best",
) -> tuple[list[tuple[str, str, str]], list[tuple[str, str]]]:
    """Baixa a playlist inteira, sem deixar que uma falha derrube o resto.

    Cada item baixado volta como (url do vídeo, caminho, qualidade). A url é
    a de cada vídeo, e não a da playlist, porque é ela que vai para o
    histórico: registrar o link da playlist em todas as linhas tornaria
    impossível voltar a um vídeo específico a partir dali.
    """
    pl = Playlist(url)
    urls = list(pl.video_urls)
    if not urls:
        raise RuntimeError("A playlist não contém vídeos disponíveis.")

    try:
        titulo = pl.title or ""
    except Exception:
        # O título é só o nome da pasta: sem ele os vídeos ainda baixam,
        # apenas soltos no destino escolhido.
        _log.exception("Não foi possível ler o título da playlist %s", url)
        titulo = ""
    destino = str(_playlist_folder(output_path, titulo))

    total = len(urls)
    downloaded: list[tuple[str, str, str]] = []
    failed: list[tuple[str, str]] = []

    for index, video_url in enumerate(urls, start=1):
        try:
            yt = YouTube(video_url, on_progress_callback=on_progress)
            if on_video_start:
                on_video_start(index, total, yt.title)
            caminho, qualidade = _download_video(yt, audio_only, destino, resolution)
            downloaded.append((video_url, caminho, qualidade))
        except Exception as exc:
            failed.append((video_url, str(exc)))

    return downloaded, failed


def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _get_progressive_stream(yt: YouTube, resolution: str):
    if resolution == "best":
        return yt.streams.filter(progressive=True).order_by("resolution").last()
    start = _RESOLUTION_FALLBACK.index(resolution) if resolution in _RESOLUTION_FALLBACK else 0
    for res in _RESOLUTION_FALLBACK[start:]:
        stream = yt.streams.filter(progressive=True, res=res).first()
        if stream:
            return stream
    return yt.streams.filter(progressive=True).order_by("resolution").last()


def _get_adaptive_video_stream(yt: YouTube, resolution: str):
    if resolution == "best":
        for res in _RESOLUTION_FALLBACK:
            stream = yt.streams.filter(adaptive=True, only_video=True, res=res).first()
            if stream:
                return stream
        return yt.streams.filter(adaptive=True, only_video=True).first()
    start = _RESOLUTION_FALLBACK.index(resolution) if resolution in _RESOLUTION_FALLBACK else 0
    for res in _RESOLUTION_FALLBACK[start:]:
        stream = yt.streams.filter(adaptive=True, only_video=True, res=res).first()
        if stream:
            return stream
    return None


def _sanitize(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(". ")


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    counter = 1
    while True:
        candidate = path.parent / f"{path.stem} ({counter}){path.suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _playlist_folder(output_path: str, title: str) -> Path:
    """Subpasta com o nome da playlist, dentro do destino escolhido.

    Uma pasta já existente é reaproveitada de propósito: baixar a mesma
    playlist de novo deve completar o que está lá, e não criar "musicas (1)"
    ao lado. Os arquivos seguem protegidos um a um por `_unique_path`, então
    reaproveitar a pasta não sobrescreve nada.

    Sem título utilizável, ou se o nome já estiver ocupado por um arquivo,
    devolve o próprio destino: perder o agrupamento é bem melhor do que
    perder o download inteiro.
    """
    nome = _sanitize(title)[:_MAX_FOLDER_NAME].strip(". ")
    if not nome:
        return Path(output_path)

    destino = Path(output_path) / nome
    try:
        destino.mkdir(parents=True, exist_ok=True)
    except OSError:
        _log.exception("Não foi possível criar %s; salvando direto em %s", destino, output_path)
        return Path(output_path)
    return destino


def _target_name(stream) -> str:
    """Nome final do arquivo: base sanitizada por nós, extensão escolhida pelo
    pytubefix.

    A extensão vem de `default_filename` de propósito — acessá-lo é o que faz o
    pytubefix trocar o subtype para m4a em streams de áudio. Já a base passa por
    `_sanitize`, garantindo o mesmo nome com e sem ffmpeg (o pytubefix apagaria
    os caracteres inválidos, enquanto nós os substituímos por "_").
    """
    raw = stream.default_filename
    base, _, ext = raw.rpartition(".")
    if not ext:
        return _sanitize(raw)
    return f"{_sanitize(base)}.{ext}"


def _download_temp(stream, output_path: str, prefix: str) -> str:
    """Baixa um stream para arquivo temporário, que o chamador deve remover.

    `skip_existing=False` evita reaproveitar um temporário deixado para trás por
    um encerramento abrupto.
    """
    target = Path(output_path) / f"{prefix}{_target_name(stream)}"
    try:
        result = stream.download(output_path=output_path, filename=target.name, skip_existing=False)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    if result is None:
        raise RuntimeError("O download falhou sem retornar o caminho do arquivo.")
    return result


def _merge_streams(video_path: str, audio_path: str, output_path: str) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-i", audio_path, "-c", "copy", output_path],
        check=True,
        capture_output=True,
    )


def _safe_download(stream, output_path: str) -> str:
    """Baixa um stream para um nome livre, sem nunca sobrescrever.

    O nome vai explícito no `filename` porque o padrão do pytubefix
    (`skip_existing=True`) pula o download quando já existe um arquivo de mesmo
    nome e mesmo tamanho, e trunca o existente quando o tamanho difere — dois
    vídeos distintos de mesmo título bastam para causar perda. Passando um nome
    único, nenhum dos dois casos ocorre, e o caminho do parcial que limpamos em
    caso de falha é de fato o que o pytubefix escreve.
    """
    target = _unique_path(Path(output_path) / _target_name(stream))
    try:
        result = stream.download(output_path=output_path, filename=target.name)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    if result is None:
        raise RuntimeError("O download falhou sem retornar o caminho do arquivo.")
    return result


def _download_video(
    yt: YouTube, audio_only: bool, output_path: str, resolution: str = "best"
) -> tuple[str, str]:
    if audio_only:
        stream = yt.streams.filter(only_audio=True).first()
        if not stream:
            raise RuntimeError("Nenhum stream de áudio disponível para este vídeo.")
        return _safe_download(stream, output_path), "áudio"

    if has_ffmpeg():
        vid = _get_adaptive_video_stream(yt, resolution)
        aud = yt.streams.filter(only_audio=True).order_by("abr").last()
        if vid and aud:
            actual_res = vid.resolution or "desconhecida"
            tmp_vid = _download_temp(vid, output_path, "_tmpv_")
            try:
                tmp_aud = _download_temp(aud, output_path, "_tmpa_")
                try:
                    out = _unique_path(Path(output_path) / f"{_sanitize(yt.title)}.mp4")
                    _merge_streams(tmp_vid, tmp_aud, str(out))
                    return str(out), actual_res
                finally:
                    Path(tmp_aud).unlink(missing_ok=True)
            finally:
                Path(tmp_vid).unlink(missing_ok=True)

    # Fallback: progressive only
    stream = _get_progressive_stream(yt, resolution)
    if not stream:
        hint = "" if has_ffmpeg() else " Instale o ffmpeg para mais opções de qualidade."
        raise RuntimeError(f"Nenhum stream de vídeo disponível para este vídeo.{hint}")
    return _safe_download(stream, output_path), stream.resolution or "desconhecida"

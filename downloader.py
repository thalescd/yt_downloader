from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from pytubefix import Playlist, YouTube
from pytubefix.exceptions import RegexMatchError

_RESOLUTION_FALLBACK = ["720p", "480p", "360p"]
_ADAPTIVE_BEST = ["1080p", "720p", "480p", "360p"]


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
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    pl = Playlist(url)
    urls = list(pl.video_urls)
    if not urls:
        raise RuntimeError("A playlist não contém vídeos disponíveis.")
    total = len(urls)
    downloaded: list[tuple[str, str]] = []
    failed: list[tuple[str, str]] = []

    for index, video_url in enumerate(urls, start=1):
        try:
            yt = YouTube(video_url, on_progress_callback=on_progress)
            if on_video_start:
                on_video_start(index, total, yt.title)
            downloaded.append(_download_video(yt, audio_only, output_path, resolution))
        except Exception as exc:
            failed.append((video_url, str(exc)))

    return downloaded, failed


def _has_ffmpeg() -> bool:
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
        for res in _ADAPTIVE_BEST:
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


def _merge_streams(video_path: str, audio_path: str, output_path: str) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-i", audio_path, "-c", "copy", output_path],
        check=True,
        capture_output=True,
    )


def _safe_download(stream, output_path: str) -> str:
    partial = Path(output_path) / stream.default_filename
    try:
        result = stream.download(output_path=output_path)
    except Exception:
        partial.unlink(missing_ok=True)
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

    if _has_ffmpeg():
        vid = _get_adaptive_video_stream(yt, resolution)
        aud = yt.streams.filter(only_audio=True).order_by("abr").last()
        if vid and aud:
            actual_res = vid.resolution or "desconhecida"
            tmp_vid = vid.download(output_path=output_path, filename_prefix="_tmpv_")
            if tmp_vid is None:
                raise RuntimeError("Download do stream de vídeo falhou.")
            try:
                tmp_aud = aud.download(output_path=output_path, filename_prefix="_tmpa_")
                if tmp_aud is None:
                    raise RuntimeError("Download do stream de áudio falhou.")
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
        hint = "" if _has_ffmpeg() else " Instale o ffmpeg para mais opções de qualidade."
        raise RuntimeError(f"Nenhum stream de vídeo disponível para este vídeo.{hint}")
    return _safe_download(stream, output_path), stream.resolution or "desconhecida"

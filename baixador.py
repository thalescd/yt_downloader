from pathlib import Path

from pytubefix import YouTube
from pytubefix.exceptions import RegexMatchError


def download(url: str, audio_only: bool, output_path: str, on_progress=None) -> str:
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
    except RegexMatchError:
        raise ValueError("URL inválida. Verifique o link e tente novamente.")

    if audio_only:
        stream = yt.streams.filter(only_audio=True).first()
        if not stream:
            raise RuntimeError("Nenhum stream de áudio disponível para este vídeo.")
    else:
        stream = yt.streams.get_highest_resolution()
        if not stream:
            raise RuntimeError("Nenhum stream de vídeo disponível para este vídeo.")

    partial = Path(output_path) / stream.default_filename
    try:
        result = stream.download(output_path=output_path)
    except Exception:
        partial.unlink(missing_ok=True)
        raise
    if result is None:
        raise RuntimeError("O download falhou sem retornar o caminho do arquivo.")
    return result

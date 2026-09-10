from __future__ import annotations

import pytest

from yt_downloader import urls


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/abc123",
        "https://www.youtube.com/live/abc123",
        "https://www.youtube.com/playlist?list=PL123",
        "https://music.youtube.com/watch?v=abc",
    ],
)
def test_aceita_urls_do_youtube(url: str) -> None:
    assert urls.is_valid_youtube_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "",
        "https://vimeo.com/12345",
        "https://youtube.com",
        "não é uma url",
        "https://example.com/watch?v=abc",
    ],
)
def test_rejeita_urls_de_fora(url: str) -> None:
    assert not urls.is_valid_youtube_url(url)


def test_validacao_ignora_maiusculas() -> None:
    assert urls.is_valid_youtube_url("HTTPS://WWW.YOUTUBE.COM/WATCH?V=ABC")


def test_detecta_youtube_music() -> None:
    assert urls.is_youtube_music("https://music.youtube.com/watch?v=abc")
    assert not urls.is_youtube_music("https://www.youtube.com/watch?v=abc")


def test_detecta_playlist() -> None:
    assert urls.is_playlist("https://www.youtube.com/playlist?list=PL123")
    assert not urls.is_playlist("https://www.youtube.com/watch?v=abc")


def test_video_dentro_de_playlist_nao_conta_como_playlist() -> None:
    """Um /watch com &list= baixa só o vídeo, não a playlist inteira."""
    assert not urls.is_playlist("https://www.youtube.com/watch?v=abc&list=PL123")

from __future__ import annotations

_VALID_HOSTS = (
    "youtube.com/watch",
    "youtu.be/",
    "youtube.com/shorts/",
    "youtube.com/live/",
    "youtube.com/playlist",
    "music.youtube.com",
)


def is_youtube_music(url: str) -> bool:
    return "music.youtube.com" in url.lower()


def is_playlist(url: str) -> bool:
    return "youtube.com/playlist" in url.lower()


def is_valid_youtube_url(url: str) -> bool:
    lowered = url.lower()
    return any(host in lowered for host in _VALID_HOSTS)

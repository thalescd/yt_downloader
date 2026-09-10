"""Ponto de entrada: `python -m yt_downloader`."""

from __future__ import annotations

from yt_downloader import log
from yt_downloader.app import App


def main() -> None:
    log.setup()
    App().mainloop()


if __name__ == "__main__":
    main()

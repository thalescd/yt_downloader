import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import sv_ttk

from baixador import download


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YT Downloader")
        self.resizable(False, False)
        self._queue = queue.Queue()
        sv_ttk.set_theme("dark")
        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=24)
        frame.grid()

        ttk.Label(frame, text="YT Downloader", font=("", 14, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 16)
        )

        ttk.Label(frame, text="URL do vídeo:").grid(row=1, column=0, sticky="w")
        self._url_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._url_var, width=52).grid(
            row=2, column=0, columnspan=2, pady=(2, 12)
        )

        self._type_var = tk.StringVar(value="video")
        type_frame = ttk.Frame(frame)
        type_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 12))
        ttk.Radiobutton(type_frame, text="Vídeo", variable=self._type_var, value="video").pack(
            side="left", padx=(0, 12)
        )
        ttk.Radiobutton(type_frame, text="Áudio", variable=self._type_var, value="audio").pack(
            side="left"
        )

        ttk.Label(frame, text="Pasta de destino:").grid(row=4, column=0, sticky="w")
        self._path_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        ttk.Entry(frame, textvariable=self._path_var, width=42, state="readonly").grid(
            row=5, column=0, pady=(2, 12), sticky="w"
        )
        ttk.Button(frame, text="Selecionar...", command=self._select_folder).grid(
            row=5, column=1, padx=(6, 0), pady=(2, 12)
        )

        self._progress_var = tk.DoubleVar()
        ttk.Progressbar(frame, variable=self._progress_var, maximum=100, length=430).grid(
            row=6, column=0, columnspan=2, pady=(0, 6)
        )

        self._status_var = tk.StringVar(value="Pronto.")
        ttk.Label(frame, textvariable=self._status_var).grid(row=7, column=0, columnspan=2)

        self._btn = ttk.Button(frame, text="Baixar", command=self._start_download)
        self._btn.grid(row=8, column=0, columnspan=2, pady=(16, 0), ipadx=16, ipady=4)

    def _select_folder(self):
        path = filedialog.askdirectory(initialdir=self._path_var.get())
        if path:
            self._path_var.set(path)

    @staticmethod
    def _is_valid_youtube_url(url: str) -> bool:
        url = url.lower()
        return any(
            host in url
            for host in (
                "youtube.com/watch",
                "youtu.be/",
                "youtube.com/shorts/",
                "youtube.com/live/",
            )
        )

    def _start_download(self):
        url = self._url_var.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Digite uma URL antes de baixar.")
            return
        if not self._is_valid_youtube_url(url):
            messagebox.showwarning(
                "Aviso",
                "URL inválida. Use um link do YouTube válido.\nExemplo: https://youtube.com/watch?v=...",
            )
            return

        self._btn.config(state="disabled")
        self._progress_var.set(0)
        self._status_var.set("Conectando...")

        threading.Thread(
            target=self._run_download,
            args=(url, self._type_var.get() == "audio", self._path_var.get()),
            daemon=True,
        ).start()

        self.after(100, self._poll_queue)

    def _run_download(self, url: str, audio_only: bool, output_path: str):
        try:
            result = download(url, audio_only, output_path, on_progress=self._on_progress)
            self._queue.put(("done", result))
        except Exception as exc:
            self._queue.put(("error", str(exc)))

    def _on_progress(self, stream, chunk, bytes_remaining: int):
        if not stream.filesize:
            return
        pct = (stream.filesize - bytes_remaining) / stream.filesize * 100
        self._queue.put(("progress", pct))

    def _poll_queue(self):
        try:
            while True:
                kind, value = self._queue.get_nowait()
                if kind == "progress":
                    self._progress_var.set(value)
                    self._status_var.set(f"Baixando... {value:.0f}%")
                elif kind == "done":
                    self._progress_var.set(100)
                    self._status_var.set("Concluído.")
                    self._btn.config(state="normal")
                    messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{value}")
                    return
                elif kind == "error":
                    self._status_var.set("Erro ao baixar.")
                    self._btn.config(state="normal")
                    messagebox.showerror("Erro", value)
                    return
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)


if __name__ == "__main__":
    App().mainloop()

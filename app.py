from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Optional

import sv_ttk

import config as cfg_module
import historico
from baixador import download, download_playlist


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YT Downloader")
        self.resizable(False, False)
        self._queue = queue.Queue()
        self._cfg = cfg_module.carregar()
        sv_ttk.set_theme(self._cfg.tema)
        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=24)
        frame.grid()

        ttk.Label(frame, text="YT Downloader", font=("", 14, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 16)
        )
        self._dark_var = tk.BooleanVar(value=self._cfg.tema == "dark")
        ttk.Checkbutton(
            frame,
            text="Modo escuro",
            variable=self._dark_var,
            command=self._on_toggle_tema,
        ).grid(row=0, column=1, sticky="e", pady=(0, 16))

        ttk.Label(frame, text="URL do vídeo:").grid(row=1, column=0, sticky="w")
        self._url_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self._url_var, width=52).grid(
            row=2, column=0, columnspan=2, pady=(2, 12)
        )

        self._type_var = tk.StringVar(value="video")
        type_frame = ttk.Frame(frame)
        type_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 12))
        self._radio_video = ttk.Radiobutton(
            type_frame, text="Vídeo", variable=self._type_var, value="video"
        )
        self._radio_video.pack(side="left", padx=(0, 12))
        self._radio_audio = ttk.Radiobutton(
            type_frame, text="Áudio", variable=self._type_var, value="audio"
        )
        self._radio_audio.pack(side="left")
        self._url_var.trace_add("write", self._on_url_change)
        self._type_var.trace_add("write", self._on_type_change)

        ttk.Label(frame, text="Qualidade:").grid(row=4, column=0, sticky="w")
        self._quality_var = tk.StringVar(value="Melhor disponível")
        self._quality_combo = ttk.Combobox(
            frame,
            textvariable=self._quality_var,
            values=["Melhor disponível", "720p", "480p", "360p"],
            state="readonly",
            width=20,
        )
        self._quality_combo.grid(row=5, column=0, columnspan=2, sticky="w", pady=(2, 12))

        ttk.Label(frame, text="Pasta de destino:").grid(row=6, column=0, sticky="w")
        self._path_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        ttk.Entry(frame, textvariable=self._path_var, width=42, state="readonly").grid(
            row=7, column=0, pady=(2, 12), sticky="w"
        )
        ttk.Button(frame, text="Selecionar...", command=self._select_folder).grid(
            row=7, column=1, padx=(6, 0), pady=(2, 12)
        )

        self._progress_var = tk.DoubleVar()
        ttk.Progressbar(frame, variable=self._progress_var, maximum=100, length=430).grid(
            row=8, column=0, columnspan=2, pady=(0, 6)
        )

        self._status_var = tk.StringVar(value="Pronto.")
        ttk.Label(frame, textvariable=self._status_var).grid(row=9, column=0, columnspan=2)

        self._btn = ttk.Button(frame, text="Baixar", command=self._start_download)
        self._btn.grid(row=10, column=0, pady=(16, 0), ipadx=16, ipady=4, sticky="ew")
        ttk.Button(frame, text="Histórico", command=self._abrir_historico).grid(
            row=10, column=1, pady=(16, 0), padx=(6, 0), ipady=4, sticky="ew"
        )

    def _abrir_historico(self) -> None:
        HistoricoWindow(self)

    def _on_toggle_tema(self) -> None:
        theme = "dark" if self._dark_var.get() else "light"
        sv_ttk.set_theme(theme)
        self._cfg.tema = theme
        try:
            cfg_module.salvar(self._cfg)
        except Exception as exc:
            messagebox.showwarning(
                "Aviso", f"Não foi possível salvar a preferência de tema:\n{exc}"
            )

    def _select_folder(self):
        path = filedialog.askdirectory(initialdir=self._path_var.get())
        if path:
            self._path_var.set(path)

    @staticmethod
    def _is_youtube_music_url(url: str) -> bool:
        return "music.youtube.com" in url.lower()

    @staticmethod
    def _is_playlist_url(url: str) -> bool:
        return "youtube.com/playlist" in url.lower()

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
                "youtube.com/playlist",
                "music.youtube.com",
            )
        )

    def _update_quality_state(self) -> None:
        is_audio = self._type_var.get() == "audio"
        self._quality_combo.config(state="disabled" if is_audio else "readonly")

    def _on_type_change(self, _name: str, _index: str, _mode: str) -> None:
        self._update_quality_state()

    def _on_url_change(self, _name: str, _index: str, _mode: str) -> None:
        url = self._url_var.get()
        if self._is_youtube_music_url(url):
            self._type_var.set("audio")
            self._radio_video.config(state="disabled")
            self._radio_audio.config(state="normal")
        else:
            self._radio_video.config(state="normal")
            self._radio_audio.config(state="normal")
        self._update_quality_state()

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

        audio_only = self._type_var.get() == "audio"
        quality = self._quality_var.get()
        resolution = "best" if quality == "Melhor disponível" else quality
        self._current_url = url
        self._current_audio_only = audio_only
        self._current_resolution = resolution

        threading.Thread(
            target=self._run_download,
            args=(url, audio_only, self._path_var.get(), resolution),
            daemon=True,
        ).start()

        self.after(100, self._poll_queue)

    def _on_video_start(self, index: int, total: int, title: str) -> None:
        self._queue.put(("video_start", (index, total, title)))

    def _run_download(self, url: str, audio_only: bool, output_path: str, resolution: str):
        try:
            if self._is_playlist_url(url):
                self._queue.put(("playlist_loading", None))
                downloaded, failed = download_playlist(
                    url,
                    audio_only,
                    output_path,
                    on_progress=self._on_progress,
                    on_video_start=self._on_video_start,
                    resolution=resolution,
                )
                self._queue.put(("done_playlist", (downloaded, failed)))
            else:
                result = download(
                    url,
                    audio_only,
                    output_path,
                    on_progress=self._on_progress,
                    resolution=resolution,
                )
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
                elif kind == "playlist_loading":
                    self._status_var.set("Carregando playlist...")
                elif kind == "video_start":
                    index, total, title = value
                    short_title = title[:50] + "..." if len(title) > 50 else title
                    self._progress_var.set(0)
                    self._status_var.set(f"Baixando {index} de {total} — {short_title}")
                elif kind == "done":
                    filepath, actual_res = value
                    self._progress_var.set(100)
                    self._status_var.set("Concluído.")
                    self._btn.config(state="normal")
                    try:
                        tipo = "áudio" if self._current_audio_only else "vídeo"
                        historico.salvar(
                            historico.nova_entrada(
                                self._current_url,
                                Path(filepath).stem,
                                tipo,
                                actual_res,
                                filepath,
                            ),
                            self._cfg.max_entradas,
                        )
                    except Exception:
                        pass
                    messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{filepath}")
                    return
                elif kind == "done_playlist":
                    downloaded, failed = value
                    self._progress_var.set(100)
                    self._btn.config(state="normal")
                    try:
                        tipo = "áudio" if self._current_audio_only else "vídeo"
                        entradas = [
                            historico.nova_entrada(
                                self._current_url,
                                Path(fp).stem,
                                tipo,
                                actual_res,
                                fp,
                            )
                            for fp, actual_res in downloaded
                        ]
                        if entradas:
                            historico.salvar_varias(entradas, self._cfg.max_entradas)
                    except Exception:
                        pass
                    if failed:
                        visible = failed[:5]
                        fail_msgs = "\n".join(f"• {url}: {reason}" for url, reason in visible)
                        if len(failed) > 5:
                            fail_msgs += f"\n...e mais {len(failed) - 5} falha(s)."
                        self._status_var.set(f"Concluído com {len(failed)} falha(s).")
                        messagebox.showwarning(
                            "Concluído com falhas",
                            f"{len(downloaded)} baixado(s), {len(failed)} falha(s):\n\n{fail_msgs}",
                        )
                    else:
                        self._status_var.set(f"Concluído. {len(downloaded)} arquivo(s) baixados.")
                        messagebox.showinfo(
                            "Sucesso", f"{len(downloaded)} arquivo(s) baixados com sucesso."
                        )
                    return
                elif kind == "error":
                    self._status_var.set("Erro ao baixar.")
                    self._btn.config(state="normal")
                    messagebox.showerror("Erro", value)
                    return
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)


class HistoricoWindow(tk.Toplevel):
    def __init__(self, parent: App):
        super().__init__(parent)
        self.title("Histórico de Downloads")
        self.resizable(True, True)
        self.geometry("900x400")
        self._entradas: list[dict] = []
        self._build_ui()
        self._carregar()

    def _build_ui(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        frame = ttk.Frame(self, padding=12)
        frame.grid(sticky="nsew")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        cols = ("data", "titulo", "tipo", "qualidade", "caminho")
        self._tree = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        self._tree.heading("data", text="Data")
        self._tree.heading("titulo", text="Título")
        self._tree.heading("tipo", text="Tipo")
        self._tree.heading("qualidade", text="Qualidade")
        self._tree.heading("caminho", text="Pasta")
        self._tree.column("data", width=140, stretch=False)
        self._tree.column("titulo", width=260)
        self._tree.column("tipo", width=55, stretch=False)
        self._tree.column("qualidade", width=90, stretch=False)
        self._tree.column("caminho", width=260)
        self._tree.grid(row=0, column=0, sticky="nsew")

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self._tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=scroll.set)
        self._tree.bind("<Double-1>", lambda _: self._copiar_url())

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky="ew")
        ttk.Button(btn_frame, text="Copiar URL", command=self._copiar_url).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(btn_frame, text="Abrir pasta", command=self._abrir_pasta).pack(side="left")
        ttk.Button(btn_frame, text="Limpar histórico", command=self._limpar).pack(side="right")

    def _carregar(self) -> None:
        self._entradas = historico.carregar()
        self._tree.delete(*self._tree.get_children())
        for e in self._entradas:
            pasta = str(Path(e.get("caminho", "")).parent) if e.get("caminho") else ""
            self._tree.insert(
                "",
                "end",
                values=(e["data"], e["titulo"], e["tipo"], e.get("resolucao", ""), pasta),
            )

    def _selected_entry(self) -> Optional[dict]:
        sel = self._tree.selection()
        if not sel:
            return None
        return self._entradas[self._tree.index(sel[0])]

    def _copiar_url(self) -> None:
        entry = self._selected_entry()
        if not entry:
            messagebox.showwarning("Aviso", "Selecione um item primeiro.", parent=self)
            return
        self.clipboard_clear()
        self.clipboard_append(entry["url"])
        self.update()

    def _abrir_pasta(self) -> None:
        entry = self._selected_entry()
        if not entry:
            messagebox.showwarning("Aviso", "Selecione um item primeiro.", parent=self)
            return
        pasta = Path(entry["caminho"]).parent
        if not pasta.exists():
            messagebox.showwarning("Aviso", "A pasta não existe mais.", parent=self)
            return
        os.startfile(pasta)

    def _limpar(self) -> None:
        if not messagebox.askyesno("Confirmar", "Limpar todo o histórico?", parent=self):
            return
        historico.limpar()
        self._carregar()


if __name__ == "__main__":
    App().mainloop()

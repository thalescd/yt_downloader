"""Nomeação de arquivo e proteção contra sobrescrita.

Cobre o defeito em que o caminho sem ffmpeg (e o modo áudio, sempre) pulava o
download ou truncava um arquivo existente, enquanto o caminho com ffmpeg
numerava o nome — mesma ação do usuário, resultados diferentes.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pytubefix.file_system import file_system_verify

from yt_downloader import downloader


class RecordingStream:
    """Dublê que reproduz a semântica de Stream.download() do pytubefix.

    Em especial: aplica a tabela de tradução do sistema de arquivos ao nome
    recebido, honra skip_existing e trunca o arquivo quando o tamanho difere.
    """

    def __init__(self, title: str = "Vídeo", subtype: str = "mp4", size: int = 100) -> None:
        self._title = title
        self.subtype = subtype
        self.filesize = size
        self.resolution = "720p"
        self.calls: list[dict] = []

    @property
    def default_filename(self) -> str:
        return f"{self._title}.{self.subtype}"

    def download(
        self,
        output_path: str,
        filename: str | None = None,
        filename_prefix: str | None = None,
        skip_existing: bool = True,
    ) -> str:
        self.calls.append(
            {"filename": filename, "prefix": filename_prefix, "skip_existing": skip_existing}
        )
        nome = (filename or self.default_filename).translate(file_system_verify("NTFS"))
        destino = Path(output_path) / f"{filename_prefix or ''}{nome}"
        if skip_existing and destino.is_file() and destino.stat().st_size == self.filesize:
            return str(destino)
        destino.write_bytes(b"x" * self.filesize)
        return str(destino)


class AudioStream(RecordingStream):
    """Áudio: o pytubefix troca o subtype para m4a ao ler default_filename."""

    @property
    def default_filename(self) -> str:
        self.subtype = "m4a"
        return f"{self._title}.{self.subtype}"


class FailingStream(RecordingStream):
    def download(self, output_path: str, filename: str | None = None, **kwargs) -> str:
        nome = (filename or self.default_filename).translate(file_system_verify("NTFS"))
        (Path(output_path) / nome).write_bytes(b"parcial")
        raise OSError("conexão perdida")


# --------------------------------------------------------------------------
# _target_name
# --------------------------------------------------------------------------
def test_target_name_sanitiza_a_base_e_preserva_a_extensao() -> None:
    stream = RecordingStream(title="Ao vivo: Rock | Show?")
    assert downloader._target_name(stream) == "Ao vivo_ Rock _ Show_.mp4"


def test_target_name_respeita_a_troca_para_m4a_do_audio() -> None:
    assert downloader._target_name(AudioStream(title="Música")) == "Música.m4a"


def test_target_name_preserva_ponto_no_meio_do_titulo() -> None:
    stream = RecordingStream(title="Versão 2.0")
    assert downloader._target_name(stream) == "Versão 2.0.mp4"


def test_target_name_sem_extensao() -> None:
    stream = RecordingStream(title="Sem")
    stream.subtype = ""
    assert downloader._target_name(stream) == "Sem"


# --------------------------------------------------------------------------
# _safe_download: sem sobrescrita, sem pulo silencioso
# --------------------------------------------------------------------------
def test_passa_o_nome_explicito_para_o_pytubefix(tmp_path: Path) -> None:
    stream = RecordingStream(title="Trailer")
    downloader._safe_download(stream, str(tmp_path))
    assert stream.calls[0]["filename"] == "Trailer.mp4"


def test_nao_sobrescreve_arquivo_de_tamanho_diferente(tmp_path: Path) -> None:
    """Dois vídeos distintos de mesmo título: o primeiro deve sobreviver."""
    existente = tmp_path / "Trailer.mp4"
    existente.write_bytes(b"primeiro video")
    tamanho_original = existente.stat().st_size

    resultado = downloader._safe_download(RecordingStream(title="Trailer"), str(tmp_path))

    assert Path(resultado).name == "Trailer (1).mp4"
    assert existente.read_bytes() == b"primeiro video"
    assert existente.stat().st_size == tamanho_original


def test_nao_pula_quando_o_tamanho_coincide(tmp_path: Path) -> None:
    """Antes, tamanho igual fazia o pytubefix pular e reportar sucesso sem
    baixar nada. Agora o nome é livre, então o download acontece."""
    stream = RecordingStream(title="Trailer", size=100)
    (tmp_path / "Trailer.mp4").write_bytes(b"y" * 100)

    resultado = downloader._safe_download(stream, str(tmp_path))

    assert Path(resultado).name == "Trailer (1).mp4"
    assert Path(resultado).read_bytes() == b"x" * 100


def test_numera_sucessivamente(tmp_path: Path) -> None:
    for _ in range(3):
        downloader._safe_download(RecordingStream(title="Trailer"), str(tmp_path))
    nomes = sorted(p.name for p in tmp_path.iterdir())
    assert nomes == ["Trailer (1).mp4", "Trailer (2).mp4", "Trailer.mp4"]


def test_remove_o_parcial_mesmo_com_titulo_de_caracteres_invalidos(tmp_path: Path) -> None:
    """O bug: `partial` vinha do default_filename cru, então para títulos com
    ? : | o unlink mirava um caminho que o pytubefix nunca escreveu."""
    stream = FailingStream(title="Ao vivo: Rock | Show?")

    with pytest.raises(OSError):
        downloader._safe_download(stream, str(tmp_path))

    assert list(tmp_path.iterdir()) == []


# --------------------------------------------------------------------------
# _download_temp
# --------------------------------------------------------------------------
def test_temp_nao_reaproveita_arquivo_deixado_para_tras(tmp_path: Path) -> None:
    stream = RecordingStream(title="Vídeo", size=100)
    (tmp_path / "_tmpv_Vídeo.mp4").write_bytes(b"z" * 100)

    resultado = downloader._download_temp(stream, str(tmp_path), "_tmpv_")

    assert stream.calls[0]["skip_existing"] is False
    assert Path(resultado).read_bytes() == b"x" * 100


def test_temp_remove_o_parcial_na_falha(tmp_path: Path) -> None:
    with pytest.raises(OSError):
        downloader._download_temp(FailingStream(title="Vídeo"), str(tmp_path), "_tmpv_")
    assert list(tmp_path.iterdir()) == []


class NullStream(RecordingStream):
    def download(self, output_path: str, **kwargs) -> None:
        return None


def test_temp_recusa_retorno_nulo(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="sem retornar o caminho"):
        downloader._download_temp(NullStream(), str(tmp_path), "_tmpv_")


def test_safe_download_recusa_retorno_nulo(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="sem retornar o caminho"):
        downloader._safe_download(NullStream(), str(tmp_path))


# --------------------------------------------------------------------------
# Consistência entre os caminhos com e sem ffmpeg
# --------------------------------------------------------------------------
def test_mesmo_nome_com_e_sem_ffmpeg() -> None:
    """A divergência original: nós substituíamos por "_", o pytubefix apagava."""
    titulo = "Ao vivo: Rock | Show?"
    com_ffmpeg = f"{downloader._sanitize(titulo)}.mp4"
    sem_ffmpeg = downloader._target_name(RecordingStream(title=titulo))
    assert com_ffmpeg == sem_ffmpeg == "Ao vivo_ Rock _ Show_.mp4"

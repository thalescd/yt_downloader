from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import opener


@pytest.fixture
def chamadas(monkeypatch: pytest.MonkeyPatch) -> list:
    """Captura o que seria executado, sem abrir gerenciador de arquivos."""
    registradas: list = []
    monkeypatch.setattr(opener.subprocess, "run", lambda cmd, **kw: registradas.append((cmd, kw)))
    monkeypatch.setattr(
        opener.os, "startfile", lambda p: registradas.append(("startfile", p)), raising=False
    )
    return registradas


def test_windows_usa_startfile(chamadas: list, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(opener.sys, "platform", "win32")
    opener.open_folder(Path("/tmp/x"))
    assert chamadas == [("startfile", Path("/tmp/x"))]


def test_macos_usa_open(chamadas: list, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(opener.sys, "platform", "darwin")
    opener.open_folder(Path("/tmp/x"))
    assert chamadas[0][0] == ["open", "/tmp/x"]


def test_linux_usa_xdg_open(chamadas: list, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(opener.sys, "platform", "linux")
    opener.open_folder(Path("/tmp/x"))
    assert chamadas[0][0] == ["xdg-open", "/tmp/x"]


def test_outros_unix_caem_em_xdg_open(chamadas: list, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(opener.sys, "platform", "freebsd14")
    opener.open_folder(Path("/tmp/x"))
    assert chamadas[0][0] == ["xdg-open", "/tmp/x"]


def test_verifica_o_codigo_de_saida(chamadas: list, monkeypatch: pytest.MonkeyPatch) -> None:
    """check=True é o que transforma um xdg-open ausente em erro visível,
    em vez de um botão que não faz nada."""
    monkeypatch.setattr(opener.sys, "platform", "linux")
    opener.open_folder(Path("/tmp/x"))
    assert chamadas[0][1]["check"] is True


def test_propaga_a_falha_do_gerenciador(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(opener.sys, "platform", "linux")

    def explode(cmd, **kwargs):
        raise FileNotFoundError("xdg-open")

    monkeypatch.setattr(opener.subprocess, "run", explode)
    with pytest.raises(FileNotFoundError):
        opener.open_folder(Path("/tmp/x"))


def test_erro_de_codigo_de_saida_propaga(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(opener.sys, "platform", "linux")

    def explode(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd)

    monkeypatch.setattr(opener.subprocess, "run", explode)
    with pytest.raises(subprocess.CalledProcessError):
        opener.open_folder(Path("/tmp/x"))

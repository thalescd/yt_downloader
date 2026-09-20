from __future__ import annotations

import sys
from pathlib import Path


def app_dir() -> Path:
    """Pasta que hospeda o estado do app.

    Congelado, é a pasta do executável. Rodando pelo código-fonte, é a raiz do
    projeto — daí o parents[1]: este módulo mora dentro do pacote, e gravar
    config.ini e logs/ ali sujaria a árvore versionada.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[1]


def download_dir(saved: str = "") -> Path:
    """Pasta de destino: a última escolhida, se ainda existir.

    A verificação não é zelo excessivo — entre uma sessão e outra a pasta pode
    ter sumido junto com o pendrive, sido renomeada ou ficado em outro perfil
    do Windows. Cair para Downloads deixa o app abrir utilizável, em vez de
    exibir um caminho que só falharia na hora de baixar.
    """
    if saved:
        escolhida = Path(saved)
        if escolhida.is_dir():
            return escolhida
    return Path.home() / "Downloads"


def log_dir() -> Path:
    """Pasta de logs, ao lado do executável.

    O app é portátil: configuração, histórico e logs ficam todos junto do
    executável, e só os downloads vão para fora. Se a pasta for
    somente-leitura, log.setup() cai para stderr em vez de impedir o app
    de abrir.
    """
    return app_dir() / "logs"

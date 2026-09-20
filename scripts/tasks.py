"""Tarefas de desenvolvimento do projeto: setup, lint e build.

Só biblioteca padrão, e isso não é preferência: o `setup` roda antes de existir
qualquer dependência — é ele quem cria o .venv e instala os pacotes —, então
não pode depender de nada que precise ser instalado antes.

Os .bat e .sh em volta são cascas de poucas linhas que chamam este arquivo. A
lógica mora aqui uma vez só, em vez de duplicada entre batch e bash, pelo mesmo
motivo que levou o CI a delegar em vez de repetir as etapas: duas cópias
divergem, e a divergência só aparece como comportamento contraditório entre a
máquina de quem desenvolve e o CI.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence

RAIZ = Path(__file__).resolve().parent.parent
VENV = RAIZ / ".venv"
PYTHON_MINIMO = (3, 12)

_VERSAO_MINIMA = ".".join(str(parte) for parte in PYTHON_MINIMO)
_COMO_CHAMAR = "python scripts/tasks.py"


def _venv_bin(nome: str) -> Path:
    """Caminho de um executável dentro do .venv.

    Windows usa Scripts\\ com sufixo .exe; o resto usa bin/ sem sufixo.
    """
    if os.name == "nt":
        return VENV / "Scripts" / f"{nome}.exe"
    return VENV / "bin" / nome


def _titulo(texto: str) -> None:
    print(f"=== YT Downloader - {texto} ===\n")


def _erro(*linhas: str) -> None:
    """Erro no stderr, no mesmo formato que os scripts antigos usavam."""
    print(f"ERRO: {linhas[0]}", file=sys.stderr)
    for linha in linhas[1:]:
        print(linha, file=sys.stderr)


def _roda(cmd: Sequence[object], env: Optional[dict] = None) -> int:
    """Executa a partir da raiz do projeto e devolve o código de saída."""
    return subprocess.run([str(parte) for parte in cmd], cwd=RAIZ, env=env).returncode


def _silencioso(cmd: Sequence[object]) -> bool:
    """Roda sem poluir a tela; devolve apenas se deu certo."""
    try:
        return (
            subprocess.run(
                [str(parte) for parte in cmd],
                cwd=RAIZ,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode
            == 0
        )
    except OSError:
        return False


# --------------------------------------------------------------------------
# setup
# --------------------------------------------------------------------------
def _interpretador() -> Optional[list[str]]:
    """Um Python novo o bastante para criar o ambiente.

    Prefere o que está executando este script. Se ele for antigo demais,
    procura um adequado: no Windows o launcher `py` sabe escolher a versão, e
    fora dele o nome versionado costuma estar no PATH.

    A busca existe porque `python` no PATH pode ser uma versão antiga, e usá-la
    criaria em silêncio um ambiente que não roda a suíte (test_tooling importa
    tomllib, de 3.11+) nem corresponde ao que Ruff e Pyright checam.
    """
    if sys.version_info >= PYTHON_MINIMO:
        return [sys.executable]

    if os.name == "nt" and shutil.which("py"):
        if _silencioso(["py", f"-{_VERSAO_MINIMA}", "--version"]):
            return ["py", f"-{_VERSAO_MINIMA}"]

    versionado = shutil.which(f"python{_VERSAO_MINIMA}")
    return [versionado] if versionado else None


def setup() -> int:
    _titulo("Setup")

    python = _interpretador()
    if python is None:
        _erro(
            f"Python {_VERSAO_MINIMA}+ não encontrado "
            f"(este script roda em {sys.version.split()[0]}).",
            'Windows : instale em https://python.org e marque "Add to PATH".',
            "Linux   : use o gerenciador de pacotes da sua distribuição.",
        )
        return 1

    # No Windows o tkinter vem junto do instalador; no Linux costuma ser um
    # pacote à parte, e a falta dele só apareceria como ImportError na hora de
    # abrir o app.
    if not _silencioso([*python, "-c", "import tkinter"]):
        _erro(
            "o módulo tkinter não está disponível.",
            "Instale o pacote correspondente à sua distribuição:",
            "  Debian/Ubuntu : sudo apt install python3-tk",
            "  Fedora        : sudo dnf install python3-tkinter",
            "  Arch          : sudo pacman -S tk",
        )
        return 1

    if VENV.is_dir():
        print("Ambiente virtual já existe, pulando criação.")
    else:
        print("Criando ambiente virtual...")
        if _roda([*python, "-m", "venv", VENV]):
            _erro(
                "falha ao criar o ambiente virtual.",
                "No Debian/Ubuntu pode faltar o pacote: sudo apt install python3-venv",
            )
            return 1

    print("Instalando dependências...")
    if _instala("requirements.txt"):
        _erro("falha ao instalar as dependências.")
        return 1

    print("\nSetup concluído! Abrindo o app...")
    return _roda([_venv_bin("python"), "-m", "yt_downloader"])


def _instala(arquivo: str) -> int:
    """Instala um requirements no .venv.

    Via `python -m pip`, e não pelo executável do pip: no Windows o .exe fica
    travado enquanto o processo roda, e atualizar o próprio pip por ele falha
    com acesso negado.
    """
    return _roda([_venv_bin("python"), "-m", "pip", "install", "-r", arquivo])


# --------------------------------------------------------------------------
# lint
# --------------------------------------------------------------------------
def _ferramentas() -> Optional[tuple[dict, str]]:
    """Comandos das ferramentas, e o prefixo a citar nas dicas de correção.

    Com .venv, usa as ferramentas dele. Sem .venv — o caso do CI, que instala
    no Python do próprio runner —, usa as do PATH.
    """
    if VENV.is_dir():
        ruff = _venv_bin("ruff")
        return (
            {
                "ruff": [ruff],
                # --pythonpath amarra a checagem ao venv: sem ele o Pyright
                # resolve os imports contra o Python do PATH, que não tem as
                # dependências instaladas.
                "pyright": [_venv_bin("pyright"), "--pythonpath", _venv_bin("python")],
                "pytest": [_venv_bin("pytest")],
            },
            str(ruff),
        )

    if shutil.which("ruff"):
        return ({"ruff": ["ruff"], "pyright": ["pyright"], "pytest": ["pytest"]}, "ruff")

    return None


def lint() -> int:
    _titulo("Verificações")

    achado = _ferramentas()
    if achado is None:
        _erro(
            "ambiente virtual não encontrado e as ferramentas não estão no PATH.",
            f'Rode "{_COMO_CHAMAR} setup" e depois instale as de desenvolvimento:',
            f"  {_venv_bin('python')} -m pip install -r requirements-dev.txt",
        )
        return 1
    cmd, ruff = achado

    # O formatador não aceita --output-format e reclama se a variável estiver
    # definida — o CI a usa para anotar o PR na etapa anterior.
    sem_output_format = dict(os.environ)
    sem_output_format.pop("RUFF_OUTPUT_FORMAT", None)

    etapas = [
        (
            "Ruff - estilo e imports",
            [*cmd["ruff"], "check", "."],
            None,
            [
                "problemas encontrados pelo Ruff.",
                f'Rode "{ruff} check --fix ." para corrigir automaticamente.',
            ],
        ),
        (
            "Ruff - formatação",
            [*cmd["ruff"], "format", "--check", "."],
            sem_output_format,
            [
                "código fora do padrão de formatação.",
                f'Rode "{ruff} format ." para corrigir automaticamente.',
            ],
        ),
        ("Pyright", cmd["pyright"], None, ["problemas de tipo encontrados pelo Pyright."]),
        ("Pytest", cmd["pytest"], None, ["testes falharam."]),
    ]

    for numero, (nome, comando, env, mensagens) in enumerate(etapas, start=1):
        print(f"[{numero}/{len(etapas)}] {nome}...")
        if _roda(comando, env=env):
            _erro(*mensagens)
            return 1

    print("\nTudo certo!")
    return 0


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------
def build() -> int:
    windows = os.name == "nt"
    _titulo("Build")

    if not windows:
        # O PyInstaller não faz compilação cruzada: o .exe do Windows só sai
        # rodando este mesmo comando no Windows.
        print("Gerando binário para este sistema — não é um .exe do Windows.\n")

    if not VENV.is_dir():
        _erro(
            "ambiente virtual não encontrado.",
            f'Execute "{_COMO_CHAMAR} setup" primeiro.',
        )
        return 1

    print("Instalando dependências de build...")
    if _instala("requirements-dev.txt"):
        _erro(
            "falha ao instalar as dependências de build.",
            f'Tente "{_COMO_CHAMAR} setup" novamente para recriar o ambiente.',
        )
        return 1

    nome = "YT Downloader" if windows else "yt-downloader"
    # --icon é ignorado fora de Windows e macOS, então nem é passado lá.
    icone = ["--icon", Path("assets") / "icon.ico"] if windows else []

    print("Gerando executável...")
    gerado = _roda(
        [
            _venv_bin("pyinstaller"),
            "--onefile",
            "--windowed",
            "--name",
            nome,
            *icone,
            "--collect-all",
            "pytubefix",
            "--collect-all",
            "sv_ttk",
            "--paths",
            ".",
            Path("yt_downloader") / "__main__.py",
        ]
    )
    if gerado:
        _erro("falha ao gerar o executável.")
        return 1

    print(f"\nPronto! Executável gerado em: {Path('dist') / (nome + ('.exe' if windows else ''))}")
    return 0


# --------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        prog=_COMO_CHAMAR,
        description="Tarefas de desenvolvimento do YT Downloader.",
    )
    tarefas = {"setup": setup, "lint": lint, "build": build}
    sub = parser.add_subparsers(dest="tarefa", required=True)
    sub.add_parser("setup", help="cria o .venv, instala as dependências e abre o app")
    sub.add_parser("lint", help="roda Ruff (estilo e formatação), Pyright e Pytest")
    sub.add_parser("build", help="gera o executável com o PyInstaller")

    return tarefas[parser.parse_args().tarefa]()


if __name__ == "__main__":
    sys.exit(main())

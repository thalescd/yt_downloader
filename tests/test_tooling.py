"""Consistência entre os arquivos que declaram versões de ferramentas.

Nada aqui exercita o app: são travas contra divergências que só apareceriam
como comportamento contraditório entre o ambiente local e o CI.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


def _pin_em_requirements(pacote: str) -> str:
    texto = (RAIZ / "requirements-dev.txt").read_text(encoding="utf-8")
    achado = re.search(rf"^{re.escape(pacote)}==(\S+)$", texto, re.MULTILINE)
    assert achado, f"{pacote} não está fixado em requirements-dev.txt"
    return achado.group(1)


def _rev_no_pre_commit(repo: str) -> str:
    texto = (RAIZ / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    achado = re.search(rf"{re.escape(repo)}\s*\n\s*rev:\s*v?(\S+)", texto)
    assert achado, f"não encontrei a rev de {repo} em .pre-commit-config.yaml"
    return achado.group(1)


def _pyproject() -> dict:
    return tomllib.loads((RAIZ / "pyproject.toml").read_text(encoding="utf-8"))


def test_ruff_do_pre_commit_bate_com_o_fixado() -> None:
    """Divergindo, o pre-commit formata com uma versão e o lint/CI cobram
    outra, deixando o commit num laço de formatar e ser reprovado."""
    assert _rev_no_pre_commit("ruff-pre-commit") == _pin_em_requirements("ruff")


def test_alvo_de_python_igual_no_ruff_e_no_pyright() -> None:
    """ "py312" e "3.12" precisam descrever a mesma versão."""
    cfg = _pyproject()
    ruff_alvo = cfg["tool"]["ruff"]["target-version"]
    pyright_alvo = cfg["tool"]["pyright"]["pythonVersion"]
    assert ruff_alvo == "py" + pyright_alvo.replace(".", "")


def test_ci_usa_a_mesma_versao_de_python_do_pyright() -> None:
    workflow = (RAIZ / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    achado = re.search(r'python-version:\s*"([^"]+)"', workflow)
    assert achado, "não encontrei python-version no workflow do CI"
    assert achado.group(1) == _pyproject()["tool"]["pyright"]["pythonVersion"]


def test_ci_delega_as_verificacoes_ao_lint_sh() -> None:
    """A razão de o CI não repetir as etapas: uma definição só, que hoje mora
    em scripts/tasks.py e chega ao CI através do scripts/lint.sh."""
    workflow = (RAIZ / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "./scripts/lint.sh" in workflow
    for ferramenta in ("run: ruff", "run: pyright", "run: pytest"):
        assert ferramenta not in workflow, f"CI voltou a chamar {ferramenta} direto"


CASCAS = [
    f"scripts/{tarefa}.{ext}" for tarefa in ("setup", "lint", "build") for ext in ("bat", "sh")
]


@pytest.mark.parametrize("casca", CASCAS)
def test_casca_delega_ao_tasks_py(casca: str) -> None:
    texto = (RAIZ / casca).read_text(encoding="utf-8")
    assert "tasks.py" in texto, f"{casca} deixou de delegar ao executor"


@pytest.mark.parametrize("casca", CASCAS)
@pytest.mark.parametrize("ferramenta", ["ruff", "pyright", "pytest", "pyinstaller"])
def test_casca_nao_chama_ferramenta_direto(casca: str, ferramenta: str) -> None:
    """A duplicação entre batch e bash é o que o tasks.py veio eliminar; uma
    ferramenta reaparecendo aqui significa lógica voltando a viver em dois
    lugares, que divergem em silêncio."""
    texto = (RAIZ / casca).read_text(encoding="utf-8")
    assert ferramenta not in texto, f"{casca} voltou a chamar {ferramenta} direto"

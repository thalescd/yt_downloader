# YT Downloader

[![CI](https://github.com/thalescd/yt_downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/thalescd/yt_downloader/actions/workflows/ci.yml)

Baixa vídeos ou áudio do YouTube com interface gráfica.

## Funcionalidades

- Download de vídeo ou áudio
- Suporte a playlists
- Detecção automática de links do YouTube Music (força modo áudio)
- Seleção de qualidade (360p a 1080p — requer ffmpeg para 720p e acima)
- Modo escuro com persistência
- Histórico de downloads

## Requisitos

- Python 3.12+ (para rodar via terminal ou gerar o executável)
- O `.exe` gerado não exige Python instalado na máquina de destino
- No Linux, o `tkinter` costuma vir em pacote separado: `python3-tk` (Debian/Ubuntu), `python3-tkinter` (Fedora), `tk` (Arch)
- **ffmpeg** (opcional) — necessário para download em 720p, 1080p e "Melhor disponível" em alta qualidade. Instale com `winget install ffmpeg`.

## Setup e execução

**Windows** — dê duplo clique em `scripts\setup.bat`.

**Linux** — rode `./scripts/setup.sh`.

Ambos fazem o mesmo:
1. Verificar se o Python está instalado
2. Criar o ambiente virtual `.venv` (apenas na primeira vez)
3. Instalar as dependências
4. Abrir o app automaticamente

No Linux, o `scripts/setup.sh` também confere se o `tkinter` está presente — ele costuma vir num pacote à parte (`python3-tk` no Debian/Ubuntu) e sua ausência só apareceria como erro ao abrir o app.

## Gerar executável

**Windows** — com o setup já feito, dê duplo clique em `scripts\build.bat`. O `.exe` será gerado em `dist\YT Downloader.exe`.

**Linux** — `./scripts/build.sh` gera um binário Linux em `dist/yt-downloader`. O PyInstaller não faz compilação cruzada: o `.exe` do Windows precisa ser gerado no Windows.

## Desenvolvimento

Instale as dependências de desenvolvimento e rode todas as verificações:

```bash
# Windows
.venv\Scripts\pip install -r requirements-dev.txt
scripts\lint.bat

# Linux
.venv/bin/pip install -r requirements-dev.txt
./scripts/lint.sh
```

Os dois rodam, em ordem: Ruff (estilo e imports), Ruff (formatação), Pyright (tipos) e Pytest. As mesmas quatro etapas rodam no CI a cada push e pull request.

Só os testes:

```bash
.venv\Scripts\pytest     # Windows
.venv/bin/pytest          # Linux
```

Para abrir o app sem passar pelo `setup`:

```bash
.venv\Scripts\python -m yt_downloader   # Windows
.venv/bin/python -m yt_downloader      # Linux
```

A suíte não acessa a rede — os objetos do `pytubefix` são substituídos por dublês.

Para ativar a verificação automática a cada commit:

```bash
.venv\Scripts\pre-commit install
```

## Logs

Erros são registrados em `logs\app.log`, na pasta do executável, com rotação a cada 512 KB (3 arquivos). Como o executável é gerado com `--windowed`, não há console: esse arquivo é a única forma de diagnosticar uma falha em máquina de usuário.

O app é portátil — `config.ini`, `history.json` e `logs\` ficam todos ao lado do executável, então basta copiar a pasta para levar tudo junto. Os downloads são a única coisa que vai para fora, na pasta de destino escolhida.

## Estrutura

```
yt_downloader/
├── yt_downloader/            # o código da aplicação
│   ├── __main__.py           # ponto de entrada (python -m yt_downloader)
│   ├── app.py                # interface gráfica (Tkinter + sv_ttk)
│   ├── downloader.py         # lógica de download (pytubefix + ffmpeg)
│   ├── urls.py               # validação e classificação de URLs
│   ├── opener.py             # abre a pasta no gerenciador do sistema
│   ├── history.py            # persistência do histórico de downloads
│   ├── config.py             # persistência de configurações (tema, limites)
│   ├── log.py                # configuração do logging em arquivo
│   ├── paths.py              # resolução de diretórios da aplicação
│   └── version.py            # nome e versão da aplicação
├── tests/                    # suíte de testes (pytest, sem rede)
├── assets/
│   └── icon.ico              # ícone do executável
├── .github/workflows/ci.yml  # dispara as verificações a cada push e PR
├── requirements.txt          # dependências de runtime
├── requirements-dev.txt      # dependências de build e dev
├── pyproject.toml            # configuração de Ruff, Pyright e Pytest
├── .pre-commit-config.yaml   # hooks de commit
├── scripts/                  # setup, lint e build (.bat e .sh)
├── LICENSE
└── README.md
```

Gerados em execução, ao lado do executável e ignorados pelo git: `config.ini`, `history.json` e `logs/`.

## Aviso

Ferramenta destinada a uso pessoal, para baixar conteúdo próprio ou de domínio público. Baixar vídeos do YouTube pode contrariar os [Termos de Serviço](https://www.youtube.com/t/terms) da plataforma — o uso é de responsabilidade de quem executa.

## Licença

[MIT](LICENSE).

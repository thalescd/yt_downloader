# YT Downloader

Baixa vídeos ou áudio do YouTube com interface gráfica.

## Funcionalidades

- Download de vídeo ou áudio
- Suporte a playlists
- Detecção automática de links do YouTube Music (força modo áudio)
- Seleção de qualidade (360p a 1080p — requer ffmpeg para 720p e acima)
- Modo escuro com persistência
- Histórico de downloads

## Requisitos

- Python 3.8+ (para rodar via terminal ou gerar o executável)
- O `.exe` gerado não exige Python instalado na máquina de destino
- **ffmpeg** (opcional) — necessário para download em 720p, 1080p e "Melhor disponível" em alta qualidade. Instale com `winget install ffmpeg`.

## Setup e execução

Dê duplo clique em `setup.bat`. Ele irá:
1. Verificar se o Python está instalado
2. Criar o ambiente virtual `.venv` (apenas na primeira vez)
3. Instalar as dependências
4. Abrir o app automaticamente

## Gerar executável

Com o setup já feito, dê duplo clique em `build.bat`. O `.exe` será gerado em `dist\YT Downloader.exe`.

## Linting

```bash
.venv\Scripts\pip install -r requirements-dev.txt
lint.bat
```

Para ativar verificação automática a cada commit:

```bash
.venv\Scripts\pre-commit install
```

## Estrutura

```
yt_downloader/
├── app.py                    # interface gráfica (Tkinter + sv_ttk)
├── downloader.py             # lógica de download (pytubefix + ffmpeg)
├── history.py                # persistência do histórico de downloads
├── config.py                 # persistência de configurações (tema, limites)
├── assets/
│   └── icon.ico              # ícone do executável
├── requirements.txt          # dependências de runtime
├── requirements-dev.txt      # dependências de build e dev
├── pyproject.toml            # configuração do Ruff e Pyright
├── .pre-commit-config.yaml   # hooks de commit
├── setup.bat                 # configura o ambiente e abre o app
├── build.bat                 # gera o executável
├── lint.bat                  # roda Ruff e Pyright
└── README.md
```

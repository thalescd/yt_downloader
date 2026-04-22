# YT Downloader

Baixa vídeos ou áudio do YouTube com interface gráfica.

## Requisitos

- Python 3.8+ (para rodar via terminal ou gerar o executável)
- O `.exe` gerado não exige Python instalado na máquina de destino

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
pip install -r requirements-dev.txt
lint.bat
```

Para ativar verificação automática a cada commit (requer git):

```bash
git init
.venv\Scripts\pre-commit install
```

## Estrutura

```
yt_downloader/
├── app.py                    # interface gráfica (Tkinter)
├── baixador.py               # lógica de download (pytubefix)
├── requirements.txt          # dependências de runtime
├── requirements-dev.txt      # dependências de build e dev
├── pyproject.toml            # configuração do Ruff e Pyright
├── .pre-commit-config.yaml   # hooks de commit
├── setup.bat                 # configura o ambiente e abre o app
├── build.bat                 # gera o executável
├── lint.bat                  # roda Ruff e Pyright
└── README.md
```

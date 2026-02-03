from pathlib import Path
import sys
import os

APP_NAME = "EstoqueONG"


def pasta_app() -> Path:
    # Quando empacotado (PyInstaller), sys.executable aponta pro .exe
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # Em desenvolvimento, aponta para a raiz do projeto (um nível acima de /src)
    return Path(__file__).resolve().parents[1]


def pasta_dados() -> Path:
    """
    Pasta oficial de dados por usuário no Windows:
    %APPDATA%\\EstoqueONG
    """
    appdata = os.getenv("APPDATA")
    base = Path(appdata) if appdata else Path.home()
    d = base / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


# Recursos do app (ficam junto do exe/projeto)
APP_DIR = pasta_app()
PUBLIC_DIR = APP_DIR / "public"
ICONE_ICO = APP_DIR / "assets" / "icon.ico"

# Dados do usuário (não dependem da pasta do exe)
DADOS_DIR = pasta_dados()
ARQUIVO_DADOS = DADOS_DIR / "dados.json"
BACKUP_DIR = DADOS_DIR / "backup"
BACKUP_DIR.mkdir(exist_ok=True)

HISTORICO_DIR = DADOS_DIR / "historico"
ARQUIVO_HISTORICO = HISTORICO_DIR / "movimentos.jsonl"
HISTORICO_DIR.mkdir(exist_ok=True)


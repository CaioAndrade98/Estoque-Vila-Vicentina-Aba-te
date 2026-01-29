from pathlib import Path

# Pasta raiz do projeto (um nível acima de /src)
ROOT_DIR = Path(__file__).resolve().parents[1]

# Arquivo de dados (fica na raiz do projeto)
ARQUIVO_DADOS = ROOT_DIR / "dados.json"

# Pasta dos arquivos estáticos (HTML/JS/CSS)
PUBLIC_DIR = ROOT_DIR / "public"

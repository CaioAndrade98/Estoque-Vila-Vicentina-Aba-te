from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

from .config import ARQUIVO_DADOS, BACKUP_DIR


class ProdutoNaoEncontrado(Exception):
    """Produto não encontrado no estoque."""


class EstoqueInsuficiente(Exception):
    """Quantidade insuficiente em estoque."""


class ProdutoDuplicado(Exception):
    """Já existe um produto com esse nome (normalizado)."""


def _normalizar_nome(nome: str) -> str:
    return " ".join(nome.strip().lower().split())


def _carregar_produtos() -> List[Dict[str, Any]]:
    if not ARQUIVO_DADOS.exists():
        return []
    try:
        with ARQUIVO_DADOS.open("r", encoding="utf-8") as f:
            dados = json.load(f)
        return dados if isinstance(dados, list) else []
    except Exception:
        return []


def _salvar_produtos(produtos: List[Dict[str, Any]]) -> None:
    ARQUIVO_DADOS.parent.mkdir(parents=True, exist_ok=True)

    with ARQUIVO_DADOS.open("w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)

    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        carimbo = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_file = BACKUP_DIR / f"dados_backup_{carimbo}.json"
        with backup_file.open("w", encoding="utf-8") as bf:
            json.dump(produtos, bf, ensure_ascii=False, indent=2)
    except Exception:
        pass


def listar_produtos() -> List[Dict[str, Any]]:
    """Retorna todos os produtos (lista de dicts) do JSON."""
    return _carregar_produtos()


def _gerar_proximo_id(produtos: List[Dict[str, Any]]) -> int:
    if not produtos:
        return 1
    return max(int(p.get("id", 0)) for p in produtos) + 1


def criar_produto(nome: str, unidade: str, estoque_minimo: float) -> Dict[str, Any]:
    """Cria produto (estoque_atual=0.0) e persiste."""
    nome = str(nome).strip()
    unidade = str(unidade).strip()
    if not nome:
        raise ValueError("Nome não pode ficar vazio.")
    if not unidade:
        raise ValueError("Unidade não pode ficar vazia.")

    try:
        estoque_min = float(str(estoque_minimo).replace(",", "."))
    except Exception:
        raise ValueError("Estoque mínimo inválido.")
    if estoque_min < 0:
        raise ValueError("Estoque mínimo inválido.")

    produtos = _carregar_produtos()
    nome_norm = _normalizar_nome(nome)
    for p in produtos:
        if _normalizar_nome(str(p.get("nome", ""))) == nome_norm:
            raise ProdutoDuplicado("Produto já existe com esse nome.")

    novo = {
        "id": _gerar_proximo_id(produtos),
        "nome": nome,
        "unidade": unidade,
        "estoque_atual": 0.0,
        "estoque_minimo": float(estoque_min),
    }
    produtos.append(novo)
    _salvar_produtos(produtos)
    return novo


def move_stock_by_id(produto_id: int, delta: float) -> Dict[str, Any]:
    """Movimenta estoque_atual por ID. delta positivo=entrada; negativo=saída."""
    try:
        pid = int(produto_id)
    except Exception:
        raise ProdutoNaoEncontrado("ID inválido.")

    try:
        d = float(delta)
    except Exception:
        raise ValueError("Quantidade inválida.")

    produtos = _carregar_produtos()
    for p in produtos:
        if int(p.get("id", 0)) == pid:
            atual = float(p.get("estoque_atual", 0.0))
            novo = atual + d
            if novo < 0:
                raise EstoqueInsuficiente(f"Estoque insuficiente para '{p.get('nome', '')}'.")
            p["estoque_atual"] = float(novo)
            _salvar_produtos(produtos)
            return p

    raise ProdutoNaoEncontrado(f"Produto com id {pid} não encontrado.")


def produtos_abaixo_minimo() -> List[Dict[str, Any]]:
    """Produtos cujo estoque_atual está abaixo do estoque_minimo."""
    produtos = _carregar_produtos()
    return [
        p for p in produtos
        if float(p.get("estoque_atual", 0.0)) < float(p.get("estoque_minimo", 0.0))
    ]

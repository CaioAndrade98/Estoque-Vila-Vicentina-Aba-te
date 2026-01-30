from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Mesmo arquivo que você já usa
from src.config import ARQUIVO_DADOS, PUBLIC_DIR


app = FastAPI(title="Estoque Restaurante API", version="1.0")

from src.config import ARQUIVO_DADOS, PUBLIC_DIR


# Serve arquivos estáticos (ex: /static/...)
app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")

# Serve a página principal
@app.get("/")
def home():
    return FileResponse(PUBLIC_DIR / "index.html")


# ---------- Persistência (JSON) ----------
def carregar_produtos() -> List[Dict[str, Any]]:
    if not ARQUIVO_DADOS.exists():
        return []
    try:
        with ARQUIVO_DADOS.open("r", encoding="utf-8") as f:
            dados = json.load(f)
        return dados if isinstance(dados, list) else []
    except json.JSONDecodeError:
        # arquivo corrompido
        return []
    except Exception:
        return []


def salvar_produtos(produtos: List[Dict[str, Any]]) -> None:
    with ARQUIVO_DADOS.open("w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)


def gerar_proximo_id(produtos: List[Dict[str, Any]]) -> int:
    if not produtos:
        return 1
    return max(p["id"] for p in produtos) + 1


def encontrar_produto_por_id(produtos: List[Dict[str, Any]], produto_id: int) -> Optional[Dict[str, Any]]:
    for p in produtos:
        if p["id"] == produto_id:
            return p
    return None

def normalizar_nome(nome: str) -> str:
    return " ".join(nome.strip().lower().split())


# ---------- Schemas (o “formato” das requisições) ----------
class ProdutoCreate(BaseModel):
    nome: str = Field(min_length=1)
    unidade: str = Field(min_length=1)
    estoque_minimo: float = Field(ge=0)


class MovimentoEstoque(BaseModel):
    produto_id: int = Field(ge=1)
    quantidade: float = Field(gt=0)


# ---------- Endpoints ----------
@app.get("/api/produtos")
def listar_produtos():
    produtos = carregar_produtos()
    produtos_ordenados = sorted(produtos, key=lambda x: x.get("nome", "").lower())
    return produtos_ordenados


@app.post("/api/produtos", status_code=201)
def cadastrar_produto(payload: ProdutoCreate):
    produtos = carregar_produtos()

    nome_norm = normalizar_nome(payload.nome)
    for p in produtos:
        if normalizar_nome(str(p.get("nome", ""))) == nome_norm:
            raise HTTPException(status_code=409, detail="Produto já existe com esse nome.")

    produto = {
        "id": gerar_proximo_id(produtos),
        "nome": payload.nome.strip(),
        "unidade": payload.unidade.strip(),
        "estoque_atual": 0.0,
        "estoque_minimo": float(payload.estoque_minimo),
    }

    produtos.append(produto)
    salvar_produtos(produtos)
    return produto



@app.post("/api/estoque/entrada")
def entrada_estoque(payload: MovimentoEstoque):
    produtos = carregar_produtos()
    produto = encontrar_produto_por_id(produtos, payload.produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    produto["estoque_atual"] = float(produto.get("estoque_atual", 0)) + float(payload.quantidade)
    salvar_produtos(produtos)
    return {"ok": True, "produto": produto}


@app.post("/api/estoque/saida")
def saida_estoque(payload: MovimentoEstoque):
    produtos = carregar_produtos()
    produto = encontrar_produto_por_id(produtos, payload.produto_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")

    atual = float(produto.get("estoque_atual", 0))
    qtd = float(payload.quantidade)

    if atual < qtd:
        raise HTTPException(status_code=400, detail="Estoque insuficiente.")

    produto["estoque_atual"] = atual - qtd
    salvar_produtos(produtos)
    return {"ok": True, "produto": produto}


@app.get("/api/produtos/abaixo-minimo")
def abaixo_do_minimo():
    produtos = carregar_produtos()
    abaixo = [
        p for p in produtos
        if float(p.get("estoque_atual", 0)) < float(p.get("estoque_minimo", 0))
    ]
    abaixo = sorted(abaixo, key=lambda x: x.get("nome", "").lower())
    return abaixo

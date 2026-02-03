from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import PUBLIC_DIR
from .estoque_core import (
    listar_produtos,
    criar_produto,
    move_stock_by_id,
    produtos_abaixo_minimo,
    listar_movimentos,
    ProdutoNaoEncontrado,
    EstoqueInsuficiente,
    ProdutoDuplicado,
)


app = FastAPI(title="Estoque ONG API", version="1.0")

app.mount("/static", StaticFiles(directory=PUBLIC_DIR), name="static")


@app.get("/")
def home():
    return FileResponse(PUBLIC_DIR / "index.html")


class ProdutoCreate(BaseModel):
    nome: str = Field(min_length=1)
    unidade: str = Field(min_length=1)
    estoque_minimo: float = Field(ge=0)


class MovimentoEstoque(BaseModel):
    produto_id: int = Field(ge=1)
    quantidade: float = Field(gt=0)


@app.get("/api/produtos")
def api_listar_produtos():
    produtos = listar_produtos()
    return sorted(produtos, key=lambda x: str(x.get("nome", "")).lower())


@app.post("/api/produtos", status_code=201)
def api_cadastrar_produto(payload: ProdutoCreate):
    try:
        return criar_produto(payload.nome, payload.unidade, payload.estoque_minimo)
    except ProdutoDuplicado:
        raise HTTPException(status_code=409, detail="Produto já existe com esse nome.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/estoque/entrada")
def api_entrada_estoque(payload: MovimentoEstoque):
    try:
        produto = move_stock_by_id(payload.produto_id, float(payload.quantidade))
        return {"ok": True, "produto": produto}
    except ProdutoNaoEncontrado:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/estoque/saida")
def api_saida_estoque(payload: MovimentoEstoque):
    try:
        produto = move_stock_by_id(payload.produto_id, -float(payload.quantidade))
        return {"ok": True, "produto": produto}
    except ProdutoNaoEncontrado:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    except EstoqueInsuficiente:
        raise HTTPException(status_code=400, detail="Estoque insuficiente.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/produtos/abaixo-minimo")
def api_abaixo_minimo():
    abaixo = produtos_abaixo_minimo()
    return sorted(abaixo, key=lambda x: str(x.get("nome", "")).lower())

@app.get("/api/historico")
def api_historico(limite: int = 200):
    """
    Retorna o histórico de movimentações (mais recentes primeiro).
    limite: quantos eventos retornar (padrão 200).
    """
    if limite < 1:
        limite = 1
    if limite > 5000:
        limite = 5000  # evita respostas gigantes

    movimentos = listar_movimentos(limite=limite)
    movimentos = list(reversed(movimentos))  # mais recentes primeiro
    return movimentos

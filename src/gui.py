import json
import tkinter as tk
from tkinter import ttk, messagebox

from config import ARQUIVO_DADOS  # funciona porque gui.py e config.py estão em src/


def carregar_produtos() -> list[dict]:
    """Lê o dados.json (lista de produtos). Se não existir/der erro, volta lista vazia."""
    if not ARQUIVO_DADOS.exists():
        return []
    try:
        with ARQUIVO_DADOS.open("r", encoding="utf-8") as f:
            dados = json.load(f)
        return dados if isinstance(dados, list) else []
    except Exception:
        return []


def abrir_tela_produtos(root: tk.Tk) -> None:
    produtos = carregar_produtos()
    produtos = sorted(produtos, key=lambda p: str(p.get("nome", "")).lower())

    win = tk.Toplevel(root)
    win.title("Produtos")
    win.geometry("720x420")

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    titulo = ttk.Label(frame, text="Produtos cadastrados", font=("Segoe UI", 12, "bold"))
    titulo.pack(anchor="w", pady=(0, 8))

    cols = ("id", "nome", "unidade", "atual", "minimo")
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
    tree.pack(fill="both", expand=True)

    tree.heading("id", text="ID")
    tree.heading("nome", text="Produto")
    tree.heading("unidade", text="Unidade")
    tree.heading("atual", text="Atual")
    tree.heading("minimo", text="Mínimo")

    tree.column("id", width=60, anchor="center")
    tree.column("nome", width=300)
    tree.column("unidade", width=90, anchor="center")
    tree.column("atual", width=90, anchor="center")
    tree.column("minimo", width=90, anchor="center")

    for p in produtos:
        tree.insert(
            "", "end",
            values=(
                p.get("id", ""),
                p.get("nome", ""),
                p.get("unidade", ""),
                p.get("estoque_atual", 0),
                p.get("estoque_minimo", 0),
            )
        )

    if not produtos:
        messagebox.showinfo("Sem dados", "Nenhum produto cadastrado ainda.\nCadastre primeiro pela API ou pelo CLI.")

def salvar_produtos(produtos: list[dict]) -> None:
    with ARQUIVO_DADOS.open("w", encoding="utf-8") as f:
        json.dump(produtos, f, ensure_ascii=False, indent=2)

def gerar_proximo_id(produtos: list[dict]) -> int:
    if not produtos:
        return 1
    return max(int(p.get("id", 0)) for p in produtos) + 1

def normalizar_nome(nome: str) -> str:
    return " ".join(nome.strip().lower().split())

def abrir_cadastro_produto(root: tk.Tk) -> None:
    win = tk.Toplevel(root)
    win.title("Cadastrar Produto")
    win.geometry("520x260")

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Nome do produto").pack(anchor="w")
    nome_var = tk.StringVar()
    ttk.Entry(frame, textvariable=nome_var).pack(fill="x", pady=(0, 10))

    ttk.Label(frame, text="Unidade (ex: un, kg, L)").pack(anchor="w")
    unidade_var = tk.StringVar()
    ttk.Entry(frame, textvariable=unidade_var).pack(fill="x", pady=(0, 10))

    ttk.Label(frame, text="Estoque mínimo").pack(anchor="w")
    minimo_var = tk.StringVar()
    ttk.Entry(frame, textvariable=minimo_var).pack(fill="x", pady=(0, 12))

    def salvar():
        nome = nome_var.get().strip()
        unidade = unidade_var.get().strip()
        minimo_txt = minimo_var.get().strip().replace(",", ".")

        if not nome:
            messagebox.showwarning("Atenção", "O nome não pode ficar vazio.")
            return
        if not unidade:
            messagebox.showwarning("Atenção", "A unidade não pode ficar vazia.")
            return
        try:
            minimo = float(minimo_txt)
            if minimo < 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Atenção", "Estoque mínimo inválido. Use um número (ex: 2 ou 2,5).")
            return

        produtos = carregar_produtos()

        nome_norm = normalizar_nome(nome)
        for p in produtos:
            if normalizar_nome(str(p.get("nome", ""))) == nome_norm:
                messagebox.showerror("Erro", "Já existe um produto com esse nome.")
                return

        novo = {
            "id": gerar_proximo_id(produtos),
            "nome": nome,
            "unidade": unidade,
            "estoque_atual": 0.0,
            "estoque_minimo": float(minimo),
        }
        produtos.append(novo)
        salvar_produtos(produtos)

        messagebox.showinfo("OK", "Produto cadastrado com sucesso.")
        win.destroy()

    ttk.Button(frame, text="Salvar", command=salvar).pack(anchor="e")

def atualizar_estoque(produto_id: int, delta: float) -> None:
    produtos = carregar_produtos()
    alvo = None
    for p in produtos:
        if int(p.get("id", 0)) == int(produto_id):
            alvo = p
            break
    if not alvo:
        raise ValueError("Produto não encontrado.")

    atual = float(alvo.get("estoque_atual", 0))
    novo = atual + float(delta)
    if novo < 0:
        raise ValueError("Estoque insuficiente.")

    alvo["estoque_atual"] = novo
    salvar_produtos(produtos)

def abrir_movimento(root: tk.Tk, tipo: str) -> None:
    # tipo: "entrada" ou "saida"
    produtos = carregar_produtos()
    produtos = sorted(produtos, key=lambda p: str(p.get("nome", "")).lower())

    if not produtos:
        messagebox.showinfo("Sem produtos", "Cadastre um produto antes.")
        return

    win = tk.Toplevel(root)
    win.title("Entrada de Estoque" if tipo == "entrada" else "Saída de Estoque")
    win.geometry("520x260")

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Produto").pack(anchor="w")
    # Combobox com "Nome (unidade) - ID"
    opcoes = [f"{p.get('nome','')} ({p.get('unidade','')})  -  ID {p.get('id','')}" for p in produtos]
    produto_var = tk.StringVar(value=opcoes[0])
    cb = ttk.Combobox(frame, textvariable=produto_var, values=opcoes, state="readonly")
    cb.pack(fill="x", pady=(0, 10))

    ttk.Label(frame, text="Quantidade (ex: 1,5)").pack(anchor="w")
    qtd_var = tk.StringVar()
    ttk.Entry(frame, textvariable=qtd_var).pack(fill="x", pady=(0, 12))

    def confirmar():
        qtd_txt = qtd_var.get().strip().replace(",", ".")
        try:
            qtd = float(qtd_txt)
            if qtd <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Atenção", "Quantidade inválida. Use um número maior que 0 (ex: 1 ou 1,5).")
            return

        # descobrir o id pelo índice do combobox (mais simples e robusto)
        idx = cb.current()
        produto = produtos[idx]
        pid = int(produto.get("id", 0))

        try:
            delta = qtd if tipo == "entrada" else -qtd
            atualizar_estoque(pid, delta)
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return

        messagebox.showinfo("OK", "Movimento registrado com sucesso.")
        win.destroy()

    ttk.Button(frame, text="Confirmar", command=confirmar).pack(anchor="e")

def abrir_abaixo_minimo(root: tk.Tk) -> None:
    produtos = carregar_produtos()
    abaixo = [
        p for p in produtos
        if float(p.get("estoque_atual", 0)) < float(p.get("estoque_minimo", 0))
    ]
    abaixo = sorted(abaixo, key=lambda p: str(p.get("nome", "")).lower())

    win = tk.Toplevel(root)
    win.title("Abaixo do mínimo")
    win.geometry("720x420")

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Produtos abaixo do estoque mínimo", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))

    cols = ("nome", "unidade", "atual", "minimo")
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
    tree.pack(fill="both", expand=True)

    tree.heading("nome", text="Produto")
    tree.heading("unidade", text="Unidade")
    tree.heading("atual", text="Atual")
    tree.heading("minimo", text="Mínimo")

    tree.column("nome", width=360)
    tree.column("unidade", width=90, anchor="center")
    tree.column("atual", width=90, anchor="center")
    tree.column("minimo", width=90, anchor="center")

    for p in abaixo:
        tree.insert(
            "", "end",
            values=(
                p.get("nome", ""),
                p.get("unidade", ""),
                p.get("estoque_atual", 0),
                p.get("estoque_minimo", 0),
            )
        )

    if not abaixo:
        messagebox.showinfo("OK", "Nenhum produto está abaixo do mínimo.")

def main():
    root = tk.Tk()
    root.title("Estoque - ONG")
    root.geometry("520x320")

    frame = ttk.Frame(root, padding=16)
    frame.pack(fill="both", expand=True)

    titulo = ttk.Label(frame, text="Controle de Estoque", font=("Segoe UI", 16, "bold"))
    titulo.pack(pady=(0, 12))

    ttk.Button(frame, text="Cadastrar Produto", command=lambda: abrir_cadastro_produto(root)).pack(fill="x", pady=6)

    ttk.Button(frame, text="Entrada", command=lambda: abrir_movimento(root, "entrada")).pack(fill="x", pady=6)

    ttk.Button(frame, text="Saída", command=lambda: abrir_movimento(root, "saida")).pack(fill="x", pady=6)

    ttk.Button(frame, text="Produtos", command=lambda: abrir_tela_produtos(root)).pack(fill="x", pady=6)

    ttk.Button(frame, text="Abaixo do mínimo", command=lambda: abrir_abaixo_minimo(root)).pack(fill="x", pady=6)



    root.mainloop()


if __name__ == "__main__":
    main()

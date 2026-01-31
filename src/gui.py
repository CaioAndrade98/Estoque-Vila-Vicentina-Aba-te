import tkinter as tk
from tkinter import ttk, messagebox
import unicodedata
import re

from .config import ICONE_ICO  # gui.py e config.py estão em src/
from .estoque_core import (
    listar_produtos,
    criar_produto,
    move_stock_by_id,
    ProdutoNaoEncontrado,
    EstoqueInsuficiente,
    ProdutoDuplicado,
)

def carregar_produtos() -> list[dict]:
    """Carrega a lista de produtos pelo core (fonte única)."""
    return listar_produtos()


def salvar_produtos(produtos: list[dict]) -> None:
    """Compatibilidade: persistência é feita no core."""
    pass


def gerar_proximo_id(produtos: list[dict]) -> int:
    """Compatibilidade: IDs são gerados no core."""
    raise NotImplementedError("IDs são gerados no core")


def normalizar_nome(nome: str) -> str:
    return " ".join(nome.strip().lower().split())


def remover_acentos(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def normalizar_busca(s: str) -> str:
    """
    Normalização 'premium':
    - lower
    - remove acentos
    - troca pontuação por espaço (coca-cola == coca cola)
    - normaliza múltiplos espaços
    """
    s = remover_acentos(s).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s, flags=re.IGNORECASE)  # pontuação -> espaço
    s = " ".join(s.split())
    return s


def match_prefix_por_palavras(query_tokens: list[str], name_tokens: list[str]) -> bool:
    """query tokens são prefixos dos tokens correspondentes do nome."""
    if not query_tokens:
        return True
    if len(query_tokens) > len(name_tokens):
        return False
    for i, qt in enumerate(query_tokens):
        if not name_tokens[i].startswith(qt):
            return False
    return True


def match_tokens_em_ordem(query_tokens: list[str], name_tokens: list[str]) -> bool:
    """Tokens do query aparecem em ordem (por prefixo), não necessariamente contíguos."""
    if not query_tokens:
        return True
    j = 0
    for nt in name_tokens:
        if nt.startswith(query_tokens[j]):
            j += 1
            if j == len(query_tokens):
                return True
    return False


def abrir_tela_produtos(root: tk.Tk) -> None:
    produtos = carregar_produtos()
    produtos = sorted(produtos, key=lambda p: str(p.get("nome", "")).lower())

    win = tk.Toplevel(root)
    win.title("Itens")
    win.geometry("720x420")

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Itens cadastrados", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))

    cols = ("id", "nome", "unidade", "atual", "minimo")
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
    tree.pack(fill="both", expand=True)

    tree.heading("id", text="ID")
    tree.heading("nome", text="Item")
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
        messagebox.showinfo("Sem dados", "Nenhum item cadastrado ainda.\nCadastre primeiro pela API ou pelo CLI.")


def abrir_cadastro_produto(root: tk.Tk) -> None:
    win = tk.Toplevel(root)
    win.title("Cadastrar Item")
    win.geometry("520x260")

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Nome do item").pack(anchor="w")
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

        try:
            criar_produto(nome=nome, unidade=unidade, estoque_minimo=float(minimo))
        except ProdutoDuplicado:
            messagebox.showerror("Erro", "Já existe um item com esse nome.")
            return
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return

        messagebox.showinfo("OK", "Item cadastrado com sucesso.")
        win.destroy()

    ttk.Button(frame, text="Salvar", command=salvar).pack(anchor="e")


def atualizar_estoque(produto_id: int, delta: float) -> None:
    """Movimenta estoque usando o core (regra única)."""
    try:
        move_stock_by_id(produto_id, delta)
    except ProdutoNaoEncontrado as e:
        raise ValueError(str(e))
    except EstoqueInsuficiente as e:
        raise ValueError(str(e))

def abrir_movimento(root: tk.Tk, tipo: str) -> None:
    # tipo: "entrada" ou "saida"
    produtos = carregar_produtos()
    produtos = sorted(produtos, key=lambda p: str(p.get("nome", "")).lower())

    if not produtos:
        messagebox.showinfo("Sem itens", "Cadastre um item antes.")
        return

    win = tk.Toplevel(root)
    win.title("Entrada de Estoque" if tipo == "entrada" else "Saída de Estoque")
    win.geometry("560x430")

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    # ---------- BUSCA ----------
    ttk.Label(frame, text="Buscar item").pack(anchor="w")

    # Exibição SEM ID: só nome; se repetir, inclui unidade; se ainda repetir, (2), (3)...
    itens_exibicao: list[str] = []
    texto_para_id: dict[str, int] = {}

    # Índices para busca premium (somente pelo NOME)
    item_para_nome_norm: dict[str, str] = {}
    item_para_tokens: dict[str, list[str]] = {}

    usados: dict[str, int] = {}

    for p in produtos:
        nome = str(p.get("nome", "")).strip()
        unidade = str(p.get("unidade", "")).strip()
        pid = int(p.get("id", 0))

        base = nome
        if base in usados:
            base = f"{nome} ({unidade})" if unidade else nome

        n = usados.get(base, 0) + 1
        usados[base] = n
        texto_exibido = base if n == 1 else f"{base} ({n})"

        itens_exibicao.append(texto_exibido)
        texto_para_id[texto_exibido] = pid

        nn = normalizar_busca(nome)
        item_para_nome_norm[texto_exibido] = nn
        item_para_tokens[texto_exibido] = nn.split() if nn else []

    itens_originais = itens_exibicao.copy()

    busca_var = tk.StringVar(value="")
    ent_busca = ttk.Entry(frame, textvariable=busca_var)
    ent_busca.pack(fill="x", pady=(0, 6))

    # Status: contador e vazio
    status_frame = ttk.Frame(frame)
    status_frame.pack(fill="x", pady=(0, 10))

    resultados_var = tk.StringVar(value=f"{len(itens_originais)} itens")
    ttk.Label(status_frame, textvariable=resultados_var).pack(side="left")

    vazio_var = tk.StringVar(value="")
    ttk.Label(status_frame, textvariable=vazio_var).pack(side="right")

    ttk.Label(frame, text="Selecione um item").pack(anchor="w")

    # ---------- LISTBOX + SCROLLBAR ----------
    list_frame = ttk.Frame(frame)
    list_frame.pack(fill="both", expand=True, pady=(0, 10))

    yscroll = ttk.Scrollbar(list_frame, orient="vertical")
    yscroll.pack(side="right", fill="y")

    lb = tk.Listbox(
        list_frame,
        height=10,
        activestyle="none",
        exportselection=False,  # mantém seleção mesmo quando foco muda
        yscrollcommand=yscroll.set,
    )
    lb.pack(side="left", fill="both", expand=True)
    yscroll.config(command=lb.yview)

    # popula lista inicial
    for item in itens_originais:
        lb.insert("end", item)

    def _atualizar_status(qtd: int):
        resultados_var.set(f"{qtd} item" if qtd == 1 else f"{qtd} itens")
        vazio_var.set("Nenhum item encontrado" if qtd == 0 else "")

    def _filtrar_rankeado_premium(texto_busca: str) -> list[str]:
        """
        Busca premium por NOME:
        - sem acentos
        - sem pontuação
        - abreviações por palavras ("arroz br")
        Ranking:
          A) nome começa com query (string)
          B) prefixo por palavras (abreviação)
          C) nome contém query (string)
          D) tokens em ordem (prefixo por token)
        """
        q = normalizar_busca(texto_busca)
        if not q:
            return itens_originais

        qtoks = q.split()

        grupo_a: list[str] = []
        grupo_b: list[str] = []
        grupo_c: list[str] = []
        grupo_d: list[str] = []

        for item_txt in itens_originais:
            nome_norm = item_para_nome_norm.get(item_txt, "")
            ntoks = item_para_tokens.get(item_txt, [])

            if nome_norm.startswith(q):
                grupo_a.append(item_txt)
            elif match_prefix_por_palavras(qtoks, ntoks):
                grupo_b.append(item_txt)
            elif q in nome_norm:
                grupo_c.append(item_txt)
            elif match_tokens_em_ordem(qtoks, ntoks):
                grupo_d.append(item_txt)

        return grupo_a + grupo_b + grupo_c + grupo_d

    def _render_lista(itens: list[str]) -> None:
        lb.delete(0, "end")
        for it in itens:
            lb.insert("end", it)

    _after_id = None

    def aplicar_filtro():
        filtradas = _filtrar_rankeado_premium(busca_var.get())
        _render_lista(filtradas)
        _atualizar_status(len(filtradas))

        # UX: se só tiver 1 resultado, já seleciona
        if len(filtradas) == 1:
            lb.selection_clear(0, "end")
            lb.selection_set(0)
            lb.activate(0)
            lb.see(0)

    def on_busca_keyrelease(event=None):
        nonlocal _after_id
        if _after_id is not None:
            win.after_cancel(_after_id)
        _after_id = win.after(120, aplicar_filtro)

    def selecionar_primeiro_da_lista():
        if lb.size() > 0:
            lb.selection_clear(0, "end")
            lb.selection_set(0)
            lb.activate(0)
            lb.see(0)

    def ir_para_lista(event=None):
        if lb.size() > 0:
            selecionar_primeiro_da_lista()
            lb.focus_set()
        return "break"

    def on_busca_enter(event=None):
        # Enter na busca: seleciona primeiro e vai pra quantidade (se existir)
        if lb.size() > 0:
            selecionar_primeiro_da_lista()
            ent_qtd.focus_set()
        return "break"

    def on_busca_escape(event=None):
        busca_var.set("")
        _render_lista(itens_originais)
        _atualizar_status(len(itens_originais))
        lb.selection_clear(0, "end")
        ent_busca.focus_set()
        return "break"

    def on_lista_enter(event=None):
        # Enter na lista: vai pra quantidade
        ent_qtd.focus_set()
        return "break"

    def on_lista_double(event=None):
        # Duplo clique: vai pra quantidade
        ent_qtd.focus_set()
        return "break"

    def on_lista_escape(event=None):
        ent_busca.focus_set()
        return "break"

    ent_busca.bind("<KeyRelease>", on_busca_keyrelease)
    ent_busca.bind("<Down>", ir_para_lista)
    ent_busca.bind("<Return>", on_busca_enter)
    ent_busca.bind("<Escape>", on_busca_escape)

    lb.bind("<Return>", on_lista_enter)
    lb.bind("<Double-Button-1>", on_lista_double)
    lb.bind("<Escape>", on_lista_escape)

    # Foco inicial
    ent_busca.focus_set()
    _atualizar_status(len(itens_originais))

    # ---------- QUANTIDADE ----------
    ttk.Label(frame, text="Quantidade (ex: 1,5)").pack(anchor="w")
    qtd_var = tk.StringVar()
    ent_qtd = ttk.Entry(frame, textvariable=qtd_var)
    ent_qtd.pack(fill="x", pady=(0, 12))

    def obter_item_selecionado() -> str | None:
        sel = lb.curselection()
        if not sel:
            return None
        idx = int(sel[0])
        try:
            return lb.get(idx)
        except Exception:
            return None

    def confirmar():
        item_txt = obter_item_selecionado()
        if not item_txt:
            messagebox.showwarning("Atenção", "Selecione um item na lista.")
            return

        qtd_txt = qtd_var.get().strip().replace(",", ".")
        try:
            qtd = float(qtd_txt)
            if qtd <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Atenção", "Quantidade inválida. Use um número maior que 0 (ex: 1 ou 1,5).")
            return

        pid = texto_para_id.get(item_txt)
        if not pid:
            messagebox.showerror("Erro", "Não foi possível identificar o item selecionado.")
            return

        try:
            delta = qtd if tipo == "entrada" else -qtd
            atualizar_estoque(pid, delta)
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return

        messagebox.showinfo("OK", "Movimento registrado com sucesso.")
        win.destroy()

    btn = ttk.Button(frame, text="Confirmar", command=confirmar)
    btn.pack(anchor="e")

    # Enter na quantidade confirma
    ent_qtd.bind("<Return>", lambda e: confirmar())


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

    ttk.Label(frame, text="Itens abaixo do estoque mínimo", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))

    cols = ("nome", "unidade", "atual", "minimo")
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
    tree.pack(fill="both", expand=True)

    tree.heading("nome", text="Item")
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
        messagebox.showinfo("OK", "Nenhum item está abaixo do mínimo.")


def ajustar_janela_ao_conteudo_e_centralizar(root: tk.Tk, margem: int = 24) -> None:
    root.update_idletasks()
    w = root.winfo_reqwidth() + margem
    h = root.winfo_reqheight() + margem

    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2

    root.geometry(f"{w}x{h}+{x}+{y}")
    root.minsize(w, h)


def main():
    root = tk.Tk()
    root.title("Estoque – Vila Vicentina de Abaeté")
    if ICONE_ICO.exists():
        try:
            root.iconbitmap(str(ICONE_ICO))
        except Exception:
            pass

    style = ttk.Style()
    style.configure("Menu.TButton", padding=(12, 10))

    frame = ttk.Frame(root, padding=16)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Controle de Estoque – Vila Vicentina", font=("Segoe UI", 15, "bold")).pack(pady=(0, 12))

    ttk.Button(frame, text="Cadastrar Item", style="Menu.TButton",
               command=lambda: abrir_cadastro_produto(root)).pack(fill="x", pady=6)

    ttk.Button(frame, text="Adicionar ao estoque", style="Menu.TButton",
               command=lambda: abrir_movimento(root, "entrada")).pack(fill="x", pady=6)

    ttk.Button(frame, text="Retirar do estoque", style="Menu.TButton",
               command=lambda: abrir_movimento(root, "saida")).pack(fill="x", pady=6)

    ttk.Button(frame, text="Estoque", style="Menu.TButton",
               command=lambda: abrir_tela_produtos(root)).pack(fill="x", pady=6)

    ttk.Button(frame, text="Itens em falta", style="Menu.TButton",
               command=lambda: abrir_abaixo_minimo(root)).pack(fill="x", pady=6)

    ajustar_janela_ao_conteudo_e_centralizar(root)
    root.mainloop()


if __name__ == "__main__":
    main()

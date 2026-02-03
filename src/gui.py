import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import unicodedata
import re

from .config import ICONE_ICO  # gui.py e config.py estão em src/
from .estoque_core import (
    listar_produtos,
    criar_produto,
    move_stock_by_id,
    listar_movimentos,
    exportar_movimentos_csv,
    exportar_movimentos_xlsx,
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
    # cadastro contínuo (não fecha, sem popup de sucesso)
    win = tk.Toplevel(root)
    win.title("Cadastrar Item")
    win.geometry("520x300")
    win.minsize(520, 300)

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Nome do item").pack(anchor="w")
    nome_var = tk.StringVar()
    nome_entry = ttk.Entry(frame, textvariable=nome_var)
    nome_entry.pack(fill="x", pady=(0, 10))

    ttk.Label(frame, text="Unidade (ex: un, kg, L)").pack(anchor="w")
    unidade_var = tk.StringVar()
    unidade_entry = ttk.Entry(frame, textvariable=unidade_var)
    unidade_entry.pack(fill="x", pady=(0, 10))

    ttk.Label(frame, text="Estoque mínimo").pack(anchor="w")
    minimo_var = tk.StringVar()
    minimo_entry = ttk.Entry(frame, textvariable=minimo_var)
    minimo_entry.pack(fill="x", pady=(0, 12))

    # feedback discreto + auto-clear
    status_var = tk.StringVar(value="")
    ttk.Label(frame, textvariable=status_var, foreground="green").pack(anchor="w", pady=(0, 8))
    status_after_id = None

    def _status_ok(msg: str, ms: int = 2000) -> None:
        nonlocal status_after_id
        status_var.set(msg)
        if status_after_id is not None:
            try:
                win.after_cancel(status_after_id)
            except Exception:
                pass
            status_after_id = None
        status_after_id = win.after(ms, lambda: status_var.set(""))

    def salvar():
        nome = nome_var.get().strip()
        unidade = unidade_var.get().strip()
        minimo_txt = minimo_var.get().strip().replace(",", ".")

        if not nome:
            messagebox.showwarning("Atenção", "O nome não pode ficar vazio.")
            nome_entry.focus_set()
            return
        if not unidade:
            messagebox.showwarning("Atenção", "A unidade não pode ficar vazia.")
            unidade_entry.focus_set()
            return
        try:
            minimo = float(minimo_txt)
            if minimo < 0:
                raise ValueError()
        except ValueError:
            messagebox.showwarning("Atenção", "Estoque mínimo inválido. Use um número (ex: 2 ou 2,5).")
            minimo_entry.focus_set()
            return

        try:
            criar_produto(nome=nome, unidade=unidade, estoque_minimo=float(minimo))
        except ProdutoDuplicado:
            messagebox.showerror("Erro", "Já existe um item com esse nome.")
            nome_entry.focus_set()
            return
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return

        _status_ok("Item cadastrado com sucesso.", ms=2000)

        nome_var.set("")
        unidade_var.set("")
        minimo_var.set("")
        nome_entry.focus_set()

    ttk.Button(frame, text="Salvar", command=salvar).pack(anchor="e")

    nome_entry.bind("<Return>", lambda e: unidade_entry.focus_set())
    unidade_entry.bind("<Return>", lambda e: minimo_entry.focus_set())
    minimo_entry.bind("<Return>", lambda e: salvar())

    nome_entry.focus_set()


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

    # Mapa id->produto para prévia (estoque atual/mínimo/unidade)
    id_para_produto: dict[int, dict] = {}
    for p in produtos:
        try:
            pid = int(p.get("id", 0))
        except Exception:
            continue
        id_para_produto[pid] = p

    win = tk.Toplevel(root)
    win.title("Entrada de Estoque" if tipo == "entrada" else "Saída de Estoque")
    win.geometry("560x470")  # ligeiro aumento para caber prévia/status

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
    status_frame.pack(fill="x", pady=(0, 4))

    resultados_var = tk.StringVar(value=f"{len(itens_originais)} itens")
    ttk.Label(status_frame, textvariable=resultados_var).pack(side="left")

    vazio_var = tk.StringVar(value="")
    ttk.Label(status_frame, textvariable=vazio_var).pack(side="right")

    # Feedback padrão (3 níveis) + auto-clear
    status_var = tk.StringVar(value="")
    lbl_status = ttk.Label(frame, textvariable=status_var, foreground="green")
    lbl_status.pack(anchor="w", pady=(0, 6))

    status_after_id = None
    CORES = {
        "success": "green",
        "warn": "#b26a00",
        "error": "#b00020",
        "info": "#1a1a1a",
    }

    def _status(msg: str, kind: str = "info", ms: int = 2200) -> None:
        nonlocal status_after_id
        lbl_status.configure(foreground=CORES.get(kind, CORES["info"]))
        status_var.set(msg)

        if status_after_id is not None:
            try:
                win.after_cancel(status_after_id)
            except Exception:
                pass
            status_after_id = None

        status_after_id = win.after(ms, lambda: status_var.set(""))

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
        exportselection=False,
        yscrollcommand=yscroll.set,
    )
    lb.pack(side="left", fill="both", expand=True)
    yscroll.config(command=lb.yview)

    for item in itens_originais:
        lb.insert("end", item)

    # ---------- PRÉVIA DO ESTOQUE DO ITEM SELECIONADO ----------
    preview_var = tk.StringVar(value="Selecione um item para ver o estoque atual.")
    lbl_preview = ttk.Label(frame, textvariable=preview_var)
    lbl_preview.pack(anchor="w", pady=(0, 10))

    def _atualizar_status(qtd: int):
        resultados_var.set(f"{qtd} item" if qtd == 1 else f"{qtd} itens")
        vazio_var.set("Nenhum item encontrado" if qtd == 0 else "")

    def _filtrar_rankeado_premium(texto_busca: str) -> list[str]:
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

    def obter_item_selecionado() -> str | None:
        sel = lb.curselection()
        if not sel:
            return None
        idx = int(sel[0])
        try:
            return lb.get(idx)
        except Exception:
            return None

    def _atualizar_preview():
        item_txt = obter_item_selecionado()
        if not item_txt:
            preview_var.set("Selecione um item para ver o estoque atual.")
            return

        pid = texto_para_id.get(item_txt)
        if not pid:
            preview_var.set("Não foi possível identificar o item selecionado.")
            return

        p = id_para_produto.get(int(pid), {})
        unidade = str(p.get("unidade", "")).strip()
        atual = p.get("estoque_atual", 0)
        minimo = p.get("estoque_minimo", 0)

        sufixo_un = f" {unidade}" if unidade else ""
        preview_var.set(f"Estoque atual: {atual}{sufixo_un}  |  Mínimo: {minimo}{sufixo_un}")

    def aplicar_filtro():
        filtradas = _filtrar_rankeado_premium(busca_var.get())
        _render_lista(filtradas)
        _atualizar_status(len(filtradas))

        if len(filtradas) == 1:
            lb.selection_clear(0, "end")
            lb.selection_set(0)
            lb.activate(0)
            lb.see(0)
            _atualizar_preview()
            _avaliar_warn_saida()  # ✅ reavalia aviso ao reduzir para 1 item
        else:
            preview_var.set("Selecione um item para ver o estoque atual.")

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
            _atualizar_preview()
            _avaliar_warn_saida()

    def ir_para_lista(event=None):
        if lb.size() > 0:
            selecionar_primeiro_da_lista()
            lb.focus_set()
        return "break"

    def on_busca_enter(event=None):
        if lb.size() > 0:
            selecionar_primeiro_da_lista()
            ent_qtd.focus_set()
        else:
            _status("Nenhum item para selecionar.", kind="warn", ms=2200)
        return "break"

    def on_busca_escape(event=None):
        busca_var.set("")
        _render_lista(itens_originais)
        _atualizar_status(len(itens_originais))
        lb.selection_clear(0, "end")
        preview_var.set("Selecione um item para ver o estoque atual.")
        ent_busca.focus_set()
        return "break"

    def on_lista_enter(event=None):
        ent_qtd.focus_set()
        return "break"

    def on_lista_double(event=None):
        ent_qtd.focus_set()
        return "break"

    def on_lista_escape(event=None):
        ent_busca.focus_set()
        return "break"

    ent_busca.bind("<KeyRelease>", on_busca_keyrelease)
    ent_busca.bind("<Down>", ir_para_lista)
    ent_busca.bind("<Return>", on_busca_enter)
    ent_busca.bind("<Escape>", on_busca_escape)

    ent_busca.focus_set()
    _atualizar_status(len(itens_originais))

    # ---------- QUANTIDADE ----------
    ttk.Label(frame, text="Quantidade (ex: 1,5)").pack(anchor="w")
    qtd_var = tk.StringVar()
    ent_qtd = ttk.Entry(frame, textvariable=qtd_var)
    ent_qtd.pack(fill="x", pady=(0, 12))

    # ✅ Aviso imediato: SAÍDA com quantidade maior que estoque atual
    _warn_ativa = False

    def _avaliar_warn_saida(event=None):
        nonlocal _warn_ativa, status_after_id

        # padrão: habilitado
        try:
            btn_confirmar.state(["!disabled"])
        except Exception:
            pass

        if tipo != "saida":
            _warn_ativa = False
            return

        item_txt = obter_item_selecionado()
        if not item_txt:
            _warn_ativa = False
            return

        pid = texto_para_id.get(item_txt)
        if not pid:
            _warn_ativa = False
            return

        p = id_para_produto.get(int(pid), {})
        try:
            atual = float(p.get("estoque_atual", 0))
        except Exception:
            atual = 0.0

        txt = qtd_var.get().strip()
        if not txt:
            # campo vazio: limpa aviso e deixa botão habilitado
            if _warn_ativa:
                status_var.set("")
            _warn_ativa = False
            return

        try:
            qtd = float(txt.replace(",", "."))
        except Exception:
            # digitando: não trava botão
            if _warn_ativa:
                status_var.set("")
            _warn_ativa = False
            return

        if qtd > atual:
            _warn_ativa = True

            # 🔒 fixa o aviso: cancela auto-clear
            if status_after_id is not None:
                try:
                    win.after_cancel(status_after_id)
                except Exception:
                    pass
                status_after_id = None

            lbl_status.configure(foreground=CORES.get("warn", "#b26a00"))
            status_var.set(f"⚠ Atenção: {qtd} é maior que o estoque atual ({atual}).")

            # 🚫 desabilita confirmar enquanto estiver inválido
            try:
                btn_confirmar.state(["disabled"])
            except Exception:
                pass
        else:
            # corrigiu: limpa aviso e habilita botão
            if _warn_ativa:
                status_var.set("")
            _warn_ativa = False
            try:
                btn_confirmar.state(["!disabled"])
            except Exception:
                pass


    def on_lista_select(event=None):
        _atualizar_preview()
        _avaliar_warn_saida()

    lb.bind("<<ListboxSelect>>", on_lista_select)
    lb.bind("<Return>", on_lista_enter)
    lb.bind("<Double-Button-1>", on_lista_double)
    lb.bind("<Escape>", on_lista_escape)

    # Avalia aviso enquanto digita a quantidade
    ent_qtd.bind("<KeyRelease>", _avaliar_warn_saida)

    def confirmar(foco_busca: bool = False):
        # 🚫 trava Enter / Ctrl+Enter se o botão estiver desabilitado
        try:
            if "disabled" in btn_confirmar.state():
                # mantém padrão visual (âmbar) e mensagem fixa curta
                lbl_status.configure(foreground=CORES.get("warn", "#b26a00"))
                status_var.set("⚠ Corrija a quantidade (está maior que o estoque atual).")
                ent_qtd.focus_set()
                return
        except Exception:
            pass

        item_txt = obter_item_selecionado()
        if not item_txt:
            _status("Selecione um item na lista.", kind="warn", ms=2500)
            lb.focus_set()
            return

        qtd_txt = qtd_var.get().strip().replace(",", ".")
        try:
            qtd = float(qtd_txt)
            if qtd <= 0:
                raise ValueError()
        except ValueError:
            _status("Quantidade inválida. Use um número maior que 0 (ex: 1 ou 1,5).", kind="warn", ms=2800)
            ent_qtd.focus_set()
            return

        pid = texto_para_id.get(item_txt)
        if not pid:
            messagebox.showerror("Erro", "Não foi possível identificar o item selecionado.")
            return

        try:
            delta = qtd if tipo == "entrada" else -qtd
            atualizar_estoque(int(pid), float(delta))
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            ent_qtd.focus_set()
            return

        _status(
            "Entrada registrada com sucesso." if tipo == "entrada" else "Saída registrada com sucesso.",
            kind="success",
            ms=2000,
        )


        qtd_var.set("")

        # Atualiza preview (estoque mudou) sem mexer no core: recarrega produtos do core
        novos = carregar_produtos()
        for pp in novos:
            try:
                pid2 = int(pp.get("id", 0))
            except Exception:
                continue
            id_para_produto[pid2] = pp

        _atualizar_preview()
        _avaliar_warn_saida()

        if foco_busca:
            ent_busca.focus_set()
        else:
            ent_qtd.focus_set()

    btn_confirmar = ttk.Button(frame, text="Confirmar", command=lambda: confirmar(False))
    btn_confirmar.pack(anchor="e")


    # Enter confirma
    ent_qtd.bind("<Return>", lambda e: confirmar(False))
    # Ctrl+Enter confirma e volta para busca
    win.bind("<Control-Return>", lambda e: (confirmar(True), "break"))
    # Esc na quantidade: limpa e volta para busca
    def _esc_qtd(event=None):
        qtd_var.set("")
        ent_busca.focus_set()
        _avaliar_warn_saida()
        return "break"
    ent_qtd.bind("<Escape>", _esc_qtd)



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

    # feedback discreto (sem popup)
    status_var = tk.StringVar(value="")
    lbl = ttk.Label(frame, textvariable=status_var, foreground="green")
    lbl.pack(anchor="w", pady=(0, 8))
    status_after_id = None

    def _status_ok(msg: str, ms: int = 2500) -> None:
        nonlocal status_after_id
        status_var.set(msg)
        if status_after_id is not None:
            try:
                win.after_cancel(status_after_id)
            except Exception:
                pass
            status_after_id = None
        status_after_id = win.after(ms, lambda: status_var.set(""))

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
        _status_ok("Nenhum item está abaixo do mínimo.", ms=2500)


def abrir_historico(root: tk.Tk) -> None:
    LIMITE_PADRAO = 300

    win = tk.Toplevel(root)
    win.title("Histórico de movimentações")
    win.geometry("900x620")
    win.minsize(820, 560)

    frame = ttk.Frame(win, padding=12)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Histórico de movimentações", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))

    filtros = ttk.Frame(frame)
    filtros.pack(fill="x", pady=(0, 10))

    ttk.Label(filtros, text="Filtrar por item").pack(side="left")
    filtro_var = tk.StringVar(value="")
    ent_filtro = ttk.Entry(filtros, textvariable=filtro_var, width=30)
    ent_filtro.pack(side="left", padx=(8, 16))

    ttk.Label(filtros, text="Limite").pack(side="left")
    limite_var = tk.StringVar(value=str(LIMITE_PADRAO))
    ent_limite = ttk.Entry(filtros, textvariable=limite_var, width=8)
    ent_limite.pack(side="left", padx=(8, 16))

    # feedback discreto
    ok_var = tk.StringVar(value="")
    ttk.Label(filtros, textvariable=ok_var, foreground="green").pack(side="right")

    ok_after_id = None

    def _ok(msg: str, ms: int = 2500) -> None:
        nonlocal ok_after_id
        ok_var.set(msg)
        if ok_after_id is not None:
            try:
                win.after_cancel(ok_after_id)
            except Exception:
                pass
            ok_after_id = None
        ok_after_id = win.after(ms, lambda: ok_var.set(""))

    status_var = tk.StringVar(value="")
    ttk.Label(filtros, textvariable=status_var).pack(side="right", padx=(0, 10))

    cols = ("ts", "nome", "tipo", "qtd", "antes", "depois")

    table_frame = ttk.Frame(frame)
    table_frame.pack(fill="both", expand=True)

    tree_frame = ttk.Frame(table_frame)
    tree_frame.pack(fill="both", expand=True)

    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=16)
    tree.pack(side="left", fill="both", expand=True)

    yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    yscroll.pack(side="right", fill="y")

    xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
    xscroll.pack(side="bottom", fill="x")

    tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

    tree.heading("ts", text="Data/Hora")
    tree.heading("nome", text="Item")
    tree.heading("tipo", text="Tipo")
    tree.heading("qtd", text="Qtd")
    tree.heading("antes", text="Antes")
    tree.heading("depois", text="Depois")

    tree.column("ts", width=150, anchor="center")
    tree.column("nome", width=320)
    tree.column("tipo", width=90, anchor="center")
    tree.column("qtd", width=90, anchor="center")
    tree.column("antes", width=90, anchor="center")
    tree.column("depois", width=90, anchor="center")

    for col in cols:
        tree.heading(col, anchor="center")

    movimentos_cache: list[dict] = []

    def _parse_limite() -> int:
        try:
            n = int(limite_var.get().strip())
        except Exception:
            n = LIMITE_PADRAO
        if n < 1:
            n = 1
        if n > 5000:
            n = 5000
        return n

    def _format_tipo(delta: float) -> str:
        return "Entrada" if float(delta) > 0 else "Saída"

    def _format_qtd(delta: float) -> float:
        return abs(float(delta))

    def carregar():
        nonlocal movimentos_cache
        limite = _parse_limite()
        movimentos = listar_movimentos(limite=limite)
        movimentos_cache = list(reversed(movimentos))  # mais recentes primeiro
        aplicar_filtro()

    def aplicar_filtro():
        tree.delete(*tree.get_children())

        termo = normalizar_busca(filtro_var.get().strip())
        count = 0

        for m in movimentos_cache:
            nome = str(m.get("nome", ""))
            nome_norm = normalizar_busca(nome)

            if termo and termo not in nome_norm:
                continue

            delta = float(m.get("delta", 0))
            ts = str(m.get("ts", ""))

            tree.insert(
                "", "end",
                values=(
                    ts,
                    nome,
                    _format_tipo(delta),
                    _format_qtd(delta),
                    m.get("estoque_antes", ""),
                    m.get("estoque_depois", ""),
                ),
            )
            count += 1

        status_var.set(f"{count} registro(s)")

    def limpar_filtro():
        filtro_var.set("")
        aplicar_filtro()

    def exportar_csv():
        from datetime import datetime
        nome_sugerido = f"historico_estoque_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        caminho = filedialog.asksaveasfilename(
            title="Salvar histórico em CSV",
            defaultextension=".csv",
            initialfile=nome_sugerido,
            filetypes=[("CSV", "*.csv")],
        )
        if not caminho:
            return

        try:
            termo = normalizar_busca(filtro_var.get().strip())
            movs = []
            for m in movimentos_cache:
                nome = str(m.get("nome", ""))
                nome_norm = normalizar_busca(nome)
                if termo and termo not in nome_norm:
                    continue
                movs.append(m)

            exportar_movimentos_csv(caminho, limite=len(movs))
            _ok("CSV exportado com sucesso.", ms=2500)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível exportar o CSV.\n\n{e}")

    def exportar_excel():
        from datetime import datetime
        nome_sugerido = f"historico_estoque_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        caminho = filedialog.asksaveasfilename(
            title="Salvar histórico em Excel",
            defaultextension=".xlsx",
            initialfile=nome_sugerido,
            filetypes=[("Excel", "*.xlsx")],
        )
        if not caminho:
            return

        try:
            termo = normalizar_busca(filtro_var.get().strip())
            movs = []
            for m in movimentos_cache:
                nome = str(m.get("nome", ""))
                nome_norm = normalizar_busca(nome)
                if termo and termo not in nome_norm:
                    continue
                movs.append(m)

            exportar_movimentos_xlsx(caminho, movs)
            _ok("Excel exportado com sucesso.", ms=2500)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível exportar o Excel.\n\n{e}")

    botoes = ttk.Frame(frame)
    botoes.pack(fill="x", pady=(10, 0))

    ttk.Button(botoes, text="Atualizar", command=carregar).pack(side="right")
    ttk.Button(botoes, text="Exportar Excel", command=exportar_excel).pack(side="right", padx=(0, 8))
    ttk.Button(botoes, text="Exportar CSV", command=exportar_csv).pack(side="right", padx=(0, 8))
    ttk.Button(botoes, text="Limpar filtro", command=limpar_filtro).pack(side="right", padx=(0, 8))

    ent_filtro.bind("<Return>", lambda e: aplicar_filtro())
    ent_filtro.bind("<Escape>", lambda e: limpar_filtro())

    carregar()
    ent_filtro.focus_set()


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

    ttk.Button(frame, text="Histórico", style="Menu.TButton",
               command=lambda: abrir_historico(root)).pack(fill="x", pady=6)

    ttk.Button(frame, text="Itens em falta", style="Menu.TButton",
               command=lambda: abrir_abaixo_minimo(root)).pack(fill="x", pady=6)

    ajustar_janela_ao_conteudo_e_centralizar(root)
    root.mainloop()


if __name__ == "__main__":
    main()

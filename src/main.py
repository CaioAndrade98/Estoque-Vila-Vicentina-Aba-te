import json
from config import ARQUIVO_DADOS
from typing import Optional



def mostrar_menu():
    print("\n=== Controle de Estoque (v1) ===")
    print("1 - Cadastrar produto")
    print("2 - Listar produtos")
    print("3 - Entrada de estoque")
    print("4 - Saída de estoque")
    print("5 - Produtos abaixo do mínimo")
    print("0 - Sair")


def ler_texto(msg: str) -> str:
    texto = input(msg).strip()
    return texto


def ler_int(msg: str) -> Optional[int]:
    valor = input(msg).strip()
    if not valor.isdigit():
        return None
    return int(valor)

def ler_float(msg: str) -> Optional[float]:
    valor = input(msg).strip().replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return None


def carregar_produtos() -> list[dict]:
    """Carrega a lista de produtos do JSON. Se não existir, retorna lista vazia."""
    if not ARQUIVO_DADOS.exists():
        return []

    try:
        with ARQUIVO_DADOS.open("r", encoding="utf-8") as f:
            dados = json.load(f)

        # Garantia mínima de formato
        if isinstance(dados, list):
            return dados

        print("⚠️ Arquivo de dados está num formato inesperado. Iniciando vazio.")
        return []
    except json.JSONDecodeError:
        print("⚠️ O arquivo dados.json está corrompido/invalidado (JSON inválido). Iniciando vazio.")
        return []
    except Exception as e:
        print(f"⚠️ Não foi possível carregar dados.json: {e}. Iniciando vazio.")
        return []


def salvar_produtos(produtos: list[dict]) -> None:
    """Salva a lista de produtos no JSON (bonitinho)."""
    try:
        with ARQUIVO_DADOS.open("w", encoding="utf-8") as f:
            json.dump(produtos, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Não foi possível salvar dados.json: {e}")


def gerar_proximo_id(produtos):
    if not produtos:
        return 1
    return max(p["id"] for p in produtos) + 1


def cadastrar_produto(produtos):
    nome = ler_texto("Nome do produto: ")
    if not nome:
        print("Nome não pode ser vazio.")
        return

    unidade = ler_texto("Unidade (ex: kg, un, L): ")
    if not unidade:
        print("Unidade não pode ser vazia.")
        return

    estoque_minimo = ler_int("Estoque mínimo (número inteiro): ")
    if estoque_minimo is None:
        print("Digite um número válido.")
        return

    produto = {
        "id": gerar_proximo_id(produtos),
        "nome": nome,
        "unidade": unidade,
        "estoque_atual": 0,
        "estoque_minimo": estoque_minimo,
    }
    produtos.append(produto)
    salvar_produtos(produtos)
    print(f"Produto cadastrado! (id={produto['id']})")


def listar_produtos(produtos):
    if not produtos:
        print("Nenhum produto cadastrado.")
        return

    print("\nID | Produto | Unidade | Atual | Mínimo")
    for p in produtos:
        print(f"{p['id']} | {p['nome']} | {p['unidade']} | {p['estoque_atual']} | {p['estoque_minimo']}")


def encontrar_produto(produtos, produto_id: int):
    for p in produtos:
        if p["id"] == produto_id:
            return p
    return None

def selecionar_produto_por_nome(produtos) -> Optional[dict]:
    termo = ler_texto("Digite parte do nome do produto: ").lower()
    if not termo:
        print("Busca vazia.")
        return None

    candidatos = [p for p in produtos if termo in p["nome"].lower()]
    if not candidatos:
        print("Nenhum produto encontrado.")
        return None

    candidatos = sorted(candidatos, key=lambda x: x["nome"].lower())

    print("\nEscolha um produto:")
    for idx, p in enumerate(candidatos, start=1):
        print(f"{idx} - {p['nome']} ({p['unidade']}) | Atual: {p['estoque_atual']}")

    escolha = ler_int("Número da lista: ")
    if escolha is None or escolha < 1 or escolha > len(candidatos):
        print("Escolha inválida.")
        return None

    return candidatos[escolha - 1]


def entrada_estoque(produtos):
    produto = selecionar_produto_por_nome(produtos)
    if not produto:
        return

    qtd = ler_float("Quantidade de entrada (ex: 1,5): ")
    if qtd is None or qtd <= 0:
        print("Quantidade inválida (precisa ser maior que 0).")
        return

    produto["estoque_atual"] += qtd
    salvar_produtos(produtos)
    print("Entrada registrada!")




def saida_estoque(produtos):
    produto = selecionar_produto_por_nome(produtos)
    if not produto:
        return

    qtd = ler_float("Quantidade de saída (ex: 0,5): ")
    if qtd is None or qtd <= 0:
        print("Quantidade inválida (precisa ser maior que 0).")
        return

    if produto["estoque_atual"] < qtd:
        print("Saída inválida: estoque insuficiente.")
        return

    produto["estoque_atual"] -= qtd
    salvar_produtos(produtos)
    print("Saída registrada!")




def listar_abaixo_do_minimo(produtos):
    abaixo = [p for p in produtos if p["estoque_atual"] < p["estoque_minimo"]]
    if not abaixo:
        print("Nenhum produto abaixo do mínimo.")
        return

    print("\nProdutos abaixo do mínimo:")
    for p in abaixo:
        print(f"- {p['nome']} (Atual: {p['estoque_atual']} / Mínimo: {p['estoque_minimo']})")


def main():
    produtos = carregar_produtos()
    if produtos:
        print(f"✅ Dados carregados de {ARQUIVO_DADOS.name} ({len(produtos)} produto(s)).")
    else:
        print("ℹ️ Iniciando com estoque vazio (nenhum dado salvo ainda).")

    while True:
        mostrar_menu()
        opcao = ler_texto("Escolha uma opção: ")

        if opcao == "1":
            cadastrar_produto(produtos)
        elif opcao == "2":
            listar_produtos(produtos)
        elif opcao == "3":
            entrada_estoque(produtos)
        elif opcao == "4":
            saida_estoque(produtos)
        elif opcao == "5":
            listar_abaixo_do_minimo(produtos)
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()

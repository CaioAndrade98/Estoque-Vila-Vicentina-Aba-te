from typing import Optional

from estoque_core_v2 import (
    EstoqueError,
    ProdutoJaExiste,
    ProdutoNaoEncontrado,
    EstoqueInsuficiente,
    ValidacaoInvalida,
    create_product,
    load_products,
    move_stock_by_id,
    list_below_minimum,
)


def mostrar_menu():
    print("\n=== Controle de Estoque (CLI) ===")
    print("1 - Cadastrar item")
    print("2 - Listar itens")
    print("3 - Entrada de estoque")
    print("4 - Saída de estoque")
    print("5 - Itens abaixo do mínimo")
    print("0 - Sair")


def ler_texto(msg: str) -> str:
    return input(msg).strip()


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


def selecionar_produto_por_nome() -> Optional[dict]:
    produtos = load_products()

    termo = ler_texto("Digite parte do nome do item: ").lower()
    if not termo:
        print("Busca vazia.")
        return None

    candidatos = [p for p in produtos if termo in str(p.get("nome", "")).lower()]
    if not candidatos:
        print("Nenhum item encontrado.")
        return None

    candidatos = sorted(candidatos, key=lambda x: str(x.get("nome", "")).lower())

    print("\nEscolha um item:")
    for idx, p in enumerate(candidatos, start=1):
        print(f"{idx} - {p.get('nome')} ({p.get('unidade')}) | Atual: {p.get('estoque_atual', 0)}")

    escolha = ler_int("Número da lista: ")
    if escolha is None or escolha < 1 or escolha > len(candidatos):
        print("Escolha inválida.")
        return None

    return candidatos[escolha - 1]


def cadastrar_item_cli():
    nome = ler_texto("Nome do item: ")
    unidade = ler_texto("Unidade (ex: kg, un, L): ")
    minimo = ler_float("Estoque mínimo (ex: 2 ou 2,5): ")

    if minimo is None:
        print("Estoque mínimo inválido.")
        return

    try:
        novo = create_product(nome=nome, unidade=unidade, estoque_minimo=minimo)
        print(f"✅ Item cadastrado! (id={novo['id']})")
    except ProdutoJaExiste as e:
        print(f"⚠️ {e}")
    except ValidacaoInvalida as e:
        print(f"⚠️ {e}")
    except EstoqueError as e:
        print(f"⚠️ Erro: {e}")


def listar_itens_cli():
    produtos = load_products()
    if not produtos:
        print("Nenhum item cadastrado.")
        return

    print("\nID | Item | Unidade | Atual | Mínimo")
    for p in produtos:
        print(f"{p.get('id')} | {p.get('nome')} | {p.get('unidade')} | {p.get('estoque_atual', 0)} | {p.get('estoque_minimo', 0)}")


def entrada_cli():
    produto = selecionar_produto_por_nome()
    if not produto:
        return

    qtd = ler_float("Quantidade de entrada (ex: 1,5): ")
    if qtd is None or qtd <= 0:
        print("Quantidade inválida (precisa ser maior que 0).")
        return

    try:
        atualizado = move_stock_by_id(int(produto["id"]), float(qtd))
        print(f"✅ Entrada registrada! Novo estoque: {atualizado.get('estoque_atual', 0)}")
    except EstoqueError as e:
        print(f"⚠️ {e}")


def saida_cli():
    produto = selecionar_produto_por_nome()
    if not produto:
        return

    qtd = ler_float("Quantidade de saída (ex: 0,5): ")
    if qtd is None or qtd <= 0:
        print("Quantidade inválida (precisa ser maior que 0).")
        return

    try:
        atualizado = move_stock_by_id(int(produto["id"]), -float(qtd))
        print(f"✅ Saída registrada! Novo estoque: {atualizado.get('estoque_atual', 0)}")
    except EstoqueInsuficiente:
        print("⚠️ Saída inválida: estoque insuficiente.")
    except ProdutoNaoEncontrado:
        print("⚠️ Item não encontrado (pode ter sido removido).")
    except EstoqueError as e:
        print(f"⚠️ {e}")


def abaixo_minimo_cli():
    abaixo = list_below_minimum()
    if not abaixo:
        print("Nenhum item abaixo do mínimo.")
        return

    print("\nItens abaixo do mínimo:")
    for p in abaixo:
        print(f"- {p.get('nome')} (Atual: {p.get('estoque_atual', 0)} / Mínimo: {p.get('estoque_minimo', 0)})")


def main():
    produtos = load_products()
    if produtos:
        print(f"✅ Dados carregados ({len(produtos)} item(ns)).")
    else:
        print("ℹ️ Iniciando com estoque vazio (nenhum dado salvo ainda).")

    while True:
        mostrar_menu()
        opcao = ler_texto("Escolha uma opção: ")

        if opcao == "1":
            cadastrar_item_cli()
        elif opcao == "2":
            listar_itens_cli()
        elif opcao == "3":
            entrada_cli()
        elif opcao == "4":
            saida_cli()
        elif opcao == "5":
            abaixo_minimo_cli()
        elif opcao == "0":
            print("Saindo...")
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    main()

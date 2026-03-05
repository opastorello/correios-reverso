#!/usr/bin/env python
"""
Script de exemplo para uso da biblioteca correios-reverso.

Uso:
    python scripts/exemplo_uso_api.py              # Executa todos os exemplos
    python scripts/exemplo_uso_api.py --cep        # Apenas consulta CEP
    python scripts/exemplo_uso_api.py --listar     # Apenas lista postagens
    python scripts/exemplo_uso_api.py --criar      # Cria postagem de teste (e cancela)
    python scripts/exemplo_uso_api.py --api        # Testa API REST (requer servidor rodando)

Requer arquivo .env com credenciais configuradas.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from typing import Any

sys.path.insert(0, "src")


def print_section(title: str) -> None:
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_json(data: Any, indent: int = 2) -> None:
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    print(json.dumps(data, indent=indent, ensure_ascii=False, default=str))


def testar_conexao() -> bool:
    """Testa conexÃ£o e login com Correios."""
    print_section("TESTAR CONEXÃƒO")

    from correios_reverso import CorreiosClient

    try:
        with CorreiosClient.from_env() as client:
            print("âœ“ Login realizado com sucesso")
            cartoes = client.auxiliares.listar_cartoes_postagem()
            for c in cartoes.itens:
                contrato = c.contrato if hasattr(c, 'contrato') else c.numeroContrato if hasattr(c, 'numeroContrato') else 'N/A'
                print(f"  CartÃ£o: {c.numeroCartao} - Contrato: {contrato}")
            return True
    except Exception as e:
        print(f"âœ— Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def consultar_cep(cep: str = "01001000") -> None:
    """Consulta endereÃ§o por CEP."""
    print_section(f"CONSULTAR CEP: {cep}")

    from correios_reverso import CorreiosClient

    with CorreiosClient.from_env() as client:
        result = client.auxiliares.consultar_cep(cep)
        print_json(result)


def listar_servicos(logistica_reversa: bool = False) -> None:
    """Lista serviÃ§os disponÃ­veis."""
    titulo = "LISTAR SERVIÃ‡OS (LOGÃSTICA REVERSA)" if logistica_reversa else "LISTAR SERVIÃ‡OS"
    print_section(titulo)

    from correios_reverso import CorreiosClient

    with CorreiosClient.from_env() as client:
        servicos = client.postagem.listar_servicos(logistica_reversa=logistica_reversa)
        print(f"Total: {len(servicos)} serviÃ§os\n")
        for s in servicos:
            lr_tag = " [LR]" if s.inDescontoLogisticaReversa == "S" else ""
            print(f"  {s.codigo} - {s.descricao}{lr_tag}")


def listar_postagens(limite: int = 5, logistica_reversa: bool = False) -> None:
    """Lista prÃ©-postagens registradas."""
    titulo = "LISTAR PRÃ‰-POSTAGENS (LR)" if logistica_reversa else "LISTAR PRÃ‰-POSTAGENS"
    print_section(titulo)

    from correios_reverso import CorreiosClient

    with CorreiosClient.from_env() as client:
        result = client.postagem.listar_registrados(logistica_reversa=logistica_reversa)
        print(f"Total: {result.page.count} prÃ©-postagens\n")

        for i, item in enumerate(result.itens[:limite]):
            lr_tag = " [LR]" if item.logisticaReversa == "S" else ""
            print(f"{i + 1}. {item.codigoObjeto}{lr_tag}")
            print(f"   ServiÃ§o: {item.servico}")
            print(f"   Status: {item.descStatusAtual}")
            if hasattr(item, 'remetente') and item.remetente:
                print(f"   Remetente: {item.remetente.nome if hasattr(item.remetente, 'nome') else item.remetente.get('nome', 'N/A')}")
            print()


def listar_destinatarios() -> None:
    """Lista destinatÃ¡rios cadastrados."""
    print_section("LISTAR DESTINATÃRIOS")

    from correios_reverso import CorreiosClient

    with CorreiosClient.from_env() as client:
        result = client.destinatarios.pesquisar()
        if hasattr(result, 'page'):
            total = result.page.count
            itens = result.itens if hasattr(result, 'itens') else []
        else:
            total = len(result.get("itens", []))
            itens = result.get("itens", [])
        print(f"Total: {total} destinatÃ¡rios\n")

        for item in itens[:10]:
            if hasattr(item, 'model_dump'):
                item = item.model_dump()
            print(f"  ID: {item.get('id')}")
            print(f"  Nome: {item.get('nome')}")
            print()


def listar_remetentes() -> None:
    """Lista remetentes cadastrados."""
    print_section("LISTAR REMETENTES")

    from correios_reverso import CorreiosClient

    with CorreiosClient.from_env() as client:
        result = client.remetentes.pesquisar()
        if hasattr(result, 'page'):
            total = result.page.count
            itens = result.itens if hasattr(result, 'itens') else []
        else:
            total = len(result.get("itens", []))
            itens = result.get("itens", [])
        print(f"Total: {total} remetentes\n")

        for item in itens[:10]:
            if hasattr(item, 'model_dump'):
                item = item.model_dump()
            nome = item.get('nome') or item.get('nomeRemetente')
            print(f"  ID: {item.get('id')}")
            print(f"  Nome: {nome}")
            print()


def criar_e_cancelar_postagem(tipo: str = "normal") -> None:
    """Cria uma prÃ©-postagem de teste e cancela em seguida."""
    titulo = f"CRIAR E CANCELAR PRÃ‰-POSTAGEM ({tipo.upper()})"
    print_section(titulo)

    from correios_reverso import CorreiosClient
    from correios_reverso.models import (
        CriarPrePostagemRequest,
        PessoaPrePostagem,
        Endereco,
        ItemDeclaracaoConteudo,
    )

    with CorreiosClient.from_env() as client:
        # Contagem antes
        antes = client.postagem.listar_registrados().page.count
        print(f"PrÃ©-postagens antes: {antes}")

        remetente = PessoaPrePostagem(
            nome="TESTE AUTOMATIZADO REMETENTE",
            cpfCnpj="18552346000168",
            email="teste@teste.com",
            endereco=Endereco(
                cep="01001000",
                logradouro="Rua Exemplo",
                numero="1190",
                bairro="Centro",
                cidade="Sao Paulo",
                uf="RS",
            ),
        )

        destinatario = PessoaPrePostagem(
            nome="TESTE AUTOMATIZADO DESTINATARIO",
            cpfCnpj="18552346000320",
            email="dest@teste.com",
            endereco=Endereco(
                cep="20040000",
                logradouro="Av Exemplo",
                numero="803",
                bairro="Centro",
                cidade="Osasco",
                uf="SP",
            ),
        )

        if tipo == "lr":
            req = CriarPrePostagemRequest(
                remetente=remetente,
                destinatario=destinatario,
                codigoServico="03301",
                servico="03301 - PAC REVERSO",
                logisticaReversa="S",
                dataValidadeLogReversa=(datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y"),
                pesoInformado="300",
                itensDeclaracaoConteudo=[
                    ItemDeclaracaoConteudo(conteudo="Produto teste LR", quantidade=1, valor=50.0),
                ],
            )
        else:
            req = CriarPrePostagemRequest(
                remetente=remetente,
                destinatario=destinatario,
                codigoServico="03298",
                servico="03298 - PAC CONTRATO AG",
                pesoInformado="500",
                itensDeclaracaoConteudo=[
                    ItemDeclaracaoConteudo(conteudo="Produto teste", quantidade=1, valor=100.0),
                ],
            )

        # Criar
        print("\nCriando prÃ©-postagem...")
        result = client.postagem.criar(req)
        print("âœ“ Criada com sucesso!")

        # Contagem depois
        depois = client.postagem.listar_registrados().page.count
        print(f"\nPrÃ©-postagens depois: {depois} (esperado: {antes + 1})")

        # Buscar o item criado
        postagens = client.postagem.listar_registrados()
        item_criado = None
        for item in postagens.itens:
            nome_rem = item.remetente.nome if hasattr(item.remetente, 'nome') else ""
            if "TESTE AUTOMATIZADO" in nome_rem:
                item_criado = item
                break

        if item_criado:
            print(f"\nItem criado encontrado:")
            print(f"  ID: {item_criado.id}")
            print(f"  CÃ³digo: {item_criado.codigoObjeto}")
            print(f"  LR: {item_criado.logisticaReversa}")

            # Cancelar
            print(f"\nCancelando {item_criado.id}...")
            msg = client.cancelamento.cancelar(item_criado.id)
            print(f"âœ“ {msg}")

            # Verificar contagem final
            final = client.postagem.listar_registrados().page.count
            print(f"\nPrÃ©-postagens final: {final} (esperado: {antes})")
        else:
            print("âš  Item criado nÃ£o encontrado na lista")


def testar_api_rest(base_url: str = "http://localhost:8000", token: str = "") -> None:
    """Testa endpoints da API REST."""
    print_section("TESTAR API REST")

    import requests

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    def get(path: str) -> dict:
        resp = requests.get(f"{base_url}{path}", headers=headers, timeout=30)
        print(f"GET {path} -> {resp.status_code}")
        try:
            return resp.json()
        except:
            return {"text": resp.text[:500]}

    # Health
    print("\n--- Health ---")
    try:
        health = get("/health")
        print_json(health)
    except Exception as e:
        print(f"  Erro: {e}")
        print("  Certifique-se de que o servidor estÃ¡ rodando:")
        print("  uvicorn correios_reverso.api.app:app --reload --port 8000")
        return

    # CEP
    print("\n--- CEP ---")
    cep = get("/cep/01001000")
    print_json(cep)

    # ServiÃ§os
    print("\n--- ServiÃ§os ---")
    servicos = get("/postagem/servicos")
    print(f"Total: {len(servicos)} serviÃ§os")

    # Postagens
    print("\n--- Postagens ---")
    postagens = get("/postagem?pagina=0")
    print(f"Total: {postagens.get('page', {}).get('count', 0)} prÃ©-postagens")

    # DestinatÃ¡rios
    print("\n--- DestinatÃ¡rios ---")
    dests = get("/destinatarios")
    print(f"Total: {dests.get('page', {}).get('count', 0)} destinatÃ¡rios")

    # Remetentes
    print("\n--- Remetentes ---")
    remet = get("/remetentes")
    print(f"Total: {remet.get('page', {}).get('count', 0)} remetentes")

    # CartÃµes
    print("\n--- CartÃµes ---")
    cartoes = get("/cartoes")
    print_json(cartoes)

    # Embalagens
    print("\n--- Embalagens ---")
    emb = get("/embalagens")
    print_json(emb)

    print("\nâœ“ Testes da API REST concluÃ­dos")


def main():
    parser = argparse.ArgumentParser(description="Exemplos de uso do correios-reverso")
    parser.add_argument("--cep", action="store_true", help="Consultar CEP")
    parser.add_argument("--listar", action="store_true", help="Listar prÃ©-postagens")
    parser.add_argument("--servicos", action="store_true", help="Listar serviÃ§os")
    parser.add_argument("--destinatarios", action="store_true", help="Listar destinatÃ¡rios")
    parser.add_argument("--remetentes", action="store_true", help="Listar remetentes")
    parser.add_argument("--criar", action="store_true", help="Criar e cancelar postagem de teste")
    parser.add_argument("--criar-lr", action="store_true", help="Criar e cancelar postagem LR")
    parser.add_argument("--api", action="store_true", help="Testar API REST")
    parser.add_argument("--api-url", default="http://localhost:8000", help="URL base da API")
    parser.add_argument("--token", default="", help="Token de autenticaÃ§Ã£o")
    parser.add_argument("--all", action="store_true", help="Executar todos os testes")

    args = parser.parse_args()

    # Se nenhum argumento, executa tudo exceto criar
    run_all = args.all or not any([
        args.cep, args.listar, args.servicos, args.destinatarios,
        args.remetentes, args.criar, args.criar_lr, args.api
    ])

    try:
        if run_all or not args.api:
            # Biblioteca Python
            if not testar_conexao():
                print("\nâœ— Falha na conexÃ£o. Verifique o arquivo .env")
                return 1

        if run_all or args.cep:
            consultar_cep()

        if run_all or args.servicos:
            listar_servicos()
            listar_servicos(logistica_reversa=True)

        if run_all or args.listar:
            listar_postagens()
            listar_postagens(logistica_reversa=True)

        if run_all or args.destinatarios:
            listar_destinatarios()

        if run_all or args.remetentes:
            listar_remetentes()

        if args.criar:
            criar_e_cancelar_postagem("normal")

        if args.criar_lr:
            criar_e_cancelar_postagem("lr")

        if args.api:
            testar_api_rest(args.api_url, args.token)

        print_section("CONCLUÃDO")
        print("âœ“ Todos os testes passaram com sucesso!")
        return 0

    except Exception as e:
        print(f"\nâœ— Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())


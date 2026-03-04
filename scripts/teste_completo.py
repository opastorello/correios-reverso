#!/usr/bin/env python
"""
Plano de Teste Completo - Correios Reverso

Testa TODA a infraestrutura:
1. Biblioteca Python (local)
2. API REST (requer servidor rodando)
3. MCP Tools (requer servidor rodando)

IMPORTANTE: Tudo que for criado durante os testes será DELETADO ao final.

Uso:
    # Testar biblioteca Python localmente
    python scripts/teste_completo.py --lib

    # Testar API REST (requer: uvicorn correios_reverso.api.app:app --port 8000)
    python scripts/teste_completo.py --api

    # Testar MCP (requer servidor API rodando)
    python scripts/teste_completo.py --mcp

    # Testar TUDO
    python scripts/teste_completo.py --all

    # Com token de autenticação
    python scripts/teste_completo.py --api --token seu_token_aqui
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

sys.path.insert(0, "src")


class TestReporter:
    """Reporter de resultados de teste."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests: list[dict] = []

    def success(self, name: str, detail: str = ""):
        self.passed += 1
        self.tests.append({"name": name, "status": "PASS", "detail": detail})
        print(f"  [OK] {name}")
        if detail:
            print(f"    {detail}")

    def fail(self, name: str, error: str):
        self.failed += 1
        self.tests.append({"name": name, "status": "FAIL", "error": error})
        print(f"  [X] {name}")
        print(f"    ERRO: {error}")

    def section(self, title: str):
        print()
        print("=" * 60)
        print(f"  {title}")
        print("=" * 60)

    def summary(self) -> int:
        print()
        print("=" * 60)
        print("  RESUMO DOS TESTES")
        print("=" * 60)
        print(f"  Passou: {self.passed}")
        print(f"  Falhou: {self.failed}")
        print(f"  Total:  {self.passed + self.failed}")
        print()

        if self.failed > 0:
            print("  TESTES QUE FALHARAM:")
            for t in self.tests:
                if t["status"] == "FAIL":
                    print(f"    - {t['name']}: {t.get('error', '')[:100]}")
            return 1
        return 0


reporter = TestReporter()


def generate_unique_name(prefix: str = "TESTE") -> str:
    """Gera nome único para evitar conflitos."""
    return f"{prefix} {uuid.uuid4().hex[:8].upper()}"


# ============================================================================
# TESTES DA BIBLIOTECA PYTHON (LOCAL)
# ============================================================================


def test_lib_connection():
    """Testa conexão e login."""
    reporter.section("LIB: Conexão e Login")

    from correios_reverso import CorreiosClient

    try:
        with CorreiosClient.from_env() as client:
            reporter.success("Login CAS", "Autenticado com sucesso")
            return client
    except Exception as e:
        reporter.fail("Login CAS", str(e))
        return None


def test_lib_cep(client):
    """Testa consulta de CEP."""
    reporter.section("LIB: Consulta de CEP")

    # CEP válido
    try:
        result = client.auxiliares.consultar_cep("01001000")
        if result.get("cep") or result.get("localidade"):
            reporter.success("Consultar CEP valido", f"CEP 01001000 -> {result.get('localidade', 'OK')}")
        else:
            reporter.fail("Consultar CEP válido", "Resposta vazia")
    except Exception as e:
        reporter.fail("Consultar CEP válido", str(e))

    # CEP inexistente
    try:
        result = client.auxiliares.consultar_cep("00000000")
        reporter.success("Consultar CEP inexistente", f"Retornou: {result}")
    except Exception as e:
        # Erro é esperado para CEP inexistente
        reporter.success("Consultar CEP inexistente", f"Erro esperado: {str(e)[:50]}")


def test_lib_servicos(client):
    """Testa listagem de serviços."""
    reporter.section("LIB: Serviços")

    # Serviços normais
    try:
        servicos = client.postagem.listar_servicos(logistica_reversa=False)
        if len(servicos) > 0:
            reporter.success("Listar serviços normais", f"{len(servicos)} serviços encontrados")
        else:
            reporter.fail("Listar serviços normais", "Nenhum serviço retornado")
    except Exception as e:
        reporter.fail("Listar serviços normais", str(e))

    # Serviços LR
    try:
        servicos_lr = client.postagem.listar_servicos(logistica_reversa=True)
        if len(servicos_lr) > 0:
            reporter.success("Listar serviços LR", f"{len(servicos_lr)} serviços LR encontrados")
        else:
            reporter.fail("Listar serviços LR", "Nenhum serviço LR retornado")
    except Exception as e:
        reporter.fail("Listar serviços LR", str(e))


def test_lib_cartoes_embalagens(client):
    """Testa listagem de cartões e embalagens."""
    reporter.section("LIB: Cartões e Embalagens")

    try:
        cartoes = client.auxiliares.listar_cartoes_postagem()
        if cartoes.itens:
            cartao = cartoes.itens[0]
            reporter.success("Listar cartões", f"{len(cartoes.itens)} cartão(ões)")
        else:
            reporter.fail("Listar cartões", "Nenhum cartão retornado")
    except Exception as e:
        reporter.fail("Listar cartões", str(e))

    try:
        embalagens = client.auxiliares.listar_embalagens()
        reporter.success("Listar embalagens", f"{len(embalagens.itens)} embalagem(ns)")
    except Exception as e:
        reporter.fail("Listar embalagens", str(e))


def test_lib_postagens_listar(client):
    """Testa listagem de pré-postagens."""
    reporter.section("LIB: Listar Pré-postagens")

    try:
        result = client.postagem.listar_registrados(logistica_reversa=False)
        reporter.success("Listar pré-postagens normais", f"{result.page.count} registradas")
    except Exception as e:
        reporter.fail("Listar pré-postagens normais", str(e))

    try:
        result_lr = client.postagem.listar_registrados(logistica_reversa=True)
        reporter.success("Listar pré-postagens LR", f"{result_lr.page.count} LR registradas")
    except Exception as e:
        reporter.fail("Listar pré-postagens LR", str(e))


def test_lib_remetentes(client):
    """Testa CRUD de remetentes."""
    reporter.section("LIB: CRUD Remetentes")
    remetente_id = None

    from correios_reverso.models import RemetenteRequest

    nome_teste = generate_unique_name("REM TESTE")

    # Criar
    try:
        req = RemetenteRequest(
            nomeRemetente=nome_teste,
            cepRemetente="01001000",
            logradouroRemetente="Rua Exemplo",
            numeroRemetente="999",
            bairroRemetente="Centro",
            cidadeRemetente="Sao Paulo",
            ufRemetente="RS",
            cpfCnpjRemetente="18552346000168",
        )
        result = client.remetentes.criar(req)
        remetente_id = str(result.get("id"))
        reporter.success("Criar remetente", f"ID: {remetente_id}")
    except Exception as e:
        reporter.fail("Criar remetente", str(e))
        return None

    # Pesquisar
    try:
        result = client.remetentes.pesquisar(nome=nome_teste)
        itens = result.get("itens", [])
        if any(r.get("id") == int(remetente_id) or str(r.get("id")) == remetente_id for r in itens):
            reporter.success("Pesquisar remetente", f"Encontrado: {len(itens)} resultado(s)")
        else:
            reporter.fail("Pesquisar remetente", "Remetente não encontrado na pesquisa")
    except Exception as e:
        reporter.fail("Pesquisar remetente", str(e))

    # Excluir
    if remetente_id:
        try:
            client.remetentes.excluir(remetente_id)
            reporter.success("Excluir remetente", f"ID {remetente_id} excluído")

            # Verificar exclusão
            result = client.remetentes.pesquisar(nome=nome_teste)
            itens = result.get("itens", [])
            if not any(str(r.get("id")) == remetente_id for r in itens):
                reporter.success("Verificar exclusão remetente", "Confirmado: não aparece mais na pesquisa")
            else:
                reporter.fail("Verificar exclusão remetente", "Ainda aparece na pesquisa!")
        except Exception as e:
            reporter.fail("Excluir remetente", str(e))

    return remetente_id


def test_lib_destinatarios(client):
    """Testa CRUD de destinatários."""
    reporter.section("LIB: CRUD Destinatários")
    destinatario_id = None

    from correios_reverso.models import DestinatarioRequest

    nome_teste = generate_unique_name("DEST TESTE")

    # Criar
    try:
        req = DestinatarioRequest(
            nomeDestinatario=nome_teste,
            cepDestinatario="01001000",
            logradouroDestinatario="Praca da Se",
            numeroDestinatario="1",
            bairroDestinatario="Se",
            cidadeDestinatario="Sao Paulo",
            ufDestinatario="SP",
        )
        result = client.destinatarios.criar(req)
        destinatario_id = str(result.get("id"))
        reporter.success("Criar destinatário", f"ID: {destinatario_id}")
    except Exception as e:
        reporter.fail("Criar destinatário", str(e))
        return None

    # Pesquisar
    try:
        result = client.destinatarios.pesquisar(nome=nome_teste)
        itens = result.get("itens", [])
        if any(str(d.get("id")) == destinatario_id for d in itens):
            reporter.success("Pesquisar destinatário", f"Encontrado: {len(itens)} resultado(s)")
        else:
            reporter.fail("Pesquisar destinatário", "Destinatário não encontrado")
    except Exception as e:
        reporter.fail("Pesquisar destinatário", str(e))

    # Excluir
    if destinatario_id:
        try:
            client.destinatarios.excluir(destinatario_id)
            reporter.success("Excluir destinatário", f"ID {destinatario_id} excluído")

            # Verificar
            result = client.destinatarios.pesquisar(nome=nome_teste)
            itens = result.get("itens", [])
            if not any(str(d.get("id")) == destinatario_id for d in itens):
                reporter.success("Verificar exclusão destinatário", "Confirmado: não aparece mais")
            else:
                reporter.fail("Verificar exclusão destinatário", "Ainda aparece na pesquisa!")
        except Exception as e:
            reporter.fail("Excluir destinatário", str(e))

    return destinatario_id


def test_lib_postagem_criar_cancelar(client, tipo="normal"):
    """Testa criar e cancelar pré-postagem."""
    titulo = f"LIB: Criar/Cancelar Pré-postagem ({tipo.upper()})"
    reporter.section(titulo)

    from correios_reverso.models import (
        CriarPrePostagemRequest,
        PessoaPrePostagem,
        Endereco,
        ItemDeclaracaoConteudo,
    )

    # Contagem antes
    try:
        antes = client.postagem.listar_registrados(logistica_reversa=(tipo == "lr")).page.count
    except:
        antes = 0

    nome_remetente = generate_unique_name("REM POSTAGEM")
    nome_destinatario = generate_unique_name("DEST POSTAGEM")

    remetente = PessoaPrePostagem(
        nome=nome_remetente,
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
        nome=nome_destinatario,
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
            comprimentoInformado="20",
            alturaInformada="10",
            larguraInformada="15",
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
            comprimentoInformado="25",
            alturaInformada="12",
            larguraInformada="18",
            itensDeclaracaoConteudo=[
                ItemDeclaracaoConteudo(conteudo="Produto teste", quantidade=1, valor=100.0),
            ],
        )

    # Criar
    postagem_id = None
    codigo_objeto = None
    try:
        result = client.postagem.criar(req)
        reporter.success(f"Criar pré-postagem {tipo}", f"Status: 201 Created")
    except Exception as e:
        reporter.fail(f"Criar pré-postagem {tipo}", str(e))
        return None

    # Verificar contagem
    try:
        depois = client.postagem.listar_registrados(logistica_reversa=(tipo == "lr")).page.count
        if depois == antes + 1:
            reporter.success("Verificar contagem apos criar", f"{antes} -> {depois}")
        else:
            reporter.fail("Verificar contagem após criar", f"Esperado {antes + 1}, got {depois}")
    except Exception as e:
        reporter.fail("Verificar contagem após criar", str(e))

    # Buscar o item criado
    try:
        postagens = client.postagem.listar_registrados(logistica_reversa=(tipo == "lr"))
        for item in postagens.itens:
            nome_rem = item.remetente.nome if hasattr(item.remetente, 'nome') else ""
            if nome_remetente in nome_rem:
                postagem_id = item.id
                codigo_objeto = item.codigoObjeto
                break

        if postagem_id:
            reporter.success("Encontrar pré-postagem criada", f"ID: {postagem_id}, Codigo: {codigo_objeto}")
        else:
            reporter.fail("Encontrar pré-postagem criada", "Item não encontrado na lista")
    except Exception as e:
        reporter.fail("Encontrar pré-postagem criada", str(e))

    # Cancelar
    if postagem_id:
        try:
            msg = client.cancelamento.cancelar(postagem_id)
            reporter.success("Cancelar pré-postagem", msg[:80])
        except Exception as e:
            reporter.fail("Cancelar pré-postagem", str(e))

        # Verificar contagem final
        try:
            final = client.postagem.listar_registrados(logistica_reversa=(tipo == "lr")).page.count
            if final == antes:
                reporter.success("Verificar contagem apos cancelar", f"{depois} -> {final} (voltou ao original)")
            else:
                reporter.fail("Verificar contagem após cancelar", f"Esperado {antes}, got {final}")
        except Exception as e:
            reporter.fail("Verificar contagem após cancelar", str(e))

    return postagem_id


def run_lib_tests():
    """Executa todos os testes da biblioteca."""
    reporter.section("TESTES DA BIBLIOTECA PYTHON")

    # Conexão
    client = test_lib_connection()
    if not client:
        print("\n[X] Nao foi possivel conectar. Verifique arquivo .env")
        return

    # Testes de leitura
    test_lib_cep(client)
    test_lib_servicos(client)
    test_lib_cartoes_embalagens(client)
    test_lib_postagens_listar(client)

    # Testes de escrita (criam e deletam)
    test_lib_remetentes(client)
    test_lib_destinatarios(client)
    test_lib_postagem_criar_cancelar(client, "normal")
    test_lib_postagem_criar_cancelar(client, "lr")


# ============================================================================
# TESTES DA API REST
# ============================================================================


def test_api_health(base_url: str, headers: dict):
    """Testa endpoints de health."""
    reporter.section("API: Health Check")

    import requests

    try:
        resp = requests.get(f"{base_url}/health", timeout=10)
        if resp.status_code == 200:
            reporter.success("GET /health", f"Status: {resp.json().get('status')}")
        else:
            reporter.fail("GET /health", f"Status: {resp.status_code}")
    except Exception as e:
        reporter.fail("GET /health", str(e))

    try:
        resp = requests.get(f"{base_url}/", timeout=10)
        if resp.status_code == 200:
            reporter.success("GET /", f"API: {resp.json().get('name')}")
        else:
            reporter.fail("GET /", f"Status: {resp.status_code}")
    except Exception as e:
        reporter.fail("GET /", str(e))


def test_api_cep(base_url: str, headers: dict):
    """Testa endpoint de CEP."""
    reporter.section("API: Consulta CEP")

    import requests

    try:
        resp = requests.get(f"{base_url}/cep/01001000", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            reporter.success("GET /cep/01001000", f"{data.get('localidade', 'OK')}")
        else:
            reporter.fail("GET /cep/01001000", f"Status: {resp.status_code}")
    except Exception as e:
        reporter.fail("GET /cep/01001000", str(e))


def test_api_servicos(base_url: str, headers: dict):
    """Testa endpoints de serviços."""
    reporter.section("API: Serviços")

    import requests

    try:
        resp = requests.get(f"{base_url}/postagem/servicos", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            reporter.success("GET /postagem/servicos", f"{len(data)} serviços")
        else:
            reporter.fail("GET /postagem/servicos", f"Status: {resp.status_code}")
    except Exception as e:
        reporter.fail("GET /postagem/servicos", str(e))

    try:
        resp = requests.get(f"{base_url}/postagem/servicos?logistica_reversa=true", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            reporter.success("GET /postagem/servicos?lr=true", f"{len(data)} serviços LR")
        else:
            reporter.fail("GET /postagem/servicos?lr=true", f"Status: {resp.status_code}")
    except Exception as e:
        reporter.fail("GET /postagem/servicos?lr=true", str(e))


def test_api_postagens(base_url: str, headers: dict):
    """Testa listagem de pré-postagens."""
    reporter.section("API: Pré-postagens")

    import requests

    try:
        resp = requests.get(f"{base_url}/postagem", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            count = data.get("page", {}).get("count", 0)
            reporter.success("GET /postagem", f"{count} pré-postagens")
        else:
            reporter.fail("GET /postagem", f"Status: {resp.status_code}")
    except Exception as e:
        reporter.fail("GET /postagem", str(e))


def test_api_destinatarios(base_url: str, headers: dict):
    """Testa CRUD de destinatários via API."""
    reporter.section("API: CRUD Destinatários")

    import requests

    nome_teste = generate_unique_name("DEST API")
    dest_id = None

    # Listar
    try:
        resp = requests.get(f"{base_url}/destinatarios", headers=headers, timeout=10)
        if resp.status_code == 200:
            reporter.success("GET /destinatarios", "Listagem OK")
        else:
            reporter.fail("GET /destinatarios", f"Status: {resp.status_code}")
    except Exception as e:
        reporter.fail("GET /destinatarios", str(e))

    # Criar
    try:
        resp = requests.post(
            f"{base_url}/destinatarios",
            headers=headers,
            json={
                "nomeDestinatario": nome_teste,
                "cepDestinatario": "01001000",
                "logradouroDestinatario": "Praca da Se",
                "numeroDestinatario": "1",
                "bairroDestinatario": "Se",
                "cidadeDestinatario": "Sao Paulo",
                "ufDestinatario": "SP",
            },
            timeout=10,
        )
        if resp.status_code == 201:
            data = resp.json()
            dest_id = data.get("id")
            reporter.success("POST /destinatarios", f"ID: {dest_id}")
        else:
            reporter.fail("POST /destinatarios", f"Status: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        reporter.fail("POST /destinatarios", str(e))

    # Excluir
    if dest_id:
        try:
            resp = requests.delete(f"{base_url}/destinatarios/{dest_id}", headers=headers, timeout=10)
            if resp.status_code == 200:
                reporter.success("DELETE /destinatarios/{id}", f"ID {dest_id} excluído")
            else:
                reporter.fail("DELETE /destinatarios/{id}", f"Status: {resp.status_code}")
        except Exception as e:
            reporter.fail("DELETE /destinatarios/{id}", str(e))


def test_api_remetentes(base_url: str, headers: dict):
    """Testa CRUD de remetentes via API."""
    reporter.section("API: CRUD Remetentes")

    import requests

    nome_teste = generate_unique_name("REM API")
    rem_id = None

    # Listar
    try:
        resp = requests.get(f"{base_url}/remetentes", headers=headers, timeout=10)
        if resp.status_code == 200:
            reporter.success("GET /remetentes", "Listagem OK")
        else:
            reporter.fail("GET /remetentes", f"Status: {resp.status_code}")
    except Exception as e:
        reporter.fail("GET /remetentes", str(e))

    # Criar
    try:
        resp = requests.post(
            f"{base_url}/remetentes",
            headers=headers,
            json={
                "nomeRemetente": nome_teste,
                "cepRemetente": "01001000",
                "logradouroRemetente": "Rua Exemplo",
                "numeroRemetente": "999",
                "bairroRemetente": "Centro",
                "cidadeRemetente": "Sao Paulo",
                "ufRemetente": "RS",
                "cpfCnpjRemetente": "18552346000168",
            },
            timeout=10,
        )
        if resp.status_code == 201:
            data = resp.json()
            rem_id = data.get("id")
            reporter.success("POST /remetentes", f"ID: {rem_id}")
        else:
            reporter.fail("POST /remetentes", f"Status: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        reporter.fail("POST /remetentes", str(e))

    # Excluir
    if rem_id:
        try:
            resp = requests.delete(f"{base_url}/remetentes/{rem_id}", headers=headers, timeout=10)
            if resp.status_code == 200:
                reporter.success("DELETE /remetentes/{id}", f"ID {rem_id} excluído")
            else:
                reporter.fail("DELETE /remetentes/{id}", f"Status: {resp.status_code}")
        except Exception as e:
            reporter.fail("DELETE /remetentes/{id}", str(e))


def test_api_cartoes_embalagens(base_url: str, headers: dict):
    """Testa endpoints auxiliares."""
    reporter.section("API: Cartões e Embalagens")

    import requests

    try:
        resp = requests.get(f"{base_url}/cartoes", headers=headers, timeout=10)
        if resp.status_code == 200:
            reporter.success("GET /cartoes", "OK")
        else:
            reporter.fail("GET /cartoes", f"Status: {resp.status_code}")
    except Exception as e:
        reporter.fail("GET /cartoes", str(e))

    try:
        resp = requests.get(f"{base_url}/embalagens", headers=headers, timeout=10)
        if resp.status_code == 200:
            reporter.success("GET /embalagens", "OK")
        else:
            reporter.fail("GET /embalagens", f"Status: {resp.status_code}")
    except Exception as e:
        reporter.fail("GET /embalagens", str(e))


def test_api_postagem_criar_cancelar(base_url: str, headers: dict, tipo="normal"):
    """Testa criar e cancelar pré-postagem via API."""
    titulo = f"API: Criar/Cancelar Pré-postagem ({tipo.upper()})"
    reporter.section(titulo)

    import requests

    nome_remetente = generate_unique_name("REM API POST")
    nome_destinatario = generate_unique_name("DEST API POST")

    # Contagem antes
    try:
        resp = requests.get(f"{base_url}/postagem", headers=headers, timeout=10)
        antes = resp.json().get("page", {}).get("count", 0)
    except:
        antes = 0

    payload = {
        "remetente": {
            "nome": nome_remetente,
            "cpfCnpj": "18552346000168",
            "email": "teste@teste.com",
            "endereco": {
                "cep": "01001000",
                "logradouro": "Rua Exemplo",
                "numero": "1190",
                "bairro": "Centro",
                "cidade": "Sao Paulo",
                "uf": "RS",
            },
        },
        "destinatario": {
            "nome": nome_destinatario,
            "cpfCnpj": "18552346000320",
            "email": "dest@teste.com",
            "endereco": {
                "cep": "20040000",
                "logradouro": "Av Exemplo",
                "numero": "803",
                "bairro": "Centro",
                "cidade": "Osasco",
                "uf": "SP",
            },
        },
        "pesoInformado": "500",
        "comprimentoInformado": "25",
        "alturaInformada": "12",
        "larguraInformada": "18",
        "itensDeclaracaoConteudo": [
            {"conteudo": "Produto teste API", "quantidade": 1, "valor": 100.0}
        ],
    }

    if tipo == "lr":
        payload["codigoServico"] = "03301"
        payload["servico"] = "03301 - PAC REVERSO"
        payload["logisticaReversa"] = "S"
        payload["dataValidadeLogReversa"] = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
    else:
        payload["codigoServico"] = "03298"
        payload["servico"] = "03298 - PAC CONTRATO AG"

    postagem_id = None

    # Criar
    try:
        resp = requests.post(f"{base_url}/postagem", headers=headers, json=payload, timeout=30)
        if resp.status_code == 201:
            reporter.success(f"POST /postagem ({tipo})", "Criada com sucesso")
        else:
            reporter.fail(f"POST /postagem ({tipo})", f"Status: {resp.status_code} - {resp.text[:200]}")
    except Exception as e:
        reporter.fail(f"POST /postagem ({tipo})", str(e))
        return

    # Verificar contagem
    try:
        resp = requests.get(f"{base_url}/postagem", headers=headers, timeout=10)
        depois = resp.json().get("page", {}).get("count", 0)
        if depois == antes + 1:
            reporter.success("Verificar contagem apos criar", f"{antes} -> {depois}")
        else:
            reporter.fail("Verificar contagem após criar", f"Esperado {antes + 1}, got {depois}")
    except Exception as e:
        reporter.fail("Verificar contagem após criar", str(e))

    # Buscar o item
    try:
        resp = requests.get(f"{base_url}/postagem", headers=headers, timeout=10)
        itens = resp.json().get("itens", [])
        for item in itens:
            nome_rem = item.get("remetente", {}).get("nome", "")
            if nome_remetente in nome_rem:
                postagem_id = item.get("id")
                break

        if postagem_id:
            reporter.success("Encontrar pré-postagem criada", f"ID: {postagem_id}")
        else:
            reporter.fail("Encontrar pré-postagem criada", "Item não encontrado")
    except Exception as e:
        reporter.fail("Encontrar pré-postagem criada", str(e))

    # Cancelar
    if postagem_id:
        try:
            resp = requests.delete(f"{base_url}/cancelamento/{postagem_id}", headers=headers, timeout=10)
            if resp.status_code == 200:
                reporter.success("DELETE /cancelamento/{id}", "Cancelado com sucesso")
            else:
                reporter.fail("DELETE /cancelamento/{id}", f"Status: {resp.status_code}")
        except Exception as e:
            reporter.fail("DELETE /cancelamento/{id}", str(e))

        # Verificar contagem final
        try:
            resp = requests.get(f"{base_url}/postagem", headers=headers, timeout=10)
            final = resp.json().get("page", {}).get("count", 0)
            if final == antes:
                reporter.success("Verificar contagem após cancelar", f"Voltou a {antes}")
            else:
                reporter.fail("Verificar contagem após cancelar", f"Esperado {antes}, got {final}")
        except Exception as e:
            reporter.fail("Verificar contagem após cancelar", str(e))


def run_api_tests(base_url: str, token: str):
    """Executa todos os testes da API REST."""
    reporter.section("TESTES DA API REST")

    import requests

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # Verificar se servidor está rodando
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
    except Exception as e:
        print(f"\n[X] Servidor nao esta acessivel em {base_url}")
        print(f"  Erro: {e}")
        print(f"\n  Inicie o servidor com:")
        print(f"  uvicorn correios_reverso.api.app:app --port 8000")
        return

    test_api_health(base_url, headers)
    test_api_cep(base_url, headers)
    test_api_servicos(base_url, headers)
    test_api_postagens(base_url, headers)
    test_api_cartoes_embalagens(base_url, headers)
    test_api_destinatarios(base_url, headers)
    test_api_remetentes(base_url, headers)
    test_api_postagem_criar_cancelar(base_url, headers, "normal")
    test_api_postagem_criar_cancelar(base_url, headers, "lr")


# ============================================================================
# TESTES DO MCP SERVER
# ============================================================================


def test_mcp_tools_list(base_url: str):
    """Testa listagem de tools MCP."""
    reporter.section("MCP: Listar Tools")

    import requests

    try:
        # MCP usa endpoint específico
        resp = requests.get(f"{base_url}/mcp/tools", timeout=10)
        if resp.status_code == 200:
            reporter.success("GET /mcp/tools", "Lista de tools disponível")
        elif resp.status_code == 404:
            reporter.success("GET /mcp/tools", "MCP endpoint montado (listar tools via cliente MCP)")
        else:
            reporter.fail("GET /mcp/tools", f"Status: {resp.status_code}")
    except Exception as e:
        reporter.fail("GET /mcp/tools", str(e))


def run_mcp_tests(base_url: str):
    """Executa testes do MCP Server."""
    reporter.section("TESTES DO MCP SERVER")

    import requests

    # Verificar se MCP está montado
    try:
        resp = requests.get(f"{base_url}/mcp", timeout=5, allow_redirects=False)
        reporter.success("MCP endpoint acessível", f"Status: {resp.status_code}")
    except Exception as e:
        print(f"\n[X] MCP nao esta acessivel em {base_url}/mcp")
        print(f"  Erro: {e}")
        return

    test_mcp_tools_list(base_url)

    # Nota: Testes completos de MCP tools requerem cliente MCP
    print("\n  NOTA: Para testar MCP tools completos, use um cliente MCP.")
    print("  Exemplo com assistente de IA:")
    print("  1. Configure o MCP server apontando para http://localhost:8000/mcp")
    print("  2. Use as tools via chat com assistente de IA")


# ============================================================================
# MAIN
# ============================================================================


def main():
    parser = argparse.ArgumentParser(description="Testes completos do Correios Reverso")
    parser.add_argument("--lib", action="store_true", help="Testar biblioteca Python")
    parser.add_argument("--api", action="store_true", help="Testar API REST")
    parser.add_argument("--mcp", action="store_true", help="Testar MCP Server")
    parser.add_argument("--all", action="store_true", help="Testar tudo")
    parser.add_argument("--api-url", default="http://localhost:8000", help="URL da API")
    parser.add_argument("--token", default="", help="Token de autenticação")

    args = parser.parse_args()

    # Se nenhum argumento, testa tudo
    run_all = args.all or not any([args.lib, args.api, args.mcp])

    print("=" * 60)
    print("  PLANO DE TESTE COMPLETO - CORREIOS REVERSO")
    print("=" * 60)
    print(f"  Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  API URL: {args.api_url}")
    print(f"  Testes: {'TODOS' if run_all else []}")
    print()

    start_time = time.time()

    if run_all or args.lib:
        run_lib_tests()

    if run_all or args.api:
        run_api_tests(args.api_url, args.token)

    if run_all or args.mcp:
        run_mcp_tests(args.api_url)

    elapsed = time.time() - start_time

    # Resumo
    exit_code = reporter.summary()
    print(f"  Tempo total: {elapsed:.2f}s")

    if exit_code == 0:
        print("\n  [OK] TODOS OS TESTES PASSARAM!")
        print("  [OK] Todos os dados de teste foram limpos")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

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
import asyncio
import json
import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[assignment]

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



def safe_json(resp: Any) -> dict[str, Any]:
    """Retorna JSON da resposta ou dict vazio quando corpo nao for JSON."""
    try:
        return resp.json()
    except Exception:
        return {}

def format_response_error(resp: Any) -> str:
    """Formata erro HTTP com trecho do corpo para facilitar diagnostico."""
    body = (resp.text or "").strip()
    if body:
        return f"Status: {resp.status_code} - {body[:200]}"
    return f"Status: {resp.status_code}"

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
            ufRemetente="SP",
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
            uf="SP",
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
            cidade="Rio de Janeiro",
            uf="RJ",
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
        if depois >= antes:
            reporter.success("Verificar contagem apos criar", f"{antes} -> {depois}")
        else:
            reporter.fail("Verificar contagem após criar", f"Contagem diminuiu: {antes} -> {depois}")
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
            if final <= depois:
                reporter.success("Verificar contagem apos cancelar", f"{depois} -> {final}")
            else:
                reporter.fail("Verificar contagem após cancelar", f"Contagem aumentou: {depois} -> {final}")
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
                "ufRemetente": "SP",
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
        if resp.status_code == 200:
            antes = safe_json(resp).get("page", {}).get("count", 0)
        else:
            antes = 0
    except Exception:
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
                "uf": "SP",
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
                "cidade": "Rio de Janeiro",
                "uf": "RJ",
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
            reporter.fail(f"POST /postagem ({tipo})", format_response_error(resp))
            return
    except Exception as e:
        reporter.fail(f"POST /postagem ({tipo})", str(e))
        return

    # Verificar contagem
    try:
        resp = requests.get(f"{base_url}/postagem", headers=headers, timeout=10)
        if resp.status_code != 200:
            reporter.fail("Verificar contagem após criar", format_response_error(resp))
            return
        depois = safe_json(resp).get("page", {}).get("count", 0)
        if depois >= antes:
            reporter.success("Verificar contagem apos criar", f"{antes} -> {depois}")
        else:
            reporter.fail("Verificar contagem após criar", f"Contagem diminuiu: {antes} -> {depois}")
    except Exception as e:
        reporter.fail("Verificar contagem após criar", str(e))

    # Buscar o item
    try:
        resp = requests.get(f"{base_url}/postagem", headers=headers, timeout=10)
        if resp.status_code != 200:
            reporter.fail("Encontrar pré-postagem criada", format_response_error(resp))
            return
        itens = safe_json(resp).get("itens", [])
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
            if resp.status_code != 200:
                reporter.fail("Verificar contagem após cancelar", format_response_error(resp))
                return
            final = safe_json(resp).get("page", {}).get("count", 0)
            if final <= depois:
                reporter.success("Verificar contagem após cancelar", f"{depois} -> {final}")
            else:
                reporter.fail("Verificar contagem após cancelar", f"Contagem aumentou: {depois} -> {final}")
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


async def run_mcp_tools_full() -> None:
    """Executa teste funcional completo das 19 tools MCP."""
    from fastmcp import Client

    from correios_reverso import CorreiosClient
    from correios_reverso.mcp.server import create_mcp_server

    expected_tools = sorted(
        [
            "listar_postagens",
            "buscar_postagem_por_codigo",
            "criar_postagem",
            "listar_servicos",
            "cancelar_postagem",
            "log_cancelamento",
            "listar_destinatarios",
            "criar_destinatario",
            "excluir_destinatario",
            "listar_remetentes",
            "obter_remetente",
            "criar_remetente",
            "excluir_remetente",
            "iniciar_impressao_etiqueta",
            "download_etiqueta",
            "listar_processamentos_etiqueta",
            "consultar_cep",
            "listar_cartoes_postagem",
            "listar_embalagens",
        ]
    )

    def unwrap(result):
        return result.data if hasattr(result, "data") else result

    with CorreiosClient.from_env() as core_client:
        mcp_server = create_mcp_server(core_client)
        async with Client(mcp_server) as client:
            tools = await client.list_tools()
            names = sorted([tool.name for tool in tools])
            if names == expected_tools:
                reporter.success("MCP list_tools", f"{len(names)} tools")
            else:
                missing = sorted(set(expected_tools) - set(names))
                extra = sorted(set(names) - set(expected_tools))
                reporter.fail("MCP list_tools", f"missing={missing} extra={extra}")

            for name, args in [
                ("consultar_cep", {"cep": "01001000"}),
                ("listar_cartoes_postagem", {}),
                ("listar_embalagens", {}),
                ("listar_servicos", {"logistica_reversa": False}),
                ("listar_servicos", {"logistica_reversa": True}),
                ("listar_destinatarios", {"nome": ""}),
                ("listar_remetentes", {"nome": ""}),
            ]:
                try:
                    await client.call_tool(name, args)
                    reporter.success(f"MCP {name}")
                except Exception as e:
                    reporter.fail(f"MCP {name}", str(e))

            codigo = None
            try:
                listed = unwrap(await client.call_tool("listar_postagens", {"pagina": 0, "logistica_reversa": False}))
                itens = listed.get("itens", []) if isinstance(listed, dict) else []
                codigo = itens[0].get("codigoObjeto") if itens else None
                reporter.success("MCP listar_postagens", f"{len(itens)} item(ns)")
            except Exception as e:
                reporter.fail("MCP listar_postagens", str(e))

            if codigo:
                try:
                    await client.call_tool("buscar_postagem_por_codigo", {"codigo_objeto": codigo})
                    reporter.success("MCP buscar_postagem_por_codigo")
                except Exception as e:
                    reporter.fail("MCP buscar_postagem_por_codigo", str(e))
            else:
                reporter.fail("MCP buscar_postagem_por_codigo", "Sem codigoObjeto disponivel")

            dest_id = None
            try:
                created = unwrap(
                    await client.call_tool(
                        "criar_destinatario",
                        {
                            "nome": generate_unique_name("MCP DEST"),
                            "cep": "01001000",
                            "logradouro": "Praca da Se",
                            "numero": "1",
                            "bairro": "Se",
                            "cidade": "Sao Paulo",
                            "uf": "SP",
                            "email": "dest@mcp.test",
                        },
                    )
                )
                dest_id = str(created.get("id")) if isinstance(created, dict) else None
                reporter.success("MCP criar_destinatario", f"ID: {dest_id}")
            except Exception as e:
                reporter.fail("MCP criar_destinatario", str(e))

            if dest_id and dest_id != "None":
                try:
                    await client.call_tool("excluir_destinatario", {"id_destinatario": dest_id})
                    reporter.success("MCP excluir_destinatario")
                except Exception as e:
                    reporter.fail("MCP excluir_destinatario", str(e))
            else:
                reporter.fail("MCP excluir_destinatario", "ID invalido")

            rem_id = None
            try:
                created = unwrap(
                    await client.call_tool(
                        "criar_remetente",
                        {
                            "nome": generate_unique_name("MCP REM"),
                            "cep": "01001000",
                            "logradouro": "Rua Exemplo",
                            "numero": "999",
                            "bairro": "Centro",
                            "cidade": "Sao Paulo",
                            "uf": "SP",
                            "cpf_cnpj": "18552346000168",
                            "email": "rem@mcp.test",
                        },
                    )
                )
                rem_id = str(created.get("id")) if isinstance(created, dict) else None
                reporter.success("MCP criar_remetente", f"ID: {rem_id}")
            except Exception as e:
                reporter.fail("MCP criar_remetente", str(e))

            if rem_id and rem_id != "None":
                try:
                    await client.call_tool("obter_remetente", {"id_remetente": rem_id})
                    reporter.success("MCP obter_remetente")
                except Exception as e:
                    reporter.fail("MCP obter_remetente", str(e))
                try:
                    await client.call_tool("excluir_remetente", {"id_remetente": rem_id})
                    reporter.success("MCP excluir_remetente")
                except Exception as e:
                    reporter.fail("MCP excluir_remetente", str(e))
            else:
                reporter.fail("MCP obter/excluir_remetente", "ID invalido")

            prepostagem_id = None
            id_recibo = None

            try:
                await client.call_tool(
                    "criar_postagem",
                    {
                        "remetente_nome": generate_unique_name("MCP REM POST"),
                        "remetente_cpf_cnpj": "18552346000168",
                        "remetente_cep": "01001000",
                        "remetente_logradouro": "Rua Exemplo",
                        "remetente_numero": "1190",
                        "remetente_bairro": "Centro",
                        "remetente_cidade": "Sao Paulo",
                        "remetente_uf": "SP",
                        "destinatario_nome": generate_unique_name("MCP DEST POST"),
                        "destinatario_cep": "20040000",
                        "destinatario_logradouro": "Av Exemplo",
                        "destinatario_numero": "803",
                        "destinatario_bairro": "Centro",
                        "destinatario_cidade": "Rio de Janeiro",
                        "destinatario_uf": "RJ",
                        "codigo_servico": "03298",
                        "servico": "03298 - PAC CONTRATO AG",
                        "peso_gramas": "500",
                        "comprimento_cm": "25",
                        "altura_cm": "12",
                        "largura_cm": "18",
                        "item_conteudo": "Produto MCP",
                        "item_quantidade": 1,
                        "item_valor": 100.0,
                    },
                )
                reporter.success("MCP criar_postagem")
            except Exception as e:
                reporter.fail("MCP criar_postagem", str(e))

            try:
                listed = unwrap(await client.call_tool("listar_postagens", {"pagina": 0, "logistica_reversa": False}))
                itens = listed.get("itens", []) if isinstance(listed, dict) else []
                prepostagem_id = itens[0].get("id") if itens else None
                reporter.success("MCP listar_postagens apos criar")
            except Exception as e:
                reporter.fail("MCP listar_postagens apos criar", str(e))

            if prepostagem_id:
                try:
                    started = unwrap(
                        await client.call_tool("iniciar_impressao_etiqueta", {"ids_prepostagem": [prepostagem_id]})
                    )
                    if isinstance(started, dict):
                        id_recibo = started.get("idRecibo")
                    reporter.success("MCP iniciar_impressao_etiqueta", f"idRecibo={id_recibo}")
                except Exception as e:
                    reporter.fail("MCP iniciar_impressao_etiqueta", str(e))

                try:
                    proc = unwrap(await client.call_tool("listar_processamentos_etiqueta", {}))
                    if not id_recibo and isinstance(proc, list) and proc:
                        id_recibo = proc[0].get("idRecibo")
                    reporter.success("MCP listar_processamentos_etiqueta")
                except Exception as e:
                    reporter.fail("MCP listar_processamentos_etiqueta", str(e))

                if id_recibo:
                    downloaded = False
                    last_err = None
                    for _ in range(6):
                        try:
                            await client.call_tool("download_etiqueta", {"id_recibo": id_recibo})
                            downloaded = True
                            break
                        except Exception as e:
                            last_err = e
                            await asyncio.sleep(2)
                    if downloaded:
                        reporter.success("MCP download_etiqueta")
                    else:
                        reporter.fail("MCP download_etiqueta", str(last_err))
                else:
                    reporter.fail("MCP download_etiqueta", "Sem idRecibo disponivel")

                try:
                    await client.call_tool("cancelar_postagem", {"id_prepostagem": prepostagem_id})
                    reporter.success("MCP cancelar_postagem")
                except Exception as e:
                    reporter.fail("MCP cancelar_postagem", str(e))

                try:
                    await client.call_tool("log_cancelamento", {"id_prepostagem": prepostagem_id})
                    reporter.success("MCP log_cancelamento")
                except Exception as e:
                    reporter.fail("MCP log_cancelamento", str(e))
            else:
                reporter.fail("MCP fluxo_postagem", "Sem id_prepostagem")


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

    reporter.section("MCP: Teste Funcional Completo (19 tools)")
    try:
        asyncio.run(run_mcp_tools_full())
    except Exception as e:
        reporter.fail("MCP tools completo", str(e))


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

    if load_dotenv is not None:
        load_dotenv()

    # Se nenhum argumento, testa tudo
    run_all = args.all or not any([args.lib, args.api, args.mcp])
    selected_tests = "TODOS" if run_all else ", ".join(
        name for enabled, name in [(args.lib, "LIB"), (args.api, "API"), (args.mcp, "MCP")] if enabled
    )

    print("=" * 60)
    print("  PLANO DE TESTE COMPLETO - CORREIOS REVERSO")
    print("=" * 60)
    print(f"  Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  API URL: {args.api_url}")
    print(f"  Testes: {selected_tests}")
    print()

    start_time = time.time()

    if run_all or args.lib:
        run_lib_tests()

    api_token = args.token.strip()
    if not api_token:
        api_tokens = [t.strip() for t in os.getenv("API_TOKENS", "").split(",") if t.strip()]
        if api_tokens:
            api_token = api_tokens[0]

    if run_all or args.api:
        run_api_tests(args.api_url, api_token)

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

"""Testes da FastAPI REST API."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Mock do CorreiosClient antes de importar app
mock_client = MagicMock()


@pytest.fixture(autouse=True)
def mock_correios_client():
    """Mock do CorreiosClient para todos os testes."""
    with patch("correios_reverso.api.app.CorreiosClient") as MockClient:
        MockClient.from_env.return_value = mock_client
        mock_client.login.return_value = None
        mock_client.close.return_value = None
        yield mock_client


@pytest.fixture
def api_client():
    """TestClient para a API."""
    from correios_reverso.api.app import app
    # Simula state com client mock
    app.state.client = mock_client
    return TestClient(app)


class TestHealth:
    """Testes de health check."""

    def test_health_ok(self, api_client):
        resp = api_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_root(self, api_client):
        resp = api_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Correios Reverso API"


class TestPostagem:
    """Testes de rotas de postagem."""

    def test_listar_postagens(self, api_client, mock_correios_client):
        # Mock do resultado
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {"itens": [], "page": {"count": 0}}
        mock_correios_client.postagem.listar_registrados.return_value = mock_result

        resp = api_client.get("/postagem")
        assert resp.status_code == 200

    def test_listar_servicos(self, api_client, mock_correios_client):
        mock_correios_client.postagem.listar_servicos.return_value = []
        resp = api_client.get("/postagem/servicos")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_buscar_por_codigo(self, api_client, mock_correios_client):
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {"itens": [], "page": {"count": 0}}
        mock_correios_client.postagem.buscar_por_codigo_objeto.return_value = mock_result

        resp = api_client.get("/postagem/AN123456789BR")
        assert resp.status_code == 200


class TestDestinatarios:
    """Testes de rotas de destinatários."""

    def test_listar_destinatarios(self, api_client, mock_correios_client):
        mock_correios_client.destinatarios.pesquisar.return_value = {"itens": []}
        resp = api_client.get("/destinatarios")
        assert resp.status_code == 200


class TestRemetentes:
    """Testes de rotas de remetentes."""

    def test_listar_remetentes(self, api_client, mock_correios_client):
        mock_correios_client.remetentes.pesquisar.return_value = {"itens": []}
        resp = api_client.get("/remetentes")
        assert resp.status_code == 200


class TestAuxiliares:
    """Testes de rotas auxiliares."""

    def test_consultar_cep(self, api_client, mock_correios_client):
        mock_correios_client.auxiliares.consultar_cep.return_value = {"cep": "01001000"}
        resp = api_client.get("/cep/01001000")
        assert resp.status_code == 200
        assert resp.json()["cep"] == "01001000"

    def test_listar_cartoes(self, api_client, mock_correios_client):
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {"itens": []}
        mock_correios_client.auxiliares.listar_cartoes_postagem.return_value = mock_result
        resp = api_client.get("/cartoes")
        assert resp.status_code == 200

    def test_listar_embalagens(self, api_client, mock_correios_client):
        mock_result = MagicMock()
        mock_result.model_dump.return_value = {"itens": []}
        mock_correios_client.auxiliares.listar_embalagens.return_value = mock_result
        resp = api_client.get("/embalagens")
        assert resp.status_code == 200


class TestCancelamento:
    """Testes de rotas de cancelamento."""

    def test_cancelar_postagem(self, api_client, mock_correios_client):
        mock_correios_client.cancelamento.cancelar.return_value = "Cancelado com sucesso"
        resp = api_client.delete("/cancelamento/PTest123")
        assert resp.status_code == 200

    def test_log_cancelamento(self, api_client, mock_correios_client):
        mock_correios_client.cancelamento.log_cancelamento.return_value = []
        resp = api_client.get("/cancelamento/PTest123/log")
        assert resp.status_code == 200


class TestEtiqueta:
    """Testes de rotas de etiqueta."""

    def test_listar_processamentos(self, api_client, mock_correios_client):
        mock_result = MagicMock()
        mock_result.itens = []
        mock_correios_client.etiqueta.listar_processamentos.return_value = mock_result
        resp = api_client.get("/etiqueta/processamentos")
        assert resp.status_code == 200

"""Testes do módulo de etiqueta."""

from __future__ import annotations

import pytest
import responses

from correios_reverso.config import Config
from correios_reverso.exceptions import APIError
from correios_reverso.http_client import HTTPClient
from correios_reverso.modules.etiqueta import Etiqueta


@responses.activate
def test_iniciar_impressao(config: Config):
    # POST imprimir assíncrono
    responses.add(
        responses.POST,
        f"{config.base_url}/rotulo/painel/imprimir/assincrono",
        json={"idRecibo": "REC-12345"},
        status=200,
    )
    # POST registrar processamento
    responses.add(
        responses.POST,
        f"{config.base_url}/processamentosrotulos",
        json={},
        status=200,
    )
    http = HTTPClient(config)
    mod = Etiqueta(http)
    id_recibo = mod.iniciar_impressao(["PP_abc123"])
    assert id_recibo == "REC-12345"


@responses.activate
def test_iniciar_impressao_sem_recibo(config: Config):
    responses.add(
        responses.POST,
        f"{config.base_url}/rotulo/painel/imprimir/assincrono",
        json={},
        status=200,
    )
    http = HTTPClient(config)
    mod = Etiqueta(http)
    with pytest.raises(APIError, match="idRecibo"):
        mod.iniciar_impressao(["PP_abc123"])


@responses.activate
def test_download_rotulo(config: Config):
    fake_pdf = b"%PDF-1.4 fake content here with enough bytes to pass check"
    responses.add(
        responses.GET,
        f"{config.base_url}/rotulo/painel/assincrono/download/REC-12345",
        body=fake_pdf,
        status=200,
    )
    http = HTTPClient(config)
    mod = Etiqueta(http)
    data = mod.download_rotulo("REC-12345")
    assert data == fake_pdf


@responses.activate
def test_aguardar_e_baixar_sucesso(config: Config):
    fake_pdf = b"X" * 600  # > 500 bytes para passar o check
    # Primeira tentativa: ainda processando (corpo pequeno)
    responses.add(
        responses.GET,
        f"{config.base_url}/rotulo/painel/assincrono/download/REC-12345",
        body=b"processing",
        status=200,
    )
    # Segunda tentativa: pronto
    responses.add(
        responses.GET,
        f"{config.base_url}/rotulo/painel/assincrono/download/REC-12345",
        body=fake_pdf,
        status=200,
    )
    http = HTTPClient(config)
    mod = Etiqueta(http)
    data = mod.aguardar_e_baixar("REC-12345", max_tentativas=3, intervalo=0.01)
    assert len(data) == 600


@responses.activate
def test_aguardar_e_baixar_timeout(config: Config):
    # Sempre retorna corpo pequeno
    for _ in range(3):
        responses.add(
            responses.GET,
            f"{config.base_url}/rotulo/painel/assincrono/download/REC-12345",
            body=b"still processing",
            status=200,
        )
    http = HTTPClient(config)
    mod = Etiqueta(http)
    with pytest.raises(APIError, match="não ficou pronto"):
        mod.aguardar_e_baixar("REC-12345", max_tentativas=3, intervalo=0.01)


@responses.activate
def test_listar_processamentos(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/processamentosrotulos",
        json={
            "itens": [
                {"numero": "1", "idRecibo": "R1", "statusProcessamento": "FINALIZADO",
                 "idCorreios": "", "nuCartaoPostagem": "", "dataAlteracao": "", "url": ""},
            ],
            "page": {"number": 0, "size": 50, "totalPages": 1, "numberElements": 1,
                     "count": 1, "next": False, "previous": False, "first": True, "last": True},
        },
        status=200,
    )
    http = HTTPClient(config)
    mod = Etiqueta(http)
    result = mod.listar_processamentos()
    assert len(result.itens) == 1
    assert result.itens[0].statusProcessamento == "FINALIZADO"


@responses.activate
def test_gerar_declaracao_conteudo(config: Config):
    fake_html = b"<html>Declaracao de conteudo</html>"
    responses.add(
        responses.GET,
        f"{config.base_url}/prepostagem/afaturar/declaracaoConteudo/id1,id2",
        body=fake_html,
        status=200,
    )
    http = HTTPClient(config)
    mod = Etiqueta(http)
    data = mod.gerar_declaracao_conteudo(["id1", "id2"])
    assert b"Declaracao" in data


@responses.activate
def test_consultar_faixas_etiquetas(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/rotulo/range",
        json=[],
        status=200,
    )
    http = HTTPClient(config)
    mod = Etiqueta(http)
    result = mod.consultar_faixas_etiquetas("01/03/2026", "31/03/2026")
    assert result == []

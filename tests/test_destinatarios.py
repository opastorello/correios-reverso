"""Testes do módulo de destinatários."""

from __future__ import annotations

import responses

from correios_reverso.config import Config
from correios_reverso.http_client import HTTPClient
from correios_reverso.models import DestinatarioRequest
from correios_reverso.modules.destinatarios import Destinatarios


@responses.activate
def test_criar_destinatario(config: Config):
    responses.add(
        responses.POST,
        f"{config.base_url}/destinatarios/salvarSemCPF",
        json={"id": "81661317", "nomeDestinatario": "TESTE"},
        status=200,
    )
    http = HTTPClient(config)
    mod = Destinatarios(http)
    result = mod.criar(DestinatarioRequest(
        nomeDestinatario="TESTE",
        cepDestinatario="01001000",
        logradouroDestinatario="Rua Exemplo",
        numeroDestinatario="1190",
        bairroDestinatario="Centro",
        cidadeDestinatario="Sao Paulo",
        ufDestinatario="RS",
    ))
    assert result["id"] == "81661317"


@responses.activate
def test_pesquisar_destinatario(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/destinatarios/pesquisa",
        json={"itens": [{"id": "1", "nome": "TESTE"}], "page": {"number": 0}},
        status=200,
    )
    http = HTTPClient(config)
    mod = Destinatarios(http)
    result = mod.pesquisar(nome="TESTE")
    assert len(result["itens"]) == 1


@responses.activate
def test_excluir_destinatario(config: Config):
    responses.add(
        responses.DELETE,
        f"{config.base_url}/destinatarios/12345",
        status=200,
    )
    http = HTTPClient(config)
    mod = Destinatarios(http)
    mod.excluir("12345")  # não levanta exceção = sucesso

"""Testes do módulo de remetentes."""

from __future__ import annotations

import responses


from correios_reverso.config import Config
from correios_reverso.http_client import HTTPClient
from correios_reverso.models import RemetenteRequest
from correios_reverso.modules.remetentes import Remetentes


@responses.activate
def test_criar_remetente(config: Config):
    responses.add(
        responses.POST,
        f"{config.base_url}/remetentes",
        json={"id": "81661979", "nomeRemetente": "TESTE API"},
        status=200,
    )
    http = HTTPClient(config)
    mod = Remetentes(http)
    result = mod.criar(RemetenteRequest(
        nomeRemetente="TESTE API",
        cepRemetente="95703344",
        logradouroRemetente="Rua Marcos Nardon",
        numeroRemetente="69",
        bairroRemetente="Fenavinho",
        cidadeRemetente="Sao Paulo",
        ufRemetente="RS",
        cpfCnpjRemetente="11144477735",
    ))
    assert result["id"] == "81661979"


@responses.activate
def test_pesquisar_remetente(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/remetentes/pesquisa",
        json={"itens": [{"id": "1", "nome": "REM TESTE"}], "page": {"number": 0}},
        status=200,
    )
    http = HTTPClient(config)
    mod = Remetentes(http)
    result = mod.pesquisar(nome="REM")
    assert len(result["itens"]) == 1
    assert result["itens"][0]["nome"] == "REM TESTE"


@responses.activate
def test_obter_remetente(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/remetentes/81661979",
        json={"itens": [{"id": "81661979", "nome": "REM TESTE"}]},
        status=200,
    )
    http = HTTPClient(config)
    mod = Remetentes(http)
    result = mod.obter("81661979")
    assert result["itens"][0]["id"] == "81661979"


@responses.activate
def test_editar_remetente(config: Config):
    responses.add(
        responses.PUT,
        f"{config.base_url}/remetentes/81661979",
        status=200,
    )
    http = HTTPClient(config)
    mod = Remetentes(http)
    mod.editar("81661979", RemetenteRequest(
        nomeRemetente="EDITADO",
        cepRemetente="95703344",
        logradouroRemetente="Rua Marcos Nardon",
        numeroRemetente="69",
        bairroRemetente="Fenavinho",
        cidadeRemetente="Sao Paulo",
        ufRemetente="RS",
        cpfCnpjRemetente="11144477735",
    ))


@responses.activate
def test_excluir_remetente(config: Config):
    responses.add(
        responses.DELETE,
        f"{config.base_url}/remetentes/81661979",
        status=200,
    )
    http = HTTPClient(config)
    mod = Remetentes(http)
    mod.excluir("81661979")

"""Testes do módulo auxiliares."""

from __future__ import annotations

import responses

from correios_reverso.config import Config
from correios_reverso.http_client import HTTPClient
from correios_reverso.modules.auxiliares import Auxiliares


@responses.activate
def test_consultar_cep(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/auxiliares/cep/01001000",
        json={"logradouro": "Rua Exemplo", "bairro": "Centro", "cidade": "Sao Paulo", "uf": "RS"},
        status=200,
    )
    http = HTTPClient(config)
    mod = Auxiliares(http)
    result = mod.consultar_cep("01001000")
    assert result["cidade"] == "Sao Paulo"


@responses.activate
def test_listar_cartoes_postagem(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/cartoespostagensclientes",
        json={
            "itens": [
                {"numeroCartao": "0070996598", "validade": "2027-12-31", "status": "ATIVO",
                 "descricaoStatus": "Ativo", "contrato": "9912345678", "drContrato": 10,
                 "cnpj": "12345678000199", "ativo": True},
            ],
            "page": {"number": 0, "size": 50000, "totalPages": 1, "numberElements": 1,
                     "count": 1, "next": False, "previous": False, "first": True, "last": True},
        },
        status=200,
    )
    http = HTTPClient(config)
    mod = Auxiliares(http)
    result = mod.listar_cartoes_postagem()
    assert len(result.itens) == 1
    assert result.itens[0].numeroCartao == "0070996598"
    assert result.itens[0].ativo is True


@responses.activate
def test_listar_embalagens(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/embalagens",
        json={
            "itens": [
                {"id": 1, "numeroContrato": "9912345678", "drContrato": 10,
                 "descricao": "Caixa P", "formatoObjeto": 1,
                 "altura": 10.0, "largura": 15.0, "comprimento": 20.0,
                 "diametro": 0.0, "peso": 0.3},
            ],
            "page": {"number": 0, "size": 50, "totalPages": 1, "numberElements": 1,
                     "count": 1, "next": False, "previous": False, "first": True, "last": True},
        },
        status=200,
    )
    http = HTTPClient(config)
    mod = Auxiliares(http)
    result = mod.listar_embalagens()
    assert len(result.itens) == 1
    assert result.itens[0].descricao == "Caixa P"

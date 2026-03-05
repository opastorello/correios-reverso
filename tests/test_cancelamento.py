"""Testes do módulo de cancelamento."""

from __future__ import annotations

import pytest
import responses

from correios_reverso.config import Config
from correios_reverso.exceptions import APIError
from correios_reverso.http_client import HTTPClient
from correios_reverso.modules.cancelamento import Cancelamento


@responses.activate
def test_cancelar_sucesso(config: Config):
    responses.add(
        responses.DELETE,
        f"{config.base_url}/prepostagem/afaturar/abc123",
        body="Cancelado com sucesso",
        status=200,
    )
    http = HTTPClient(config)
    mod = Cancelamento(http)
    result = mod.cancelar("abc123")
    assert "Cancelado" in result


@responses.activate
def test_cancelar_erro(config: Config):
    responses.add(
        responses.DELETE,
        f"{config.base_url}/prepostagem/afaturar/abc123",
        json={"mensagem": "Pré-postagem não pode ser cancelada"},
        status=400,
    )
    http = HTTPClient(config)
    mod = Cancelamento(http)
    with pytest.raises(APIError):
        mod.cancelar("abc123")


@responses.activate
def test_log_cancelamento(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/prepostagem/v1/log/cancelamento",
        json=[],
        status=200,
    )
    http = HTTPClient(config)
    mod = Cancelamento(http)
    result = mod.log_cancelamento("abc123")
    assert result == []

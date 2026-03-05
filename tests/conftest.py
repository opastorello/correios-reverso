"""Fixtures compartilhadas para pytest."""

from __future__ import annotations

import pytest
import responses

from correios_reverso.config import Config
from correios_reverso.http_client import HTTPClient


@pytest.fixture
def config() -> Config:
    return Config(
        base_url="https://prepostagem.correios.com.br",
        cas_url="https://cas.correios.com.br",
        username="test_user",
        password="test_pass",
        timeout=5,
        verify_ssl=False,
        retry_attempts=1,
        retry_backoff=0.01,
    )


@pytest.fixture
def http(config: Config) -> HTTPClient:
    return HTTPClient(config)


@pytest.fixture
def mocked_responses():
    """Ativa o mock de responses para bloquear chamadas HTTP reais."""
    with responses.RequestsMock() as rsps:
        yield rsps

"""Testes do HTTPClient."""

from __future__ import annotations

import pytest
import responses

from correios_reverso.config import Config
from correios_reverso.exceptions import APIError, RateLimitError, SessionExpiredError
from correios_reverso.http_client import HTTPClient


@responses.activate
def test_get_json(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/test",
        json={"ok": True},
        status=200,
    )
    http = HTTPClient(config)
    result = http.get_json("/test")
    assert result == {"ok": True}


@responses.activate
def test_post_json(config: Config):
    responses.add(
        responses.POST,
        f"{config.base_url}/test",
        json={"id": "123"},
        status=200,
    )
    http = HTTPClient(config)
    result = http.post_json("/test", json={"name": "test"})
    assert result == {"id": "123"}


@responses.activate
def test_rate_limit_429(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/test",
        status=429,
    )
    http = HTTPClient(config)
    with pytest.raises(RateLimitError):
        http.get("/test")


@responses.activate
def test_server_error_500(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/test",
        status=500,
        body="Internal Server Error",
    )
    http = HTTPClient(config)
    with pytest.raises(APIError, match="500"):
        http.get("/test")


@responses.activate
def test_session_expired_redirect_cas(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/test",
        status=200,
        body='<html><script>window.location="https://cas.correios.com.br/login?service=..."</script></html>',
        content_type="text/html",
    )
    http = HTTPClient(config)
    with pytest.raises(SessionExpiredError):
        http.get("/test")

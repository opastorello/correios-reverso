"""Testes do CorreiosClient (fachada)."""

from __future__ import annotations

import responses

from correios_reverso.client import CorreiosClient
from correios_reverso.config import Config


CAS_LOGIN_HTML = """
<html><form>
    <input name="execution" value="e1s1_FAKE" />
</form></html>
"""

HOME_HTML = "<html><title>Pré-Postagem</title><body>Home</body></html>"


def test_client_init(config: Config):
    client = CorreiosClient(config)
    assert client.is_authenticated is False
    assert client.postagem is not None
    assert client.destinatarios is not None
    assert client.remetentes is not None
    assert client.etiqueta is not None
    assert client.cancelamento is not None
    assert client.auxiliares is not None


def test_client_from_env(monkeypatch):
    monkeypatch.setenv("CORREIOS_USERNAME", "fake_user")
    monkeypatch.setenv("CORREIOS_PASSWORD", "fake_pass")
    monkeypatch.setenv("CORREIOS_TIMEOUT", "10")
    client = CorreiosClient.from_env()
    assert client.config.username == "fake_user"
    assert client.config.timeout == 10


@responses.activate
def test_client_context_manager(config: Config):
    # Mock CAS login
    responses.add(responses.GET, f"{config.cas_url}/login", body=CAS_LOGIN_HTML, status=200)
    responses.add(responses.POST, f"{config.cas_url}/login", body=HOME_HTML, status=200)
    # Mock logout
    responses.add(responses.GET, f"{config.cas_url}/logout", status=200)

    with CorreiosClient(config) as client:
        assert client.is_authenticated is True
    # Após sair do context manager
    assert client.is_authenticated is False


@responses.activate
def test_client_login_e_close(config: Config):
    responses.add(responses.GET, f"{config.cas_url}/login", body=CAS_LOGIN_HTML, status=200)
    responses.add(responses.POST, f"{config.cas_url}/login", body=HOME_HTML, status=200)
    responses.add(responses.GET, f"{config.cas_url}/logout", status=200)

    client = CorreiosClient(config)
    client.login()
    assert client.is_authenticated is True
    client.close()
    assert client.is_authenticated is False

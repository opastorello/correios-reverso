"""Testes de autenticação CAS."""

from __future__ import annotations

import pytest
import responses

from correios_reverso.auth import AuthManager
from correios_reverso.config import Config
from correios_reverso.exceptions import AuthenticationError
from correios_reverso.http_client import HTTPClient

CAS_LOGIN_HTML = """
<html>
<form action="/login" method="post">
    <input name="username" />
    <input name="password" type="password" />
    <input name="execution" value="e1s1_TOKEN_FAKE_12345" />
    <input name="_eventId" value="submit" />
    <input name="geolocation" value="" />
    <button name="submitBtn">Entrar</button>
</form>
</html>
"""

HOME_HTML = """
<html><head><title>Pré-Postagem</title></head>
<body>Bem-vindo</body></html>
"""


@responses.activate
def test_login_sucesso(config: Config):
    # 1) GET página CAS
    responses.add(
        responses.GET,
        f"{config.cas_url}/login",
        body=CAS_LOGIN_HTML,
        status=200,
    )
    # 2) POST login → redirect (responses segue automaticamente)
    responses.add(
        responses.POST,
        f"{config.cas_url}/login",
        body=HOME_HTML,
        status=200,
    )

    http = HTTPClient(config)
    auth = AuthManager(http, config)
    auth.login()
    assert auth.is_authenticated is True


@responses.activate
def test_login_sem_execution(config: Config):
    responses.add(
        responses.GET,
        f"{config.cas_url}/login",
        body="<html>sem campo execution</html>",
        status=200,
    )

    http = HTTPClient(config)
    auth = AuthManager(http, config)
    with pytest.raises(AuthenticationError, match="execution"):
        auth.login()


@responses.activate
def test_login_credenciais_invalidas(config: Config):
    responses.add(
        responses.GET,
        f"{config.cas_url}/login",
        body=CAS_LOGIN_HTML,
        status=200,
    )
    # POST volta pro form de login (credenciais erradas)
    responses.add(
        responses.POST,
        f"{config.cas_url}/login",
        body=CAS_LOGIN_HTML,
        status=200,
        headers={"Location": f"{config.cas_url}/login?error=true"},
    )

    http = HTTPClient(config)
    auth = AuthManager(http, config)
    with pytest.raises(AuthenticationError, match="[Cc]redenciais|formulário"):
        auth.login()

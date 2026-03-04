"""Autenticacao CAS SSO dos Correios.

Este modulo fornece a classe AuthManager para gerenciar o fluxo
de autenticacao CAS (Central Authentication Service) dos Correios.

Fluxo completo:
    1. GET https://prepostagem.correios.com.br/  -> 302 para CAS
    2. GET https://cas.correios.com.br/login?service=...  -> HTML com form
    3. Extrair campo `execution` (dinamico, nunca reutilizar)
    4. POST https://cas.correios.com.br/login  (form-urlencoded)
    5. 302 -> callback /login/cas?ticket=...
    6. 302 -> / (sessao autenticada)

Note:
    O campo `execution` e dinamico e deve ser extraido do HTML
    a cada tentativa de login. Nunca reutilize esse valor.

Example:
    >>> from correios_reverso.auth import AuthManager
    >>> from correios_reverso.http_client import HTTPClient
    >>> from correios_reverso.config import Config
    >>>
    >>> config = Config.from_env()
    >>> http = HTTPClient(config)
    >>> auth = AuthManager(http, config)
    >>> auth.login()  # Realiza autenticacao CAS
"""

from __future__ import annotations

import logging
import re

from correios_reverso.config import Config
from correios_reverso.exceptions import AuthenticationError
from correios_reverso.http_client import HTTPClient

logger = logging.getLogger("correios_reverso.auth")

_EXECUTION_RE = re.compile(r'name="execution"\s+value="([^"]+)"')


class AuthManager:
    """Gerencia login/logout via CAS Correios."""

    def __init__(self, http: HTTPClient, config: Config):
        self._http = http
        self._config = config
        self._authenticated = False

    @property
    def is_authenticated(self) -> bool:
        return self._authenticated

    def login(self) -> None:
        """Executa o fluxo CAS completo. Levanta AuthenticationError em caso de falha."""
        session = self._http.session

        # 1) GET na home → segue redirects até chegar na página de login CAS
        cas_service_url = (
            f"{self._config.cas_url}/login"
            f"?service={self._config.base_url}/login/cas"
        )
        logger.info("Iniciando login CAS: %s", cas_service_url)
        resp = session.get(
            cas_service_url,
            timeout=self._config.timeout,
            allow_redirects=True,
        )
        if resp.status_code != 200:
            raise AuthenticationError(
                f"Falha ao carregar página CAS: HTTP {resp.status_code}",
                status_code=resp.status_code,
            )

        # 2) Extrair campo execution do HTML
        match = _EXECUTION_RE.search(resp.text)
        if not match:
            raise AuthenticationError(
                "Campo 'execution' não encontrado no formulário CAS. "
                "Verifique se a URL do CAS está correta."
            )
        execution = match.group(1)
        logger.debug("execution token extraído (%d chars)", len(execution))

        # 3) POST login com credenciais
        login_data = {
            "username": self._config.username,
            "password": self._config.password,
            "execution": execution,
            "_eventId": "submit",
            "geolocation": "",
            "submitBtn": "",
        }
        resp = session.post(
            f"{self._config.cas_url}/login",
            data=login_data,
            timeout=self._config.timeout,
            allow_redirects=True,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": self._config.cas_url,
                "Referer": cas_service_url,
            },
        )

        # Após os redirects, devemos estar autenticados na home
        if resp.status_code != 200:
            raise AuthenticationError(
                f"Login CAS falhou: HTTP {resp.status_code}",
                status_code=resp.status_code,
            )

        # Validar que chegamos na home autenticada (não no form de login)
        # Checamos tanto a URL quanto o conteúdo — se o HTML ainda contém
        # o formulário CAS com campo execution, o login falhou.
        if 'name="execution"' in resp.text and "cas.correios.com.br" in resp.url:
            raise AuthenticationError(
                "Credenciais inválidas — CAS retornou ao formulário de login."
            )

        self._authenticated = True
        logger.info("Login CAS bem-sucedido. URL final: %s", resp.url)

    def ensure_authenticated(self) -> None:
        """Login se ainda não autenticado."""
        if not self._authenticated:
            self.login()

    def logout(self) -> None:
        """Tenta logout (melhor esforço)."""
        try:
            self._http.session.get(
                f"{self._config.cas_url}/logout",
                timeout=self._config.timeout,
            )
        except Exception:
            pass
        self._authenticated = False
        logger.info("Logout realizado.")

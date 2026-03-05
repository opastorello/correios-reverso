"""Cliente HTTP base com retry, timeout e gerenciamento de sessao.

Este modulo fornece a classe HTTPClient, que encapsula requests.Session
com as seguintes funcionalidades:

- Retry automatico com backoff exponencial para erros transitorios
- Deteccao automatica de sessao expirada (redirect para CAS)
- Tratamento de rate limit (HTTP 429)
- Timeouts configuraveis

Note:
    Metodos POST e DELETE nao fazem retry automatico (risco de duplicacao).

Example:
    >>> from correios_reverso.http_client import HTTPClient
    >>> from correios_reverso.config import Config
    >>>
    >>> config = Config.from_env()
    >>> http = HTTPClient(config)
    >>> data = http.get_json("/prepostagem/afaturar/servicos/semSegmentoNovoMalote")
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import requests

from correios_reverso.config import Config
from correios_reverso.exceptions import (
    APIError,
    RateLimitError,
    SessionExpiredError,
)

logger = logging.getLogger("correios_reverso.http")

# Métodos que NÃO devem ter retry automático (risco de duplicação).
_NON_IDEMPOTENT_METHODS = {"POST", "DELETE"}


class HTTPClient:
    """Wrapper sobre requests.Session com retry e detecção de sessão expirada."""

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.user_agent,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        })
        self.session.verify = config.verify_ssl

    # ----- helpers internos -----

    def _full_url(self, path: str) -> str:
        if path.startswith("http"):
            return path
        return f"{self.config.base_url}{path}"

    def _is_session_expired(self, resp: requests.Response) -> bool:
        """Detecta redirect para CAS login (sessão expirou)."""
        # Verifica cadeia de redirects intermediários
        for r in resp.history:
            location = r.headers.get("Location", "")
            if "cas.correios.com.br/login" in location:
                return True
        # Fallback: resposta final é HTML com conteúdo CAS
        if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
            if "cas.correios.com.br/login" in resp.text[:2000]:
                return True
        return False

    def _handle_response(self, resp: requests.Response) -> requests.Response:
        if self._is_session_expired(resp):
            raise SessionExpiredError("Sessão expirada — necessário re-autenticar.")
        if resp.status_code == 429:
            raise RateLimitError("Rate limit atingido.", status_code=429)
        if resp.status_code >= 500:
            raise APIError(
                f"Erro servidor: {resp.status_code}",
                status_code=resp.status_code,
                response_body=resp.text[:500],
            )
        if 200 <= resp.status_code < 300:
            return resp
        body = resp.text[:500]
        try:
            data = resp.json()
            msg = data.get("mensagem", body)
        except Exception:
            msg = body
        raise APIError(
            f"Erro HTTP {resp.status_code}: {msg}",
            status_code=resp.status_code,
            response_body=body,
        )

    def _request_with_retry(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        timeout = kwargs.pop("timeout", self.config.timeout)
        # POST e DELETE não fazem retry (risco de duplicação)
        is_idempotent = method.upper() not in _NON_IDEMPOTENT_METHODS
        attempts = self.config.retry_attempts if is_idempotent else 1
        last_exc: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                logger.debug("%s %s (attempt %d)", method.upper(), url, attempt)
                resp = self.session.request(method, url, timeout=timeout, **kwargs)
                return self._handle_response(resp)
            except (RateLimitError, APIError) as exc:
                last_exc = exc
                if attempt < attempts:
                    delay = self.config.retry_backoff * (2 ** (attempt - 1))
                    logger.warning("Retry em %.1fs após %s", delay, exc)
                    time.sleep(delay)
                else:
                    raise
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < attempts:
                    delay = self.config.retry_backoff * (2 ** (attempt - 1))
                    logger.warning("Retry em %.1fs após erro de rede: %s", delay, exc)
                    time.sleep(delay)
                else:
                    raise APIError(f"Erro de rede após {attempts} tentativas: {exc}") from exc
        raise last_exc  # type: ignore[misc]  # unreachable

    # ----- API pública -----

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request_with_retry("GET", self._full_url(path), **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request_with_retry("POST", self._full_url(path), **kwargs)

    def put(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request_with_retry("PUT", self._full_url(path), **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request_with_retry("DELETE", self._full_url(path), **kwargs)

    def get_json(self, path: str, **kwargs: Any) -> Any:
        resp = self.get(path, **kwargs)
        return resp.json()

    def post_json(self, path: str, **kwargs: Any) -> Any:
        resp = self.post(path, **kwargs)
        if resp.text.strip():
            return resp.json()
        return None

    def close(self) -> None:
        self.session.close()

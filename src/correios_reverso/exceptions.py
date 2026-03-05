"""Excecoes customizadas para correios-reverso.

Hierarquia de excecoes:

    CorreiosError (base)
    ├── AuthenticationError  - Falha na autenticacao CAS
    ├── SessionExpiredError  - Sessao expirou
    ├── APIError            - Erro retornado pela API
    ├── ValidationError     - Dados de entrada invalidos
    ├── RateLimitError      - Rate limit atingido
    └── CancelamentoError   - Erro ao cancelar pre-postagem

Example:
    >>> from correios_reverso import CorreiosClient, APIError, AuthenticationError
    >>>
    >>> try:
    ...     with CorreiosClient.from_env() as client:
    ...         result = client.postagem.criar(req)
    ... except AuthenticationError as e:
    ...     print(f"Credenciais invalidas: {e}")
    ... except APIError as e:
    ...     print(f"Erro da API ({e.status_code}): {e}")
"""

from __future__ import annotations

from typing import Optional


class CorreiosError(Exception):
    """Exceção base para todas as operações Correios."""

    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class AuthenticationError(CorreiosError):
    """Falha na autenticação CAS."""


class SessionExpiredError(CorreiosError):
    """Sessão expirou e precisa re-autenticar."""


class APIError(CorreiosError):
    """Erro retornado pela API Correios."""


class ValidationError(CorreiosError):
    """Dados de entrada inválidos."""


class RateLimitError(CorreiosError):
    """Rate limit atingido."""


class CancelamentoError(CorreiosError):
    """Erro ao cancelar pré-postagem."""

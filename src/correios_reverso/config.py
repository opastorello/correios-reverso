"""Configuracao centralizada carregada de variaveis de ambiente.

Este modulo fornece a classe Config, que carrega configuracoes de
variaveis de ambiente ou arquivo .env (via python-dotenv).

Variaveis de ambiente:
    CORREIOS_BASE_URL: URL base da API (default: https://prepostagem.correios.com.br)
    CORREIOS_USERNAME: Usuario para autenticacao
    CORREIOS_PASSWORD: Senha para autenticacao
    CORREIOS_TIMEOUT: Timeout em segundos (default: 30)
    CORREIOS_VERIFY_SSL: Verificar SSL (default: true)
    CORREIOS_RETRY_ATTEMPTS: Tentativas de retry (default: 3)

Example:
    >>> from correios_reverso.config import Config
    >>>
    >>> # Carregar de variaveis de ambiente
    >>> config = Config.from_env()
    >>>
    >>> # Ou instanciar diretamente
    >>> config = Config(
    ...     username="meu_usuario",
    ...     password="minha_senha",
    ... )
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None  # type: ignore[assignment]


def _load_dotenv_once() -> None:
    """Carrega .env do diretório raiz do projeto (se python-dotenv disponível)."""
    if load_dotenv is None:
        return
    # Procura .env subindo a partir do diretório atual
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        env_file = parent / ".env"
        if env_file.is_file():
            load_dotenv(env_file)
            return


@dataclass
class Config:
    base_url: str = "https://prepostagem.correios.com.br"
    cas_url: str = "https://cas.correios.com.br"
    username: str = ""
    password: str = ""
    timeout: int = 30
    verify_ssl: bool = True
    retry_attempts: int = 3
    retry_backoff: float = 1.0
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )

    @classmethod
    def from_env(cls) -> Config:
        _load_dotenv_once()
        return cls(
            base_url=os.getenv("CORREIOS_BASE_URL", cls.base_url).rstrip("/"),
            username=os.getenv("CORREIOS_USERNAME", ""),
            password=os.getenv("CORREIOS_PASSWORD", ""),
            timeout=int(os.getenv("CORREIOS_TIMEOUT", "30")),
            verify_ssl=os.getenv("CORREIOS_VERIFY_SSL", "true").lower() == "true",
            retry_attempts=int(os.getenv("CORREIOS_RETRY_ATTEMPTS", "3")),
        )

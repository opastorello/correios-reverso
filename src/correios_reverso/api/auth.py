"""Token-based authentication shared by FastAPI and FastMCP."""

from __future__ import annotations

import os
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException

# Tokens carregados do ambiente (comma-separated)
_API_TOKENS: set[str] = set()


def _load_tokens() -> set[str]:
    """Carrega tokens do ambiente (lazy)."""
    global _API_TOKENS
    if not _API_TOKENS:
        raw = os.getenv("API_TOKENS", "")
        _API_TOKENS = {t.strip() for t in raw.split(",") if t.strip()}
    return _API_TOKENS


def get_valid_tokens() -> set[str]:
    """Retorna o conjunto de tokens válidos."""
    return _load_tokens()


async def verify_token(
    authorization: Annotated[Optional[str], Header()] = None,
) -> str:
    """Dependency que valida Bearer token.

    Returns:
        O token validado.

    Raises:
        HTTPException: 401 se header ausente/malformado, 403 se token inválido.
    """
    tokens = get_valid_tokens()

    if not tokens:
        # Se não há tokens configurados, permite tudo (dev mode)
        return "anonymous"

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format. Use: Bearer <token>")

    token = authorization[7:]

    if token not in tokens:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

    return token


# Type alias para uso em dependências
TokenDep = Annotated[str, Depends(verify_token)]

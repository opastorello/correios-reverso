"""Dependencies compartilhadas entre rotas e MCP tools."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request

from correios_reverso import CorreiosClient


def get_client(request: Request) -> CorreiosClient:
    """Retorna o CorreiosClient do state da aplicação atual."""
    client = getattr(request.app.state, "client", None)
    if client is None:
        raise HTTPException(status_code=503, detail="CorreiosClient not initialized")
    return client


# Type alias para injeção
ClientDep = Annotated[CorreiosClient, Depends(get_client)]

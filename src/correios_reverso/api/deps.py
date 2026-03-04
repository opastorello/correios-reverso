"""Dependencies compartilhadas entre rotas e MCP tools."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from correios_reverso import CorreiosClient


def get_client() -> CorreiosClient:
    """Retorna o CorreiosClient do state da aplicação.

    O client é inicializado no lifespan (app.py) e mantido em app.state.
    """
    from correios_reverso.api.app import app
    return app.state.client


# Type alias para injeção
ClientDep = Annotated[CorreiosClient, Depends(get_client)]

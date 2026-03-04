"""FastAPI application com FastMCP montado.

Este modulo define a aplicacao FastAPI principal com:

- Lifespan management (login on startup, logout on shutdown)
- Rotas REST para todas as operacoes
- MCP Server montado em /mcp
- CORS configuravel
- Documentacao OpenAPI automatica

Uso:
    # Desenvolvimento
    uvicorn correios_reverso.api.app:app --reload --port 8000

    # Producao
    uvicorn correios_reverso.api.app:app --host 0.0.0.0 --port 8000

Endpoints:
    - REST API: http://localhost:8000/...
    - MCP: http://localhost:8000/mcp
    - OpenAPI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
    - Health: http://localhost:8000/health
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from correios_reverso import CorreiosClient
from correios_reverso.api.routes import (
    auxiliares_router,
    cancelamento_router,
    destinatarios_router,
    etiqueta_router,
    postagem_router,
    remetentes_router,
)

logger = logging.getLogger("correios_reverso.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida do CorreiosClient."""
    # Startup: criar e autenticar client
    logger.info("Iniciando CorreiosClient...")
    try:
        client = CorreiosClient.from_env()
        client.login()
        app.state.client = client
        logger.info("CorreiosClient autenticado com sucesso.")
    except Exception as e:
        logger.error(f"Falha ao autenticar CorreiosClient: {e}")
        raise

    # Montar MCP após client estar pronto
    _mount_mcp(app)

    yield

    # Shutdown: fechar client
    logger.info("Fechando CorreiosClient...")
    try:
        app.state.client.close()
    except Exception as e:
        logger.warning(f"Erro ao fechar client: {e}")


app = FastAPI(
    title="Correios Reverso API",
    description="API REST e MCP server para automação de pré-postagens Correios",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health", tags=["Health"])
async def health() -> dict[str, Any]:
    """Verifica se a API está funcionando."""
    return {"status": "ok", "authenticated": hasattr(app.state, "client")}


@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    """Informações da API."""
    return {
        "name": "Correios Reverso API",
        "version": "0.2.0",
        "docs": "/docs",
        "mcp": "/mcp",
    }


# Registrar rotas REST
app.include_router(postagem_router)
app.include_router(destinatarios_router)
app.include_router(remetentes_router)
app.include_router(etiqueta_router)
app.include_router(cancelamento_router)
app.include_router(auxiliares_router)


# Exception handler global
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler global para HTTPException."""
    return {"error": exc.detail, "status_code": exc.status_code}


# FastMCP montado dentro do lifespan
_mcp_mounted = False


def _mount_mcp(app: FastAPI):
    """Monta o FastMCP server na rota /mcp."""
    global _mcp_mounted
    if _mcp_mounted:
        return

    try:
        from fastmcp import FastMCP

        from correios_reverso.mcp.server import create_mcp_server

        mcp = create_mcp_server(app.state.client)
        mcp_app = mcp.http_app()
        app.mount("/mcp", mcp_app)
        _mcp_mounted = True
        logger.info("FastMCP montado em /mcp")
    except ImportError:
        logger.warning("FastMCP não disponível. MCP server desabilitado.")
    except Exception as e:
        logger.error(f"Erro ao montar FastMCP: {e}")

"""Rotas de pré-postagem."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from correios_reverso.api.auth import TokenDep
from correios_reverso.api.deps import ClientDep
from correios_reverso.exceptions import APIError, CorreiosError
from correios_reverso.models import CriarPrePostagemRequest

router = APIRouter(prefix="/postagem", tags=["Postagem"])


@router.get("", summary="Listar pré-postagens registradas")
def listar_postagens(
    token: TokenDep,
    client: ClientDep,
    status: str = Query("PREPOSTADO", description="Status das pré-postagens"),
    pagina: int = Query(0, ge=0, description="Número da página"),
    busca: str = Query("", description="Busca por código de objeto"),
    logistica_reversa: bool = Query(False, description="Filtrar logística reversa"),
) -> dict[str, Any]:
    try:
        result = client.postagem.listar_registrados(
            status=status,
            pagina=pagina,
            busca=busca,
            logistica_reversa=logistica_reversa,
        )
        return result.model_dump()
    except CorreiosError as e:
        raise _map_error(e)


@router.post("", summary="Criar pré-postagem", status_code=201)
def criar_postagem(
    token: TokenDep,
    client: ClientDep,
    dados: CriarPrePostagemRequest,
) -> dict[str, Any]:
    try:
        return client.postagem.criar(dados)
    except CorreiosError as e:
        raise _map_error(e)


# Rotas estáticas ANTES de rotas parametrizadas
@router.get("/servicos", summary="Listar serviços disponíveis")
def listar_servicos(
    token: TokenDep,
    client: ClientDep,
    logistica_reversa: bool = Query(False, description="Serviços de logística reversa"),
) -> list[dict[str, Any]]:
    try:
        result = client.postagem.listar_servicos(logistica_reversa=logistica_reversa)
        return [s.model_dump() for s in result]
    except CorreiosError as e:
        raise _map_error(e)


@router.get("/servicos/{codigo_servico}/adicionais", summary="Listar serviços adicionais")
def listar_servicos_adicionais(
    codigo_servico: str,
    token: TokenDep,
    client: ClientDep,
) -> Any:
    try:
        return client.postagem.listar_servicos_adicionais(codigo_servico)
    except CorreiosError as e:
        raise _map_error(e)


# Rota parametrizada POR ÚLTIMO
@router.get("/{codigo_objeto}", summary="Buscar pré-postagem por código")
def buscar_por_codigo(
    codigo_objeto: str,
    token: TokenDep,
    client: ClientDep,
    status: str = Query("PREPOSTADO"),
) -> dict[str, Any]:
    try:
        result = client.postagem.buscar_por_codigo_objeto(codigo_objeto, status=status)
        return result.model_dump()
    except CorreiosError as e:
        raise _map_error(e)


def _map_error(e: CorreiosError) -> HTTPException:
    """Mapeia CorreiosError para HTTPException."""
    from correios_reverso.exceptions import (
        AuthenticationError,
        RateLimitError,
        SessionExpiredError,
        ValidationError,
    )

    if isinstance(e, AuthenticationError):
        return HTTPException(status_code=401, detail=str(e))
    if isinstance(e, SessionExpiredError):
        return HTTPException(status_code=401, detail=str(e))
    if isinstance(e, ValidationError):
        return HTTPException(status_code=400, detail=str(e))
    if isinstance(e, RateLimitError):
        return HTTPException(status_code=429, detail=str(e))
    if isinstance(e, APIError):
        if e.status_code and 400 <= e.status_code < 500:
            return HTTPException(status_code=e.status_code, detail=str(e))
        return HTTPException(status_code=502, detail=str(e))
    return HTTPException(status_code=500, detail=str(e))

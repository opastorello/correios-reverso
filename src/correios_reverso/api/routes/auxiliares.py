"""Rotas auxiliares (CEP, cartões, embalagens)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from correios_reverso.api.auth import TokenDep
from correios_reverso.api.deps import ClientDep
from correios_reverso.api.routes.postagem import _map_error
from correios_reverso.exceptions import CorreiosError

router = APIRouter(tags=["Auxiliares"])


@router.get("/cep/{cep}", summary="Consultar CEP")
def consultar_cep(
    cep: str,
    token: TokenDep,
    client: ClientDep,
) -> dict[str, Any]:
    """Consulta endereço por CEP."""
    try:
        return client.auxiliares.consultar_cep(cep)
    except CorreiosError as e:
        raise _map_error(e)


@router.get("/cartoes", summary="Listar cartões de postagem")
def listar_cartoes(
    token: TokenDep,
    client: ClientDep,
) -> dict[str, Any]:
    try:
        result = client.auxiliares.listar_cartoes_postagem()
        return result.model_dump()
    except CorreiosError as e:
        raise _map_error(e)


@router.get("/embalagens", summary="Listar embalagens")
def listar_embalagens(
    token: TokenDep,
    client: ClientDep,
) -> dict[str, Any]:
    try:
        result = client.auxiliares.listar_embalagens()
        return result.model_dump()
    except CorreiosError as e:
        raise _map_error(e)

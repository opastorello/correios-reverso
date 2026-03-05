"""Rotas de remetentes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from correios_reverso.api.auth import TokenDep
from correios_reverso.api.deps import ClientDep
from correios_reverso.api.routes.postagem import _map_error
from correios_reverso.exceptions import CorreiosError
from correios_reverso.models import RemetenteRequest

router = APIRouter(prefix="/remetentes", tags=["Remetentes"])


@router.get("", summary="Listar remetentes")
def listar_remetentes(
    token: TokenDep,
    client: ClientDep,
    nome: str = Query("", description="Filtrar por nome"),
) -> dict[str, Any]:
    try:
        return client.remetentes.pesquisar(nome=nome)
    except CorreiosError as e:
        raise _map_error(e)


@router.get("/{id_remetente}", summary="Obter remetente por ID")
def obter_remetente(
    id_remetente: str,
    token: TokenDep,
    client: ClientDep,
) -> dict[str, Any]:
    try:
        return client.remetentes.obter(id_remetente)
    except CorreiosError as e:
        raise _map_error(e)


@router.post("", summary="Criar remetente", status_code=201)
def criar_remetente(
    token: TokenDep,
    client: ClientDep,
    dados: RemetenteRequest,
) -> dict[str, Any]:
    try:
        return client.remetentes.criar(dados)
    except CorreiosError as e:
        raise _map_error(e)


@router.put("/{id_remetente}", summary="Editar remetente")
def editar_remetente(
    id_remetente: str,
    token: TokenDep,
    client: ClientDep,
    dados: RemetenteRequest,
) -> dict[str, Any]:
    try:
        return client.remetentes.editar(id_remetente, dados)
    except CorreiosError as e:
        raise _map_error(e)


@router.delete("/{id_remetente}", summary="Excluir remetente")
def excluir_remetente(
    id_remetente: str,
    token: TokenDep,
    client: ClientDep,
) -> dict[str, Any]:
    try:
        client.remetentes.excluir(id_remetente)
        return {"status": "ok", "message": f"Remetente {id_remetente} excluido"}
    except CorreiosError as e:
        raise _map_error(e)

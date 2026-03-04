"""Rotas de destinatários."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from correios_reverso.api.auth import TokenDep
from correios_reverso.api.deps import ClientDep
from correios_reverso.api.routes.postagem import _map_error
from correios_reverso.exceptions import CorreiosError
from correios_reverso.models import DestinatarioRequest

router = APIRouter(prefix="/destinatarios", tags=["Destinatários"])


@router.get("", summary="Listar destinatarios")
def listar_destinatarios(
    token: TokenDep,
    client: ClientDep,
    nome: str = Query("", description="Filtrar por nome"),
) -> dict[str, Any]:
    try:
        if nome:
            return client.destinatarios.pesquisar_por_nome(nome)
        return client.destinatarios.pesquisar()
    except CorreiosError as e:
        raise _map_error(e)


@router.post("", summary="Criar destinatário", status_code=201)
def criar_destinatario(
    token: TokenDep,
    client: ClientDep,
    dados: DestinatarioRequest,
) -> dict[str, Any]:
    try:
        return client.destinatarios.criar(dados)
    except CorreiosError as e:
        raise _map_error(e)


@router.put("/{id_destinatario}", summary="Editar destinatário")
def editar_destinatario(
    id_destinatario: str,
    token: TokenDep,
    client: ClientDep,
    dados: DestinatarioRequest,
) -> dict[str, Any]:
    try:
        return client.destinatarios.editar(id_destinatario, dados)
    except CorreiosError as e:
        raise _map_error(e)


@router.delete("/{id_destinatario}", summary="Excluir destinatario")
def excluir_destinatario(
    id_destinatario: str,
    token: TokenDep,
    client: ClientDep,
) -> dict[str, Any]:
    try:
        client.destinatarios.excluir(id_destinatario)
        return {"status": "ok", "message": f"Destinatario {id_destinatario} excluido"}
    except CorreiosError as e:
        raise _map_error(e)

"""Rotas de cancelamento."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from correios_reverso.api.auth import TokenDep
from correios_reverso.api.deps import ClientDep
from correios_reverso.api.routes.postagem import _map_error
from correios_reverso.exceptions import CorreiosError

router = APIRouter(prefix="/cancelamento", tags=["Cancelamento"])


@router.delete("/{id_prepostagem}", summary="Cancelar pré-postagem")
def cancelar_postagem(
    id_prepostagem: str,
    token: TokenDep,
    client: ClientDep,
) -> dict[str, Any]:
    """Cancela uma pré-postagem. Operação irreversível."""
    try:
        result = client.cancelamento.cancelar(id_prepostagem)
        return {"id_prepostagem": id_prepostagem, "mensagem": result}
    except CorreiosError as e:
        raise _map_error(e)


@router.get("/{id_prepostagem}/log", summary="Histórico de cancelamento")
def log_cancelamento(
    id_prepostagem: str,
    token: TokenDep,
    client: ClientDep,
) -> list[dict[str, Any]]:
    try:
        return client.cancelamento.log_cancelamento(id_prepostagem)
    except CorreiosError as e:
        raise _map_error(e)

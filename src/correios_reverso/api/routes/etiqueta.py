"""Rotas de etiquetas/rótulos."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from correios_reverso.api.auth import TokenDep
from correios_reverso.api.deps import ClientDep
from correios_reverso.api.routes.postagem import _map_error
from correios_reverso.exceptions import CorreiosError

router = APIRouter(prefix="/etiqueta", tags=["Etiqueta"])


@router.post("/imprimir", summary="Iniciar impressão de etiquetas")
def iniciar_impressao(
    token: TokenDep,
    client: ClientDep,
    ids_prepostagem: list[str] = Query(..., description="IDs das pré-postagens"),
) -> dict[str, Any]:
    try:
        return client.etiqueta.iniciar_impressao(ids_prepostagem)
    except CorreiosError as e:
        raise _map_error(e)


# Rotas estáticas ANTES de rotas parametrizadas
@router.get("/processamentos", summary="Listar processamentos de etiquetas")
def listar_processamentos(
    token: TokenDep,
    client: ClientDep,
) -> list[dict[str, Any]]:
    try:
        result = client.etiqueta.listar_processamentos()
        return [p.model_dump() for p in result.itens]
    except CorreiosError as e:
        raise _map_error(e)


@router.post("/declaracao-conteudo", summary="Gerar declaração de conteúdo")
def gerar_declaracao(
    token: TokenDep,
    client: ClientDep,
    ids_prepostagem: list[str] = Query(..., description="IDs das pré-postagens"),
) -> dict[str, Any]:
    try:
        return client.etiqueta.gerar_declaracao_conteudo(ids_prepostagem)
    except CorreiosError as e:
        raise _map_error(e)


@router.get("/faixas", summary="Consultar faixas de etiquetas")
def consultar_faixas(
    token: TokenDep,
    client: ClientDep,
) -> Any:
    try:
        return client.etiqueta.consultar_faixas_etiquetas()
    except CorreiosError as e:
        raise _map_error(e)


# Rota parametrizada POR ÚLTIMO
@router.get("/{id_recibo}", summary="Download etiqueta/rotulo")
def download_rotulo(
    id_recibo: str,
    token: TokenDep,
    client: ClientDep,
) -> dict[str, Any]:
    """Retorna o PDF da etiqueta em base64."""
    try:
        result = client.etiqueta.download_rotulo(id_recibo)
        return {"id_recibo": id_recibo, "pdf_base64": result}
    except CorreiosError as e:
        raise _map_error(e)

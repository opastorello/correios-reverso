"""Rotas da API."""

from correios_reverso.api.routes.auxiliares import router as auxiliares_router
from correios_reverso.api.routes.cancelamento import router as cancelamento_router
from correios_reverso.api.routes.destinatarios import router as destinatarios_router
from correios_reverso.api.routes.etiqueta import router as etiqueta_router
from correios_reverso.api.routes.postagem import router as postagem_router
from correios_reverso.api.routes.remetentes import router as remetentes_router

__all__ = [
    "postagem_router",
    "destinatarios_router",
    "remetentes_router",
    "etiqueta_router",
    "cancelamento_router",
    "auxiliares_router",
]

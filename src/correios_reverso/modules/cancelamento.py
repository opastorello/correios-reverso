"""Cancelamento de pre-postagens.

Este modulo fornece operacoes para cancelamento de pre-postagens
na plataforma Pre-Postagem dos Correios.

Endpoints:
    - DELETE /prepostagem/afaturar/{idPrepostagem}  (cancelar)
    - GET    /prepostagem/v1/log/cancelamento       (historico)

Example:
    >>> from correios_reverso import CorreiosClient
    >>>
    >>> with CorreiosClient.from_env() as client:
    ...     # Cancelar pre-postagem
    ...     msg = client.cancelamento.cancelar("PRabc123...")
    ...     print(msg)  # "Cancelamento da Prepostagem PRabc... efetuado com sucesso."
    ...     # Consultar historico
    ...     log = client.cancelamento.log_cancelamento("PRabc123...")
"""

from __future__ import annotations

import logging
from typing import Any

from correios_reverso.http_client import HTTPClient

logger = logging.getLogger("correios_reverso.cancelamento")


class Cancelamento:
    def __init__(self, http: HTTPClient):
        self._http = http

    def cancelar(self, id_prepostagem: str) -> str:
        """DELETE /prepostagem/afaturar/{id} — retorna mensagem de resultado.

        Erros HTTP (4xx/5xx) são levantados como APIError pelo HTTPClient.
        """
        resp = self._http.delete(f"/prepostagem/afaturar/{id_prepostagem}")
        logger.info("Pré-postagem %s cancelada.", id_prepostagem)
        return resp.text

    def log_cancelamento(self, id_prepostagem: str) -> list[dict[str, Any]]:
        """GET /prepostagem/v1/log/cancelamento — histórico de cancelamento."""
        return self._http.get_json(
            "/prepostagem/v1/log/cancelamento",
            params={"idPrepostagem": id_prepostagem},
        )

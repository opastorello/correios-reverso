"""Endpoints auxiliares: CEP, cartoes, embalagens.

Este modulo fornece operacoes auxiliares da plataforma Pre-Postagem.

Endpoints:
    - GET /auxiliares/cep/{cep}          (consultar CEP)
    - GET /cartoespostagensclientes      (listar cartoes)
    - GET /embalagens                    (listar embalagens)

Example:
    >>> from correios_reverso import CorreiosClient
    >>>
    >>> with CorreiosClient.from_env() as client:
    ...     # Consultar CEP
    ...     endereco = client.auxiliares.consultar_cep("01001000")
    ...     # Listar cartoes
    ...     cartoes = client.auxiliares.listar_cartoes_postagem()
    ...     # Listar embalagens
    ...     embalagens = client.auxiliares.listar_embalagens()
"""

from __future__ import annotations

from typing import Any

from correios_reverso.http_client import HTTPClient
from correios_reverso.models import CartaoPostagemResponse, EmbalagemResponse


class Auxiliares:
    def __init__(self, http: HTTPClient):
        self._http = http

    def consultar_cep(self, cep: str) -> dict[str, Any]:
        """GET /auxiliares/cep/{cep} — resolve endereço."""
        return self._http.get_json(f"/auxiliares/cep/{cep}")

    def listar_cartoes_postagem(self, pagina: int = 0, tamanho: int = 50000) -> CartaoPostagemResponse:
        """GET /cartoespostagensclientes."""
        data = self._http.get_json(
            "/cartoespostagensclientes",
            params={"pagina": pagina, "tamanho": tamanho},
        )
        return CartaoPostagemResponse.model_validate(data)

    def listar_embalagens(self, pagina: int = 0) -> EmbalagemResponse:
        """GET /embalagens."""
        data = self._http.get_json("/embalagens", params={"pagina": pagina})
        return EmbalagemResponse.model_validate(data)

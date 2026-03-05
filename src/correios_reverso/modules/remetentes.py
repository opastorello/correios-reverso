"""CRUD de remetentes.

Este modulo fornece operacoes para gerenciamento de remetentes
cadastrados na plataforma Pre-Postagem dos Correios.

Endpoints validados:
    - POST   /remetentes          (criar)
    - PUT    /remetentes/{id}     (editar)
    - DELETE /remetentes/{id}     (excluir)
    - GET    /remetentes/pesquisa (buscar)
    - GET    /remetentes/{id}     (detalhe)

Example:
    >>> from correios_reverso import CorreiosClient
    >>> from correios_reverso.models import RemetenteRequest
    >>>
    >>> with CorreiosClient.from_env() as client:
    ...     # Listar
    ...     remetentes = client.remetentes.pesquisar()
    ...     # Criar
    ...     novo = client.remetentes.criar(RemetenteRequest(
    ...         nomeRemetente="EMPRESA LTDA",
    ...         cepRemetente="01001000",
    ...         logradouroRemetente="Rua Exemplo",
    ...         numeroRemetente="1190",
    ...         bairroRemetente="Centro",
    ...         cidadeRemetente="Sao Paulo",
    ...         ufRemetente="RS",
    ...     ))
"""

from __future__ import annotations

from typing import Any

from correios_reverso.http_client import HTTPClient
from correios_reverso.models import RemetenteRequest


class Remetentes:
    def __init__(self, http: HTTPClient):
        self._http = http

    def pesquisar(
        self,
        nome: str = "",
        pagina: int = 0,
        numero_cartao_postagem: str = "",
    ) -> dict[str, Any]:
        """GET /remetentes/pesquisa — retorna JSON paginado."""
        params: dict[str, Any] = {
            "pagina": pagina,
            "isMesmoContrato": "true",
            "nome": nome,
            "codigo": "",
            "numeroCartaoPostagem": numero_cartao_postagem,
            "indicadorMalote": "",
            "indicadorArquivo": "",
        }
        return self._http.get_json("/remetentes/pesquisa", params=params)

    def obter(self, id_remetente: str) -> dict[str, Any]:
        """GET /remetentes/{id} — retorna detalhe do remetente."""
        return self._http.get_json(f"/remetentes/{id_remetente}")

    def criar(self, dados: RemetenteRequest) -> dict[str, Any]:
        """POST /remetentes — retorna JSON com `id`."""
        resp = self._http.post(
            "/remetentes",
            json=dados.model_dump(),
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.json()

    def editar(self, id_remetente: str, dados: RemetenteRequest) -> None:
        """PUT /remetentes/{id}."""
        resp = self._http.put(
            f"/remetentes/{id_remetente}",
            json=dados.model_dump(),
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()

    def excluir(self, id_remetente: str) -> None:
        """DELETE /remetentes/{id}."""
        resp = self._http.delete(f"/remetentes/{id_remetente}")
        resp.raise_for_status()

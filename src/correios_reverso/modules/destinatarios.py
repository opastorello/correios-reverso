"""CRUD de destinatarios.

Este modulo fornece operacoes para gerenciamento de destinatarios
cadastrados na plataforma Pre-Postagem dos Correios.

Endpoints validados:
    - POST /destinatarios/salvarSemCPF  (criar)
    - PUT  /destinatarios/{id}          (editar)
    - DELETE /destinatarios/{id}        (excluir)
    - GET  /destinatarios/pesquisa      (buscar)
    - GET  /destinatarios/pesquisaPorNome (busca simplificada)

Note:
    O endpoint de criacao usa /salvarSemCPF, nao /destinatarios.

Example:
    >>> from correios_reverso import CorreiosClient
    >>> from correios_reverso.models import DestinatarioRequest
    >>>
    >>> with CorreiosClient.from_env() as client:
    ...     # Listar
    ...     destinatarios = client.destinatarios.pesquisar()
    ...     # Criar
    ...     novo = client.destinatarios.criar(DestinatarioRequest(
    ...         nomeDestinatario="CLIENTE NOVO",
    ...         cepDestinatario="01001000",
    ...         logradouroDestinatario="Praca da Se",
    ...         numeroDestinatario="1",
    ...         bairroDestinatario="Se",
    ...         cidadeDestinatario="Sao Paulo",
    ...         ufDestinatario="SP",
    ...     ))
"""

from __future__ import annotations

from typing import Any

from correios_reverso.http_client import HTTPClient
from correios_reverso.models import DestinatarioRequest


class Destinatarios:
    def __init__(self, http: HTTPClient):
        self._http = http

    def pesquisar(
        self,
        nome: str = "",
        pagina: int = 0,
        numero_cartao_postagem: str = "",
    ) -> dict[str, Any]:
        """GET /destinatarios/pesquisa — retorna JSON paginado com `itens` e `page`."""
        params: dict[str, Any] = {
            "pagina": pagina,
            "isMesmoContrato": "true",
            "nome": nome,
            "codigo": "",
            "numeroCartaoPostagem": numero_cartao_postagem,
            "indicadorMalote": "",
            "indicadorArquivo": "",
        }
        return self._http.get_json("/destinatarios/pesquisa", params=params)

    def pesquisar_por_nome(self, nome: str, pagina: int = 0) -> dict[str, Any]:
        """GET /destinatarios/pesquisaPorNome — busca simplificada usada na tela avulsa."""
        return self._http.get_json(
            "/destinatarios/pesquisaPorNome",
            params={"pagina": pagina, "nome": nome},
        )

    def criar(self, dados: DestinatarioRequest) -> dict[str, Any]:
        """POST /destinatarios/salvarSemCPF — retorna JSON com `id`."""
        resp = self._http.post(
            "/destinatarios/salvarSemCPF",
            json=dados.model_dump(),
            headers={
                "Content-Type": "application/json",
                "Origin": "https://prepostagem.correios.com.br",
                "Referer": "https://prepostagem.correios.com.br/usuario/destinatario",
            },
        )
        resp.raise_for_status()
        return resp.json()

    def editar(self, id_destinatario: str, dados: DestinatarioRequest) -> None:
        """PUT /destinatarios/{id}."""
        resp = self._http.put(
            f"/destinatarios/{id_destinatario}",
            json=dados.model_dump(),
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()

    def excluir(self, id_destinatario: str) -> None:
        """DELETE /destinatarios/{id}."""
        resp = self._http.delete(f"/destinatarios/{id_destinatario}")
        resp.raise_for_status()

"""Pre-postagem: criar, listar, consultar.

Este modulo fornece operacoes para gerenciamento de pre-postagens
na plataforma Pre-Postagem dos Correios.

Endpoints principais:
    - POST /prepostagem/afaturar              (criar pre-postagem)
    - GET  /prepostagem/afaturar/registrados  (listar painel)
    - GET  /prepostagem/afaturar/servicos/... (listar servicos)

Logistica Reversa:
    Para criar pre-postagens de logistica reversa, use:
    - logisticaReversa="S" no body
    - dataValidadeLogReversa no formato DD/MM/YYYY

    Nota: O parametro `filtraLogisticaReseva` tem typo no backend - usar "S".

Example:
    >>> from correios_reverso import CorreiosClient
    >>> from correios_reverso.models import CriarPrePostagemRequest
    >>>
    >>> with CorreiosClient.from_env() as client:
    ...     # Listar servicos
    ...     servicos = client.postagem.listar_servicos()
    ...     # Criar pre-postagem
    ...     req = CriarPrePostagemRequest(...)
    ...     result = client.postagem.criar(req)
"""

from __future__ import annotations

from typing import Any

from correios_reverso.http_client import HTTPClient
from correios_reverso.models import (
    CriarPrePostagemRequest,
    PrePostagemListResponse,
    ServicoDisponivel,
)


class Postagem:
    def __init__(self, http: HTTPClient):
        self._http = http

    def listar_registrados(
        self,
        status: str = "PREPOSTADO",
        pagina: int = 0,
        busca: str = "",
        logistica_reversa: bool = False,
    ) -> PrePostagemListResponse:
        """GET /prepostagem/afaturar/registrados."""
        params = {
            "pagina": pagina,
            "status": status,
            "busca": busca,
            "filtraLogisticaReseva": "S" if logistica_reversa else "",
        }
        data = self._http.get_json("/prepostagem/afaturar/registrados", params=params)
        return PrePostagemListResponse.model_validate(data)

    def buscar_por_codigo_objeto(self, codigo_objeto: str, status: str = "PREPOSTADO") -> PrePostagemListResponse:
        """Busca pré-postagem por codigoObjeto (param `busca`)."""
        return self.listar_registrados(status=status, busca=codigo_objeto)

    def criar(self, dados: CriarPrePostagemRequest) -> dict[str, Any]:
        """POST /prepostagem/afaturar — cria pré-postagem.

        A API retorna 201 Created com o payload expandido no body.
        """
        resp = self._http.post(
            "/prepostagem/afaturar",
            json=dados.model_dump(exclude_none=True),
        )
        if resp.text.strip():
            return resp.json()
        return {"mensagem": "Incluido com sucesso!"}

    def listar_servicos(self, logistica_reversa: bool = False) -> list[ServicoDisponivel]:
        """GET /prepostagem/afaturar/servicos/..."""
        if logistica_reversa:
            path = "/prepostagem/afaturar/servicos/logisticareversa/semSegmentoNovoMalote"
        else:
            path = "/prepostagem/afaturar/servicos/semSegmentoNovoMalote"
        data = self._http.get_json(path)
        return [ServicoDisponivel.model_validate(s) for s in data]

    def consultar_prazo(
        self,
        codigo_servico: str,
        cep_origem: str,
        cep_destino: str,
        data_evento: str = "",
    ) -> Any:
        """GET /prazos."""
        params = {
            "coServico": codigo_servico,
            "cepOrigem": cep_origem,
            "cepDestino": cep_destino,
            "dtEvento": data_evento,
        }
        return self._http.get_json("/prazos", params=params)

    def listar_servicos_adicionais(self, codigo_servico: str) -> Any:
        """GET /rotulo/servicosadicionais/{codigoServico}."""
        return self._http.get_json(f"/rotulo/servicosadicionais/{codigo_servico}")

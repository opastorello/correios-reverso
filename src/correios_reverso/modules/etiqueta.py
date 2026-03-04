"""Geracao de rotulos/etiquetas.

Este modulo fornece operacoes para geracao de etiquetas de postagem
na plataforma Pre-Postagem dos Correios.

Fluxo assincrono:
    1. POST /rotulo/painel/imprimir/assincrono  -> retorna { idRecibo }
    2. POST /processamentosrotulos              -> registra processamento
    3. GET  /rotulo/painel/assincrono/download/{idRecibo}  -> poll ate pronto

Example:
    >>> from correios_reverso import CorreiosClient
    >>>
    >>> with CorreiosClient.from_env() as client:
    ...     # Iniciar impressao
    ...     id_recibo = client.etiqueta.iniciar_impressao(["PRabc123..."])
    ...     # Aguardar e baixar PDF
    ...     pdf_bytes = client.etiqueta.aguardar_e_baixar(id_recibo)
    ...     # Salvar arquivo
    ...     with open("etiqueta.pdf", "wb") as f:
    ...         f.write(pdf_bytes)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from correios_reverso.exceptions import APIError
from correios_reverso.http_client import HTTPClient
from correios_reverso.models import ProcessamentoRotuloListResponse

logger = logging.getLogger("correios_reverso.etiqueta")


class Etiqueta:
    def __init__(self, http: HTTPClient):
        self._http = http

    def iniciar_impressao(
        self,
        ids_prepostagem: list[str],
        tipo_rotulo: str = "P",
        formato_rotulo: str = "ET",
        imprime_remetente: str = "S",
        layout_impressao: str = "PADRAO",
    ) -> str:
        """Inicia geração assíncrona. Retorna idRecibo."""
        body = [
            {"idPrePostagem": id_pp, "sequencial": idx + 1}
            for idx, id_pp in enumerate(ids_prepostagem)
        ]
        params = {
            "tipoRotulo": tipo_rotulo,
            "formatoRotulo": formato_rotulo,
            "imprimeRemetente": imprime_remetente,
            "layoutImpressao": layout_impressao,
        }
        resp = self._http.post(
            "/rotulo/painel/imprimir/assincrono",
            params=params,
            json=body,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        id_recibo = data.get("idRecibo", "")
        if not id_recibo:
            raise APIError("Resposta sem idRecibo na geração de rótulo.")

        # Registrar processamento
        self._http.post(
            "/processamentosrotulos",
            json={
                "idRecibo": id_recibo,
                "statusProcessamento": "EM_PROCESSAMENTO",
                "url": f"/rotulo/painel/imprimir/assincrono?tipoRotulo={tipo_rotulo}&formatoRotulo={formato_rotulo}&imprimeRemetente={imprime_remetente}&layoutImpressao={layout_impressao}",
            },
            headers={"Content-Type": "application/json"},
        )

        logger.info("Impressão iniciada, idRecibo=%s", id_recibo)
        return id_recibo

    def download_rotulo(self, id_recibo: str) -> bytes:
        """Baixa o arquivo do rótulo gerado."""
        resp = self._http.get(f"/rotulo/painel/assincrono/download/{id_recibo}")
        resp.raise_for_status()
        return resp.content

    def aguardar_e_baixar(
        self,
        id_recibo: str,
        max_tentativas: int = 20,
        intervalo: float = 3.0,
    ) -> bytes:
        """Poll até rótulo estar pronto e retorna bytes."""
        for tentativa in range(1, max_tentativas + 1):
            logger.debug("Poll rótulo %s (tentativa %d/%d)", id_recibo, tentativa, max_tentativas)
            resp = self._http.get(f"/rotulo/painel/assincrono/download/{id_recibo}")
            if resp.status_code == 200 and len(resp.content) > 500:
                logger.info("Rótulo pronto (%d bytes)", len(resp.content))
                return resp.content
            time.sleep(intervalo)
        raise APIError(f"Rótulo não ficou pronto após {max_tentativas} tentativas.")

    def listar_processamentos(self, pagina: int = 0) -> ProcessamentoRotuloListResponse:
        """GET /processamentosrotulos — lista rótulos gerados."""
        params = {
            "pagina": pagina,
            "status": ["EM_PROCESSAMENTO", "FINALIZADO", "ERRO_PROCESSAMENTO"],
        }
        data = self._http.get_json("/processamentosrotulos", params=params)
        return ProcessamentoRotuloListResponse.model_validate(data)

    def gerar_declaracao_conteudo(
        self,
        ids: list[str],
        formato: str = "A4",
        quebra_pagina: str = "N",
    ) -> bytes:
        """GET /prepostagem/afaturar/declaracaoConteudo/{ids}."""
        ids_str = ",".join(ids)
        resp = self._http.get(
            f"/prepostagem/afaturar/declaracaoConteudo/{ids_str}",
            params={"tamFolhaImpressao": formato, "quebraPaginaImpressao": quebra_pagina},
        )
        resp.raise_for_status()
        return resp.content

    def consultar_faixas_etiquetas(self, data_inicial: str, data_final: str) -> Any:
        """GET /rotulo/range — faixas de etiquetas por período (DD/MM/AAAA)."""
        return self._http.get_json(
            "/rotulo/range",
            params={"dataInicial": data_inicial, "dataFinal": data_final},
        )

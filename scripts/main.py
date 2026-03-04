#!/usr/bin/env python3
"""Script principal — fluxo completo de automação Correios.

Uso:
    # Configurar .env com credenciais primeiro
    python scripts/main.py

Requer:
    pip install -e ".[dev]"
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Garantir que src/ está no path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv()

from correios_reverso import CorreiosClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("main")


def main() -> None:
    client = CorreiosClient.from_env()

    try:
        # 1. Login
        logger.info("=== Login ===")
        client.login()
        logger.info("Autenticado: %s", client.is_authenticated)

        # 2. Listar cartões de postagem
        logger.info("=== Cartões de Postagem ===")
        cartoes = client.auxiliares.listar_cartoes_postagem()
        for c in cartoes.itens:
            logger.info("  Cartão: %s | Contrato: %s | Ativo: %s", c.numeroCartao, c.contrato, c.ativo)

        # 3. Listar serviços disponíveis
        logger.info("=== Serviços Disponíveis ===")
        servicos = client.postagem.listar_servicos()
        for s in servicos:
            logger.info("  %s - %s", s.codigo, s.descricao)

        # 4. Listar serviços de LR
        logger.info("=== Serviços Logística Reversa ===")
        servicos_lr = client.postagem.listar_servicos(logistica_reversa=True)
        for s in servicos_lr:
            logger.info("  %s - %s (desconto LR: %s)", s.codigo, s.descricao, s.inDescontoLogisticaReversa)

        # 5. Listar pré-postagens registradas
        logger.info("=== Pré-Postagens (PREPOSTADO) ===")
        registrados = client.postagem.listar_registrados(status="PREPOSTADO")
        logger.info("  Total: %d", registrados.page.count)
        for item in registrados.itens[:5]:
            logger.info(
                "  %s | %s | %s | LR=%s",
                item.codigoObjeto, item.servico, item.descStatusAtual, item.logisticaReversa,
            )

        # 6. Pesquisar remetentes
        logger.info("=== Remetentes ===")
        remetentes = client.remetentes.pesquisar()
        for r in remetentes.get("itens", [])[:3]:
            logger.info("  %s (id=%s)", r.get("nome"), r.get("id"))

        # 7. Pesquisar destinatários
        logger.info("=== Destinatários ===")
        destinatarios = client.destinatarios.pesquisar()
        for d in destinatarios.get("itens", [])[:3]:
            logger.info("  %s (id=%s)", d.get("nome"), d.get("id"))

        logger.info("=== Fluxo completo executado com sucesso ===")

    finally:
        client.close()


if __name__ == "__main__":
    main()

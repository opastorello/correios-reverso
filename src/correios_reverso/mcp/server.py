"""FastMCP server com tools para todas as operacoes Correios.

Este modulo define o MCP (Model Context Protocol) server que expoe
as funcionalidades da biblioteca como tools para uso com assistente de IA.

Tools disponiveis (19):

Postagem:
    - listar_postagens: Lista pre-postagens registradas
    - buscar_postagem_por_codigo: Busca por codigo de objeto
    - criar_postagem: Cria nova pre-postagem
    - listar_servicos: Lista servicos disponiveis

Cancelamento:
    - cancelar_postagem: Cancela pre-postagem (irreversivel)
    - log_cancelamento: Historico de cancelamento

Destinatarios:
    - listar_destinatarios: Lista destinatarios
    - criar_destinatario: Cria destinatario
    - excluir_destinatario: Exclui destinatario

Remetentes:
    - listar_remetentes: Lista remetentes
    - obter_remetente: Obtem remetente por ID
    - criar_remetente: Cria remetente
    - excluir_remetente: Exclui remetente

Etiquetas:
    - iniciar_impressao_etiqueta: Inicia impressao assincrona
    - download_etiqueta: Download PDF em base64
    - listar_processamentos_etiqueta: Lista processamentos

Auxiliares:
    - consultar_cep: Consulta endereco por CEP
    - listar_cartoes_postagem: Lista cartoes de postagem
    - listar_embalagens: Lista embalagens disponiveis

Uso:
    O MCP server e montado automaticamente em /mcp pela aplicacao FastAPI.
    Configure no assistente de IA para conectar em http://localhost:8000/mcp
"""

from __future__ import annotations

import base64
import logging
from typing import Annotated, Any, Optional

from fastmcp import FastMCP
from pydantic import Field

from correios_reverso import CorreiosClient
from correios_reverso.models import (
    CriarPrePostagemRequest,
    DestinatarioRequest,
    ItemDeclaracaoConteudo,
    RemetenteRequest,
)

logger = logging.getLogger("correios_reverso.mcp")

# Instância global (será configurada com client)
mcp = FastMCP(
    name="Correios Reverso",
    instructions="MCP server para automação de pré-postagens Correios",
)


def create_mcp_server(client: CorreiosClient) -> FastMCP:
    """Cria e configura o MCP server com o client injetado."""

    # ============================================================
    # POSTAGEM
    # ============================================================

    @mcp.tool(annotations={"readOnlyHint": True})
    async def listar_postagens(
        status: Annotated[str, Field(description="Status das pré-postagens")] = "PREPOSTADO",
        pagina: Annotated[int, Field(ge=0, description="Número da página")] = 0,
        busca: Annotated[str, Field(description="Busca por código de objeto")] = "",
        logistica_reversa: Annotated[bool, Field(description="Filtrar LR")] = False,
    ) -> dict[str, Any]:
        """Lista pré-postagens registradas no painel Correios."""
        result = client.postagem.listar_registrados(
            status=status,
            pagina=pagina,
            busca=busca,
            logistica_reversa=logistica_reversa,
        )
        return result.model_dump()

    @mcp.tool(annotations={"readOnlyHint": True})
    async def buscar_postagem_por_codigo(
        codigo_objeto: Annotated[str, Field(description="Código do objeto (ex: AN656815056BR)")],
    ) -> dict[str, Any]:
        """Busca uma pré-postagem pelo código de objeto."""
        result = client.postagem.buscar_por_codigo_objeto(codigo_objeto)
        return result.model_dump()

    @mcp.tool(annotations={"destructiveHint": False})
    async def criar_postagem(
        remetente_nome: Annotated[str, Field(description="Nome do remetente")],
        remetente_cpf_cnpj: Annotated[str, Field(description="CPF/CNPJ do remetente")],
        remetente_cep: Annotated[str, Field(description="CEP do remetente")],
        remetente_logradouro: Annotated[str, Field(description="Logradouro do remetente")],
        remetente_numero: Annotated[str, Field(description="Número do endereço")],
        remetente_bairro: Annotated[str, Field(description="Bairro")],
        remetente_cidade: Annotated[str, Field(description="Cidade")],
        remetente_uf: Annotated[str, Field(description="UF (sigla)")],
        destinatario_nome: Annotated[str, Field(description="Nome do destinatário")],
        destinatario_cep: Annotated[str, Field(description="CEP do destinatário")],
        destinatario_logradouro: Annotated[str, Field(description="Logradouro")],
        destinatario_numero: Annotated[str, Field(description="Número")],
        destinatario_bairro: Annotated[str, Field(description="Bairro")],
        destinatario_cidade: Annotated[str, Field(description="Cidade")],
        destinatario_uf: Annotated[str, Field(description="UF")],
        codigo_servico: Annotated[str, Field(description="Código do serviço (ex: 03298)")],
        servico: Annotated[str, Field(description="Descrição do serviço (ex: 03298 - PAC CONTRATO AG)")],
        peso_gramas: Annotated[str, Field(description="Peso em gramas")] = "500",
        comprimento_cm: Annotated[str, Field(description="Comprimento em cm")] = "25",
        altura_cm: Annotated[str, Field(description="Altura em cm")] = "12",
        largura_cm: Annotated[str, Field(description="Largura em cm")] = "18",
        item_conteudo: Annotated[str, Field(description="Descricao resumida do conteudo")] = "Produto",
        item_quantidade: Annotated[int, Field(description="Quantidade do item")] = 1,
        item_valor: Annotated[float, Field(description="Valor unitario do item")] = 50.0,
        logistica_reversa: Annotated[bool, Field(description="É logística reversa?")] = False,
    ) -> dict[str, Any]:
        """Cria uma nova pré-postagem (normal ou logística reversa)."""
        from correios_reverso.models import Endereco, PessoaPrePostagem

        req = CriarPrePostagemRequest(
            remetente=PessoaPrePostagem(
                nome=remetente_nome,
                cpfCnpj=remetente_cpf_cnpj,
                endereco=Endereco(
                    cep=remetente_cep,
                    logradouro=remetente_logradouro,
                    numero=remetente_numero,
                    bairro=remetente_bairro,
                    cidade=remetente_cidade,
                    uf=remetente_uf,
                ),
            ),
            destinatario=PessoaPrePostagem(
                nome=destinatario_nome,
                endereco=Endereco(
                    cep=destinatario_cep,
                    logradouro=destinatario_logradouro,
                    numero=destinatario_numero,
                    bairro=destinatario_bairro,
                    cidade=destinatario_cidade,
                    uf=destinatario_uf,
                ),
            ),
            codigoServico=codigo_servico,
            servico=servico,
            pesoInformado=peso_gramas,
            comprimentoInformado=comprimento_cm,
            alturaInformada=altura_cm,
            larguraInformada=largura_cm,
            itensDeclaracaoConteudo=[
                ItemDeclaracaoConteudo(
                    conteudo=item_conteudo,
                    quantidade=item_quantidade,
                    valor=item_valor,
                )
            ],
            logisticaReversa="S" if logistica_reversa else "N",
        )
        return client.postagem.criar(req)

    @mcp.tool(annotations={"readOnlyHint": True})
    async def listar_servicos(
        logistica_reversa: Annotated[bool, Field(description="Listar serviços LR")] = False,
    ) -> list[dict[str, Any]]:
        """Lista serviços disponíveis para pré-postagem."""
        result = client.postagem.listar_servicos(logistica_reversa=logistica_reversa)
        return [s.model_dump() for s in result]

    # ============================================================
    # CANCELAMENTO
    # ============================================================

    @mcp.tool(annotations={"destructiveHint": True})
    async def cancelar_postagem(
        id_prepostagem: Annotated[str, Field(description="ID da pré-postagem")],
    ) -> str:
        """Cancela uma pré-postagem. Operação IRREVERSÍVEL."""
        return client.cancelamento.cancelar(id_prepostagem)

    @mcp.tool(annotations={"readOnlyHint": True})
    async def log_cancelamento(
        id_prepostagem: Annotated[str, Field(description="ID da pré-postagem")],
    ) -> list[dict[str, Any]]:
        """Retorna histórico de cancelamento de uma pré-postagem."""
        return client.cancelamento.log_cancelamento(id_prepostagem)

    # ============================================================
    # DESTINATÁRIOS
    # ============================================================

    @mcp.tool(annotations={"readOnlyHint": True})
    async def listar_destinatarios(
        nome: Annotated[str, Field(description="Filtrar por nome")] = "",
    ) -> dict[str, Any]:
        """Lista destinatários cadastrados."""
        if nome:
            return client.destinatarios.pesquisar_por_nome(nome)
        return client.destinatarios.pesquisar()

    @mcp.tool(annotations={"destructiveHint": False})
    async def criar_destinatario(
        nome: Annotated[str, Field(description="Nome do destinatário")],
        cep: Annotated[str, Field(description="CEP")],
        logradouro: Annotated[str, Field(description="Logradouro")],
        numero: Annotated[str, Field(description="Número")],
        bairro: Annotated[str, Field(description="Bairro")],
        cidade: Annotated[str, Field(description="Cidade")],
        uf: Annotated[str, Field(description="UF")],
        email: Annotated[Optional[str], Field(description="Email")] = None,
    ) -> dict[str, Any]:
        """Cria um novo destinatário."""
        req = DestinatarioRequest(
            nomeDestinatario=nome,
            cepDestinatario=cep,
            logradouroDestinatario=logradouro,
            numeroDestinatario=numero,
            bairroDestinatario=bairro,
            cidadeDestinatario=cidade,
            ufDestinatario=uf,
            emailDestinatario=email or "",
        )
        return client.destinatarios.criar(req)

    @mcp.tool(annotations={"destructiveHint": True})
    async def excluir_destinatario(
        id_destinatario: Annotated[str, Field(description="ID do destinatário")],
    ) -> dict[str, Any]:
        """Exclui um destinatário."""
        client.destinatarios.excluir(id_destinatario)
        return {"ok": True, "id": id_destinatario}

    # ============================================================
    # REMETENTES
    # ============================================================

    @mcp.tool(annotations={"readOnlyHint": True})
    async def listar_remetentes(
        nome: Annotated[str, Field(description="Filtrar por nome")] = "",
    ) -> dict[str, Any]:
        """Lista remetentes cadastrados."""
        return client.remetentes.pesquisar(nome=nome)

    @mcp.tool(annotations={"readOnlyHint": True})
    async def obter_remetente(
        id_remetente: Annotated[str, Field(description="ID do remetente")],
    ) -> dict[str, Any]:
        """Obtém um remetente por ID."""
        return client.remetentes.obter(id_remetente)

    @mcp.tool(annotations={"destructiveHint": False})
    async def criar_remetente(
        nome: Annotated[str, Field(description="Nome do remetente")],
        cep: Annotated[str, Field(description="CEP")],
        logradouro: Annotated[str, Field(description="Logradouro")],
        numero: Annotated[str, Field(description="Número")],
        bairro: Annotated[str, Field(description="Bairro")],
        cidade: Annotated[str, Field(description="Cidade")],
        uf: Annotated[str, Field(description="UF")],
        cpf_cnpj: Annotated[str, Field(description="CPF/CNPJ")],
        email: Annotated[Optional[str], Field(description="Email")] = None,
    ) -> dict[str, Any]:
        """Cria um novo remetente."""
        req = RemetenteRequest(
            nomeRemetente=nome,
            cepRemetente=cep,
            logradouroRemetente=logradouro,
            numeroRemetente=numero,
            bairroRemetente=bairro,
            cidadeRemetente=cidade,
            ufRemetente=uf,
            cpfCnpjRemetente=cpf_cnpj,
            emailRemetente=email or "",
        )
        return client.remetentes.criar(req)

    @mcp.tool(annotations={"destructiveHint": True})
    async def excluir_remetente(
        id_remetente: Annotated[str, Field(description="ID do remetente")],
    ) -> dict[str, Any]:
        """Exclui um remetente."""
        client.remetentes.excluir(id_remetente)
        return {"ok": True, "id": id_remetente}

    # ============================================================
    # ETIQUETAS
    # ============================================================

    @mcp.tool(annotations={"destructiveHint": False})
    async def iniciar_impressao_etiqueta(
        ids_prepostagem: Annotated[list[str], Field(description="IDs das pré-postagens")],
    ) -> dict[str, Any]:
        """Inicia impressão de etiquetas (assíncrono). Retorna ID do recibo."""
        id_recibo = client.etiqueta.iniciar_impressao(ids_prepostagem)
        return {"idRecibo": id_recibo}

    @mcp.tool(annotations={"readOnlyHint": True})
    async def download_etiqueta(
        id_recibo: Annotated[str, Field(description="ID do recibo de impressão")],
    ) -> str:
        """Download do PDF da etiqueta em base64."""
        pdf_bytes = client.etiqueta.download_rotulo(id_recibo)
        return base64.b64encode(pdf_bytes).decode("ascii")

    @mcp.tool(annotations={"readOnlyHint": True})
    async def listar_processamentos_etiqueta() -> list[dict[str, Any]]:
        """Lista processamentos de etiquetas."""
        result = client.etiqueta.listar_processamentos()
        return [p.model_dump() for p in result.itens]

    # ============================================================
    # AUXILIARES
    # ============================================================

    @mcp.tool(annotations={"readOnlyHint": True})
    async def consultar_cep(
        cep: Annotated[str, Field(description="CEP para consulta")],
    ) -> dict[str, Any]:
        """Consulta endereço por CEP."""
        return client.auxiliares.consultar_cep(cep)

    @mcp.tool(annotations={"readOnlyHint": True})
    async def listar_cartoes_postagem() -> dict[str, Any]:
        """Lista cartões de postagem do contrato."""
        result = client.auxiliares.listar_cartoes_postagem()
        return result.model_dump()

    @mcp.tool(annotations={"readOnlyHint": True})
    async def listar_embalagens() -> dict[str, Any]:
        """Lista embalagens disponíveis."""
        result = client.auxiliares.listar_embalagens()
        return result.model_dump()

    return mcp

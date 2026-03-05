"""Modelos Pydantic baseados nos contratos reais observados na plataforma.

Este modulo define todos os modelos de dados usados para comunicacao
com a API dos Correios, usando Pydantic v2 para validacao.

Categorias de modelos:
    - Endereco: Dados de endereco
    - PessoaPrePostagem: Remetente/Destinatario
    - ItemDeclaracaoConteudo: Itens da declaracao de conteudo
    - CriarPrePostagemRequest: Request para criar pre-postagem
    - PrePostagemItem/Response: Response de pre-postagens
    - DestinatarioRequest: Request para CRUD de destinatarios
    - RemetenteRequest: Request para CRUD de remetentes
    - PageInfo: Informacoes de paginacao

Example:
    >>> from correios_reverso.models import (
    ...     CriarPrePostagemRequest,
    ...     PessoaPrePostagem,
    ...     Endereco,
    ... )
    >>>
    >>> req = CriarPrePostagemRequest(
    ...     remetente=PessoaPrePostagem(
    ...         nome="EMPRESA LTDA",
    ...         cpfCnpj="12345678000199",
    ...         endereco=Endereco(
    ...             cep="01001000",
    ...             logradouro="Rua Exemplo",
    ...             numero="1190",
    ...             bairro="Centro",
    ...             cidade="Sao Paulo",
    ...             uf="RS",
    ...         ),
    ...     ),
    ...     destinatario=...,
    ...     codigoServico="03298",
    ...     servico="03298 - PAC CONTRATO AG",
    ... )
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Modelos compartilhados
# ---------------------------------------------------------------------------

class Endereco(BaseModel):
    cep: str
    logradouro: str
    numero: str
    complemento: str = ""
    bairro: str
    cidade: str
    uf: str
    cepFormatado: Optional[str] = None


class PessoaPrePostagem(BaseModel):
    """Pessoa (remetente ou destinatário) dentro de uma pré-postagem."""
    codigo: Optional[str] = None
    indicadorMalote: str = "N"
    dddTelefone: str = ""
    telefone: str = ""
    dddCelular: str = ""
    celular: str = ""
    email: str = ""
    cpfCnpj: Optional[str] = None
    documentoEstrangeiro: Optional[str] = None
    nome: str = ""
    endereco: Optional[Endereco] = None


# ---------------------------------------------------------------------------
# Declaração de conteúdo e serviços adicionais
# ---------------------------------------------------------------------------

class ItemDeclaracaoConteudo(BaseModel):
    conteudo: str
    quantidade: int
    valor: float


class ServicoAdicionalItem(BaseModel):
    codigoServicoAdicional: str
    nomeServicoAdicional: Optional[str] = None
    siglaServicoAdicional: Optional[str] = None
    valorDeclarado: Optional[float] = None
    orientacaoEntregaVizinho: Optional[str] = None
    tipoChecklist: Optional[str] = None
    subitensCheckList: Optional[list] = None


# ---------------------------------------------------------------------------
# Paginação genérica
# ---------------------------------------------------------------------------

class PageInfo(BaseModel):
    number: int = 0
    size: int = 0
    totalPages: int = 0
    numberElements: int = 0
    count: int = 0
    next: bool = False
    previous: bool = False
    first: bool = True
    last: bool = True


# ---------------------------------------------------------------------------
# Pré-postagem
# ---------------------------------------------------------------------------

class PrePostagemItem(BaseModel):
    id: str
    codigoObjeto: str = ""
    codigoServico: str = ""
    servico: str = ""
    logisticaReversa: str = "N"
    descStatusAtual: str = ""
    statusAtual: int = 0
    prazoPostagem: str = ""
    dataHora: str = ""
    dataHoraStatusAtual: str = ""
    numeroCartaoPostagem: str = ""
    pesoInformado: str = ""
    alturaInformada: str = ""
    larguraInformada: str = ""
    comprimentoInformado: str = ""
    codigoFormatoObjetoInformado: str = ""
    remetente: Optional[PessoaPrePostagem] = None
    destinatario: Optional[PessoaPrePostagem] = None
    itensDeclaracaoConteudo: list[ItemDeclaracaoConteudo] = []
    listaServicoAdicional: Optional[list[ServicoAdicionalItem]] = None
    dataValidadeLogReversa: Optional[str] = None
    chaveNFe: Optional[str] = None
    tipoRotulo: Optional[str] = None
    solicitarColeta: Optional[str] = None
    codigoObjetoIda: Optional[str] = None


class PrePostagemListResponse(BaseModel):
    itens: list[PrePostagemItem] = []
    page: PageInfo = PageInfo()


class CriarPrePostagemRequest(BaseModel):
    """Body do POST /prepostagem/afaturar — montado pelo frontend."""
    remetente: PessoaPrePostagem
    destinatario: PessoaPrePostagem
    codigoServico: str
    servico: str = ""
    logisticaReversa: str = "N"
    pesoInformado: Optional[str] = None
    alturaInformada: Optional[str] = None
    comprimentoInformado: Optional[str] = None
    diametroInformado: Optional[str] = None
    larguraInformada: Optional[str] = None
    codigoFormatoObjetoInformado: str = "2"
    chaveNFe: Optional[str] = None
    numeroNotaFiscal: Optional[str] = None
    cienteObjetoNaoProibido: int = 1
    rfidObjeto: Optional[str] = None
    observacao: Optional[str] = None
    itensDeclaracaoConteudo: list[ItemDeclaracaoConteudo] = []
    listaServicoAdicional: list[ServicoAdicionalItem] = []
    dataValidadeLogReversa: Optional[str] = None
    dataPrevistaPostagem: Optional[str] = None
    prazoPostagem: Optional[str] = None
    codigoObjetoIda: Optional[str] = None


# ---------------------------------------------------------------------------
# Cadastro: Destinatário
# ---------------------------------------------------------------------------

class DestinatarioRequest(BaseModel):
    """Body para POST /destinatarios/salvarSemCPF e PUT /destinatarios/{id}."""
    nomeDestinatario: str
    cepDestinatario: str
    logradouroDestinatario: str
    numeroDestinatario: str
    complementoDestinatario: str = ""
    bairroDestinatario: str
    cidadeDestinatario: str
    ufDestinatario: str
    cpfCnpjDestinatario: str = ""
    emailDestinatario: str = ""
    telefoneDestinatario: str = ""
    dddTelefoneDestinatario: str = ""
    celularDestinatario: str = ""
    dddCelularDestinatario: str = ""
    codigoDestinatario: str = ""
    indicadorMaloteDestinatario: str = "false"
    indicadorArquivoDestinatario: str = "false"
    celularRem: str = ""
    telefoneRem: str = ""


# ---------------------------------------------------------------------------
# Cadastro: Remetente
# ---------------------------------------------------------------------------

class RemetenteRequest(BaseModel):
    """Body para POST /remetentes e PUT /remetentes/{id}."""
    nomeRemetente: str
    cepRemetente: str
    logradouroRemetente: str
    numeroRemetente: str
    complementoRemetente: str = ""
    bairroRemetente: str
    cidadeRemetente: str
    ufRemetente: str
    cpfCnpjRemetente: str = ""
    documentoEstrangeiroRemetente: str = ""
    emailRemetente: str = ""
    telefoneRemetente: str = ""
    dddTelefoneRemetente: str = ""
    celularRemetente: str = ""
    dddCelularRemetente: str = ""
    codigoRemetente: str = ""
    indicadorMaloteRemetente: str = "false"
    indicadorArquivoRemetente: str = "false"


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

class CartaoPostagem(BaseModel):
    numeroCartao: str
    validade: str = ""
    status: str = ""
    descricaoStatus: str = ""
    contrato: str = ""
    drContrato: int = 0
    cnpj: str = ""
    ativo: bool = True


class CartaoPostagemResponse(BaseModel):
    itens: list[CartaoPostagem] = []
    page: PageInfo = PageInfo()


class Embalagem(BaseModel):
    id: int
    numeroContrato: str = ""
    drContrato: int = 0
    descricao: str = ""
    formatoObjeto: int = 0
    altura: float = 0
    largura: float = 0
    comprimento: float = 0
    diametro: float = 0
    peso: float = 0


class EmbalagemResponse(BaseModel):
    itens: list[Embalagem] = []
    page: PageInfo = PageInfo()


class ServicoDisponivel(BaseModel):
    codigo: str
    descricao: str = ""
    segmento: str = ""
    novoMalote: bool = False
    inDescontoLogisticaReversa: str = ""


class ProcessamentoRotulo(BaseModel):
    numero: str = ""
    idRecibo: str = ""
    idCorreios: str = ""
    nuCartaoPostagem: str = ""
    dataAlteracao: str = ""
    statusProcessamento: str = ""
    erroProcessamento: Optional[str] = None
    url: str = ""


class ProcessamentoRotuloListResponse(BaseModel):
    itens: list[ProcessamentoRotulo] = []
    page: PageInfo = PageInfo()

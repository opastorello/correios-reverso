"""Testes do módulo de postagem."""

from __future__ import annotations

import responses

from correios_reverso.config import Config
from correios_reverso.http_client import HTTPClient
from correios_reverso.models import (
    CriarPrePostagemRequest,
    Endereco,
    PessoaPrePostagem,
)
from correios_reverso.modules.postagem import Postagem


MOCK_REGISTRADOS = {
    "itens": [
        {
            "id": "abc123",
            "codigoObjeto": "AN655590419BR",
            "codigoServico": "03298",
            "servico": "PAC CONTRATO AG",
            "logisticaReversa": "N",
            "descStatusAtual": "PRE-POSTADO",
            "statusAtual": 1,
            "prazoPostagem": "10/03/2026",
            "dataHora": "2026-03-03T10:00:00",
            "dataHoraStatusAtual": "2026-03-03T10:00:00",
            "numeroCartaoPostagem": "0070996598",
            "pesoInformado": "500",
            "alturaInformada": "10",
            "larguraInformada": "15",
            "comprimentoInformado": "20",
            "codigoFormatoObjetoInformado": "1",
            "remetente": {"nome": "REM", "email": "", "cpfCnpj": "111", "endereco": {
                "cep": "01001000", "logradouro": "Rua X", "numero": "1",
                "complemento": "", "bairro": "B", "cidade": "C", "uf": "RS"
            }},
            "destinatario": {"nome": "DEST", "email": "", "cpfCnpj": "222", "endereco": {
                "cep": "01001000", "logradouro": "Rua Y", "numero": "2",
                "complemento": "", "bairro": "B2", "cidade": "SP", "uf": "SP"
            }},
            "itensDeclaracaoConteudo": [],
        }
    ],
    "page": {
        "number": 0, "size": 50, "totalPages": 1,
        "numberElements": 1, "count": 1,
        "next": False, "previous": False, "first": True, "last": True,
    },
}


@responses.activate
def test_listar_registrados(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/prepostagem/afaturar/registrados",
        json=MOCK_REGISTRADOS,
        status=200,
    )
    http = HTTPClient(config)
    postagem = Postagem(http)
    result = postagem.listar_registrados()
    assert len(result.itens) == 1
    assert result.itens[0].codigoObjeto == "AN655590419BR"
    assert result.page.count == 1


@responses.activate
def test_listar_servicos(config: Config):
    mock_servicos = [
        {"codigo": "03298", "descricao": "PAC CONTRATO AG", "segmento": "SEG", "novoMalote": False, "inDescontoLogisticaReversa": "N"},
        {"codigo": "03220", "descricao": "SEDEX CONTRATO AG", "segmento": "SEG", "novoMalote": False, "inDescontoLogisticaReversa": "N"},
    ]
    responses.add(
        responses.GET,
        f"{config.base_url}/prepostagem/afaturar/servicos/semSegmentoNovoMalote",
        json=mock_servicos,
        status=200,
    )
    http = HTTPClient(config)
    postagem = Postagem(http)
    servicos = postagem.listar_servicos()
    assert len(servicos) == 2
    assert servicos[0].codigo == "03298"


@responses.activate
def test_listar_servicos_lr(config: Config):
    mock_servicos = [
        {"codigo": "03301", "descricao": "PAC REVERSO", "segmento": "SEG", "novoMalote": False, "inDescontoLogisticaReversa": "S"},
    ]
    responses.add(
        responses.GET,
        f"{config.base_url}/prepostagem/afaturar/servicos/logisticareversa/semSegmentoNovoMalote",
        json=mock_servicos,
        status=200,
    )
    http = HTTPClient(config)
    postagem = Postagem(http)
    servicos = postagem.listar_servicos(logistica_reversa=True)
    assert len(servicos) == 1
    assert servicos[0].inDescontoLogisticaReversa == "S"


@responses.activate
def test_buscar_por_codigo_objeto(config: Config):
    responses.add(
        responses.GET,
        f"{config.base_url}/prepostagem/afaturar/registrados",
        json=MOCK_REGISTRADOS,
        status=200,
    )
    http = HTTPClient(config)
    postagem = Postagem(http)
    result = postagem.buscar_por_codigo_objeto("AN655590419BR")
    assert result.itens[0].id == "abc123"


@responses.activate
def test_criar_pre_postagem(config: Config):
    """Test criação de pré-postagem."""
    mock_response = {
        "id": "new123",
        "codigoObjeto": "AN123456789BR",
        "status": "SUCESSO",
    }
    responses.add(
        responses.POST,
        f"{config.base_url}/prepostagem/afaturar",
        json=mock_response,
        status=201,
    )

    http = HTTPClient(config)
    postagem = Postagem(http)

    # Criar request de exemplo
    endereco = Endereco(
        cep="01001000",
        logradouro="Rua Teste",
        numero="123",
        complemento="Apto 1",
        bairro="Centro",
        cidade="São Paulo",
        uf="SP",
    )

    remetente = PessoaPrePostagem(
        nome="Teste Remetente",
        cpfCnpj="12345678900",
        endereco=endereco,
    )

    destinatario = PessoaPrePostagem(
        nome="Teste Destinatário",
        cpfCnpj="09876543200",
        endereco=endereco,
    )

    dados = CriarPrePostagemRequest(
        remetente=remetente,
        destinatario=destinatario,
        codigoServico="03298",
        servico="PAC CONTRATO AG",
        pesoInformado="500",
        alturaInformada="10",
        larguraInformada="15",
        comprimentoInformado="20",
    )

    result = postagem.criar(dados)
    assert result["id"] == "new123"
    assert result["codigoObjeto"] == "AN123456789BR"


@responses.activate
def test_criar_pre_postagem_resposta_vazia(config: Config):
    """Test criação de pré-postagem com resposta vazia."""
    responses.add(
        responses.POST,
        f"{config.base_url}/prepostagem/afaturar",
        body="",
        status=201,
    )

    http = HTTPClient(config)
    postagem = Postagem(http)

    endereco = Endereco(
        cep="01001000",
        logradouro="Rua Teste",
        numero="123",
        bairro="Centro",
        cidade="São Paulo",
        uf="SP",
    )

    remetente = PessoaPrePostagem(
        nome="Teste Remetente",
        endereco=endereco,
    )

    destinatario = PessoaPrePostagem(
        nome="Teste Destinatário",
        endereco=endereco,
    )

    dados = CriarPrePostagemRequest(
        remetente=remetente,
        destinatario=destinatario,
        codigoServico="03298",
    )

    result = postagem.criar(dados)
    assert result == {"mensagem": "Incluido com sucesso!"}


@responses.activate
def test_consultar_prazo(config: Config):
    """Test consulta de prazo de entrega."""
    mock_prazo = {
        "prazo": 3,
        "dataEntrega": "10/03/2026",
        "entregaSabado": False,
        "entregaDomiciliar": True,
    }
    responses.add(
        responses.GET,
        f"{config.base_url}/prazos",
        json=mock_prazo,
        status=200,
    )

    http = HTTPClient(config)
    postagem = Postagem(http)

    result = postagem.consultar_prazo(
        codigo_servico="03298",
        cep_origem="01001000",
        cep_destino="01310000",
    )

    assert result["prazo"] == 3
    assert result["dataEntrega"] == "10/03/2026"


@responses.activate
def test_consultar_prazo_com_data_evento(config: Config):
    """Test consulta de prazo com data do evento."""
    mock_prazo = {
        "prazo": 5,
        "dataEntrega": "15/03/2026",
    }
    responses.add(
        responses.GET,
        f"{config.base_url}/prazos",
        json=mock_prazo,
        status=200,
    )

    http = HTTPClient(config)
    postagem = Postagem(http)

    result = postagem.consultar_prazo(
        codigo_servico="03220",
        cep_origem="01001000",
        cep_destino="20040000",
        data_evento="10/03/2026",
    )

    assert result["prazo"] == 5


@responses.activate
def test_listar_servicos_adicionais(config: Config):
    """Test lista de serviços adicionais."""
    mock_servicos = [
        {"codigo": "001", "descricao": "Mão Própria", "preco": "5.00"},
        {"codigo": "002", "descricao": "Aviso de Recebimento", "preco": "2.50"},
    ]
    responses.add(
        responses.GET,
        f"{config.base_url}/rotulo/servicosadicionais/03298",
        json=mock_servicos,
        status=200,
    )

    http = HTTPClient(config)
    postagem = Postagem(http)

    result = postagem.listar_servicos_adicionais("03298")

    assert len(result) == 2
    assert result[0]["codigo"] == "001"
    assert result[1]["descricao"] == "Aviso de Recebimento"

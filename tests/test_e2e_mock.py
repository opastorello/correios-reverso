"""Teste E2E completo com dados mockados — simula fluxo real sem tocar no Correios.

Fluxo: login → listar serviços → criar pré-postagem → gerar etiqueta → cancelar.
"""

from __future__ import annotations

import responses

from correios_reverso.client import CorreiosClient
from correios_reverso.config import Config
from correios_reverso.models import (
    CriarPrePostagemRequest,
    Endereco,
    ItemDeclaracaoConteudo,
    PessoaPrePostagem,
)


CAS_LOGIN_HTML = '<html><form><input name="execution" value="e1s1_FAKE" /></form></html>'
HOME_HTML = "<html><title>Pré-Postagem</title></html>"

MOCK_SERVICOS = [
    {"codigo": "03298", "descricao": "PAC CONTRATO AG", "segmento": "SEG", "novoMalote": False, "inDescontoLogisticaReversa": "N"},
    {"codigo": "03301", "descricao": "PAC REVERSO", "segmento": "SEG", "novoMalote": False, "inDescontoLogisticaReversa": "S"},
]

MOCK_CRIAR_RESP = {"id": "PP_novo_123", "codigoObjeto": "TEST12345BR", "mensagem": "Incluido com sucesso!"}

MOCK_REGISTRADOS = {
    "itens": [{
        "id": "PP_novo_123",
        "codigoObjeto": "TEST12345BR",
        "codigoServico": "03298",
        "servico": "PAC CONTRATO AG",
        "logisticaReversa": "N",
        "descStatusAtual": "PRE-POSTADO",
        "statusAtual": 1,
        "prazoPostagem": "15/03/2026",
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
            "complemento": "", "bairro": "B", "cidade": "C", "uf": "RS"}},
        "destinatario": {"nome": "DEST", "email": "", "cpfCnpj": "222", "endereco": {
            "cep": "01001000", "logradouro": "Rua Y", "numero": "2",
            "complemento": "", "bairro": "B2", "cidade": "SP", "uf": "SP"}},
        "itensDeclaracaoConteudo": [{"conteudo": "Produto teste", "quantidade": 1, "valor": 50.0}],
    }],
    "page": {"number": 0, "size": 50, "totalPages": 1, "numberElements": 1,
             "count": 1, "next": False, "previous": False, "first": True, "last": True},
}


@responses.activate
def test_fluxo_completo_e2e(config: Config):
    """Login → listar serviços → criar pré-postagem → buscar → cancelar."""

    # --- Auth mocks ---
    responses.add(responses.GET, f"{config.cas_url}/login", body=CAS_LOGIN_HTML, status=200)
    responses.add(responses.POST, f"{config.cas_url}/login", body=HOME_HTML, status=200)
    responses.add(responses.GET, f"{config.cas_url}/logout", status=200)

    # --- Serviços ---
    responses.add(
        responses.GET,
        f"{config.base_url}/prepostagem/afaturar/servicos/semSegmentoNovoMalote",
        json=MOCK_SERVICOS,
        status=200,
    )

    # --- Criar pré-postagem (API real retorna 201 Created) ---
    responses.add(
        responses.POST,
        f"{config.base_url}/prepostagem/afaturar",
        json=MOCK_CRIAR_RESP,
        status=201,
    )

    # --- Buscar registrados ---
    responses.add(
        responses.GET,
        f"{config.base_url}/prepostagem/afaturar/registrados",
        json=MOCK_REGISTRADOS,
        status=200,
    )

    # --- Cancelar ---
    responses.add(
        responses.DELETE,
        f"{config.base_url}/prepostagem/afaturar/PP_novo_123",
        body="Cancelado com sucesso",
        status=200,
    )

    # --- Executar fluxo completo ---
    with CorreiosClient(config) as client:
        # 1. Listar serviços
        servicos = client.postagem.listar_servicos()
        assert len(servicos) == 2
        assert servicos[0].codigo == "03298"

        # 2. Criar pré-postagem com dados FICTÍCIOS
        req = CriarPrePostagemRequest(
            remetente=PessoaPrePostagem(
                nome="REMETENTE MOCK",
                cpfCnpj="00000000000",
                email="mock@mock.test",
                endereco=Endereco(
                    cep="01001000", logradouro="Rua Mock", numero="100",
                    bairro="Centro", cidade="Mock City", uf="RS",
                ),
            ),
            destinatario=PessoaPrePostagem(
                nome="DESTINATARIO MOCK",
                cpfCnpj="11111111111",
                email="dest@mock.test",
                endereco=Endereco(
                    cep="01001000", logradouro="Rua Dest", numero="200",
                    bairro="Centro", cidade="Mock SP", uf="SP",
                ),
            ),
            codigoServico="03298",
            servico="03298 - PAC CONTRATO AG",
            pesoInformado="500",
            itensDeclaracaoConteudo=[
                ItemDeclaracaoConteudo(conteudo="Produto teste", quantidade=1, valor=50.0),
            ],
        )
        result = client.postagem.criar(req)
        assert result["codigoObjeto"] == "TEST12345BR"

        # 3. Buscar por código
        registrados = client.postagem.buscar_por_codigo_objeto("TEST12345BR")
        assert registrados.itens[0].id == "PP_novo_123"

        # 4. Cancelar
        msg = client.cancelamento.cancelar("PP_novo_123")
        assert "Cancelado" in msg

    # Client fechou (logout automático)
    assert client.is_authenticated is False

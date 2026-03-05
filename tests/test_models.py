"""Testes de validação dos modelos Pydantic."""

from correios_reverso.models import (  # noqa: PGH003
    CriarPrePostagemRequest,
    DestinatarioRequest,
    Endereco,
    PageInfo,
    PessoaPrePostagem,
    PrePostagemListResponse,
    RemetenteRequest,
    ServicoDisponivel,
)


def test_endereco_basico():
    e = Endereco(cep="01001000", logradouro="Rua Exemplo", numero="1190", bairro="Centro", cidade="Sao Paulo", uf="RS")
    assert e.cep == "01001000"
    assert e.complemento == ""


def test_prepostagem_list_response_vazia():
    r = PrePostagemListResponse(itens=[], page=PageInfo())
    assert r.itens == []
    assert r.page.count == 0


def test_destinatario_request():
    d = DestinatarioRequest(
        nomeDestinatario="TESTE",
        cepDestinatario="01001000",
        logradouroDestinatario="Rua Exemplo",
        numeroDestinatario="1190",
        bairroDestinatario="Centro",
        cidadeDestinatario="Sao Paulo",
        ufDestinatario="RS",
    )
    data = d.model_dump()
    assert data["indicadorMaloteDestinatario"] == "false"
    assert data["indicadorArquivoDestinatario"] == "false"


def test_remetente_request():
    r = RemetenteRequest(
        nomeRemetente="TESTE",
        cepRemetente="95703344",
        logradouroRemetente="Rua Marcos Nardon",
        numeroRemetente="69",
        bairroRemetente="Fenavinho",
        cidadeRemetente="Sao Paulo",
        ufRemetente="RS",
        cpfCnpjRemetente="11144477735",
    )
    data = r.model_dump()
    assert data["indicadorMaloteRemetente"] == "false"


def test_servico_disponivel():
    s = ServicoDisponivel(codigo="03298", descricao="PAC CONTRATO AG", segmento="SEG")
    assert s.novoMalote is False


def test_criar_prepostagem_request_lr():
    req = CriarPrePostagemRequest(
        remetente=PessoaPrePostagem(nome="REM", endereco=Endereco(
            cep="01001000", logradouro="Rua X", numero="1", bairro="B", cidade="C", uf="RS"
        )),
        destinatario=PessoaPrePostagem(nome="DEST", endereco=Endereco(
            cep="01001000", logradouro="Rua Y", numero="2", bairro="B2", cidade="SP", uf="SP"
        )),
        codigoServico="03301",
        logisticaReversa="S",
        pesoInformado="1",
    )
    data = req.model_dump(exclude_none=True)
    assert data["logisticaReversa"] == "S"
    assert data["pesoInformado"] == "1"

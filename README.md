# correios-reverso

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.2.0-green.svg)](https://github.com/opastorello/correios-reverso)

Biblioteca Python para automacao da plataforma Pre-Postagem dos Correios (https://prepostagem.correios.com.br/).

**Versao:** 0.2.0 | **Python:** >=3.9

## Visao Geral

O `correios-reverso` oferece tres formas de integracao:

| Modo | Descricao | Caso de Uso |
|------|-----------|-------------|
| **Biblioteca Python** | Uso programatico direto | Automacao de processos, scripts |
| **API REST FastAPI** | Endpoints HTTP | Integracao com outros sistemas |
| **MCP Server FastMCP** | Tools para assistente de IA | Uso com assistentes de IA |

### Funcionalidades

- Autenticacao CAS SSO automatica
- Criar, listar e cancelar pre-postagens
- Logistica Reversa (domiciliar)
- CRUD de destinatarios e remetentes
- Geracao de etiquetas/rotulos (PDF)
- Consulta de CEP
- Listagem de servicos, cartoes e embalagens
- Retry automatico com backoff exponencial
- Deteccao de sessao expirada

## Instalacao

```bash
# Instalacao basica (apenas biblioteca)
pip install -e "."

# Com suporte a API REST e MCP Server
pip install -e ".[api,dev]"

# Dependencias de desenvolvimento
pip install -e ".[dev]"
```

### Dependencias

**Core:**
- requests >= 2.31.0
- pydantic >= 2.0
- python-dotenv >= 1.0.0

**Opcionais (API/MCP):**
- fastapi >= 0.115.0
- uvicorn[standard] >= 0.34.0
- fastmcp >= 2.14.0

**Desenvolvimento:**
- pytest >= 8.0
- pytest-cov >= 4.0
- responses >= 0.25.0
- httpx >= 0.27.0

## Configuracao

Crie um arquivo `.env` na raiz do projeto:

```env
# Credenciais Correios
CORREIOS_BASE_URL=https://prepostagem.correios.com.br/
CORREIOS_USERNAME=seu_usuario
CORREIOS_PASSWORD=sua_senha
CORREIOS_TIMEOUT=30
CORREIOS_VERIFY_SSL=true
CORREIOS_RETRY_ATTEMPTS=3

# Token de autenticacao da API (opcional, separados por virgula)
API_TOKENS=token1,token2,token3

# CORS (opcional)
CORS_ORIGINS=http://localhost:3000,https://meusite.com
```

## Uso Rapido

### Biblioteca Python

```python
from correios_reverso import CorreiosClient

# Via contexto (login/logout automatico)
with CorreiosClient.from_env() as client:
    # Listar pre-postagens
    postagens = client.postagem.listar_registrados()
    for item in postagens.itens:
        print(f"{item.codigoObjeto} - {item.servico}")

    # Consultar CEP
    endereco = client.auxiliares.consultar_cep("01001000")
    print(endereco)

    # Listar servicos
    servicos = client.postagem.listar_servicos()
    for s in servicos:
        print(f"{s.codigo} - {s.descricao}")
```

### Criar Pre-Postagem

```python
from correios_reverso import CorreiosClient
from correios_reverso.models import (
    CriarPrePostagemRequest,
    PessoaPrePostagem,
    Endereco,
    ItemDeclaracaoConteudo,
)

with CorreiosClient.from_env() as client:
    req = CriarPrePostagemRequest(
        remetente=PessoaPrePostagem(
            nome="EMPRESA LTDA",
            cpfCnpj="12345678000199",
            email="empresa@email.com",
            endereco=Endereco(
                cep="01001000",
                logradouro="Rua Exemplo",
                numero="123",
                bairro="Centro",
                cidade="Sao Paulo",
                uf="SP",
            ),
        ),
        destinatario=PessoaPrePostagem(
            nome="CLIENTE FULANO",
            cpfCnpj="12345678901",
            endereco=Endereco(
                cep="20040000",
                logradouro="Av Exemplo",
                numero="456",
                bairro="Centro",
                cidade="Rio de Janeiro",
                uf="RJ",
            ),
        ),
        codigoServico="03298",
        servico="03298 - PAC CONTRATO AG",
        pesoInformado="500",
        # DIMENSOES OBRIGATORIAS (cm)
        comprimentoInformado="25",
        alturaInformada="12",
        larguraInformada="18",
        itensDeclaracaoConteudo=[
            ItemDeclaracaoConteudo(conteudo="Produto X", quantidade=1, valor=100.0),
        ],
    )
    result = client.postagem.criar(req)
    print(f"Codigo: {result.get('codigoObjeto')}")
```

### Logistica Reversa

```python
from datetime import datetime, timedelta

req = CriarPrePostagemRequest(
    remetente=remetente,
    destinatario=destinatario,
    codigoServico="03301",
    servico="03301 - PAC REVERSO",
    logisticaReversa="S",
    dataValidadeLogReversa=(datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y"),
    pesoInformado="300",
    comprimentoInformado="20",
    alturaInformada="10",
    larguraInformada="15",
    itensDeclaracaoConteudo=[
        ItemDeclaracaoConteudo(conteudo="Produto retorno", quantidade=1, valor=50.0),
    ],
)
result = client.postagem.criar(req)
```

### API REST

```bash
# Iniciar servidor
uvicorn correios_reverso.api.app:app --reload --port 8000

# Documentacao interativa
# http://localhost:8000/docs
# http://localhost:8000/redoc

# Health check
curl http://localhost:8000/health

# Consultar CEP (sem autenticacao)
curl http://localhost:8000/cep/01001000

# Listar servicos (requer token se configurado)
curl -H "Authorization: Bearer seu_token" \
  "http://localhost:8000/postagem/servicos"

# Listar pre-postagens
curl -H "Authorization: Bearer seu_token" \
  "http://localhost:8000/postagem?pagina=0"
```

### MCP Server

Disponivel em `http://localhost:8000/mcp` quando a API esta rodando.

Tools disponiveis (19):

| Tool | Descricao |
|------|-----------|
| `listar_postagens` | Lista pre-postagens |
| `buscar_postagem_por_codigo` | Busca por codigo objeto |
| `criar_postagem` | Cria nova pre-postagem |
| `listar_servicos` | Lista servicos disponiveis |
| `cancelar_postagem` | Cancela pre-postagem |
| `listar_destinatarios` | Lista destinatarios |
| `criar_destinatario` | Cria destinatario |
| `excluir_destinatario` | Exclui destinatario |
| `listar_remetentes` | Lista remetentes |
| `obter_remetente` | Obtem remetente por ID |
| `criar_remetente` | Cria remetente |
| `excluir_remetente` | Exclui remetente |
| `iniciar_impressao_etiqueta` | Inicia impressao |
| `download_etiqueta` | Download PDF base64 |
| `listar_processamentos_etiqueta` | Lista processamentos |
| `consultar_cep` | Consulta CEP |
| `listar_cartoes_postagem` | Lista cartoes |
| `listar_embalagens` | Lista embalagens |
| `log_cancelamento` | Historico de cancelamento |

## Tratamento de Erros

```python
from correios_reverso import (
    CorreiosError,
    AuthenticationError,
    SessionExpiredError,
    APIError,
    RateLimitError,
)

try:
    result = client.postagem.criar(req)
except AuthenticationError as e:
    print(f"Erro de autenticacao: {e}")
except SessionExpiredError as e:
    print(f"Sessao expirou, fazer login novamente: {e}")
except RateLimitError as e:
    print(f"Rate limit atingido: {e}")
except APIError as e:
    print(f"Erro da API ({e.status_code}): {e}")
except CorreiosError as e:
    print(f"Erro generico: {e}")
```

## Codigos de Servico Comuns

| Codigo | Descricao | Tipo |
|--------|-----------|------|
| 03298 | PAC CONTRATO AG | Normal |
| 03220 | SEDEX CONTRATO AG | Normal |
| 03204 | SEDEX HOJE CONTRATO AG | Normal |
| 03301 | PAC REVERSO | Logistica Reversa |
| 03247 | SEDEX REVERSO | Logistica Reversa |
| 03182 | SEDEX 10 REVERSO | Logistica Reversa |

## Testes

```bash
# Executar todos os testes
pytest

# Com cobertura
pytest --cov=correios_reverso --cov-report=term-missing

# Teste especifico
pytest tests/test_postagem.py -v

# Testes lentos (chamadas reais)
pytest -m slow
```

### Cobertura

| Categoria | Testes | Status |
|-----------|--------|--------|
| Biblioteca Python | 35 | OK |
| API REST | 18 | OK |
| E2E Mock | 5 | OK |
| **Total** | **58** | >95% |

## Documentacao Completa

Veja [docs/DOCUMENTACAO_COMPLETA.md](docs/DOCUMENTACAO_COMPLETA.md) para:

- Todos os endpoints da API REST
- Lista completa de tools MCP
- Exemplos detalhados de uso
- Tratamento de erros
- Detalhes tecicos da autenticacao CAS

## Scripts Disponiveis

| Script | Descricao |
|--------|-----------|
| `scripts/main.py` | Demo completo - login + listar recursos |
| `scripts/exemplo_uso_api.py` | Exemplos de uso da biblioteca e API |
| `scripts/teste_completo.py` | Teste abrangente de toda infraestrutura |

## Arquitetura

```
src/correios_reverso/
├── client.py          # CorreiosClient - fachada principal
├── auth.py            # Autenticacao CAS SSO
├── http_client.py     # Cliente HTTP com retry/backoff
├── models.py          # Modelos Pydantic v2
├── exceptions.py      # Hierarquia de excecoes
├── config.py          # Configuracao via env vars
├── modules/           # Modulos de dominio
│   ├── postagem.py
│   ├── destinatarios.py
│   ├── remetentes.py
│   ├── etiqueta.py
│   ├── cancelamento.py
│   └── auxiliares.py
├── api/               # FastAPI REST
│   ├── app.py
│   ├── auth.py
│   ├── deps.py
│   └── routes/
└── mcp/               # FastMCP Server
    └── server.py
```

## Requisitos

- Python 3.9+
- Conta ativa na plataforma Pre-Postagem dos Correios

## Licenca

Este projeto esta licenciado sob a licenca MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para diretrizes de contribuicao.

## Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para o historico de alteracoes.

## Autor

Nicolas Pastorello

## Links

- [Repositorio](https://github.com/opastorello/correios-reverso)
- [Issues](https://github.com/opastorello/correios-reverso/issues)
- [Plataforma Pre-Postagem](https://prepostagem.correios.com.br/)

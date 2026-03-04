# Correios Reverso - Documentacao Completa

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Versao:** 0.2.0 | **Python:** >=3.9

## Visao Geral

O **correios-reverso** e uma biblioteca Python completa para automacao da plataforma Pre-Postagem dos Correios (https://prepostagem.correios.com.br/). O projeto oferece tres formas de integracao:

1. **Biblioteca Python** - Uso programatico direto
2. **API REST FastAPI** - Endpoints HTTP para integracao
3. **MCP Server FastMCP** - Tools para uso com assistente de IA

---

## Arquitetura do Projeto

```
src/correios_reverso/
├── __init__.py              # Exports principais
├── client.py                # CorreiosClient - ponto de entrada
├── config.py                # Configuracao via env vars
├── auth.py                  # Autenticacao CAS SSO
├── http_client.py           # Cliente HTTP com retry/backoff
├── models.py                # Modelos Pydantic v2
├── exceptions.py            # Hierarquia de excecoes
├── modules/
│   ├── postagem.py          # Criar/listar pre-postagens
│   ├── destinatarios.py     # CRUD destinatarios
│   ├── remetentes.py        # CRUD remetentes
│   ├── etiqueta.py          # Geracao de etiquetas/rotulos
│   ├── cancelamento.py      # Cancelar pre-postagens
│   └── auxiliares.py        # CEP, cartoes, embalagens
├── api/                     # FastAPI REST
│   ├── __init__.py
│   ├── app.py               # Aplicacao FastAPI + lifespan
│   ├── auth.py              # Validacao de token Bearer
│   ├── deps.py              # Dependencias (get_client)
│   └── routes/
│       ├── postagem.py
│       ├── destinatarios.py
│       ├── remetentes.py
│       ├── etiqueta.py
│       ├── cancelamento.py
│       └── auxiliares.py
└── mcp/                     # FastMCP Server
    └── server.py            # 19 MCP tools
```

---

## Instalacao

```bash
# Instalacao basica
pip install -e "."

# Com suporte a API/MCP
pip install -e ".[api,dev]"
```

### Dependencias

- Python 3.9+
- requests
- pydantic >= 2.0
- python-dotenv
- FastAPI (opcional, para API)
- uvicorn (opcional, para API)
- FastMCP (opcional, para MCP)

---

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

# Token de autenticacao da API (separados por virgula)
API_TOKENS=token1,token2,token3

# CORS (opcional)
CORS_ORIGINS=http://localhost:3000,https://meusite.com
```

---

## Biblioteca Python

### Cliente Basico

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
                numero="1190",
                bairro="Centro",
                cidade="Sao Paulo",
                uf="RS",
            ),
        ),
        destinatario=PessoaPrePostagem(
            nome="CLIENTE FULANO",
            cpfCnpj="12345678901",
            endereco=Endereco(
                cep="20040000",
                logradouro="Av Exemplo",
                numero="803",
                bairro="Centro",
                cidade="Osasco",
                uf="SP",
            ),
        ),
        codigoServico="03298",
        servico="03298 - PAC CONTRATO AG",
        pesoInformado="500",
        # DIMENSOES OBRIGATORIAS
        comprimentoInformado="25",
        alturaInformada="12",
        larguraInformada="18",
        itensDeclaracaoConteudo=[
            ItemDeclaracaoConteudo(conteudo="Produto X", quantidade=1, valor=100.0),
        ],
    )
    result = client.postagem.criar(req)
    print(f"Criado: {result}")
```

### Logistica Reversa (Domiciliar)

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
        ItemDeclaracaoConteudo(conteudo="Produto teste LR", quantidade=1, valor=50.0),
    ],
)
result = client.postagem.criar(req)
```

### CRUD Destinatarios

```python
from correios_reverso.models import DestinatarioRequest

# Criar
novo = client.destinatarios.criar(DestinatarioRequest(
    nomeDestinatario="CLIENTE NOVO",
    cepDestinatario="01001000",
    logradouroDestinatario="Praca da Se",
    numeroDestinatario="1",
    bairroDestinatario="Se",
    cidadeDestinatario="Sao Paulo",
    ufDestinatario="SP",
))

# Listar
destinatarios = client.destinatarios.pesquisar()

# Excluir
client.destinatarios.excluir(str(novo["id"]))
```

### Cancelar Pre-Postagem

```python
result = client.cancelamento.cancelar("PRabc123...")
print(result)  # "Cancelamento da Prepostagem PRabc123... efetuado com sucesso."
```

### Gerar Etiqueta

```python
# Iniciar impressao
result = client.etiqueta.iniciar_impressao(["PRabc123...", "PRdef456..."])
id_recibo = result["idRecibo"]

# Baixar PDF (base64)
pdf_base64 = client.etiqueta.download_rotulo(id_recibo)

# Listar processamentos
processamentos = client.etiqueta.listar_processamentos()
```

---

## API REST

### Iniciar o Servidor

```bash
# Desenvolvimento
uvicorn correios_reverso.api.app:app --reload --port 8000

# Producao
uvicorn correios_reverso.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Endpoints Disponiveis

| Metodo            | Endpoint                                 | Descricao             |
| ----------------- | ---------------------------------------- | --------------------- |
| **Health**        |                                          |                       |
| GET               | `/health`                                | Status da API         |
| GET               | `/`                                      | Informacoes gerais    |
| **Postagem**      |                                          |                       |
| GET               | `/postagem`                              | Listar pre-postagens  |
| POST              | `/postagem`                              | Criar pre-postagem    |
| GET               | `/postagem/servicos`                     | Listar servicos       |
| GET               | `/postagem/servicos/{codigo}/adicionais` | Servicos adicionais   |
| GET               | `/postagem/{codigo}`                     | Buscar por codigo     |
| **Destinatarios** |                                          |                       |
| GET               | `/destinatarios`                         | Listar destinatarios  |
| POST              | `/destinatarios`                         | Criar destinatario    |
| PUT               | `/destinatarios/{id}`                    | Editar destinatario   |
| DELETE            | `/destinatarios/{id}`                    | Excluir destinatario  |
| **Remetentes**    |                                          |                       |
| GET               | `/remetentes`                            | Listar remetentes     |
| GET               | `/remetentes/{id}`                       | Obter remetente       |
| POST              | `/remetentes`                            | Criar remetente       |
| PUT               | `/remetentes/{id}`                       | Editar remetente      |
| DELETE            | `/remetentes/{id}`                       | Excluir remetente     |
| **Etiqueta**      |                                          |                       |
| POST              | `/etiqueta/imprimir`                     | Iniciar impressao     |
| GET               | `/etiqueta/{id}`                         | Download PDF          |
| GET               | `/etiqueta/processamentos`               | Listar processamentos |
| POST              | `/etiqueta/declaracao-conteudo`          | Gerar declaracao      |
| GET               | `/etiqueta/faixas`                       | Consultar faixas      |
| **Cancelamento**  |                                          |                       |
| DELETE            | `/cancelamento/{id}`                     | Cancelar pre-postagem |
| GET               | `/cancelamento/{id}/log`                 | Historico             |
| **Auxiliares**    |                                          |                       |
| GET               | `/cep/{cep}`                             | Consultar CEP         |
| GET               | `/cartoes`                               | Listar cartoes        |
| GET               | `/embalagens`                            | Listar embalagens     |

### Autenticacao

```bash
# Sem token configurado (dev): permite tudo
# Com token configurado: requer header Authorization

curl -H "Authorization: Bearer seu_token" http://localhost:8000/postagem
```

### Exemplos de Uso

```bash
# Health check
curl http://localhost:8000/health

# Listar servicos
curl -H "Authorization: Bearer token123" \
  "http://localhost:8000/postagem/servicos?logistica_reversa=true"

# Consultar CEP
curl http://localhost:8000/cep/01001000

# Criar pre-postagem
curl -X POST http://localhost:8000/postagem \
  -H "Authorization: Bearer token123" \
  -H "Content-Type: application/json" \
  -d '{
    "remetente": {...},
    "destinatario": {...},
    "codigoServico": "03298",
    "servico": "03298 - PAC CONTRATO AG",
    "pesoInformado": "500",
    "comprimentoInformado": "25",
    "alturaInformada": "12",
    "larguraInformada": "18"
  }'

# Cancelar
curl -X DELETE http://localhost:8000/cancelamento/PRabc123
```

---

## MCP Server (assistente de IA)

### Configurar no assistente de IA

O MCP server esta disponivel em `http://localhost:8000/mcp` quando a API esta rodando.

### Tools Disponiveis (19 tools)

| Tool                             | Descricao                  |
| -------------------------------- | -------------------------- |
| `listar_postagens`               | Lista pre-postagens        |
| `buscar_postagem_por_codigo`     | Busca por codigo objeto    |
| `criar_postagem`                 | Cria nova pre-postagem     |
| `listar_servicos`                | Lista servicos disponiveis |
| `cancelar_postagem`              | Cancela pre-postagem       |
| `log_cancelamento`               | Historico de cancelamento  |
| `listar_destinatarios`           | Lista destinatarios        |
| `criar_destinatario`             | Cria destinatario          |
| `excluir_destinatario`           | Exclui destinatario        |
| `listar_remetentes`              | Lista remetentes           |
| `obter_remetente`                | Obtem remetente por ID     |
| `criar_remetente`                | Cria remetente             |
| `excluir_remetente`              | Exclui remetente           |
| `iniciar_impressao_etiqueta`     | Inicia impressao           |
| `download_etiqueta`              | Download PDF base64        |
| `listar_processamentos_etiqueta` | Lista processamentos       |
| `consultar_cep`                  | Consulta CEP               |
| `listar_cartoes_postagem`        | Lista cartoes              |
| `listar_embalagens`              | Lista embalagens           |

---

## Codigos de Servico Comuns

| Codigo | Descricao              | Tipo              |
| ------ | ---------------------- | ----------------- |
| 03298  | PAC CONTRATO AG        | Normal            |
| 03220  | SEDEX CONTRATO AG      | Normal            |
| 03204  | SEDEX HOJE CONTRATO AG | Normal            |
| 03301  | PAC REVERSO            | Logistica Reversa |
| 03247  | SEDEX REVERSO          | Logistica Reversa |
| 03182  | SEDEX 10 REVERSO       | Logistica Reversa |

---

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

### Mapeamento HTTP

| Exception             | HTTP Status     |
| --------------------- | --------------- |
| `AuthenticationError` | 401             |
| `SessionExpiredError` | 401             |
| `ValidationError`     | 400             |
| `RateLimitError`      | 429             |
| `APIError` (4xx)      | codigo original |
| `APIError` (5xx)      | 502             |
| `CorreiosError`       | 500             |

---

## Testes

### Executar Testes

```bash
# Todos os testes unitarios
pytest

# Com coverage
pytest --cov=correios_reverso --cov-report=term-missing

# Apenas testes da biblioteca
pytest tests/ --ignore=tests/test_api.py

# Apenas testes da API
pytest tests/test_api.py -v
```

### Script de Teste Completo

O projeto inclui um script abrangente para testar toda a infraestrutura:

```bash
# Testar biblioteca Python localmente
python scripts/teste_completo.py --lib

# Testar API REST (requer servidor rodando)
python scripts/teste_completo.py --api

# Testar MCP (requer servidor API rodando)
python scripts/teste_completo.py --mcp

# Testar TUDO
python scripts/teste_completo.py --all

# Com token de autenticacao
python scripts/teste_completo.py --api --token seu_token_aqui
```

### Cobertura de Testes

| Categoria         | Testes | Status |
| ----------------- | ------ | ------ |
| Biblioteca Python | 35     | OK     |
| API REST          | 18     | OK     |
| E2E Mock          | 5      | OK     |
| **TOTAL**         | **58** | OK     |

### Por que somente 2 testes MCP?

O MCP Server usa o protocolo JSON-RPC sobre SSE (Server-Sent Events), não endpoints REST tradicionais. Para testar as ferramentas MCP (invocar tools), e necessário:

um cliente MCP real (como assistente de IA, ou um script de teste Python simples). O script de teste atual:

1. Verifica se o endpoint `/mcp` esta acessivel (retorna 307)
2. Verifica se a lista de tools esta disponivel (GET /mcp/tools retorna 404 porque FastMCP usa JSON-RPC, nao HTTP REST simples. Os testes mais robustos das tools via MCP requerem um cliente MCP real (como o assistente de IA, conectando ao `http://localhost:8000/mcp`).

Para sequivos testes MCP são mais completos, use um cliente MCP real (como o assistente de IA ou o MCP Inspector) ou a script Python que implemente o cliente MCP (por exemplo, com a biblioteca `mcp` ou `fastmcp`):

### O que e testado (Biblioteca Python)

- Conexao e login CAS
- Consulta de CEP (valido e invalido)
- Listar servicos (normais + LR)
- Listar cartoes e embalagens
- Listar pre-postagens
- CRUD remetentes (criar/pesquisar/excluir/verificar)
- CRUD destinatarios (criar/pesquisar/excluir/verificar)
- Criar/cancelar pre-postagem normal
- Criar/cancelar pre-postagem LR

### O que e Testado

**Biblioteca Python:**

- Conexao e login CAS
- Consulta de CEP (valido e invalido)
- Listar servicos (normais + LR)
- Listar cartoes e embalagens
- Listar pre-postagens
- CRUD remetentes (criar/pesquisar/excluir/verificar)
- CRUD destinatarios (criar/pesquisar/excluir/verificar)
- Criar/cancelar pre-postagem normal
- Criar/cancelar pre-postagem LR

**API REST:**

- Health check
- Consulta CEP
- Listar servicos
- Listar pre-postagens
- Cartoes e embalagens
- CRUD destinatarios
- CRUD remetentes
- Criar/cancelar pre-postagem normal
- Criar/cancelar pre-postagem LR

**MCP Server:**

- Endpoint acessivel
- Listar tools

### Limpeza Automatica

O script de teste cria e deleta automaticamente todos os registros criados durante os testes, garantindo que o ambiente permaneca limpo.

---

## Scripts Disponiveis

| Script                       | Descricao                               |
| ---------------------------- | --------------------------------------- |
| `scripts/main.py`            | Demo completo - login + listar recursos |
| `scripts/exemplo_uso_api.py` | Exemplos de uso da biblioteca e API     |
| `scripts/teste_completo.py`  | Teste abrangente de toda infraestrutura |

---

## Detalhes Tecicos Importantes

### Autenticacao CAS SSO

- Login **NAO** e uma API JSON
- Requer parsing de HTML form → POST `application/x-www-form-urlencoded`
- O campo `execution` e dinamico e deve ser extraido a cada tentativa
- Flow envolve multiplos redirects 302
- Cookies criticos: `TGC`, `SESSION`, F5/Dynatrace

### Rate Limiting

- F5 load balancer e Dynatrace presentes
- Serializar operacoes de create/cancel
- Backoff exponencial em 429, 403, 5xx
- User-Agent realista

### Campos Obrigatorios para Pre-Postagem

A API dos Correios agora exige dimensoes do pacote:

```python
CriarPrePostagemRequest(
    # ... demais campos
    pesoInformado="500",
    comprimentoInformado="25",  # OBRIGATORIO
    alturaInformada="12",        # OBRIGATORIO
    larguraInformada="18",       # OBRIGATORIO
)
```

### Ordem das Rotas

Rotas estaticas devem vir **ANTES** de rotas parametrizadas:

```python
# CORRETO
@router.get("/servicos")        # Estatica primeiro
@router.get("/{codigo}")        # Parametrizada depois

# INCORRETO - causa 404
@router.get("/{codigo}")        # Parametrizada primeiro
@router.get("/servicos")        # Estatica nunca alcançada
```

---

## Historico de Desenvolvimento

### v0.1.0: Biblioteca Core (Sprint 2-4)

- Cliente HTTP com retry/backoff
- Autenticacao CAS SSO
- Modulos: postagem, destinatarios, remetentes, etiqueta, cancelamento, auxiliares
- Modelos Pydantic v2
- Excecoes customizadas

### v0.2.0: API REST + MCP (Fase 5)

- FastAPI com lifespan (login on startup, logout on shutdown)
- 25+ endpoints REST
- Autenticacao via token Bearer
- FastMCP server com 19 tools
- Documentacao OpenAPI automatica
- 58 testes unitarios e de integracao

### Correcoes Recentes

1. **Campos de dimensao obrigatorios**: API Correios passou a exigir `comprimentoInformado`, `alturaInformada`, `larguraInformado`

2. **Rotas DELETE retornando dict**: Corrigido para retornar `{"status": "ok", "message": "..."}` em vez de `None`

3. **Parametro inexistente**: Removido `codigo` da rota GET /destinatarios

4. **Compatibilidade Windows**: Substituidos caracteres Unicode por ASCII nos scripts

---

## Manutencao

### Atualizar Credenciais

Edite o arquivo `.env` com novas credenciais quando necessario.

### Debug

```bash
# Ver logs do servidor
uvicorn correios_reverso.api.app:app --reload --log-level debug

# Testar conexao
python -c "from correios_reverso import CorreiosClient; c = CorreiosClient.from_env(); print('OK')"
```

### Problemas Comuns

| Problema             | Solucao                        |
| -------------------- | ------------------------------ |
| Erro 401             | Verificar credenciais no .env  |
| SessionExpired       | Fazer logout/login novamente   |
| Erro 400 comprimento | Adicionar campos de dimensao   |
| Erro 429             | Aguardar ou reduzir frequencia |
| Porta em uso         | Matar processo existente       |

---

## Licenca

Este projeto esta licenciado sob a licenca MIT - veja o arquivo [LICENSE](../LICENSE) para detalhes.

---

## Contato

Para duvidas ou problemas, abra uma issue no repositorio do projeto:

- **Repositorio:** https://github.com/opastorello/correios-reverso
- **Issues:** https://github.com/opastorello/correios-reverso/issues

---

## Links Relacionados

- [README.md](../README.md) - Visao geral do projeto
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Guia de contribuicao
- [CHANGELOG.md](../CHANGELOG.md) - Historico de alteracoes
- [Plataforma Pre-Postagem](https://prepostagem.correios.com.br/)

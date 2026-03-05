# Correios Reverso - Documentacao Completa

Biblioteca Python, API REST (FastAPI) e MCP Server (FastMCP) para automacao da plataforma Pre-Postagem dos Correios.

## Sumario

- Visao Geral
- Instalacao
- Configuracao
- API REST
- MCP Server
- Docker e Docker Compose
- Testes
- Arquitetura
- Erros comuns

## Visao Geral

Formas de uso:

1. Biblioteca Python
2. API REST (FastAPI)
3. MCP Server (FastMCP)

Recursos principais:

- Login CAS SSO
- Criar, listar e cancelar pre-postagens
- Logistica reversa
- CRUD de destinatarios e remetentes
- Etiquetas (impressao e download)
- CEP, cartoes e embalagens

## Instalacao

```bash
# Basico
pip install -e "."

# API + dev
pip install -e ".[api,dev]"
```

## Configuracao

Crie `.env` na raiz:

```env
CORREIOS_BASE_URL=https://prepostagem.correios.com.br/
CORREIOS_USERNAME=seu_usuario
CORREIOS_PASSWORD=sua_senha
CORREIOS_TIMEOUT=30
CORREIOS_VERIFY_SSL=true
CORREIOS_RETRY_ATTEMPTS=3

# Opcional: protege API e MCP
API_TOKENS=meu_token_super_secreto

# Opcional
CORS_ORIGINS=http://localhost:3000,https://meusite.com
```

Regra de token:

- `API_TOKENS` vazio/ausente: acesso liberado (dev)
- `API_TOKENS` definido: enviar `Authorization: Bearer <token>`

## API REST

Subir localmente:

```bash
uvicorn correios_reverso.api.app:app --reload --port 8000
```

Endpoints:

- Base: `http://localhost:8000`
- Health: `GET /health`
- Docs: `GET /docs`
- MCP: `http://localhost:8000/mcp`

Exemplos:

```bash
# Health
curl http://localhost:8000/health

# CEP (com token)
curl -H "Authorization: Bearer seu_token" \
  http://localhost:8000/cep/01001000

# Servicos
curl -H "Authorization: Bearer seu_token" \
  "http://localhost:8000/postagem/servicos"
```

## MCP Server

Endpoint MCP:

- `http://localhost:8000/mcp`

Exemplo com cliente FastMCP:

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp", auth="seu_token") as c:
        tools = await c.list_tools()
        print(len(tools))

asyncio.run(main())
```

Tools disponiveis (19):

- listar_postagens
- buscar_postagem_por_codigo
- criar_postagem
- listar_servicos
- cancelar_postagem
- log_cancelamento
- listar_destinatarios
- criar_destinatario
- excluir_destinatario
- listar_remetentes
- obter_remetente
- criar_remetente
- excluir_remetente
- iniciar_impressao_etiqueta
- download_etiqueta
- listar_processamentos_etiqueta
- consultar_cep
- listar_cartoes_postagem
- listar_embalagens

Configuracao de clientes MCP:

### Claude Desktop

```json
{
  "mcpServers": {
    "correios-reverso": {
      "transport": {
        "type": "http",
        "url": "http://localhost:8000/mcp"
      },
      "headers": {
        "Authorization": "Bearer seu_token"
      }
    }
  }
}
```

### Cursor

```json
{
  "mcpServers": {
    "correios-reverso": {
      "transport": {
        "type": "http",
        "url": "http://localhost:8000/mcp"
      },
      "headers": {
        "Authorization": "Bearer seu_token"
      }
    }
  }
}
```

### Gemini (cliente MCP)

Use o mesmo padrao de endpoint e header `Authorization`.

## Docker e Docker Compose

Arquivos:

- `Dockerfile`
- `docker-compose.yml`

Uso:

```bash
# 1) Preparar .env
cp .env.example .env

# 2) Subir API + MCP
docker compose up -d api mcp

# 3) Health
curl http://localhost:8000/health

# 4) MCP dedicado (opcional)
curl -I http://localhost:8001/mcp
```

Teste completo em compose:

```bash
docker compose --profile test up --build --abort-on-container-exit --exit-code-from testes testes
```

## Testes

### Pytest

```bash
python -m pytest -q
```

### Teste completo da infraestrutura

```bash
# Biblioteca + API + MCP
python scripts/teste_completo.py --all

# Apenas API
python scripts/teste_completo.py --api

# Apenas MCP (inclui fluxo funcional completo das 19 tools)
python scripts/teste_completo.py --mcp
```

## Arquitetura

```text
src/correios_reverso/
|- client.py
|- auth.py
|- http_client.py
|- models.py
|- exceptions.py
|- config.py
|- modules/
|  |- postagem.py
|  |- destinatarios.py
|  |- remetentes.py
|  |- etiqueta.py
|  |- cancelamento.py
|  `- auxiliares.py
|- api/
|  |- app.py
|  |- auth.py
|  |- deps.py
|  `- routes/
`- mcp/
   `- server.py
```

## Erros comuns

- `401 Unauthorized`
  - confira `API_TOKENS` e header `Authorization`
- `SessionExpiredError`
  - refazer login
- `400` em criacao de pre-postagem
  - verificar campos obrigatorios (peso, dimensoes, declaracao de conteudo)
- `429`
  - reduzir taxa de chamadas

## Referencias

- README: ../README.md
- Contribuicao: ../CONTRIBUTING.md
- Changelog: ../CHANGELOG.md
- Plataforma Correios: https://prepostagem.correios.com.br/

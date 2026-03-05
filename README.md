# correios-reverso

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/opastorello/correios-reverso)

Biblioteca Python para automacao da plataforma Pre-Postagem dos Correios.

## Visao Geral

O projeto oferece 3 formas de uso:

- Biblioteca Python
- API REST (FastAPI)
- MCP Server (FastMCP)

Principais recursos:

- Autenticacao CAS SSO
- Criacao, listagem e cancelamento de pre-postagens
- Logistica reversa
- CRUD de destinatarios e remetentes
- Geracao de etiquetas (PDF)
- Consulta de CEP
- Listagem de servicos, cartoes e embalagens

## Instalacao

```bash
# Basico
pip install -e "."

# API + desenvolvimento
pip install -e ".[api,dev]"

# Apenas dev
pip install -e ".[dev]"
```

## Configuracao (.env)

Crie um arquivo `.env` na raiz:

```env
# Credenciais Correios
CORREIOS_BASE_URL=https://prepostagem.correios.com.br/
CORREIOS_USERNAME=seu_usuario
CORREIOS_PASSWORD=sua_senha
CORREIOS_TIMEOUT=30
CORREIOS_VERIFY_SSL=true
CORREIOS_RETRY_ATTEMPTS=3

# Token da API/MCP (opcional)
API_TOKENS=meu_token_super_secreto

# CORS (opcional)
CORS_ORIGINS=http://localhost:3000,https://meusite.com
```

Regra de autenticacao:

- Se `API_TOKENS` estiver vazio/ausente: acesso liberado (modo dev)
- Se `API_TOKENS` estiver definido: use `Authorization: Bearer <token>`

## Quick Start (Local)

```bash
# Subir API
uvicorn correios_reverso.api.app:app --reload --port 8000
```

Endpoints:

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- MCP: `http://localhost:8000/mcp`

## Docker / Compose

```bash
# 1) Prepare .env
cp .env.example .env

# 2) Suba API + MCP
docker compose up -d api mcp

# 3) Health
curl http://localhost:8000/health

# 4) MCP dedicado (opcional)
curl -I http://localhost:8001/mcp
```

Teste funcional completo (biblioteca + API + MCP):

```bash
docker compose --profile test up --build --abort-on-container-exit --exit-code-from testes testes
```

## Uso da API

Exemplos com token:

```bash
# Health e root
curl http://localhost:8000/health
curl http://localhost:8000/

# Consultar CEP
curl -H "Authorization: Bearer seu_token" \
  http://localhost:8000/cep/01001000

# Listar servicos
curl -H "Authorization: Bearer seu_token" \
  "http://localhost:8000/postagem/servicos"

# Listar pre-postagens
curl -H "Authorization: Bearer seu_token" \
  "http://localhost:8000/postagem?pagina=0"
```

## Uso do MCP

Endpoint MCP:

- `http://localhost:8000/mcp`

Exemplo Python com FastMCP Client:

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp", auth="seu_token") as client:
        tools = await client.list_tools()
        print(f"Tools: {len(tools)}")
        cep = await client.call_tool("consultar_cep", {"cep": "01001000"})
        print(cep)

asyncio.run(main())
```

### Configuracao de clientes MCP

Claude Desktop (`claude_desktop_config.json`):

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

Cursor (`.cursor/mcp.json`):

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

Gemini (cliente MCP):

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

## Biblioteca Python (Exemplo)

```python
from correios_reverso import CorreiosClient

with CorreiosClient.from_env() as client:
    endereco = client.auxiliares.consultar_cep("01001000")
    print(endereco)

    servicos = client.postagem.listar_servicos()
    print(len(servicos))
```

## Tools MCP Disponiveis (19)

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

## Testes

```bash
# Unitarios / integracao local (mock)
python -m pytest -q

# Teste completo da infraestrutura
python scripts/teste_completo.py --all

# Apenas API
python scripts/teste_completo.py --api

# Apenas MCP (inclui teste funcional das 19 tools)
python scripts/teste_completo.py --mcp
```

## Scripts

- `scripts/main.py`: demo rapido
- `scripts/exemplo_uso_api.py`: exemplos de uso
- `scripts/teste_completo.py`: teste completo (LIB + API + MCP)

## Estrutura

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

## Requisitos

- Python 3.9+
- Conta ativa na plataforma Pre-Postagem dos Correios

## Licenca

MIT. Veja [LICENSE](LICENSE).

## Contribuicao

Veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Changelog

Veja [CHANGELOG.md](CHANGELOG.md).

## Links

- Repositorio: https://github.com/opastorello/correios-reverso
- Issues: https://github.com/opastorello/correios-reverso/issues
- Plataforma Correios: https://prepostagem.correios.com.br/

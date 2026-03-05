# Changelog

Todas as alteracoes notaveis neste projeto serao documentadas neste arquivo.

O formato e baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semantico](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2026-03-05

### Adicionado

- Dockerizacao oficial do projeto com:
  - `Dockerfile`
  - `.dockerignore`
  - `docker-compose.yml` (servico API e perfil de testes)
- Documentacao atualizada no `README.md` com:
  - setup local e Docker/Compose
  - uso de token para API e MCP
  - exemplos de integracao para Claude Desktop, Cursor e Gemini
- Teste funcional completo de MCP integrado ao `scripts/teste_completo.py --mcp`
  - valida as 19 tools do MCP com fluxo real

### Alterado

- Versao de release para `1.0.0` em:
  - `pyproject.toml`
  - metadata da API FastAPI (`src/correios_reverso/api/app.py`)
  - badge de versao no `README.md`
- Endpoint MCP HTTP estabilizado em `/mcp` para uso por clientes externos e Docker

### Corrigido

- Handler global de excecoes HTTP da API para retornar `JSONResponse` com status correto
- Lifespan do MCP (FastMCP 3.x) para evitar erro de session manager em transporte HTTP
- Retornos e payloads das tools MCP para compatibilidade de schema e validacao
- Normalizacao de tipos em processamentos de etiqueta (`numero` como string)

## [0.2.0] - 2025-03-04

### Adicionado

- API REST FastAPI com 25+ endpoints para integracao HTTP
- MCP Server FastMCP com 19 tools para assistente de IA
- Modulos de dominio completos: postagem, destinatarios, remetentes, etiqueta, cancelamento e auxiliares
- Modelos Pydantic v2 para validacao de dados
- Hierarquia de excecoes customizadas
- Cliente HTTP com retry e backoff exponencial
- Suite de testes unitarios e integracao
- Scripts de exemplo e teste abrangente

### Corrigido

- Campos de dimensao obrigatorios em criacao de pre-postagem
- Ajustes em rotas e payloads de CRUD
- Compatibilidade em ambiente Windows

## [0.1.0] - 2025-02-01

### Adicionado

- Versao inicial da biblioteca
- Autenticacao CAS SSO
- Cliente HTTP base com retry
- Modulos iniciais de dominio
- Modelos e excecoes iniciais

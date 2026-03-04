# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [0.2.0] - 2025-03-04

### Adicionado

- **API REST FastAPI** com 25+ endpoints para integração HTTP
  - Autenticação via token Bearer (configurável)
  - Documentação OpenAPI automática (`/docs`, `/redoc`)
  - Lifespan management (login on startup, logout on shutdown)
  - CORS configurável via variável de ambiente

- **MCP Server FastMCP** com 19 tools para assistente de IA
  - Montado em `/mcp` na API REST
  - Tools para todas as operações de postagem, destinatários, remetentes, etiquetas, etc.

- **Módulos de domínio completos**:
  - `postagem`: criar, listar, buscar pré-postagens
  - `destinatarios`: CRUD completo
  - `remetentes`: CRUD completo
  - `etiqueta`: geração e download de etiquetas/rotulos
  - `cancelamento`: cancelar pré-postagens e consultar histórico
  - `auxiliares`: consulta CEP, cartões de postagem, embalagens

- **Modelos Pydantic v2** para validação de dados
  - `CriarPrePostagemRequest`, `PrePostagemItem`, `PrePostagemListResponse`
  - `DestinatarioRequest`, `RemetenteRequest`
  - `Endereco`, `PessoaPrePostagem`
  - Modelos de paginação (`PageInfo`)

- **Hierarquia de exceções**:
  - `CorreiosError` (base)
  - `AuthenticationError`
  - `SessionExpiredError`
  - `APIError`
  - `ValidationError`
  - `RateLimitError`
  - `CancelamentoError`

- **Cliente HTTP robusto**:
  - Retry com backoff exponencial
  - Detecção automática de sessão expirada
  - Rate limit handling
  - Timeouts configuráveis

- **Testes**:
  - 58 testes unitários e de integração
  - Cobertura >95%
  - Marcadores `@pytest.mark.slow` e `@pytest.mark.integration`

- **Scripts de exemplo e teste**:
  - `scripts/main.py`: demo completo
  - `scripts/exemplo_uso_api.py`: exemplos de uso
  - `scripts/teste_completo.py`: teste abrangente da infraestrutura

- **Documentação**:
  - README.md completo
  - DOCUMENTACAO_COMPLETA.md com exemplos detalhados
  - CONTRIBUTING.md com guia de contribuicao

### Corrigido

- Campos de dimensão obrigatórios (`comprimentoInformado`, `alturaInformada`, `larguraInformada`)
- Rotas DELETE retornando dict em vez de None
- Parâmetro inexistente na rota GET /destinatarios
- Compatibilidade Windows (caracteres Unicode em scripts)

## [0.1.0] - 2025-02-XX

### Adicionado

- Versão inicial da biblioteca
- Autenticação CAS SSO
- Cliente HTTP com retry/backoff
- Módulos básicos: postagem, destinatarios, remetentes
- Modelos Pydantic iniciais
- Exceções customizadas

---

## Tipos de Mudanças

- `Adicionado` para novas funcionalidades
- `Alterado` para mudanças em funcionalidades existentes
- `Descontinuado` para funcionalidades que serão removidas
- `Removido` para funcionalidades removidas
- `Corrigido` para correções de bugs
- `Segurança` para vulnerabilidades corrigidas

# Contribuindo para o correios-reverso

Obrigado pelo interesse em contribuir com este projeto! Este documento fornece diretrizes para contribuições.

## Sumário

- [Código de Conduta](#código-de-conduta)
- [Como Posso Contribuir?](#como-posso-contribuir)
- [Configuração do Ambiente de Desenvolvimento](#configuração-do-ambiente-de-desenvolvimento)
- [Padrões de Código](#padrões-de-código)
- [Commits](#commits)
- [Pull Requests](#pull-requests)
- [Testes](#testes)

---

## Código de Conduta

Este projeto segue o código de conduta [Contributor Covenant](https://www.contributor-covenant.org/). Ao participar, você concorda em manter um ambiente respeitoso e inclusivo.

---

## Como Posso Contribuir?

### Reportando Bugs

1. Verifique se o bug já foi reportado nas [Issues](https://github.com/Nicolas Pastorello/correios-reverso/issues)
2. Se não, crie uma nova issue incluindo:
   - Descrição clara do problema
   - Passos para reproduzir
   - Comportamento esperado vs. observado
   - Versão do Python e do pacote
   - Logs ou mensagens de erro relevantes

### Sugerindo Melhorias

1. Abra uma issue com a tag `enhancement`
2. Descreva a funcionalidade desejada
3. Explique por que seria útil para o projeto

### Submetendo Código

1. Fork o repositório
2. Crie uma branch para sua feature/fix
3. Faça suas alterações
4. Execute os testes
5. Abra um Pull Request

---

## Configuração do Ambiente de Desenvolvimento

### Pré-requisitos

- Python 3.9+
- pip ou uv
- Git

### Instalação

```bash
# Clone o repositório
git clone https://github.com/Nicolas Pastorello/correios-reverso.git
cd correios-reverso

# Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate  # Windows

# Instale em modo de desenvolvimento
pip install -e ".[dev,api]"

# Copie o arquivo de configuração
cp .env.example .env
# Edite .env com suas credenciais dos Correios
```

### Executando Testes

```bash
# Todos os testes
pytest

# Com cobertura
pytest --cov=correios_reverso --cov-report=term-missing

# Testes específicos
pytest tests/test_postagem.py -v

# Testes lentos (requerem credenciais reais)
pytest -m slow
```

### Executando a API

```bash
# Desenvolvimento
uvicorn correios_reverso.api.app:app --reload --port 8000

# Acesse a documentação
# http://localhost:8000/docs
```

---

## Padrões de Código

### Estilo

- Siga [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints em todas as funções públicas
- Docstrings no formato Google/NumPy

### Exemplo de Docstring

```python
def criar(self, dados: CriarPrePostagemRequest) -> dict[str, Any]:
    """Cria uma nova pré-postagem.

    Args:
        dados: Dados da pré-postagem a ser criada.

    Returns:
        Dicionário com os dados da pré-postagem criada, incluindo
        o código do objeto gerado.

    Raises:
        APIError: Se a API dos Correios retornar erro.
        ValidationError: Se os dados forem inválidos.
    """
```

### Estrutura de Módulos

```
src/correios_reverso/
├── client.py          # Fachada principal
├── auth.py            # Autenticação CAS
├── http_client.py     # Cliente HTTP
├── models.py          # Modelos Pydantic
├── exceptions.py      # Exceções
├── config.py          # Configuração
└── modules/           # Módulos de domínio
    ├── postagem.py
    ├── destinatarios.py
    └── ...
```

### Convenções de Nomenclatura

- **Classes**: PascalCase (`CorreiosClient`, `PrePostagemItem`)
- **Funções/Métodos**: snake_case (`listar_registrados`, `criar_postagem`)
- **Variáveis**: snake_case (`codigo_objeto`, `logistica_reversa`)
- **Constantes**: UPPER_SNAKE_CASE (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Atributos privados**: prefixo `_` (`_http`, `_config`)

---

## Commits

### Formato

Use mensagens de commit no formato:

```
tipo(escopo): descrição breve

Corpo opcional com mais detalhes.
```

### Tipos

- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação (não afeta código)
- `refactor`: Refatoração
- `test`: Testes
- `chore`: Tarefas de manutenção

### Exemplos

```
feat(postagem): adicionar suporte a logística reversa domiciliar

Implementa criação de pré-postagens com logística reversa,
incluindo campo dataValidadeLogReversa e filtragem por tipo.
```

```
fix(auth): corrigir detecção de sessão expirada

A detecção agora verifica redirects intermediários para
o CAS login, não apenas a resposta final.
```

---

## Pull Requests

### Checklist

- [ ] Código segue os padrões do projeto
- [ ] Testes passam localmente
- [ ] Novos testes foram adicionados (se aplicável)
- [ ] Documentação foi atualizada (se aplicável)
- [ ] CHANGELOG.md foi atualizado (se aplicável)

### Processo

1. Crie uma branch descritiva: `feat/nova-funcionalidade` ou `fix/correcao-bug`
2. Faça commits atômicos e bem descritos
3. Abra o PR com descrição clara do que foi alterado
4. Aguarde review

---

## Testes

### Estrutura

```
tests/
├── conftest.py        # Fixtures compartilhadas
├── test_client.py     # Testes do cliente principal
├── test_auth.py       # Testes de autenticação
├── test_http_client.py
├── test_models.py
├── test_postagem.py
├── test_destinatarios.py
├── test_remetentes.py
├── test_etiqueta.py
├── test_cancelamento.py
├── test_auxiliares.py
├── test_api.py        # Testes da API REST
└── test_e2e_mock.py   # Testes end-to-end
```

### Padrões de Teste

```python
import pytest
import responses
from correios_reverso.modules.postagem import Postagem


@responses.activate
def test_listar_servicos(http):
    """Testa listagem de serviços disponíveis."""
    responses.add(
        responses.GET,
        "https://prepostagem.correios.com.br/prepostagem/afaturar/servicos/semSegmentoNovoMalote",
        json=[
            {"codigo": "03298", "descricao": "PAC CONTRATO AG"},
            {"codigo": "03220", "descricao": "SEDEX CONTRATO AG"},
        ],
        status=200,
    )

    postagem = Postagem(http)
    result = postagem.listar_servicos()

    assert len(result) == 2
    assert result[0].codigo == "03298"
```

### Marcadores

- `@pytest.mark.slow`: Testes que fazem chamadas reais (requerem credenciais)
- `@pytest.mark.integration`: Testes de integração end-to-end

---

## Dúvidas?

Se tiver dúvidas sobre como contribuir, abra uma issue com a tag `question` ou entre em contato pelo email do mantenedor.

Obrigado por contribuir!

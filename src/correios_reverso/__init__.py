"""correios-reverso: Automacao da plataforma Pre-Postagem dos Correios.

Esta biblioteca oferece tres formas de integracao:

1. **Biblioteca Python** - Uso programatico direto via CorreiosClient
2. **API REST FastAPI** - Endpoints HTTP para integracao externa
3. **MCP Server FastMCP** - Tools para uso com assistente de IA

Exemplo basico:
    >>> from correios_reverso import CorreiosClient
    >>> with CorreiosClient.from_env() as client:
    ...     postagens = client.postagem.listar_registrados()
    ...     endereco = client.auxiliares.consultar_cep("01001000")

Veja tambem:
    - README.md para visao geral
    - docs/DOCUMENTACAO_COMPLETA.md para exemplos detalhados

Versao: 0.2.0
Autor: Nicolas Pastorello
Licenca: MIT
"""

from correios_reverso.client import CorreiosClient
from correios_reverso.exceptions import (
    CorreiosError,
    AuthenticationError,
    SessionExpiredError,
    APIError,
    ValidationError,
    RateLimitError,
    CancelamentoError,
)

__version__ = "0.2.0"
__author__ = "Nicolas Pastorello"
__license__ = "MIT"

__all__ = [
    # Core
    "CorreiosClient",
    # Exceptions
    "CorreiosError",
    "AuthenticationError",
    "SessionExpiredError",
    "APIError",
    "ValidationError",
    "RateLimitError",
    "CancelamentoError",
]

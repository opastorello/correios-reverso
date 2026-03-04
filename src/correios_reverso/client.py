"""CorreiosClient - entry point principal da biblioteca.

Este modulo fornece a classe CorreiosClient, que atua como fachada
para todos os modulos de negocio da biblioteca.

Uso:
    >>> from correios_reverso import CorreiosClient
    >>>
    >>> # Via contexto (recomendado - login/logout automatico)
    >>> with CorreiosClient.from_env() as client:
    ...     servicos = client.postagem.listar_servicos()
    ...     endereco = client.auxiliares.consultar_cep("01001000")
    >>>
    >>> # Manual
    >>> client = CorreiosClient.from_env()
    >>> client.login()
    >>> try:
    ...     servicos = client.postagem.listar_servicos()
    ... finally:
    ...     client.close()

Modulos disponiveis:
    - client.postagem: Criar, listar e buscar pre-postagens
    - client.destinatarios: CRUD de destinatarios
    - client.remetentes: CRUD de remetentes
    - client.etiqueta: Geracao de etiquetas/rotulos
    - client.cancelamento: Cancelar pre-postagens
    - client.auxiliares: CEP, cartoes, embalagens

Veja tambem:
    - correios_reverso.models: Modelos Pydantic para requests
    - correios_reverso.exceptions: Hierarquia de excecoes
"""

from __future__ import annotations

import logging

from correios_reverso.auth import AuthManager
from correios_reverso.config import Config
from correios_reverso.http_client import HTTPClient
from correios_reverso.modules.auxiliares import Auxiliares
from correios_reverso.modules.cancelamento import Cancelamento
from correios_reverso.modules.destinatarios import Destinatarios
from correios_reverso.modules.etiqueta import Etiqueta
from correios_reverso.modules.postagem import Postagem
from correios_reverso.modules.remetentes import Remetentes

logger = logging.getLogger("correios_reverso")


class CorreiosClient:
    """Fachada que agrupa todos os modulos de negocio.

    Esta classe e o ponto de entrada principal da biblioteca. Ela gerencia
    a autenticacao CAS e fornece acesso aos modulos de dominio.

    Attributes:
        config: Configuracao carregada de variaveis de ambiente.
        http: Cliente HTTP com retry/backoff.
        auth: Gerenciador de autenticacao CAS.
        postagem: Modulo de pre-postagens.
        destinatarios: Modulo de destinatarios.
        remetentes: Modulo de remetentes.
        etiqueta: Modulo de etiquetas/rotulos.
        cancelamento: Modulo de cancelamentos.
        auxiliares: Modulo de funcoes auxiliares (CEP, cartoes, embalagens).

    Example:
        >>> with CorreiosClient.from_env() as client:
        ...     # Listar pre-postagens
        ...     postagens = client.postagem.listar_registrados()
        ...     # Consultar CEP
        ...     endereco = client.auxiliares.consultar_cep("01001000")
    """

    def __init__(self, config: Config | None = None):
        self.config = config or Config.from_env()
        self.http = HTTPClient(self.config)
        self.auth = AuthManager(self.http, self.config)

        # Módulos de negócio
        self.destinatarios = Destinatarios(self.http)
        self.remetentes = Remetentes(self.http)
        self.postagem = Postagem(self.http)
        self.etiqueta = Etiqueta(self.http)
        self.cancelamento = Cancelamento(self.http)
        self.auxiliares = Auxiliares(self.http)

    @classmethod
    def from_env(cls) -> CorreiosClient:
        """Cria client a partir de variáveis de ambiente / .env."""
        return cls(Config.from_env())

    def login(self) -> None:
        """Autentica via CAS SSO."""
        self.auth.login()

    @property
    def is_authenticated(self) -> bool:
        return self.auth.is_authenticated

    def close(self) -> None:
        """Logout e fecha sessão HTTP."""
        self.auth.logout()
        self.http.close()

    def __enter__(self) -> CorreiosClient:
        self.login()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

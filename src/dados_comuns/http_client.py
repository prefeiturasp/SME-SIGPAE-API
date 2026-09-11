import httpx
from sme_sidecar_sdk import build_http_client

from .constants import (
    DJANGO_AUTENTICA_CORESSO_API_URL,
    DJANGO_EOL_API_URL,
    DJANGO_EOL_PAPA_API_URL,
    DJANGO_EOL_SGP_API_URL,
    DJANGO_NOVO_SGP_API_URL,
)

_LIMITS = httpx.Limits(
    max_connections=100,
    max_keepalive_connections=50,
    keepalive_expiry=30.0,
)

EOL_CLIENT = build_http_client("eol", base_url=DJANGO_EOL_API_URL, limits=_LIMITS)
EOL_SGP_CLIENT = build_http_client(
    "eol-sgp", base_url=DJANGO_EOL_SGP_API_URL, limits=_LIMITS
)
EOL_PAPA_CLIENT = build_http_client(
    "eol-papa", base_url=DJANGO_EOL_PAPA_API_URL, limits=_LIMITS
)
AUTENTICA_CORESSO_CLIENT = build_http_client(
    "autentica-coresso", base_url=DJANGO_AUTENTICA_CORESSO_API_URL, limits=_LIMITS
)
NOVO_SGP_CLIENT = build_http_client(
    "novo-sgp", base_url=DJANGO_NOVO_SGP_API_URL, limits=_LIMITS
)
GITHUB_CLIENT = build_http_client(
    "github", base_url="https://api.github.com", limits=_LIMITS
)


def executar_chamada(client, method, url, **kwargs):
    """Executa a chamada externa devolvendo a resposta com o status.

    O SDK levanta ``HTTPStatusError`` para respostas 4xx/5xx. Aqui a
    exceção é capturada e a resposta é devolvida, preservando a lógica
    de status já existente nos chamadores.
    """
    try:
        return getattr(client, method)(url, **kwargs)
    except httpx.HTTPStatusError as exc:
        return exc.response

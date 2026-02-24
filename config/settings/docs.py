"""
Configuração Django para geração de documentação com Sphinx.
Substitui banco de dados e cache por backends locais para evitar conexões externas.
"""

from .local import *  # noqa
from .local import env  # noqa

# Forçar leitura do .env desativada no contexto de documentação
READ_DOT_ENV_FILE = False

# Banco de dados em memória — evita tentativas de conexão ao PostgreSQL
# durante a inspeção de querysets feita pelo sphinx.ext.autodoc
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Cache local — evita dependência do Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Desativar django-debug-toolbar (não é necessário para docs)
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]  # noqa
MIDDLEWARE = [m for m in MIDDLEWARE if "debug_toolbar" not in m]  # noqa

# Celery — usar broker fake para não precisar do Redis
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = "memory://"

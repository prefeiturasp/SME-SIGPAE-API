from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env("DJANGO_DEBUG", default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="6fEIQS2aeFhyGongtjqGdLNfjiIhmAdTE8q5UycOPMWbUEDbmiefODftEQBx1mPK",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS", default=["sigpae.sme.prefeitura.sp.gov.br"]
)

READ_DOT_ENV_FILE = env.bool("DJANGO_READ_DOT_ENV_FILE", default=True)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env.local
    env.read_env(str(ROOT_DIR.path(".env")))  # noqa F405

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
del TEMPLATES[0]["OPTIONS"]["loaders"]  # noqa F405
TEMPLATES[0]["APP_DIRS"] = True  # noqa F405
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG  # noqa F405

# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]  # noqa F405
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa F405
    # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
    DEBUG_TOOLBAR_CONFIG = {
        "DISABLE_PANELS": [
            "debug_toolbar.panels.redirects.RedirectsPanel",
        ],
        "SHOW_TEMPLATE_CONTEXT": True,
    }
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1"]

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
if DEBUG:
    INSTALLED_APPS += ["django_extensions"]  # noqa F405

# Your stuff...
# ------------------------------------------------------------------------------
# Para permitir acesso de navegadores sem problema.
CORS_ORIGIN_ALLOW_ALL = True

JWT_AUTH = {
    "JWT_EXPIRATION_DELTA": datetime.timedelta(hours=8),  # noqa
    "JWT_REFRESH_EXPIRATION_DELTA": datetime.timedelta(hours=1),  # noqa
    "JWT_ALLOW_REFRESH": True,
}

# Alterado para rodar a geração de PDF localmente
STATIC_URL = os.path.join(ROOT_DIR, "staticfiles/")  # noqa F405

SPECTACULAR_SETTINGS["SCHEMA_PATH_PREFIX_INSERT"] = ""  # noqa F405

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

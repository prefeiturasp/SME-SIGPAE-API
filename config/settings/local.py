from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env('DJANGO_DEBUG', default=True)
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env('DJANGO_SECRET_KEY', default='6fEIQS2aeFhyGongtjqGdLNfjiIhmAdTE8q5UycOPMWbUEDbmiefODftEQBx1mPK')
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['terceirizadas.sme.prefeitura.sp.gov.br'])

READ_DOT_ENV_FILE = env.bool('DJANGO_READ_DOT_ENV_FILE', default=True)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env.local
    print('Loading local environment...', str(ROOT_DIR.path('.env')))  # noqa F405
    env.read_env(str(ROOT_DIR.path('.env')))  # noqa F405

# CACHES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': ''
    }
}

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG  # noqa F405

# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']  # noqa F405
    # https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']  # noqa F405
    # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
    DEBUG_TOOLBAR_CONFIG = {
        'DISABLE_PANELS': [
            'debug_toolbar.panels.redirects.RedirectsPanel',
        ],
        'SHOW_TEMPLATE_CONTEXT': True,
    }
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ['127.0.0.1', '10.0.2.2']

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
if DEBUG:
    INSTALLED_APPS += ['django_extensions']  # noqa F405

# Your stuff...
# ------------------------------------------------------------------------------
# Para permitir acesso de navegadores sem problema.
CORS_ORIGIN_ALLOW_ALL = True

JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(hours=8),  # noqa
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(hours=1),  # noqa
    'JWT_ALLOW_REFRESH': True,
}

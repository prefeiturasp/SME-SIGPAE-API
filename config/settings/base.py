"""Base settings to build other settings files upon."""

import datetime
import logging.config
import os

import environ
import sentry_sdk
from celery.schedules import crontab
from sentry_sdk.integrations.django import DjangoIntegration

# (sme_terceirizadas/config/settings/base.py - 3 = sme_terceirizadas/)

ROOT_DIR = environ.Path(__file__) - 3
APPS_DIR = ROOT_DIR.path('sme_terceirizadas')

env = environ.Env()

READ_DOT_ENV_FILE = env.bool('DJANGO_READ_DOT_ENV_FILE', default=False)
if READ_DOT_ENV_FILE:
    # OS environment variables take precedence over variables from .env
    env.read_env(str(ROOT_DIR.path('.env')))

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = env.bool('DJANGO_DEBUG', False)
# Local time zone. Choices are
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# though not all of them may be available with every OS.
# In Windows, this must be set to your system time zone.
TIME_ZONE = 'America/Sao_Paulo'
# https://docs.djangoproject.com/en/dev/ref/settings/#language-code
LANGUAGE_CODE = 'pt-BR'
# https://docs.djangoproject.com/en/dev/ref/settings/#site-id
SITE_ID = 1
# https://docs.djangoproject.com/en/dev/ref/settings/#use-i18n
USE_I18N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-l10n
USE_L10N = True
# https://docs.djangoproject.com/en/dev/ref/settings/#use-tz
USE_TZ = False
LOCALE_PATHS = (
    os.path.join(ROOT_DIR, 'locale'),
)
# DATABASES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST'),
        'PORT': env('POSTGRES_PORT'),
    }
}

DATABASES['default']['ATOMIC_REQUESTS'] = True

# URLS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#root-urlconf
ROOT_URLCONF = 'config.urls'
# https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application
WSGI_APPLICATION = 'config.wsgi.application'

# APPS
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    'corsheaders',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'django.contrib.humanize', # Handy template tags
    'django.contrib.admin',
    'django.contrib.postgres'
]
THIRD_PARTY_APPS = [
    'crispy_forms',
    'django_filters',
    'django_prometheus',
    'rest_framework',
    'rest_framework_swagger',
    'rest_framework_xml',
    'rest_framework.authtoken',
    'des',  # for email configuration in database
    'django_xworkflows',
    'simple_email_confirmation',
    'sass_processor',
    'sequences.apps.SequencesConfig',
    'django_celery_beat',
    'multiselectfield'
]
LOCAL_APPS = [
    'sme_terceirizadas.perfil.apps.PerfilConfig',
    'sme_terceirizadas.dados_comuns.apps.DadosComunsConfig',
    'sme_terceirizadas.escola.apps.EscolaConfig',
    'sme_terceirizadas.kit_lanche.apps.KitLancheConfig',
    'sme_terceirizadas.inclusao_alimentacao.apps.InclusaoAlimentacaoConfig',
    'sme_terceirizadas.cardapio.apps.CardapioConfig',
    'sme_terceirizadas.terceirizada.apps.TerceirizadaConfig',
    'sme_terceirizadas.paineis_consolidados.apps.PaineisConsolidadosConfig',
    'sme_terceirizadas.dieta_especial.apps.DietaEspecialConfig',
    'sme_terceirizadas.relatorios.apps.RelatoriosConfig',
    'sme_terceirizadas.produto.apps.ProdutoConfig',
    'sme_terceirizadas.lancamento_inicial.apps.LancamentoInicialConfig',
    'sme_terceirizadas.logistica.apps.LogisticaConfig',
]
# https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# MIGRATIONS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#migration-modules
MIGRATION_MODULES = {
    'sites': 'sme_terceirizadas.contrib.sites.migrations'
}

# AUTHENTICATION
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#authentication-backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-user-model
AUTH_USER_MODEL = 'perfil.Usuario'
# https://docs.djangoproject.com/en/dev/ref/settings/#login-redirect-url
LOGIN_REDIRECT_URL = 'perfil:redirect'
# https://docs.djangoproject.com/en/dev/ref/settings/#login-url
LOGIN_URL = 'account_login'

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = [
    # https://docs.djangoproject.com/en/dev/topics/auth/passwords/#using-argon2-with-django
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# MIDDLEWARE
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#middleware
DEV_MIDDLEWARE = []

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware'
]

# STATIC
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#static-root
STATIC_ROOT = str(ROOT_DIR('staticfiles'))
# https://docs.djangoproject.com/en/dev/ref/settings/#static-url
STATIC_URL = '/django_static/'
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#std:setting-STATICFILES_DIRS
STATICFILES_DIRS = [
    str(APPS_DIR.path('static')),
]
# https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/#staticfiles-finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'sass_processor.finders.CssFinder',
]
# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-root
MEDIA_ROOT = str(APPS_DIR('media'))
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = '/media/'

# TEMPLATES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#templates
TEMPLATES = [
    {
        # https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        'DIRS': [
            str(APPS_DIR.path('templates')),
        ],
        'OPTIONS': {
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            'debug': DEBUG,
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            # https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
# http://django-crispy-forms.readthedocs.io/en/latest/install.html#template-packs
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# FIXTURES
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#fixture-dirs
FIXTURE_DIRS = (
    str(APPS_DIR.path('fixtures')),
)

# SECURITY
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#session-cookie-httponly
SESSION_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#csrf-cookie-httponly
CSRF_COOKIE_HTTPONLY = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secure-browser-xss-filter
SECURE_BROWSER_XSS_FILTER = True
# https://docs.djangoproject.com/en/dev/ref/settings/#x-frame-options
X_FRAME_OPTIONS = 'DENY'

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env('DJANGO_EMAIL_BACKEND', default='des.backends.ConfiguredEmailBackend')
DES_TEST_SUBJECT = 'TESTE'
DES_TEST_TEXT_TEMPLATE = os.path.join(APPS_DIR, 'templates', 'email', 'test_email.txt')

# ADMIN
# ------------------------------------------------------------------------------
# Django Admin URL.
ADMIN_URL = 'admin/'
# https://docs.djangoproject.com/en/dev/ref/settings/#admins
ADMINS = [
    ("""Equipe AMCOM|SME""", 'equipe-amcom|sme@example.com'),
]
# https://docs.djangoproject.com/en/dev/ref/settings/#managers
MANAGERS = ADMINS

# Your stuff...
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    # https://www.django-rest-framework.org/api-guide/settings/
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DATETIME_FORMAT': '%d/%m/%Y %H:%M:%S',
    'DATETIME_INPUT_FORMATS': ['%d/%m/%Y %H:%M:%S', 'iso-8601'],
    'DATE_FORMAT': '%d/%m/%Y',
    'DATE_INPUT_FORMATS': ['%d/%m/%Y', 'iso-8601'],
    'TIME_FORMAT': '%H:%M:%S',
    'TIME_INPUT_FORMATS': ['%H:%M:%S', 'iso-8601'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100
}

SWAGGER_SETTINGS = {
    'LOGIN_URL': 'rest_framework:login',
    'LOGOUT_URL': 'rest_framework:logout',
    'USE_SESSION_AUTH': True,
    'DOC_EXPANSION': 'list',
    'APIS_SORTER': 'alpha',
    'SECURITY_DEFINITIONS': None,
}

JWT_AUTH = {
    # TODO: rever a configuração...
    'JWT_EXPIRATION_DELTA': datetime.timedelta(hours=100),
    'JWT_REFRESH_EXPIRATION_DELTA': datetime.timedelta(hours=100),
    'JWT_ALLOW_REFRESH': True,
}

URL_CONFIGS = {
    # TODO: rever essa logica de link para trabalhar no front, tá dando voltas
    'CONFIRMAR_EMAIL': '/confirmar-email?uuid={uuid}&confirmationKey={confirmation_key}',
    'RECUPERAR_SENHA': '/recuperar-senha?uuid={uuid}&confirmationKey={confirmation_key}',
    'LOGIN_TERCEIRIZADAS': '/login?tab=terceirizadas',
    'API': '/api{uri}'
}

REDIS_URL = env('REDIS_URL')

# CACHES
# ------------------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'{REDIS_URL}/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            # Mimicing memcache behavior.
            # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
            'IGNORE_EXCEPTIONS': True,
        }
    }
}

# http://docs.celeryproject.org/en/v4.3.0/userguide/configuration.html
CELERY_BROKER_URL = f'{REDIS_URL}/1'
CELERY_RESULT_BACKEND = f'{REDIS_URL}/2'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TIMEZONE = TIME_ZONE

CELERY_BEAT_SCHEDULE = {
    'cancela-dietas-ativas-automaticamente': {
        'task': 'sme_terceirizadas.dieta_especial.tasks.cancela_dietas_ativas_automaticamente_task',
        'schedule': crontab(hour='8-17', minute='*/5')
    },
    'atualiza-totais-das-escolas': {
        'task': 'sme_terceirizadas.escola.tasks.atualiza_total_alunos_escolas',
        'schedule': crontab(hour=0, minute=0)
    },
    'atualiza-dados-das-escolas': {
        'task': 'sme_terceirizadas.escola.tasks.atualiza_dados_escolas',
        'schedule': crontab(hour=0, minute=30)
    },
    'ativa-desativa-vinculos-alimentacao': {
        'task': 'sme_terceirizadas.cardapio.tasks.ativa_desativa_vinculos_alimentacao_com_periodo_escolar_e_tipo_unidade_escolar',  # noqa E501
        'schedule': crontab(hour=1, minute=0)
    },
    'termina-dietas-especiais': {
        'task': 'sme_terceirizadas.dieta_especial.tasks.processa_dietas_especiais_task',
        'schedule': crontab(hour=1, minute=30)
    },
    'atualiza-alunos-escolas': {
        'task': 'sme_terceirizadas.escola.tasks.atualiza_alunos_escolas',
        'schedule': crontab(hour=2, minute=0)
    }
}

# reset password
PASSWORD_RESET_TIMEOUT_DAYS = 1

sentry_sdk.init(
    dsn=env('SENTRY_URL'),
    integrations=[DjangoIntegration()]
)

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': 'terceirizadas.log'
        }
    },
    'loggers': {
        'sigpae': {
            'level': 'DEBUG',
            'handlers': [
                'console'
            ],
        }
    }
})

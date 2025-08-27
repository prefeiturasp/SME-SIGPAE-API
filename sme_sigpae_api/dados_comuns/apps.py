import importlib

from django.apps import AppConfig


class DadosComunsConfig(AppConfig):
    name = "sme_sigpae_api.dados_comuns"

    def ready(self):
        importlib.import_module("sme_sigpae_api.dados_comuns.signals")

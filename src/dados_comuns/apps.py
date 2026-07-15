import importlib

from django.apps import AppConfig


class DadosComunsConfig(AppConfig):
    name = "src.dados_comuns"

    def ready(self):
        importlib.import_module("src.dados_comuns.signals")

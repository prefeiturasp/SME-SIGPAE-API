import importlib

from django.apps import AppConfig


class EscolaConfig(AppConfig):
    name = "src.escola"

    def import_models(self):
        super().import_models()
        importlib.import_module("src.escola.dias_letivos.models")
